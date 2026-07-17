# -*- coding: utf-8 -*-
"""hwpx_insert_figs — hwpx 본문에 그림(PNG)을 앵커 텍스트 기준으로 일괄 삽입.

md2hwpx는 이미지를 넣지 않으므로(텍스트·표·코드만), 변환 후 이 도구로 그림을 박는다.
앵커 문단의 paraPrIDRef를 상속하므로 템플릿(A5/B5/워크북) 무관하게 동작한다.
원본: 생성형AI활용첫걸음집필/hx_insert_figs.py 를 범용화(2026-06).

플랜 파일(TSV, # 주석·빈줄 무시). 2열 또는 3열:
    png<TAB>anchor                     # 섹션 자동 탐색(앵커가 전체에서 유일해야 함)
    png<TAB>section_index<TAB>anchor    # Contents/section{N}.xml 지정
예)
    fig1_3_tokenflow.png	이 과정을 반복해 응답을 완성한다.
    fig2_1_prompt5.png	5	좋은 프롬프트가 갖추어야 할 핵심 요소는 다섯 가지다.

사용:
    python hwpx_insert_figs.py --hwpx 초안.hwpx --plan figplan.tsv --figdir figs
    python hwpx_insert_figs.py --hwpx 초안.hwpx --plan figplan.tsv --dry-run   # 앵커만 점검
옵션:
    --width 32000      이미지 표시 폭(HWPUNIT). B5 본문폭≈36000, A5≈29196
    --bodywidth 36000  lineseg 가로폭(본문폭). 미지정 시 --width 사용
    --parapr N / --charpr N   앵커 상속 대신 강제 지정
    --no-backup        .bak 백업 생략(기본은 <hwpx>.bak 생성)

주의(SKILL.md 함정 참고): mimetype은 STORED 첫 항목, opf:item에 isEmbeded="1" 필수,
lineseg는 직접 기록하되 본문폭과 일치시킨다. 삽입 후 validate_hwpx.py로 검증, 한글로 직접 열어 확인.
"""
import argparse, json, os, re, sys, zipfile
import xml.etree.ElementTree as ET
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
from PIL import Image


def pic_para(img_id, pid, iid, pw, ph, wd, bodyw, parapr, charpr):
    """treatAsChar 중앙 정렬 그림 한 문단 생성."""
    Hd = round(wd * ph / pw); base = round(Hd * 0.85)
    rawR = pw * 75; rawB = ph * 75
    return (f'<hp:p id="0" paraPrIDRef="{parapr}" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">'
      f'<hp:run charPrIDRef="{charpr}"><hp:pic id="{pid}" zOrder="0" numberingType="PICTURE" textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" href="" groupLevel="0" instid="{iid}" reverse="0">'
      f'<hp:offset x="0" y="0"/><hp:orgSz width="{wd}" height="{Hd}"/><hp:curSz width="{wd}" height="{Hd}"/>'
      f'<hp:flip horizontal="0" vertical="0"/><hp:rotationInfo angle="0" centerX="{wd//2}" centerY="{Hd//2}" rotateimage="1"/>'
      f'<hp:renderingInfo><hc:transMatrix e1="1" e2="0" e3="0" e4="0" e5="1" e6="0"/><hc:scaMatrix e1="1" e2="0" e3="0" e4="0" e5="1" e6="0"/><hc:rotMatrix e1="1" e2="0" e3="0" e4="0" e5="1" e6="0"/></hp:renderingInfo>'
      f'<hp:imgRect><hc:pt0 x="0" y="0"/><hc:pt1 x="{wd}" y="0"/><hc:pt2 x="{wd}" y="{Hd}"/><hc:pt3 x="0" y="{Hd}"/></hp:imgRect>'
      f'<hp:imgClip left="0" right="{rawR}" top="0" bottom="{rawB}"/><hp:inMargin left="0" right="0" top="0" bottom="0"/>'
      f'<hc:img binaryItemIDRef="{img_id}" bright="0" contrast="0" effect="REAL_PIC" alpha="0"/><hp:effects/>'
      f'<hp:sz width="{wd}" widthRelTo="ABSOLUTE" height="{Hd}" heightRelTo="ABSOLUTE" protect="0"/>'
      f'<hp:pos treatAsChar="1" affectLSpacing="0" flowWithText="1" allowOverlap="1" holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="PARA" vertAlign="TOP" horzAlign="CENTER" vertOffset="0" horzOffset="0"/>'
      f'<hp:outMargin left="0" right="0" top="0" bottom="0"/></hp:pic><hp:t/></hp:run>'
      f'<hp:linesegarray><hp:lineseg textpos="0" vertpos="0" vertsize="{Hd}" textheight="{Hd}" baseline="{base}" spacing="1000" horzpos="0" horzsize="{bodyw}" flags="1441792"/></hp:linesegarray></hp:p>')


