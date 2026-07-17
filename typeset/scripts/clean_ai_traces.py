# -*- coding: utf-8 -*-
"""
clean_ai_traces.py — 이수미 책 공용 AI 흔적(금지 은유어·띄어쓴 엠대시) 일괄 정리 도구.

왜 이 도구인가: 매번 일회용 치환 스크립트를 만들었다 지우면 일관성이 깨지고(넣었다 뺐다),
재빌드 때 회귀한다. 이 한 파일이 단일 진실 도구다. hwpx와 md 모두 처리한다.

원칙(안전):
- hwpx는 Contents/section0.xml 의 <hp:t> 텍스트만 치환. header.xml(폰트·스타일)·BinData(그림)·
  content.hpf·표는 바이트 그대로 보존. mimetype STORED 첫 항목 유지. 마크다운 재빌드 안 함.
- 곡선따옴표(" " ' ')는 건드리지 않는다(한글 문서엔 자연스러움 — 사용자 결정).
- 맥락에 따라 답이 갈리는 단어(관문·받친다·흐른다·꿰·관통)는 검증된 구절만 자동 치환하고,
  남는 것은 사람이 보도록 보고만 한다(틀린 치환 강요 금지).

- 이수미 고유 은유어 외에, 흔한 AI 티 표현(오늘 우리가·산출물·결과물·시사하는 바·결론적으로 등)도
  보고만 한다(REPORT_RE). 맥락 의존이라 자동치환은 안 하고 dry-run 보고에 함께 띄운다.
  목록 출처: imnotai(https://github.com/sumilee-pcu/imnotai)에서 책 맥락에 맞는 것만 추렸다.

사용:
  python clean_ai_traces.py <file.hwpx | file.md>            # dry-run: 바뀔 것 + 남는 것(은유어+AI티) 보고
  python clean_ai_traces.py <file.hwpx | file.md> --apply    # 백업 후 적용(자동치환 대상만)
"""
import sys, os, re, io, zipfile, shutil

# ── TIER 1: 안전한 전역 치환 ───────────────────────────────
GLOBAL = [('출발점', '시작점'), ('여정', '과정')]
GIDUNG = [('기둥이', '요소가'), ('기둥을', '요소를'), ('기둥으로', '요소로'),
          ('기둥은', '요소는'), ('기둥', '요소')]
CHUKCHU = [('척추가 되는', '중심이 되는'), ('척추로', '중심으로'),
           ('척추를', '중심을'), ('척추', '중심')]

# ── TIER 2: 맥락별 검증된 구절(확장 가능) ──────────────────
PHRASE = [
    # 관통
    ('이 책을 관통하는 멘탈 모델', '이 책 전체에서 쓰는 멘탈 모델'),
    ('이 책 전체를 관통한다', '이 책 전체에서 거듭 다룬다'),
    ('책의 나머지를 관통하는 예제', '책의 나머지에 이어지는 예제'),
    # 흐른다(서술)
    ('각 장은 같은 리듬으로 흐른다. 개념을 세우고, 프롬프트와 결과로 보이고, 함정을 짚는 순으로 흐른다.',
     '각 장은 같은 순서를 따른다. 개념을 세우고, 프롬프트와 결과로 보이고, 함정을 짚는 순서다.'),
    ('작업은 다음처럼 흐른다.', '작업은 다음처럼 이어진다.'),
    ('전체 사이클은 다섯 단계로 흐른다.', '전체 사이클은 다섯 단계로 이어진다.'),
    # 관문
    ('감별의 첫 관문이 된다', '감별의 첫 단계가 된다'),
    ('관문이 제대로 서 있는지만', '검사가 제대로 서 있는지만'),
    ('승인 관문을 두는 것이 좋다', '승인 단계를 두는 것이 좋다'),
    ('관문으로 작동하는 Plan', '검사로 작동하는 Plan'),
    ('정해진 관문을 거치는', '정해진 검사를 거치는'),
    ('승인 관문은 더 단단히', '승인 단계는 더 단단히'),
    ('마지막 관문이다', '마지막 점검이다'),
    ('통과해야 할 관문', '통과해야 할 기준'),
    # 받친다/받치는(지탱 은유)
    ('테스트로 받친다', '테스트로 확인한다'),
    ('이 단계를 받친다', '이 단계를 지켜 준다'),
    ('정리로 받친다', '정리로 지킨다'),
    ('안정적으로 일하도록 받치는', '안정적으로 일하도록 감싸는'),
    ('틀로 받치는', '틀로 잡는'),
    # 꿰
    ('하나의 줄로 꿰어 놓는다', '하나로 이어 놓는다'),
    ('한 줄로 꿰는 일이다', '하나로 잇는 일이다'),
    ('한 줄로 꿰어', '하나로 이어'),
    # 뿌리(원인 은유)
    ('안티패턴의 뿌리는', '안티패턴의 원인은'),
    ('함정들의 뿌리는', '함정들의 원인은'),
    # 쥐다(손에 쥐는 은유)
    ('위임할 것과 쥐고 있을 것', '무엇을 맡기고 무엇을 사람이 정할지'),
]
# 코드 주석 안 엠대시는 쉼표(콜론 아님)
CODE_EMDASH = [('(객체) — name과 email', '(객체), name과 email')]

# ── TIER 3: 남으면 사람이 보도록 보고만 하는 스템(이수미 고유 은유어) ──
STEMS = ['관통', '쥐고', '쥔', '척추', '기둥', '관문', '받치', '받쳐', '떠받',
         '꿰', '흐른다', '뿌리', '여정', '출발점']

