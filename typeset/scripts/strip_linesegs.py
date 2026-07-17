# -*- coding: utf-8 -*-
"""Strip every <hp:linesegarray> from a hwpx so Hangul reopens it cleanly.

Use this whenever you have edited an existing (Hangul-saved) hwpx from Python —
especially header.xml — and Hangul then refuses to open it with the
"파일 손상/유출 위험" / "문서가 손상되었거나 변조되었을 가능성" tamper dialog
(the COM Open returns False; the GUI hard-blocks even after clicking through).

linesegarray is Hangul's own cached line-break layout. Removing it section-wide
makes Hangul recompute layout on open and load without the warning. Pagination is
preserved because the cache was Hangul's output on this same machine/fonts —
but ALWAYS re-export to PDF and re-check page count afterward.

Rules (SKILL.md 함정 3):
  * Must reach 0 occurrences across ALL Contents/section*.xml — partial removal
    does NOT clear the block.
  * Repack with mimetype STORED (first entry, uncompressed).
  * A .before_stripseg.hwpx backup is written next to the file.

Usage:
    python strip_linesegs.py <book.hwpx>
"""
from __future__ import annotations

import os
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path


def strip(hwpx: Path) -> int:
    backup = hwpx.with_name(hwpx.stem + ".before_stripseg.hwpx")
    if not backup.exists():
        shutil.copy2(hwpx, backup)

    with zipfile.ZipFile(hwpx, "r") as zin:
        names = zin.namelist()
        data = {name: zin.read(name) for name in names}

    total = 0
    for name in names:
        if re.match(r"Contents/section\d+\.xml", name):
            xml = data[name].decode("utf-8")
            before = xml.count("<hp:linesegarray")
            xml = re.sub(r"<hp:linesegarray>.*?</hp:linesegarray>", "", xml, flags=re.S)
            xml = xml.replace("<hp:linesegarray/>", "")
            after = xml.count("<hp:linesegarray")
            total += before - after
            data[name] = xml.encode("utf-8")
            print(f"{name}: removed {before - after} (remaining {after})")

    fd, tmp_name = tempfile.mkstemp(suffix=".hwpx", dir=str(hwpx.parent))
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED) as zout:
            for name in names:
                compress = zipfile.ZIP_STORED if name == "mimetype" else zipfile.ZIP_DEFLATED
                zout.writestr(name, data[name], compress_type=compress)
        shutil.move(str(tmp), hwpx)
    finally:
        if tmp.exists():
            tmp.unlink()

    print(f"total removed: {total}")
    print(f"backup: {backup}")
    return total


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("usage: python strip_linesegs.py <book.hwpx>")
    strip(Path(sys.argv[1]).resolve())


if __name__ == "__main__":
    main()
