# -*- coding: utf-8 -*-
"""Render a .hwpx to PDF via the installed Hangul (한글) COM automation.

Why: hwpx layout (line breaks, page numbers, dot-leader tabs, font embedding)
can only be resolved by Hangul itself — no Python library reproduces it. This is
the reliable way to (a) get the *actual* printed page numbers for a table of
contents, and (b) eyeball-verify an externally edited hwpx.

Safety choices baked in (learned the hard way, 2026-07 blockchain book):
  * Visible=True — an invisible window HARD-BLOCKS on any modal dialog and the
    call hangs forever.
  * SetMessageBoxMode — auto-answers dialogs (incl. Hangul's tamper/access-risk
    prompt) so the run never stalls. If that prompt appears at all, the real fix
    is to strip linesegarray first (see strip_linesegs / SKILL 함정 3).
  * Does NOT call Quit() by default — Hangul is single-instance, so Quit() would
    close ANY document the user already has open. Instead it closes only the
    document it opened (FileClose). Pass --quit only when you know no other
    Hangul window is open.

Usage:
    python hwpx_pdf_export.py <book.hwpx> [out.pdf] [--quit]
    # out.pdf defaults to <book>.pdf next to the source.

Requires: Windows + 한글(HWPFrame.HwpObject registered) + pywin32.
"""
from __future__ import annotations

import sys
from pathlib import Path

import win32com.client


def export(src: str, pdf: str, quit_app: bool = False) -> bool:
    hwp = win32com.client.gencache.EnsureDispatch("HWPFrame.HwpObject")
    try:
        hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
    except Exception:
        pass
    try:
        hwp.SetMessageBoxMode(0x00020000)  # auto-answer any dialog -> no hang
    except Exception as e:
        print("msgbox mode skip:", e)
    try:
        hwp.XHwpWindows.Item(0).Visible = True  # invisible => modal hard-block
    except Exception as e:
        print("visible skip:", e)

    ok = hwp.Open(src, "", "forceopen:true")
    print("open:", ok)
    if not ok:
        # Almost always Hangul's tamper block on an externally edited file.
        # Fix: strip every <hp:linesegarray> from Contents/section*.xml, repack
        # (mimetype STORED), then retry. See SKILL.md 함정 3.
        print("OPEN FAILED — strip linesegarray and retry (SKILL 함정 3)")
        if quit_app:
            hwp.Quit()
        return False

    ok2 = hwp.SaveAs(pdf, "PDF", "")
    print("saveas pdf:", ok2)

    if quit_app:
        hwp.Quit()
    else:
        try:
            hwp.Run("FileClose")  # close only our doc; keep the app + other docs
            print("closed opened doc (app left running)")
        except Exception as e:
            print("close skip:", e)
    print("done" if ok2 else "SAVE FAILED")
    return bool(ok2)


def main() -> None:
    args = [a for a in sys.argv[1:] if a != "--quit"]
    quit_app = "--quit" in sys.argv
    if not args:
        raise SystemExit("usage: python hwpx_pdf_export.py <book.hwpx> [out.pdf] [--quit]")
    src = str(Path(args[0]).resolve())
    pdf = str(Path(args[1]).resolve()) if len(args) > 1 else str(Path(src).with_suffix(".pdf"))
    ok = export(src, pdf, quit_app)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
