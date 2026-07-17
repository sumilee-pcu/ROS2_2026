# -*- coding: utf-8 -*-
"""Markdown -> HWPX 변환기 (부크크 승인 B5 교재 스타일 재사용).

원리: 승인된 본책 hwpx 를 템플릿으로 삼아 컨테이너(mimetype, header.xml,
settings.xml, content.hpf, META-INF)는 그대로 복제하고 Contents/section0.xml 만
md 내용으로 교체한다. 첫 문단(secPr=B5 페이지 설정 포함)은 반드시 보존한다.

스타일 매핑(본책 header.xml 기준 — 다른 템플릿이면 hwpx_outline.py --styles 로 확인):
  char 33 (1500 bold) : 장/Lab 제목 (#)
  char 23 (1100 bold) : 절 제목 (##)
  char 50 (1100 bold) : 소절 제목 (###)
  char  7 (1000 bold) : 굵은 라벨(####, **bold**, 표 머리행)
  char 12 (1000)      : 본문/불릿/표 본문
  char  9 ( 900)      : 인용(>)/캡션
  para 16: 본문 문단   para 1: 표 래퍼   para 22: 표 셀

사용:
  python md2hwpx.py --template <본책.hwpx 또는 풀린 폴더> --out <출력.hwpx> \
                    [--keep-bindata] <장1.md> <장2.md> ...
각 md 파일은 새 쪽(pageBreak)에서 시작한다.
"""
import argparse, os, re, shutil, sys, tempfile, zipfile

TEXT_W = 36000  # B5 본문 폭 (HWPUNIT)

# 기본값: _wbtmpl/book 템플릿 기준. 다른 템플릿이면 --charmap 으로 교체
# (hwpx_outline.py --analyze 로 id 확인. 예: 최종본책은 h1:70,h2:19,h3:7,bold:7,body:11,quote:9)
C_TITLE, C_H2, C_H3, C_BOLD, C_BODY, C_QUOTE = 33, 23, 50, 7, 12, 9
C_CODE = C_BODY   # 코드블록 글자 모양 (--charmap code:N 으로 교체)
CODE_BF = 4       # 코드블록 테두리 채움 (--charmap codefill:N 으로 교체)
C_OPENER_ITEM = C_QUOTE   # "이 장에서 다루는 내용" 항목 (--charmap opener_item:N)
HEIGHT = {C_TITLE: 1500, C_H2: 1100, C_H3: 1100, C_BOLD: 1000, C_BODY: 1000, C_QUOTE: 900}

_tbl_id = [1107880100]

# lineseg 는 한글이 저장 시 기록하는 "줄 배치 캐시"다. 생성기에서 한 줄짜리로
# 기록하면 여러 줄 문단이 겹쳐 보이는 문제가 생기므로 기본은 기록하지 않는다
# (없으면 한글이 열 때 스스로 계산). --legacy-lineseg 로만 재활성화.
EMIT_LINESEG = False


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def lineseg(h, w=None):
    if not EMIT_LINESEG:
        return ""
    base = int(h * 0.85)
    return (f'<hp:linesegarray><hp:lineseg textpos="0" vertpos="0" vertsize="{h}" '
            f'textheight="{h}" baseline="{base}" spacing="600" horzpos="0" '
            f'horzsize="{w if w else TEXT_W}" flags="393216"/></hp:linesegarray>')


def inline_runs(text, default_char):
    """**bold**, `code`, *italic*, [t](u) 를 run 으로 분해."""
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    runs = []
    parts = re.split(r'(\*\*[^*]+\*\*|`[^`]+`)', text)
    for p in parts:
        if not p:
            continue
        if p.startswith('**') and p.endswith('**'):
            runs.append((C_BOLD, p[2:-2]))
        elif p.startswith('`') and p.endswith('`'):
            runs.append((C_BOLD, p[1:-1]))
        else:
            p = re.sub(r'\*([^*]+)\*', r'\1', p)
            runs.append((default_char, p))
    return runs or [(default_char, "")]


def para(text, char, para_id=16, page_break=False):
    runs = inline_runs(text, char)
    r = "".join(f'<hp:run charPrIDRef="{c}"><hp:t>{esc(t)}</hp:t></hp:run>' for c, t in runs)
    h = HEIGHT.get(char, 1000)
    pb = "1" if page_break else "0"
    return (f'<hp:p id="0" paraPrIDRef="{para_id}" styleIDRef="0" pageBreak="{pb}" '
            f'columnBreak="0" merged="0">{r}{lineseg(h)}</hp:p>')


