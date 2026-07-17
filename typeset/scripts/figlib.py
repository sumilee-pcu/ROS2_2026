# -*- coding: utf-8 -*-
"""figlib — 교재 삽화(개념 다이어그램) 공용 스타일·프리미티브 라이브러리.

박스·화살표·스텝·패널 프리미티브로 흐름도/비교도/와이어프레임을 그린다.
개별 그림(책별 데이터)은 각 책 폴더의 gen_figs 스크립트에서 import해서 사용.
원본: 생성형AI활용첫걸음집필/gen_figs.py 를 범용화(2026-06).

사용 예:
    from figlib import *                 # 스킬 scripts 폴더를 path에 추가하거나 복사
    set_outdir("figs")
    fig, ax = canvas(8.6, 3.4, ylim=6.0)
    gtitle(ax, 8, 5.6, "그림 1-3  LLM 응답 생성 흐름")
    hflow(ax, [("입력","사용자 프롬프트",BLUE_L,BLUE),
               ("토큰화","문장 분할",PURPLE_L,PURPLE),
               ("응답","문장 완성",GOLD_L,GOLD)], y=3.0, w=3.3, h=2.0, gap=0.9)
    save(fig, "fig1_3_tokenflow.png")     # 300DPI, 흰 배경, figs/에 저장

설치 확인:  python figlib.py --demo   →  figs/_figlib_demo.png 생성
"""
import os, sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
try:
    from PIL import Image
except Exception:
    Image = None


# ---- 한글 폰트(여러 OS 대응; 없으면 첫 한글 폰트로 폴백) ----
def _setup_font():
    for p in (r"C:/Windows/Fonts/malgun.ttf", r"C:/Windows/Fonts/malgunbd.ttf",
              "/System/Library/Fonts/AppleSDGothicNeo.ttc",
              "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"):
        if os.path.exists(p):
            try: fm.fontManager.addfont(p)
            except Exception: pass
    fams = {f.name for f in fm.fontManager.ttflist}
    for cand in ("Malgun Gothic", "Apple SD Gothic Neo", "AppleGothic",
                 "NanumGothic", "Noto Sans CJK KR", "Noto Sans KR"):
        if cand in fams:
            plt.rcParams["font.family"] = cand
            break
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["savefig.dpi"] = 300

_setup_font()

# ---- 통일 타이포 ----
F_TITLE = 15   # 그림 제목
F_HEAD  = 13   # 박스 헤더 / 스텝 제목 (bold)
F_BODY  = 11.5 # 본문 / 인용 / 불릿
F_SUB   = 10.5 # 보조 설명(회색)

# ---- 통일 팔레트 ----
BLUE='#5B8FF9'; BLUE_L='#DCE8FF'; PURPLE='#8E5BD9'; PURPLE_L='#ECE2FA'
GOLD='#F2B705'; GOLD_L='#FCEFC7'; GREEN='#3FAE6B'; GREEN_L='#E6F6EC'
RED='#D98E8E'; RED_L='#F7E4E4'; INK='#2B2B43'; GRAY='#7A7A8C'
HEAD_BLUE='#2F5BBF'; HEAD_RED='#B5524F'; HEAD_GREEN='#2E8B57'; HEAD_PURPLE='#6B3FB0'

_OUTDIR = "figs"
def set_outdir(path):
    """그림 저장 폴더 지정(없으면 생성)."""
    global _OUTDIR
    _OUTDIR = path
    os.makedirs(_OUTDIR, exist_ok=True)
os.makedirs(_OUTDIR, exist_ok=True)


# ---- 캔버스 ----
def canvas(w_in, h_in, xlim=16, ylim=6.0, dpi=300):
    """가로 16 단위 좌표계 캔버스. (fig, ax) 반환."""
    fig, ax = plt.subplots(figsize=(w_in, h_in), dpi=dpi)
    ax.set_xlim(0, xlim); ax.set_ylim(0, ylim); ax.axis("off")
    return fig, ax


# ---- 프리미티브 ----
def box(ax, x, y, w, h, fc, ec, lw=2):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.08", fc=fc, ec=ec, lw=lw))

def T(ax, x, y, s, size=F_BODY, color=INK, weight="normal", ha="center", va="center"):
    ax.text(x, y, s, ha=ha, va=va, fontsize=size, fontweight=weight, color=color)

