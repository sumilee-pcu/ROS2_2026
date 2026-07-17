# -*- coding: utf-8 -*-
"""hwpx 무결성 검증: ZIP 구조(mimetype 첫 항목·무압축) + 모든 XML 파싱.

사용: python validate_hwpx.py <파일.hwpx>
출력 마지막 줄이 VALID HWPX 면 한글에서 열린다. (최종 확인은 한글 뷰어로)
"""
import sys, zipfile
import xml.parsers.expat as X


def main():
    p = sys.argv[1]
    z = zipfile.ZipFile(p)
    names = z.namelist()
    print("entries:", len(names))
    print("first entry:", names[0])
    stored = z.getinfo("mimetype").compress_type == zipfile.ZIP_STORED
    print("mimetype stored(uncompressed):", stored)
    print("mimetype content:", z.read("mimetype").decode("utf-8"))
    bad = 0
    for n in names:
        if n.endswith((".xml", ".hpf", ".rdf")):
            try:
                x = X.ParserCreate()
                x.Parse(z.read(n), 1)
            except Exception as e:
                bad += 1
                print("XML ERROR:", n, "->", e)
    print("xml files checked, errors:", bad)
    if "Contents/section0.xml" in names:
        print("section0 size:", z.getinfo("Contents/section0.xml").file_size)
    print("VALID HWPX" if bad == 0 and names[0] == "mimetype" and stored else "PROBLEM")


if __name__ == "__main__":
    main()