def empty_para():
    return para("", C_BODY)


def _cell_lines(text, w):
    """텍스트가 셀 폭 w(HWPUNIT)에서 몇 줄로 나뉘는지 추정 (최소 1)."""
    vis = _vis_len(text)
    chars_per_line = max(1, w / 560)  # 한글 1자≈560 HWPUNIT
    return max(1, int(vis / chars_per_line) + 1)


def cell(text, char, col, row, w, header=False):
    runs = inline_runs(text, char)
    r = "".join(f'<hp:run charPrIDRef="{c}"><hp:t>{esc(t)}</hp:t></hp:run>' for c, t in runs)
    h = HEIGHT.get(char, 1000)
    nlines = _cell_lines(text, w)
    cell_h = max(1600, nlines * (h + 200) + 280)
    para_pr = "26" if header else "15"  # CENTER(헤더)/LEFT(본문) - 양쪽정렬·큰들여쓰기 paraPr22 불가
    p = (f'<hp:p id="0" paraPrIDRef="{para_pr}" styleIDRef="0" pageBreak="0" columnBreak="0" '
         f'merged="0">{r}{lineseg(h, w)}</hp:p>')
    hd = "1" if header else "0"
    return (f'<hp:tc name="" header="{hd}" hasMargin="0" protect="0" editable="0" '
            f'dirty="0" borderFillIDRef="4"><hp:subList id="" textDirection="HORIZONTAL" '
            f'lineWrap="BREAK" vertAlign="CENTER" linkListIDRef="0" linkListNextIDRef="0" '
            f'textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">{p}</hp:subList>'
            f'<hp:cellAddr colAddr="{col}" rowAddr="{row}"/>'
            f'<hp:cellSpan colSpan="1" rowSpan="1"/>'
            f'<hp:cellSz width="{w}" height="{cell_h}"/>'
            f'<hp:cellMargin left="510" right="510" top="141" bottom="141"/></hp:tc>')


def _vis_len(s):
    """셀 텍스트의 시각 폭 추정(한글 1.0, 라틴/숫자/기호 0.55)."""
    s = re.sub(r'\*\*([^*]+)\*\*|`([^`]+)`', lambda m: m.group(1) or m.group(2), s)
    return sum(0.55 if ord(c) < 0x2E80 else 1.0 for c in s)


def _col_widths(rows, total):
    """내용 길이에 비례해 칼럼 폭 배분(최소폭 보장). 행이 한 줄에 들어오도록."""
    ncols = len(rows[0])
    w = [max(max(_vis_len(r[ci].strip()) for r in rows), 3.0) for ci in range(ncols)]
    minw = 2600
    widths = [max(minw, int(total * wi / sum(w))) for wi in w]
    widths[-1] += total - sum(widths)  # 반올림 오차는 마지막 칼럼에
    return widths


def table(rows, has_header=True):
    ncols = max(len(r) for r in rows)
    rows = [r + [""] * (ncols - len(r)) for r in rows]
    widths = _col_widths(rows, TEXT_W)
    tblw = sum(widths)
    nrows = len(rows)
    tblh = 1600 * nrows
    _tbl_id[0] += 1
    tid = _tbl_id[0]
    trs = []
    for ri, row in enumerate(rows):
        is_h = has_header and ri == 0
        cells = "".join(cell(t.strip(), C_BOLD if is_h else C_BODY, ci, ri, widths[ci], header=is_h)
                        for ci, t in enumerate(row))
        trs.append(f'<hp:tr>{cells}</hp:tr>')
    tbl = (f'<hp:tbl id="{tid}" zOrder="{tid}" numberingType="TABLE" '
           f'textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" '
           f'pageBreak="CELL" repeatHeader="1" rowCnt="{nrows}" colCnt="{ncols}" '
           f'cellSpacing="0" borderFillIDRef="4" noAdjust="0">'
           f'<hp:sz width="{tblw}" widthRelTo="ABSOLUTE" height="{tblh}" '
           f'heightRelTo="ABSOLUTE" protect="0"/>'
           f'<hp:pos treatAsChar="1" affectLSpacing="0" flowWithText="1" allowOverlap="0" '
           f'holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="PARA" vertAlign="TOP" '
           f'horzAlign="LEFT" vertOffset="0" horzOffset="0"/>'
           f'<hp:outMargin left="283" right="283" top="283" bottom="283"/>'
           f'<hp:inMargin left="510" right="510" top="141" bottom="141"/>'
           f'{"".join(trs)}</hp:tbl>')
    return (f'<hp:p id="0" paraPrIDRef="1" styleIDRef="0" pageBreak="0" columnBreak="0" '
            f'merged="0"><hp:run charPrIDRef="{C_BODY}">{tbl}<hp:t/></hp:run>'
            f'{lineseg(1000)}</hp:p>')


