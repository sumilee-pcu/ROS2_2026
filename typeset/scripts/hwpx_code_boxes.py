# -*- coding: utf-8 -*-
"""코드박스 정규화: md2hwpx가 만든 1열 코드'표'를 블록체인식 '테두리 문단'으로 변환.

md2hwpx는 코드펜스를 1열 표로 조판하는데, 표 셀 패딩 때문에 코드가 좌측 액센트바에서
떨어지고 폭·정렬이 불규칙해진다. 이 스크립트는 각 1열 코드표를 연결된 테두리 문단
(border + connect=1)으로 바꿔, 코드가 좌측바에 밀착하고 박스가 본문폭에 규칙적으로 맞게 한다.

전제: 코드표에 이미 코드 스타일(Consolas charPr + 좌측바 borderFill)이 입혀져 있어야 한다
(hwpx-book의 스타일 단계 또는 책별 restyle 스크립트가 1열 표의 borderFill/charPr을 코드용으로
바꿔 둔 상태). 이 스크립트는 그 표를 문단으로 옮기기만 한다 — id는 파일에서 실측한다.

사용:
  python hwpx_code_boxes.py <in.hwpx> [out.hwpx]
     out 생략 시 제자리 덮어쓰기(한글에서 열려 있으면 잠김 — 새 out 경로 지정).
옵션:
  --margin N       좌우 여백 HWPUNIT (기본 1100)
  --linespacing P  줄간격 % (기본 140)
"""
import zipfile, re, os, sys


def convert_section(sec, hdr):
    tbls = list(re.finditer(r'<hp:tbl\b.*?</hp:tbl>', sec, re.S))
    codet = [m for m in tbls if 'colCnt="1"' in m.group(0)]
    if not codet:
        return sec, hdr, 0, None
    # 실측: 코드표의 셀 텍스트 run charPr, 표 borderFill
    first = codet[0].group(0)
    run_cprs = re.findall(r'<hp:run charPrIDRef="(\d+)"><hp:t>', first)
    code_cpr = run_cprs[0] if run_cprs else re.search(r'charPrIDRef="(\d+)"', first).group(1)
    bf = re.search(r'<hp:tbl[^>]*borderFillIDRef="(\d+)"', first).group(1)
    # 신규 코드 paraPr id
    max_ppr = max(int(x) for x in re.findall(r'<hh:paraPr id="(\d+)"', hdr))
    new_ppr = max_ppr + 1
    itemcnt = re.search(r'<hh:paraProperties itemCnt="(\d+)"', hdr).group(1)
    ppr_xml = (
        f'<hh:paraPr id="{new_ppr}" tabPrIDRef="0" condense="0" fontLineHeight="0" snapToGrid="0" suppressLineNumbers="0" checked="0">'
        '<hh:align horizontal="LEFT" vertical="BASELINE"/><hh:heading type="NONE" idRef="0" level="0"/>'
        '<hh:breakSetting breakLatinWord="KEEP_WORD" breakNonLatinWord="KEEP_WORD" widowOrphan="0" keepWithNext="0" keepLines="0" pageBreakBefore="0" lineWrap="BREAK"/>'
        '<hh:autoSpacing eAsianEng="0" eAsianNum="0"/><hh:margin><hc:intent value="0" unit="HWPUNIT"/>'
        f'<hc:left value="{MARGIN}" unit="HWPUNIT"/><hc:right value="{MARGIN}" unit="HWPUNIT"/><hc:prev value="200" unit="HWPUNIT"/><hc:next value="200" unit="HWPUNIT"/></hh:margin>'
        f'<hh:lineSpacing type="PERCENT" value="{LINESPACING}" unit="HWPUNIT"/>'
        f'<hh:border borderFillIDRef="{bf}" offsetLeft="350" offsetRight="350" offsetTop="400" offsetBottom="400" connect="1" ignoreMargin="0"/></hh:paraPr>'
    )
    hdr = hdr.replace(f'<hh:paraProperties itemCnt="{itemcnt}">',
                      f'<hh:paraProperties itemCnt="{int(itemcnt)+1}">', 1)
    hdr = hdr.replace('</hh:paraProperties>', ppr_xml + '</hh:paraProperties>', 1)

    def cpara(text):
        if text == "":
            return f'<hp:p id="0" paraPrIDRef="{new_ppr}" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0"><hp:run charPrIDRef="{code_cpr}"/></hp:p>'
        return f'<hp:p id="0" paraPrIDRef="{new_ppr}" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0"><hp:run charPrIDRef="{code_cpr}"><hp:t>{text}</hp:t></hp:run></hp:p>'

    repls = []
    for m in codet:
        ts, te = m.start(), m.end()
        ws = sec.rfind('<hp:p ', 0, ts)
        we = sec.find('</hp:p>', te) + len('</hp:p>')
        lines = []
        for pm in re.finditer(r'<hp:p\b[^>]*>(.*?)</hp:p>', m.group(0), re.S):
            tparts = re.findall(r'<hp:t>(.*?)</hp:t>', pm.group(1), re.S)
            lines.append(''.join(tparts))
        repls.append((ws, we, ''.join(cpara(l) for l in lines)))
    for ws, we, new in sorted(repls, reverse=True):
        sec = sec[:ws] + new + sec[we:]
    return sec, hdr, len(codet), (code_cpr, bf, new_ppr)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    global MARGIN, LINESPACING
    MARGIN = 1100
    LINESPACING = 140
    for i, a in enumerate(sys.argv):
        if a == '--margin':
            MARGIN = int(sys.argv[i+1])
        if a == '--linespacing':
            LINESPACING = int(sys.argv[i+1])
    src = args[0]
    out = args[1] if len(args) > 1 else src
    z = zipfile.ZipFile(src)
    M = {n: z.read(n) for n in z.namelist()}
    names = list(z.namelist())
    z.close()
    sec = M["Contents/section0.xml"].decode("utf-8")
    hdr = M["Contents/header.xml"].decode("utf-8")
    sec, hdr, n, info = convert_section(sec, hdr)
    # 외부편집 변조차단 방지
    sec = re.sub(r'<hp:linesegarray>.*?</hp:linesegarray>', '', sec, flags=re.S).replace('<hp:linesegarray/>', '')
    M["Contents/section0.xml"] = sec.encode("utf-8")
    M["Contents/header.xml"] = hdr.encode("utf-8")
    tmp = out + ".tmp"
    with zipfile.ZipFile(tmp, "w") as zo:
        zo.writestr(zipfile.ZipInfo("mimetype"), M["mimetype"], compress_type=zipfile.ZIP_STORED)
        for nm in names:
            if nm == "mimetype":
                continue
            zo.writestr(nm, M[nm], compress_type=zipfile.ZIP_DEFLATED)
    os.replace(tmp, out)
    print(f"converted {n} code tables -> bordered paragraphs {info}")
    print("OUT:", out)


if __name__ == "__main__":
    main()
