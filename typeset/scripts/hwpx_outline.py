# -*- coding: utf-8 -*-
"""hwpx 구조/목차 추출기.

hwpx(ZIP)를 풀지 않고 직접 읽어 제목 문단을 분류해 목차(부/장/절)를 출력한다.
- header.xml 에서 charPr id -> (height, bold) 매핑을 만들고
- section*.xml 의 각 문단을 첫 run 의 charPrIDRef 로 분류한다.

사용:
  python hwpx_outline.py <책.hwpx>                      # 기본 맵(33:1, 23:2, 50:3)
  python hwpx_outline.py <책.hwpx> --map "33:1,23:2,50:3"
  python hwpx_outline.py <책.hwpx> --styles             # 글자모양 일람만 출력
  python hwpx_outline.py <책.hwpx> --out outline.md     # 결과를 md 로 저장
"""
import argparse, html, re, sys, zipfile


def char_styles(header_xml):
    """charPr id -> dict(height, bold). 주의: 내부 자식 태그가 />로 끝나므로
    정규식 한 방이 아니라 다음 charPr 시작 위치까지를 한 블록으로 잘라 검사한다."""
    styles = {}
    starts = [m for m in re.finditer(r'<hh:charPr id="(\d+)" height="(\d+)"', header_xml)]
    for i, m in enumerate(starts):
        end = starts[i + 1].start() if i + 1 < len(starts) else len(header_xml)
        block = header_xml[m.start():end]
        styles[int(m.group(1))] = {"height": int(m.group(2)),
                                   "bold": "<hh:bold/>" in block}
    return styles


def paragraphs(section_xml):
    """(첫 run 의 charPrIDRef, 문단 텍스트) 목록. 표 내부 중첩 문단도 포함된다."""
    out = []
    for pm in re.finditer(r'<hp:p [^>]*paraPrIDRef="\d+"[^>]*>(.*?)</hp:p>', section_xml, re.S):
        body = pm.group(1)
        rm = re.search(r'<hp:run charPrIDRef="(\d+)"', body)
        if not rm:
            continue
        texts = re.findall(r'<hp:t>(.*?)</hp:t>', body, re.S)
        text = html.unescape("".join(texts)).strip()
        if text:
            out.append((int(rm.group(1)), text))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("hwpx")
    ap.add_argument("--map", default="33:1,23:2,50:3",
                    help="charPrID:레벨 매핑 (레벨 1=#, 2=##, 3=###)")
    ap.add_argument("--styles", action="store_true", help="글자모양 일람만 출력")
    ap.add_argument("--analyze", action="store_true",
                    help="문단 시작 charPr id별 사용 횟수와 샘플 텍스트 — 제목 id 찾기용")
    ap.add_argument("--out", help="출력 md 파일 경로(생략 시 stdout)")
    args = ap.parse_args()

    z = zipfile.ZipFile(args.hwpx)
    header = z.read("Contents/header.xml").decode("utf-8")
    styles = char_styles(header)

    if args.styles:
        for cid in sorted(styles):
            s = styles[cid]
            print(f'charPr {cid:>3}: height={s["height"]:>5} bold={s["bold"]}')
        return

    secs_all = sorted((n for n in z.namelist()
                       if re.fullmatch(r"Contents/section\d+\.xml", n)),
                      key=lambda n: int(re.search(r"\d+", n).group()))
    if args.analyze:
        from collections import OrderedDict
        usage = OrderedDict()
        for name in secs_all:
            for cid, text in paragraphs(z.read(name).decode("utf-8")):
                u = usage.setdefault(cid, {"count": 0, "samples": []})
                u["count"] += 1
                if len(u["samples"]) < 3 and len(text) < 60:
                    u["samples"].append(text)
        rows = sorted(usage.items(),
                      key=lambda kv: (-styles.get(kv[0], {}).get("height", 0), kv[0]))
        out = []
        for cid, u in rows:
            s = styles.get(cid, {"height": "?", "bold": "?"})
            out.append(f'charPr {cid:>3} h={s["height"]:>5} bold={str(s["bold"]):<5} '
                       f'x{u["count"]:>4} | ' + " / ".join(u["samples"]))
        sys.stdout.buffer.write(("\n".join(out) + "\n").encode("utf-8"))
        return

    level = {}
    for pair in args.map.split(","):
        k, v = pair.split(":")
        level[int(k)] = int(v)

    lines = []
    for name in secs_all:
        for cid, text in paragraphs(z.read(name).decode("utf-8")):
            if cid in level:
                lines.append("#" * level[cid] + " " + text)
            elif styles.get(cid, {}).get("bold") and styles[cid]["height"] >= 1100:
                # 맵에 없는 큰 굵은 글씨 — 제목 후보로 표시
                lines.append(f"(?cid={cid}) {text}")
    result = "\n".join(lines)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(result + "\n")
        print(f"OK -> {args.out} ({len(lines)} headings)")
    else:
        sys.stdout.buffer.write((result + "\n").encode("utf-8"))


if __name__ == "__main__":
    main()