def code_box(lines):
    """코드블록 -> 1열 표(테두리 박스) 안에 줄별 문단."""
    _tbl_id[0] += 1
    tid = _tbl_id[0]
    w = TEXT_W
    ps = ""
    for ln in (lines or [""]):
        ps += (f'<hp:p id="0" paraPrIDRef="15" styleIDRef="0" pageBreak="0" '
               f'columnBreak="0" merged="0"><hp:run charPrIDRef="{C_CODE}">'
               f'<hp:t>{esc(ln)}</hp:t></hp:run>{lineseg(950, w)}</hp:p>')
    hgt = max(1600, len(lines) * 520)
    c = (f'<hp:tc name="" header="0" hasMargin="0" protect="0" editable="0" dirty="0" '
         f'borderFillIDRef="{CODE_BF}"><hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" '
         f'vertAlign="TOP" linkListIDRef="0" linkListNextIDRef="0" textWidth="0" '
         f'textHeight="0" hasTextRef="0" hasNumRef="0">{ps}</hp:subList>'
         f'<hp:cellAddr colAddr="0" rowAddr="0"/><hp:cellSpan colSpan="1" rowSpan="1"/>'
         f'<hp:cellSz width="{w}" height="{hgt}"/>'
         f'<hp:cellMargin left="400" right="400" top="300" bottom="300"/></hp:tc>')
    tbl = (f'<hp:tbl id="{tid}" zOrder="{tid}" numberingType="TABLE" '
           f'textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" '
           f'pageBreak="CELL" repeatHeader="0" rowCnt="1" colCnt="1" cellSpacing="0" '
           f'borderFillIDRef="{CODE_BF}" noAdjust="0">'
           f'<hp:sz width="{w}" widthRelTo="ABSOLUTE" height="{hgt}" '
           f'heightRelTo="ABSOLUTE" protect="0"/>'
           f'<hp:pos treatAsChar="1" affectLSpacing="0" flowWithText="1" allowOverlap="0" '
           f'holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="PARA" vertAlign="TOP" '
           f'horzAlign="LEFT" vertOffset="0" horzOffset="0"/>'
           f'<hp:outMargin left="283" right="283" top="283" bottom="283"/>'
           f'<hp:inMargin left="400" right="400" top="300" bottom="300"/>'
           f'<hp:tr>{c}</hp:tr></hp:tbl>')
    return (f'<hp:p id="0" paraPrIDRef="1" styleIDRef="0" pageBreak="0" columnBreak="0" '
            f'merged="0"><hp:run charPrIDRef="{C_BODY}">{tbl}<hp:t/></hp:run>'
            f'{lineseg(1000)}</hp:p>')


_BLOCK_RE = re.compile(
    r'^#{1,6}\s|^```|^>\s?|^- |^- \[[ xX]\]|\|.*\||^---$|^!\['
)
_CAPTION_RE = re.compile(r'^그림\s+\d+-\d+[.\s]')


def _is_block_line(s):
    """연속 body 행 병합 시 중단해야 하는 줄이면 True."""
    if not s:
        return True
    if re.match(r'^\d+\.\s', s):
        return True
    if s.startswith("::::"):
        return True
    if _CAPTION_RE.match(s):
        return True
    return bool(_BLOCK_RE.match(s))