def arrow(ax, x1, y1, x2, y2, color=BLUE, lw=2.4, rad=0.0):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
        mutation_scale=20, lw=lw, color=color, shrinkA=2, shrinkB=2,
        connectionstyle="arc3,rad=%s" % rad))

def gtitle(ax, cx, y, s):
    """그림 제목(굵게, 중앙)."""
    T(ax, cx, y, s, size=F_TITLE, color=INK, weight="bold")

def save(fig, name):
    """figs/<name>으로 300DPI·흰배경 저장."""
    os.makedirs(_OUTDIR, exist_ok=True)
    p = os.path.join(_OUTDIR, name)
    fig.savefig(p, bbox_inches="tight", facecolor="white", pad_inches=0.16)
    plt.close(fig)
    if Image:
        print(name, Image.open(p).size)
    else:
        print(name, "saved")
    return p


# ---- 합성 컴포넌트 ----
def stepbox(ax, x, y, w, h, fc, ec, title, sub=None):
    """스텝 박스(제목 + 보조설명). 흐름도 공통."""
    box(ax, x, y, w, h, fc, ec)
    if sub:
        T(ax, x+w/2, y+h*0.60, title, size=F_HEAD, weight="bold")
        T(ax, x+w/2, y+h*0.28, sub, size=F_SUB, color=GRAY)
    else:
        T(ax, x+w/2, y+h/2, title, size=F_HEAD, weight="bold")

TOPGAP = 0.62
def panel(ax, x, y, w, h, fc, ec, header, hcolor):
    """헤더가 상단에 붙는 패널. 비교/목록형 공통."""
    box(ax, x, y, w, h, fc, ec)
    T(ax, x+w/2, y+h-TOPGAP, header, size=F_HEAD, weight="bold", color=hcolor)

def hflow(ax, steps, y, w, h, gap, acolor=BLUE):
    """가로 흐름도. steps=[(title, sub, fc, ec), ...]. 중앙 정렬. 박스 중심 x 리스트 반환."""
    x = (16 - (len(steps)*w + (len(steps)-1)*gap)) / 2
    cxs = []
    for t, s, fc, ec in steps:
        stepbox(ax, x, y, w, h, fc, ec, t, s); cxs.append(x+w/2); x += w+gap
    for i in range(len(steps)-1):
        arrow(ax, cxs[i]+w/2, y+h/2, cxs[i+1]-w/2, y+h/2, color=acolor)
    return cxs

def list_panel(ax, x, y, w, h, fc, ec, header, hcolor, items, itemcolor=INK, sub=None):
    """헤더 + 불릿 목록 패널. 비교 양쪽에 쓰기 좋음."""
    panel(ax, x, y, w, h, fc, ec, header, hcolor)
    yy = y + h - TOPGAP - 0.95
    if sub:
        T(ax, x+w/2, yy, sub, size=F_SUB, color=GRAY); yy -= 0.8
    for it in items:
        T(ax, x+0.65, yy, "•  "+it, size=F_BODY, color=itemcolor, ha="left"); yy -= 0.8


# ---- 설치 확인 데모 ----
def _demo():
    set_outdir("figs")
    fig, ax = canvas(8.6, 3.4, ylim=6.0)
    gtitle(ax, 8, 5.6, "그림 0-0  figlib 데모 — 흐름도")
    cxs = hflow(ax, [("입력","사용자 프롬프트",BLUE_L,BLUE),
                     ("처리","모델 추론",PURPLE_L,PURPLE),
                     ("출력","응답 생성",GREEN_L,GREEN)],
                y=2.6, w=3.6, h=2.0, gap=1.0)
    arrow(ax, cxs[2], 2.6-0.02, cxs[1], 2.6-0.02, color=GRAY, lw=1.8, rad=-0.5)
    T(ax, 8, 1.2, "한글 폰트·팔레트·프리미티브가 정상이면 이 그림이 깨지지 않는다",
      size=F_SUB, color=GRAY)
    p = save(fig, "_figlib_demo.png")
    print("DEMO OK ->", p)

if __name__ == "__main__":
    if "--demo" in sys.argv:
        _demo()
    else:
        print(__doc__)
