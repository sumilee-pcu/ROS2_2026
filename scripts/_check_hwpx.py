"""HWPX 조판 규칙 점검 스크립트."""
import sys, zipfile, re, xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")

# 참조 템플릿 (상대 경로 — 이 스크립트에서 두 단계 위)
_ROOT = Path(__file__).parent.parent
TEMPLATE = _ROOT / "typeset/template/ROS2첫걸음1_B5_이수미_1장_최종.hwpx"

# 우리 charmap — scripts/md2hwpx.py CHARMAP 과 동일
# key=charPr ID, value=(역할, h1 여부)
CHARMAP_ROLES = {
    "22": "h1", "15": "h2", "7": "h3", "13": "bold",
    "11": "body", "9": "quote", "39": "code", "37": "opener_item",
}

HH = "http://www.hancom.co.kr/hwpml/2011/head"


def _charpr_table(hdr_xml: str) -> dict:
    """header.xml 문자열에서 charPr id → (height, bold, face) 추출."""
    root = ET.fromstring(hdr_xml.encode("utf-8"))
    fonts = {}
    for ff in root.iter(f"{{{HH}}}fontface"):
        if ff.get("lang") == "HANGUL":
            for fnt in ff.findall(f"{{{HH}}}font"):
                fonts[fnt.get("id")] = fnt.get("face", "")
    result = {}
    for cp in root.iter(f"{{{HH}}}charPr"):
        cid = cp.get("id")
        ht  = int(cp.get("height", 0))
        bold = cp.find(f"{{{HH}}}bold") is not None
        fr = cp.find(f"{{{HH}}}fontRef")
        face = fonts.get(fr.get("hangul", "") if fr is not None else "", "?")
        result[cid] = (ht, bold, face)
    return result


def _load_template_charpr() -> dict | None:
    if not TEMPLATE.exists():
        return None
    hdr = zipfile.ZipFile(TEMPLATE).read("Contents/header.xml").decode("utf-8")
    return _charpr_table(hdr)