def load_plan(path):
    """TSV 또는 JSON 플랜 → [(png, section_or_None, anchor), ...]."""
    txt = open(path, encoding="utf-8").read()
    rows = []
    if txt.lstrip().startswith("["):
        for it in json.loads(txt):
            if len(it) == 3: rows.append((it[0], int(it[1]), it[2]))
            else:            rows.append((it[0], None, it[1]))
        return rows
    for ln in txt.splitlines():
        if not ln.strip() or ln.lstrip().startswith("#"): continue
        parts = ln.rstrip("\n").split("\t")
        if len(parts) >= 3:   rows.append((parts[0].strip(), int(parts[1]), "\t".join(parts[2:])))
        elif len(parts) == 2: rows.append((parts[0].strip(), None, parts[1]))
        else: raise SystemExit(f"플랜 행 형식 오류(탭 구분 2~3열): {ln!r}")
    return rows


def inherit_ids(sx, apos, parapr_override, charpr_override):
    """앵커가 속한 문단의 paraPrIDRef·charPrIDRef 상속(없으면 0, override 우선)."""
    pstart = sx.rfind("<hp:p ", 0, apos)
    parapr = parapr_override
    charpr = charpr_override
    if pstart != -1:
        ptag = sx[pstart: sx.find(">", pstart) + 1]
        if parapr is None:
            m = re.search(r'paraPrIDRef="(\d+)"', ptag); parapr = m.group(1) if m else "0"
        if charpr is None:
            pend = sx.find("</hp:p>", apos)
            mc = re.search(r'charPrIDRef="(\d+)"', sx[pstart:pend if pend != -1 else apos])
            charpr = mc.group(1) if mc else "0"
    return (parapr or "0"), (charpr or "0")