def convert_md(md):
    out = []
    lines = md.split("\n")
    i = 0
    while i < len(lines):
        s = lines[i].strip()

        # :::opener ... ::: 블록 — "이 장에서 다루는 내용" 박스
        if s == ":::opener":
            out.append(para("이 장에서 다루는 내용", C_H3))
            i += 1
            while i < len(lines) and lines[i].strip() not in (":::", ""):
                item = lines[i].strip()
                if item:
                    text = item.lstrip("•").strip()
                    if text:
                        out.append(para("• " + text, C_OPENER_ITEM))
                i += 1
            i += 1  # ::: 소비
            continue

        # 코드 블록
        if s.startswith("```"):
            block = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                block.append(lines[i])
                i += 1
            i += 1
            out.append(code_box(block))
            out.append(empty_para())
            continue

        # 표
        if s.startswith("|") and "|" in s[1:]:
            tbl_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                tbl_lines.append(lines[i].strip())
                i += 1
            rows = [[c.strip() for c in tl.strip().strip("|").split("|")]
                    for tl in tbl_lines if not re.match(r'^\|[\s:|-]+\|?$', tl)]
            if rows:
                out.append(table(rows, has_header=True))
                out.append(empty_para())
            continue

        if s.startswith("# "):
            out.append(empty_para())
            out.append(para(s[2:].strip(), C_TITLE))
        elif s.startswith("## "):
            out.append(empty_para())
            out.append(para(s[3:].strip(), C_H2))
        elif s.startswith("### "):
            out.append(empty_para())
            out.append(para(s[4:].strip(), C_H3))
        elif s.startswith("#### "):
            out.append(para(s[5:].strip(), C_BOLD))
        elif s == "---":
            out.append(empty_para())
        elif re.match(r'^!\[', s):
            alt = re.sub(r'^!\[([^\]]*)\]\([^)]*\)$', r'\1', s).strip()
            if alt:
                out.append(para(alt, C_QUOTE))
        elif _CAPTION_RE.match(s):
            out.append(para(s, C_QUOTE))
        elif s.startswith(">"):
            out.append(para(s.lstrip(">").strip(), C_QUOTE))
        elif re.match(r'^- \[[ xX]\] ', s):
            mark = "☑" if re.match(r'^- \[[xX]\]', s) else "☐"
            out.append(para(mark + " " + s.split("]", 1)[1].strip(), C_BODY))
        elif s.startswith("- "):
            out.append(para("• " + s[2:].strip(), C_BODY))
        elif re.match(r'^\d+\.\s', s):
            out.append(para(s, C_BODY))
        elif s == "":
            pass
        else:
            # 일반 body — 연속 행을 한 문단으로 병합 (마크다운 소프트 줄바꿈)
            parts = [s]
            while i + 1 < len(lines):
                ns = lines[i + 1].strip()
                if _is_block_line(ns):
                    break
                parts.append(ns)
                i += 1
            out.append(para(" ".join(p for p in parts if p), C_BODY))
        i += 1
    return "".join(out)