def check(path):
    print(f"\n{'='*60}")
    print(f"검사: {path}")
    print('='*60)
    issues = []

    z = zipfile.ZipFile(path)
    names = z.namelist()

    # 1) mimetype
    mt = z.read("mimetype").decode()
    ok = mt == "application/hwp+zip"
    print(f"  {'[OK]' if ok else '[!!]'} mimetype: {mt!r}")
    if not ok:
        issues.append(f"mimetype 오류: {mt!r}")

    # 2) mimetype STORED 첫 항목
    info0 = z.infolist()[0]
    ok = info0.filename == "mimetype" and info0.compress_type == 0
    print(f"  {'[OK]' if ok else '[!!]'} mimetype STORED 첫 항목")
    if not ok:
        issues.append(f"mimetype STORED 위반: {info0.filename}, compress={info0.compress_type}")

    # 3) 판형 B5 — section0.xml의 hp:pagePr
    sec = z.read("Contents/section0.xml").decode("utf-8")
    hdr = z.read("Contents/header.xml").decode("utf-8")

    m = re.search(r'<hp:pagePr[^>]*\bwidth="(\d+)"[^>]*\bheight="(\d+)"', sec)
    if not m:
        m = re.search(r'<hp:pagePr[^>]*\bheight="(\d+)"[^>]*\bwidth="(\d+)"', sec)
        pw, ph = (m.group(2), m.group(1)) if m else (None, None)
    else:
        pw, ph = m.group(1), m.group(2)
    if pw and ph:
        ok = pw == "53291" and ph == "74551"
        print(f"  {'[OK]' if ok else '[!!]'} 판형(secPr.pagePr): {pw}x{ph} {'B5' if ok else '(B5=53291x74551 아님)'}")
        if not ok:
            issues.append(f"판형 오류: {pw}x{ph} — B5는 53291x74551")
    else:
        issues.append("hp:pagePr 태그 없음 — 판형 확인 불가")
        print("  [!!] 판형 정보 없음")

    # 4) 이미지
    bins = [n for n in names if n.startswith("BinData/")]
    hpf = z.read("Contents/content.hpf").decode("utf-8")
    img_items = re.findall(r'id="(image\d+)"', hpf)
    ok = len(bins) == len(img_items)
    print(f"  {'[OK]' if ok else '[!!]'} 이미지: BinData {len(bins)}개, manifest {len(img_items)}개")
    if not ok:
        issues.append(f"BinData({len(bins)}) ≠ manifest({len(img_items)})")

    # 5) isEmbeded='1'
    bad = re.findall(r'<opf:item id="image[^"]*"(?![^>]*isEmbeded="1")[^>]*/>', hpf)
    ok = not bad
    if img_items:
        print(f"  {'[OK]' if ok else '[!!]'} isEmbeded='1': {'모두 OK' if ok else f'{len(bad)}개 누락'}")
        if not ok:
            issues.append(f"isEmbeded='1' 누락 {len(bad)}개")

    # 6) XML 무결성
    errs = []
    for n in names:
        if n.endswith(".xml") or n.endswith(".hpf"):
            try:
                ET.fromstring(z.read(n))
            except Exception as e:
                errs.append(f"{n}: {e}")
    print(f"  {'[OK]' if not errs else '[!!]'} XML well-formed: {len(errs)}개 오류")
    issues.extend(errs)

    # 7) 폰트 크기 — charPr 정의를 참조 템플릿과 비교
    file_cpr = _charpr_table(hdr)
    tmpl_cpr = _load_template_charpr()

    ids_used = Counter(re.findall(r'charPrIDRef="(\d+)"', sec))

    font_issues = []
    if tmpl_cpr is None:
        print(f"  [  ] 폰트 점검 생략 (템플릿 없음: {TEMPLATE})")
    else:
        # 7a) charPr 정의 일치 여부 (header.xml vs 참조 템플릿)
        header_mismatch = []
        for cid, role in CHARMAP_ROLES.items():
            fc = file_cpr.get(cid)
            tc = tmpl_cpr.get(cid)
            if tc is None:
                continue
            if fc is None:
                header_mismatch.append(f"charPr {cid} ({role}) 정의 없음")
            elif fc[0] != tc[0]:
                header_mismatch.append(
                    f"charPr {cid} ({role}) 높이 불일치: "
                    f"파일={fc[0]/100:.1f}pt vs 템플릿={tc[0]/100:.1f}pt"
                )
        if header_mismatch:
            print(f"  [!!] header.xml ↔ 템플릿 charPr 불일치 {len(header_mismatch)}개 (재변환 필요)")
            for msg in header_mismatch:
                print(f"       • {msg}")
            font_issues.extend(header_mismatch)
        else:
            print(f"  [OK] header.xml charPr 정의 — 템플릿 일치")

        # 7b) section0.xml 사용 현황
        print("  -- 글자 모양(charPr) 사용 현황 --")
        for cid, cnt in sorted(ids_used.items(), key=lambda x: int(x[0])):
            fc = file_cpr.get(cid, (0, False, "?"))
            pt = fc[0] / 100
            bold_str = "B" if fc[1] else " "
            role = CHARMAP_ROLES.get(cid, "")
            label = f"  [{role}]" if role else ""
            print(f"    [  ] charPr {cid:>3}: {cnt:>5}회  {pt:.1f}pt  {bold_str}  {fc[2]}{label}")

        # 사용되어야 하는 charPr가 없으면 경고 (h1 제외)
        for cid, role in CHARMAP_ROLES.items():
            if cid not in ids_used and role not in ("h1", "opener_item"):
                font_issues.append(f"charPr {cid} ({role}) section0 미사용")
                print(f"    [!!] charPr {cid:>3}:     0회  ({role}) 미사용")

    issues.extend(font_issues)

    # 8) linesegarray (경고 원인 — strip_linesegs.py 필요)
    ls = sec.count("<hp:linesegarray>")
    if ls > 0:
        print(f"  [!!] linesegarray {ls}개 — 한글 '변조 가능성' 경고 유발")
        issues.append(f"linesegarray {ls}개 (strip_linesegs.py 필요)")
    else:
        print(f"  [OK] linesegarray 없음")

    # 9) 정보
    sec_kb = len(sec.encode()) // 1024
    total_kb = sum(z.getinfo(n).file_size for n in names) // 1024
    print(f"  [  ] section0: {sec_kb}KB  /  전체: {total_kb}KB")

    print(f"\n  {'[PASS] 이상 없음' if not issues else f'[FAIL] {len(issues)}개 문제'}")
    for iss in issues:
        print(f"    - {iss}")
    return issues


if __name__ == "__main__":
    paths = sys.argv[1:] if len(sys.argv) > 1 else [
        "docx/02_워크스페이스와빌드시스템.hwpx",
        "docx/06_파라미터와커스텀인터페이스.hwpx",
    ]
    results = [check(p) for p in paths]
    all_ok = not any(results)
    print("\n" + ("=== 전체 PASS ===" if all_ok else "=== 문제 있음 ==="))