def main():
    ap = argparse.ArgumentParser(description="hwpx에 그림을 앵커 기준 일괄 삽입")
    ap.add_argument("--hwpx", required=True)
    ap.add_argument("--plan", required=True, help="TSV/JSON 플랜 파일")
    ap.add_argument("--figdir", default=None, help="PNG 폴더(기본: 플랜 파일과 같은 폴더의 figs/)")
    ap.add_argument("--width", type=int, default=32000, help="이미지 표시폭 HWPUNIT")
    ap.add_argument("--bodywidth", type=int, default=None, help="lineseg 가로폭(본문폭). 기본=--width")
    ap.add_argument("--parapr", default=None, help="paraPrIDRef 강제 지정(기본: 앵커 상속)")
    ap.add_argument("--charpr", default=None, help="charPrIDRef 강제 지정(기본: 앵커 상속)")
    ap.add_argument("--no-backup", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="앵커 탐색만 하고 저장 안 함")
    ap.add_argument("--before", action="store_true", help="이미지를 앵커 문단 앞에 삽입(기본: 뒤)")
    a = ap.parse_args()

    F = a.hwpx
    WD = a.width; BODYW = a.bodywidth or a.width
    figdir = a.figdir or os.path.join(os.path.dirname(os.path.abspath(a.plan)), "figs")
    plan = load_plan(a.plan)

    zin = zipfile.ZipFile(F, "r"); names = zin.namelist()
    data = {n: zin.read(n) for n in names}; zin.close()
    sec = {n: data[n].decode("utf-8") for n in names
           if n.startswith("Contents/section") and n.endswith(".xml")}
    hpf = data["Contents/content.hpf"].decode("utf-8")

    # 기존 image 항목 최대번호 → 다음 번호부터
    existing = [int(m) for m in re.findall(r'id="image(\d+)"', hpf)]
    nxt = (max(existing) + 1) if existing else 1

    new_items = []; new_bins = {}; errors = []
    for k, (png, sidx, anchor) in enumerate(plan):
        fp = os.path.join(figdir, png)
        if not os.path.exists(fp):
            errors.append((png, "PNG NOT FOUND", fp)); continue
        # 섹션 결정
        if sidx is not None:
            target = f"Contents/section{sidx}.xml"
            if target not in sec: errors.append((png, "SECTION MISSING", target)); continue
            cands = [target]
        else:
            cands = [n for n, sx in sec.items() if anchor in sx]
        hit = [n for n in cands if anchor in sec[n]]
        if not hit:
            errors.append((png, "ANCHOR NOT FOUND", anchor[:40])); continue
        if len(hit) > 1 or sec[hit[0]].count(anchor) > 1:
            errors.append((png, "ANCHOR NOT UNIQUE", anchor[:40])); continue
        n = hit[0]; sx = sec[n]; apos = sx.find(anchor)
        if a.dry_run:
            print(f"  OK  {png:32s} -> {n}"); continue
        parapr, charpr = inherit_ids(sx, apos, a.parapr, a.charpr)
        imgid = f"image{nxt}"; pid = 2200000000 + nxt * 97; iid = 1100000000 + nxt * 131; nxt += 1
        pw, ph = Image.open(fp).size
        if a.before:
            pstart = sx.rfind("<hp:p ", 0, apos)
            ins = pstart if pstart != -1 else apos
            sec[n] = sx[:ins] + pic_para(imgid, pid, iid, pw, ph, WD, BODYW, parapr, charpr) + sx[ins:]
        else:
            close = sx.find("</hp:p>", apos) + len("</hp:p>")
            sec[n] = sx[:close] + pic_para(imgid, pid, iid, pw, ph, WD, BODYW, parapr, charpr) + sx[close:]
        new_items.append(f'<opf:item id="{imgid}" href="BinData/{imgid}.png" media-type="image/png" isEmbeded="1"/>')
        new_bins[f"BinData/{imgid}.png"] = open(fp, "rb").read()
        print(f"  {imgid:8s} <= {png:32s} ({pw}x{ph}) -> {n}  [paraPr {parapr}]")

    if errors:
        print("\n!!! ERRORS:")
        for e in errors: print("   ", e)
    if a.dry_run:
        print("\n[dry-run] 저장하지 않음."); return
    if not new_bins:
        print("\n삽입할 그림이 없습니다(에러 확인)."); return

    # manifest: </opf:manifest> 앞에 새 item 추가(없으면 image1 뒤 폴백)
    if "</opf:manifest>" in hpf:
        pos = hpf.find("</opf:manifest>")
        hpf = hpf[:pos] + "".join(new_items) + hpf[pos:]
    else:
        anchor_item = hpf.find('<opf:item')
        end = hpf.find("/>", anchor_item) + 2
        hpf = hpf[:end] + "".join(new_items) + hpf[end:]

    # XML well-formed 검증
    for n, sx in sec.items():
        ET.fromstring(sx); data[n] = sx.encode("utf-8")
    ET.fromstring(hpf); data["Contents/content.hpf"] = hpf.encode("utf-8")
    print("\nXML well-formed: OK")

    if not a.no_backup:
        bak = F + ".bak"
        if not os.path.exists(bak):
            import shutil; shutil.copy(F, bak); print("backup ->", bak)

    tmp = F + ".tmp"
    zout = zipfile.ZipFile(tmp, "w")
    zout.writestr(zipfile.ZipInfo("mimetype"), data["mimetype"], compress_type=zipfile.ZIP_STORED)
    for n in names:
        if n == "mimetype": continue
        zout.writestr(n, data[n], compress_type=zipfile.ZIP_DEFLATED)
    for bn, bd in new_bins.items():
        zout.writestr(bn, bd, compress_type=zipfile.ZIP_DEFLATED)
    zout.close(); os.replace(tmp, F)
    print("saved ->", F, os.path.getsize(F))
    print("inserted:", len(new_bins), "images")


if __name__ == "__main__":
    main()
