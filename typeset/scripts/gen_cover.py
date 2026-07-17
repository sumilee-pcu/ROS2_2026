# -*- coding: utf-8 -*-
"""파라메트릭 앞표지 생성기 — 이수미 시리즈 표지 디자인(네이비+골드).
cover_spec.json 하나로 판형+도련 300DPI 인쇄용 앞표지를 렌더링한다.
AI 이미지 생성과 달리 판형 비율·도련·해상도가 처음부터 정확해 부크크 입고 규격을 바로 만족.

사용: python gen_cover.py <cover_spec.json> [출력접두어]
스펙 템플릿: assets/cover_spec.template.json (블록체인 실물 값. format.trim_mm으로 B5/A5 전환)
출력: <접두어>_front_300dpi.png (도련 포함, spec 폴더에 저장), <접두어>_preview.png (적색선=재단선)
책등·날개: 업체 의뢰 — 쪽수·판형 스펙만 전달 (부크크 표지 레이아웃이 책등 폭 산출)
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

sys.stdout.reconfigure(encoding='utf-8')

FONT_DIRS = [
    os.path.expandvars(r"%LOCALAPPDATA%/Microsoft/Windows/Fonts"),
    r"C:/Windows/Fonts",
    os.path.expanduser("~/Library/Fonts"),   # Mac 이식 대비
    "/Library/Fonts", "/System/Library/Fonts",
]
# 지정 폰트가 없는 환경용 대체 사슬(굵은 순) — 경고 후 계속 진행
FONT_FALLBACKS = ["GmarketSansTTFBold.ttf", "malgunbd.ttf", "arialbd.ttf",
                  "AppleSDGothicNeo.ttc", "impact.ttf"]
_font_cache = {}

def find_font(name):
    if name in _font_cache:
        return _font_cache[name]
    for n in [name] + FONT_FALLBACKS:
        for d in FONT_DIRS:
            p = os.path.join(d, n)
            if os.path.exists(p):
                if n != name:
                    print(f"[경고] 폰트 {name} 없음 → {n}로 대체 (spec tokens.font_*를 설치 폰트로 바꾸면 경고 제거)")
                _font_cache[name] = p
                return p
    raise FileNotFoundError(
        f"{name} — 폰트를 찾을 수 없습니다. spec의 tokens.font_* 값을 이 PC에 설치된 폰트 파일명으로 바꾸세요.")

def load_font(name, px):
    return ImageFont.truetype(find_font(name), px)

def fit_font(name, text, target_w, draw, start_px=100):
    """target_w 픽셀 폭에 맞는 최대 폰트 크기를 이진 탐색."""
    lo, hi = 10, start_px * 40
    while lo < hi:
        mid = (lo + hi + 1) // 2
        f = load_font(name, mid)
        w = draw.textlength(text, font=f)
        if w <= target_w:
            lo = mid
        else:
            hi = mid - 1
    return load_font(name, lo)

def main(spec_path, prefix="cover"):
    spec = json.load(open(spec_path, encoding='utf-8'))
    fmt, tok, lay, book = spec['format'], spec['tokens'], spec['layout'], spec['book']

    mm = lambda v: round(v / 25.4 * fmt['dpi'])
    trim_w, trim_h = fmt['trim_mm']
    bleed = fmt['bleed_mm']
    W, H = mm(trim_w + 2 * bleed), mm(trim_h + 2 * bleed)   # 도련 포함 캔버스
    BX, BY = mm(bleed), mm(bleed)                            # 재단 원점
    TW, TH = mm(trim_w), mm(trim_h)                          # 재단 후 크기

    img = Image.new('RGB', (W, H), tok['navy'])
    d = ImageDraw.Draw(img)

    # 1) 좌측 골드 바 (도련까지 연장)
    bar_x = BX + int(TW * lay['left_bar']['x_pct'])
    bar_w = int(TW * lay['left_bar']['w_pct'])
    d.rectangle([bar_x, 0, bar_x + bar_w, H], fill=tok['gold'])

    # 본문 영역: 골드 바 오른쪽 ~ 우측 여백
    content_l = bar_x + bar_w + int(TW * 0.055)
    content_r = BX + TW - int(TW * 0.045)
    content_w = content_r - content_l

    # 2) 타이틀 (줄별로 폭 맞춤 → 시각적 저스티파이)
    # layout.title_v_stretch(기본 1.0): 글자를 세로로 늘여 컨덴스드 포스터 느낌을 낸다(한글 1.2~1.35 권장)
    y = BY + int(TH * lay['title_top_pct'])
    block_h = int(TH * lay['title_block_h_pct'])
    n = len(book['title_lines'])
    line_h = block_h // n
    stretch = float(lay.get('title_v_stretch', 1.0))
    for line in book['title_lines']:
        f = fit_font(tok['font_title'], line, content_w, d)
        bbox = d.textbbox((0, 0), line, font=f)
        th = bbox[3] - bbox[1]
        if stretch != 1.0:
            tw = int(d.textlength(line, font=f))
            pad = 4
            tmp = Image.new('RGBA', (tw + 2 * pad, th + 2 * pad), (0, 0, 0, 0))
            td = ImageDraw.Draw(tmp)
            td.text((pad, pad - bbox[1]), line, font=f, fill=tok['white'])
            tmp = tmp.resize((tmp.width, int(tmp.height * stretch)), Image.LANCZOS)
            img.paste(tmp, (content_l + (content_w - tw) // 2 - pad,
                            y + line_h // 2 - tmp.height // 2), tmp)
        else:
            d.text((content_l + content_w // 2, y + line_h // 2 - bbox[1] - th // 2),
                   line, font=f, fill=tok['white'], anchor='ma')
        y += line_h

    # 3) 골드 박스 부제 (네이비 텍스트)
    sub = book['subtitle']
    f_sub = fit_font(tok['font_kr_bold'], sub, int(content_w * 0.88), d)
    sb = d.textbbox((0, 0), sub, font=f_sub)
    sw, sh = sb[2] - sb[0], sb[3] - sb[1]
    pad_x, pad_y = int(TW * lay['subtitle_box_pad_pct'][0]), int(TH * lay['subtitle_box_pad_pct'][1])
    box_y = y + int(TH * 0.012)
    cx = content_l + content_w // 2
    d.rectangle([cx - sw // 2 - pad_x, box_y, cx + sw // 2 + pad_x, box_y + sh + 2 * pad_y],
                fill=tok['gold'])
    d.text((cx, box_y + pad_y - sb[1]), sub, font=f_sub, fill=tok['navy'], anchor='ma')

    # 4) 키워드 스트립 (골드 헤어라인 + 골드 도트 구분)
    ky = BY + int(TH * lay['keywords_y_pct'])
    sep = '  ·  '
    kw_text = sep.join(book['keywords'])
    f_kw = fit_font(tok['font_kr_bold'], kw_text, int(content_w * 0.94), d)
    kb = d.textbbox((0, 0), kw_text, font=f_kw)
    kh = kb[3] - kb[1]
    line_pad = int(TH * 0.018)
    for ly in (ky - line_pad, ky + kh + line_pad):
        d.line([content_l + int(content_w * 0.03), ly,
                content_r - int(content_w * 0.03), ly], fill=tok['gold'], width=max(2, mm(0.25)))
    # 도트만 골드로: 텍스트를 통짜로 흰색 출력 후 도트 위치에 골드 재출력
    d.text((cx, ky - kb[1]), kw_text, font=f_kw, fill=tok['white'], anchor='ma')
    total_w = d.textlength(kw_text, font=f_kw)
    x_cursor = cx - total_w / 2
    for i, k in enumerate(book['keywords']):
        x_cursor += d.textlength(k, font=f_kw)
        if i < len(book['keywords']) - 1:
            d.text((x_cursor, ky - kb[1]), sep, font=f_kw, fill=tok['gold'])
            x_cursor += d.textlength(sep, font=f_kw)

    # 5) 저자명
    f_au = load_font(tok['font_kr_author'], int(TH * 0.022))
    d.text((cx, BY + int(TH * lay['author_y_pct'])), book['author'],
           font=f_au, fill=tok['white'], anchor='ma')

    out_dir = os.path.dirname(os.path.abspath(spec_path))
    p_print = os.path.join(out_dir, f'{prefix}_front_300dpi.png')
    img.save(p_print, dpi=(fmt['dpi'], fmt['dpi']))

    # 검수용 프리뷰: 재단선 표시 + 1000px 축소
    pv = img.copy()
    dv = ImageDraw.Draw(pv)
    dv.rectangle([BX, BY, BX + TW, BY + TH], outline='#FF3355', width=6)
    pv.thumbnail((1000, 1500))
    p_prev = os.path.join(out_dir, f'{prefix}_preview.png')
    pv.save(p_prev)

    print(f'인쇄용: {p_print}  ({img.size[0]}x{img.size[1]}px @{fmt["dpi"]}DPI, 도련 {bleed}mm 포함)')
    print(f'프리뷰: {p_prev}  (적색선=재단선)')

if __name__ == '__main__':
    if len(sys.argv) < 2 or not os.path.exists(sys.argv[1]):
        print(__doc__)
        print('spec 예시: <스킬>/assets/cover_spec.template.json 를 복사해 book 필드만 수정하세요.')
        sys.exit(1)
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else 'cover')
