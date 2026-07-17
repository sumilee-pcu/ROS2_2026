# -*- coding: utf-8 -*-
"""Extract plain text from a HWPX file.

HWPX files are ZIP archives. This helper reads either the preview text
(`Preview/PrvText.txt`) or the section XML files (`Contents/section*.xml`)
and writes UTF-8 plain text to stdout or a file.

Usage:
  python scripts/hwpx_text.py input.hwpx
  python scripts/hwpx_text.py input.hwpx --source sections --out text.txt
"""

from __future__ import annotations

import argparse
import html
import re
import sys
import zipfile
from pathlib import Path


SECTION_RE = re.compile(r"Contents/section(\d+)\.xml$")


def _configure_stdout() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass


def _sorted_sections(names: list[str]) -> list[str]:
    sections = []
    for name in names:
        match = SECTION_RE.fullmatch(name)
        if match:
            sections.append((int(match.group(1)), name))
    return [name for _, name in sorted(sections)]


def extract_preview(zf: zipfile.ZipFile) -> str:
    if "Preview/PrvText.txt" not in zf.namelist():
        return ""
    data = zf.read("Preview/PrvText.txt")
    for encoding in ("utf-8", "utf-16", "cp949"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def _paragraph_text(paragraph_xml: str) -> str:
    pieces: list[str] = []
    token_re = re.compile(
        r"<hp:t(?:\s[^>]*)?>(.*?)</hp:t>|<hp:(?:lineBreak|br)\b[^>]*/>|<hp:tab\b[^>]*/>",
        re.S,
    )
    for match in token_re.finditer(paragraph_xml):
        if match.group(1) is not None:
            pieces.append(match.group(1))
        else:
            token = match.group(0)
            if token.startswith("<hp:tab"):
                pieces.append("\t")
            else:
                pieces.append("\n")
    return html.unescape("".join(pieces)).strip()


def extract_sections(zf: zipfile.ZipFile) -> str:
    paragraphs: list[str] = []
    for name in _sorted_sections(zf.namelist()):
        section_xml = zf.read(name).decode("utf-8", errors="replace")
        for match in re.finditer(r"<hp:p\b[^>]*>(.*?)</hp:p>", section_xml, re.S):
            text = _paragraph_text(match.group(1))
            if text:
                paragraphs.append(text)
    return "\n".join(paragraphs)


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in text.split("\n")]
    return "\n".join(lines).strip() + ("\n" if lines else "")


def extract_text(path: Path, source: str = "auto") -> str:
    with zipfile.ZipFile(path) as zf:
        if source == "preview":
            text = extract_preview(zf)
        elif source == "sections":
            text = extract_sections(zf)
        else:
            text = extract_preview(zf).strip()
            if not text:
                text = extract_sections(zf)
    return normalize_text(text)


def main() -> None:
    _configure_stdout()
    parser = argparse.ArgumentParser(description="Extract plain text from HWPX.")
    parser.add_argument("hwpx", type=Path)
    parser.add_argument(
        "--source",
        choices=("auto", "preview", "sections"),
        default="auto",
        help="Text source. auto uses Preview text first, then section XML.",
    )
    parser.add_argument("--out", type=Path, help="Write UTF-8 text to this file.")
    args = parser.parse_args()

    text = extract_text(args.hwpx, args.source)
    if args.out:
        args.out.write_text(text, encoding="utf-8", newline="\n")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