# 동봉 기본 템플릿(승인 본책)과 그 템플릿에서 검증된 charmap — --template 생략 시 사용
_ASSET_TEMPLATE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets", "B5_book_template.hwpx")
_ASSET_CHARMAP = "h1:70,h2:19,h3:7,bold:7,body:11,quote:9"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", default=None,
                    help="승인 본책 .hwpx 또는 풀린 템플릿 폴더 (생략 시 동봉 본책 템플릿)")
    ap.add_argument("--out", required=True, help="출력 .hwpx 경로")
    ap.add_argument("--keep-bindata", action="store_true",
                    help="템플릿의 BinData(이미지) 유지 (기본: 제거)")
    ap.add_argument("--charmap",
                    help='글자모양 id 교체: "h1:70,h2:19,h3:7,bold:7,body:11,quote:9"')
    ap.add_argument("--legacy-lineseg", action="store_true",
                    help="레거시: 한 줄짜리 lineseg 캐시 기록 (여러 줄 문단 겹침의 원인 — 비권장)")
    ap.add_argument("--textwidth", type=int, default=None,
                    help="본문 폭 HWPUNIT (표·코드박스 폭 기준). 기본 36000(B5). 템플릿 lineseg의 horzsize 값 참고")
    ap.add_argument("md_files", nargs="+")
    args = ap.parse_args()

    if args.template is None:
        if not os.path.exists(_ASSET_TEMPLATE):
            ap.error(f"--template 을 지정하세요 (동봉 템플릿 없음: {_ASSET_TEMPLATE})")
        args.template = _ASSET_TEMPLATE
        if not args.charmap:
            args.charmap = _ASSET_CHARMAP  # 동봉 템플릿에서 검증된 매핑

    global C_TITLE, C_H2, C_H3, C_BOLD, C_BODY, C_QUOTE, C_CODE, CODE_BF, C_OPENER_ITEM, HEIGHT, EMIT_LINESEG, TEXT_W
    EMIT_LINESEG = args.legacy_lineseg
    if args.textwidth:
        TEXT_W = args.textwidth
    if args.charmap:
        m = dict(kv.split(":") for kv in args.charmap.split(","))
        C_TITLE = int(m.get("h1", C_TITLE))
        C_H2 = int(m.get("h2", C_H2))
        C_H3 = int(m.get("h3", C_H3))
        C_BOLD = int(m.get("bold", C_BOLD))
        C_BODY = int(m.get("body", C_BODY))
        C_QUOTE = int(m.get("quote", C_QUOTE))
        C_CODE = int(m.get("code", C_CODE))
        CODE_BF = int(m.get("codefill", CODE_BF))
        C_OPENER_ITEM = int(m.get("opener_item", C_OPENER_ITEM))

    # 템플릿 준비 (.hwpx 면 임시 폴더에 풀기)
    tmpdir = None
    tmpl = args.template
    if tmpl.lower().endswith(".hwpx"):
        tmpdir = tempfile.mkdtemp(prefix="hwpxtmpl_")
        with zipfile.ZipFile(tmpl) as z:
            z.extractall(tmpdir)
        tmpl = tmpdir

    # 템플릿 header.xml 에서 실제 글자 높이를 읽어 lineseg 높이를 맞춘다
    with open(os.path.join(tmpl, "Contents", "header.xml"), encoding="utf-8") as f:
        header = f.read()
    for cid in {C_TITLE, C_H2, C_H3, C_BOLD, C_BODY, C_QUOTE}:
        hm = re.search(r'<hh:charPr id="%d" height="(\d+)"' % cid, header)
        if hm:
            HEIGHT[cid] = int(hm.group(1))
        elif cid not in HEIGHT:
            sys.exit(f"ERROR: charPr id {cid} 가 템플릿 header.xml 에 없습니다. "
                     f"--charmap 을 확인하세요 (hwpx_outline.py --analyze 참고).")

    # 본문 생성 — md 파일마다 새 쪽에서 시작
    body = []
    for idx, mf in enumerate(args.md_files):
        with open(mf, encoding="utf-8") as f:
            md = f.read()
        if idx > 0:
            body.append(f'<hp:p id="0" paraPrIDRef="16" styleIDRef="0" pageBreak="1" '
                        f'columnBreak="0" merged="0"><hp:run charPrIDRef="{C_BODY}"><hp:t/></hp:run>'
                        + lineseg(HEIGHT.get(C_BODY, 1000)) + '</hp:p>')
        body.append(convert_md(md))
    body_xml = "".join(body)

    build = tempfile.mkdtemp(prefix="hwpxbuild_")
    shutil.rmtree(build)
    shutil.copytree(tmpl, build)

    # section0: 첫 문단(secPr=페이지 설정) 보존 + 본문 교체
    sec_path = os.path.join(build, "Contents", "section0.xml")
    with open(sec_path, encoding="utf-8") as f:
        sec = f.read()
    first_close = sec.index("</hp:p>") + len("</hp:p>")
    new_sec = sec[:first_close] + body_xml + "</hs:sec>"
    with open(sec_path, "w", encoding="utf-8") as f:
        f.write(new_sec)

    # 추가 섹션이 있으면 제거(본문은 section0 하나로 합침)
    cdir = os.path.join(build, "Contents")
    for fn in os.listdir(cdir):
        if re.fullmatch(r"section[1-9]\d*\.xml", fn):
            os.remove(os.path.join(cdir, fn))
    hpf_path = os.path.join(cdir, "content.hpf")
    with open(hpf_path, encoding="utf-8") as f:
        hpf = f.read()
    hpf = re.sub(r'<opf:item id="section[1-9]\d*"[^>]*/>', "", hpf)
    hpf = re.sub(r'<opf:itemref idref="section[1-9]\d*"[^>]*/>', "", hpf)

    if not args.keep_bindata:
        bindir = os.path.join(build, "BinData")
        if os.path.exists(bindir):
            shutil.rmtree(bindir)
        hpf = re.sub(r'<opf:item id="image\d+"[^>]*/>', "", hpf)
    with open(hpf_path, "w", encoding="utf-8") as f:
        f.write(hpf)

    # 패키징 — mimetype 은 반드시 첫 항목 + 무압축(STORED)
    if os.path.exists(args.out):
        os.remove(args.out)
    with zipfile.ZipFile(args.out, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(os.path.join(build, "mimetype"), "mimetype",
                compress_type=zipfile.ZIP_STORED)
        for root, _, files in os.walk(build):
            for fn in files:
                full = os.path.join(root, fn)
                rel = os.path.relpath(full, build).replace("\\", "/")
                if rel != "mimetype":
                    z.write(full, rel)
    shutil.rmtree(build)
    if tmpdir:
        shutil.rmtree(tmpdir)
    print("OK ->", args.out)
    print("section0.xml bytes:", len(new_sec.encode("utf-8")))


if __name__ == "__main__":
    main()