# ── TIER 3b: 흔한 AI 티 표현(맥락 의존 → 보고만, 자동치환 안 함) ──
# 출처: imnotai(github.com/sumilee-pcu/imnotai)에서 책 본문 맥락에 맞는 고신뢰 항목만 추림.
# (라벨, 정규식). 오탐 적은 것만 — 일반 부사 매우/다양한 등은 일부러 제외.
REPORT_RE = [
    # 자기 지칭 — 부·장 번호로 구체 지칭할 것 (2026-07 AI영상분석 시안에서 금지)
    ('이 책 자기지칭', r'이\s*책|책\s*전체'),
    # 프레젠테이션·마케팅 호명/티저 (SKILL.md 금지)
    ('오늘 우리가', r'오늘\s*우리(?:가|는)'),
    ('우리가 함께', r'우리가\s*함께'),
    ('이 한 문장이/줄이', r'이\s*한\s*(?:문장|줄|마디)'),
    ('~의 비밀', r'[가-힣]{2,}의\s*비밀'),
    # AI가 즐겨 쓰는 추상 명사
    ('산출물', r'산출물'),
    ('결과물', r'결과물'),
    # 번역투·피동·클리셰
    ('~에 있어서', r'에\s*있어서?'),
    ('되어진다(이중 피동)', r'되어\s*지'),
    ('시사하는 바', r'시사하는\s*바'),
    ('결론적으로', r'결론적으로'),
    ('이러한 맥락에서', r'이러한\s*맥락에서'),
    ('주목할 만하다', r'주목할\s*만'),
    ('살펴보도록 하겠습니다', r'살펴보도록\s*하겠습니다'),
]


def transform(text):
    """text(본문 문자열)에 모든 치환 적용. (new_text, n_changes) 반환."""
    before = text
    for old, new in CODE_EMDASH:
        text = text.replace(old, new)
    for old, new in PHRASE:
        text = text.replace(old, new)
    text = text.replace(' — ', ': ')          # 남은 띄어쓴 엠대시 → 콜론
    for old, new in CHUKCHU:
        text = text.replace(old, new)
    for old, new in GIDUNG:
        text = text.replace(old, new)
    for old, new in GLOBAL:
        text = text.replace(old, new)
    return text, (before != text)


def remaining(visible):
    """치환 후 남은 은유어 스템/엠대시(metaphor)와 흔한 AI 티 표현(ai)을 맥락과 함께 반환."""
    metaphor, ai = [], []
    for s in STEMS + [' — ']:
        for m in re.finditer(re.escape(s), visible):
            ctx = visible[max(0, m.start() - 28):m.start() + 28].replace('\n', ' ')
            metaphor.append((s, ctx))
    for label, rx in REPORT_RE:
        for m in re.finditer(rx, visible):
            ctx = visible[max(0, m.start() - 28):m.start() + 28].replace('\n', ' ')
            ai.append((label, ctx))
    return metaphor, ai


def visible_text_hwpx(section_xml):
    t = ''.join(re.findall(r'<hp:t>(.*?)</hp:t>', section_xml, re.S))
    return t.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')


def run(path, apply):
    is_hwpx = path.lower().endswith('.hwpx')
    if is_hwpx:
        zin = zipfile.ZipFile(path, 'r'); infos = zin.infolist()
        data = {i.filename: zin.read(i.filename) for i in infos}; zin.close()
        sec = 'Contents/section0.xml'
        raw = data[sec].decode('utf-8')
        new_raw, changed = transform(raw)
        rem, ai = remaining(visible_text_hwpx(new_raw))
    else:
        raw = open(path, encoding='utf-8').read()
        new_raw, changed = transform(raw)
        rem, ai = remaining(new_raw)

    print(f'[{os.path.basename(path)}] changed={changed}')
    if rem:
        print(f'  ⚠ 남은 은유어 {len(rem)}건 (수동 검토 — PHRASE에 구절 추가 후 재실행):')
        for s, ctx in rem:
            print(f'    [{s!r}] ...{ctx}...')
    else:
        print('  ✓ 금지 은유어 0건')
    if ai:
        print(f'  · 흔한 AI 티 표현 {len(ai)}건 (보고만 — 자동치환 안 함, 사람이 윤문):')
        for label, ctx in ai:
            print(f'    [{label}] ...{ctx}...')

    if not apply:
        print('  (dry-run. 적용하려면 --apply)')
        return 0 if not rem else 2
    if rem:
        print('  ✗ 남은 은유어가 있어 저장 안 함. PHRASE 보강 후 다시 --apply.')
        return 2
    if not changed:
        print('  변경 없음, 저장 생략.')
        return 0
    # 백업
    bdir = os.path.join(os.path.dirname(path) or '.', '_backup')
    os.makedirs(bdir, exist_ok=True)
    shutil.copy2(path, os.path.join(bdir, os.path.basename(path) + '.preclean'))
    if is_hwpx:
        data[sec] = new_raw.encode('utf-8')
        tmp = path + '.tmp'
        zo = zipfile.ZipFile(tmp, 'w')
        for i in sorted(infos, key=lambda i: 0 if i.filename == 'mimetype' else 1):
            zi = zipfile.ZipInfo(i.filename, date_time=i.date_time)
            zi.compress_type = zipfile.ZIP_STORED if i.filename == 'mimetype' else i.compress_type
            zi.external_attr = i.external_attr; zi.internal_attr = i.internal_attr
            zi.create_system = i.create_system
            zo.writestr(zi, data[i.filename])
        zo.close(); os.replace(tmp, path)
    else:
        open(path, 'w', encoding='utf-8').write(new_raw)
    print('  ✓ 적용 완료(백업: _backup/*.preclean)')
    return 0


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    apply = '--apply' in sys.argv[2:]
    sys.exit(run(sys.argv[1], apply))
