"""MD -> B5 HWPX 변환 래퍼 (ROS2 첫걸음 전용).

템플릿: typeset/template/ROS2첫걸음1_B5_이수미_1장_최종.hwpx
charmap: h1:22,h2:15,h3:7,bold:13,body:11,quote:9

사용:
    python scripts/md2hwpx.py <입력.md> <출력.hwpx>
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
TEMPLATE = ROOT / "typeset/template/ROS2첫걸음1_B5_이수미_1장_최종.hwpx"
CHARMAP = "h1:22,h2:15,h3:7,bold:13,body:11,quote:9,code:39,codefill:6,opener_item:37"

CONVERT = ROOT / "typeset/scripts/md2hwpx.py"
CODE_BOXES = ROOT / "typeset/scripts/hwpx_code_boxes.py"
VALIDATE = ROOT / "typeset/scripts/validate_hwpx.py"


def run(args):
    result = subprocess.run([sys.executable] + args, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout.strip())
    if result.stderr:
        print(result.stderr.strip(), file=sys.stderr)
    if result.returncode != 0:
        sys.exit(result.returncode)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("사용: python scripts/md2hwpx.py <입력.md> <출력.hwpx>")
        sys.exit(1)

    md_path = sys.argv[1]
    out_path = sys.argv[2]

    print(f"[1/3] 변환: {md_path} → {out_path}")
    run([str(CONVERT), "--template", str(TEMPLATE), "--charmap", CHARMAP,
         "--out", out_path, md_path])

    print(f"[2/3] 코드박스 변환: {out_path}")
    run([str(CODE_BOXES), out_path])

    print(f"[3/3] 검증: {out_path}")
    run([str(VALIDATE), out_path])
