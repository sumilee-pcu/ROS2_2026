# -*- coding: utf-8 -*-
"""부·장 간지(표제지) + 반표지/속표지 파라메트릭 생성기 — 이수미 시리즈 내지 디자인.

09_AI영상분석(NAVY) → 블록체인(진초록)으로 검증된 디자인을 spec JSON으로 일반화.
책마다 팔레트·문안만 바꾼 spec을 만들면 전체 간지를 한 번에 뽑는다.

사용:
    python gen_openers.py <opener_spec.json> [출력폴더]
스펙 템플릿: assets/opener_spec.template.json (블록체인 실물 값)

출력(300DPI PNG):
    partN_opener.png  chNN_opener.png  title_front.png  title_inner.png
주입은 책별 스크립트(hwpx_insert_figs.py 또는 전용 inject)로 — 생성과 주입은 분리.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
import matplotlib.patches as mp
import json, os, sys, time

sys.stdout.reconfigure(encoding='utf-8')

FONT_DIRS = [
    os.path.expandvars(r'%LOCALAPPDATA%/Microsoft/Windows/Fonts'),
    r'C:/Windows/Fonts',
    os.path.expanduser('~/Library/Fonts'),   # Mac 이식 대비
    '/Library/Fonts', '/System/Library/Fonts',
]

def find_font(*names):
    """이름 후보를 순서대로 찾아 첫 실물 경로 반환(없으면 None)."""
    for n in names:
        for d in FONT_DIRS:
            p = os.path.join(d, n)
            if os.path.exists(p):
                return p
    return None


class OpenerGen:
    def __init__(self, spec, outdir):
        self.s = spec
        self.pal = spec['palette']
        self.fmt = spec.get('format', {})
        self.W_IN = self.fmt.get('w_in', 4.537)
        self.H_IN = self.fmt.get('h_in', 7.28)
        self.dpi = self.fmt.get('dpi', 300)
        self.out = outdir
        os.makedirs(outdir, exist_ok=True)

        # 한글 폰트 자동 탐색 (Windows→Mac 이식 대비, figlib과 동일 순서)
        fams = {f.name for f in fm.fontManager.ttflist}
        fam = next((f for f in ['Malgun Gothic', 'Apple SD Gothic Neo', 'AppleGothic',
                                'NanumGothic', 'Noto Sans KR'] if f in fams), 'sans-serif')
        plt.rcParams['font.family'] = fam
        plt.rcParams['axes.unicode_minus'] = False
        self.BOLD = fm.FontProperties(family=fam, weight='bold')
        semi = find_font('malgunsl.ttf')
        self.SEMI = fm.FontProperties(fname=semi) if semi else self.BOLD
        # 표제지 라틴 대제목: GmarketSans → 없으면 Malgun bold
        disp = find_font('GmarketSansTTFBold.ttf', 'GmarketSansBold.otf')
        self.DISPLAY = fm.FontProperties(fname=disp) if disp else self.BOLD

    # --- 공통 캔버스 ---
    def blank(self, bg):
        fig = plt.figure(figsize=(self.W_IN, self.H_IN), dpi=self.dpi)
        ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
        ax.axis('off')
        ax.add_patch(mp.Rectangle((0, 0), 1, 1, facecolor=bg, edgecolor='none'))
        return fig, ax

    def save(self, fig, name):
        fig.savefig(os.path.join(self.out, name), dpi=self.dpi)
        plt.close(fig)

    # --- 장 간지: 어두운 배경 + 장번호 워터마크 + 우측정렬 제목 ---
    def chapter_opener(self, num, title_lines, intro):
        p = self.pal
        fig, ax = self.blank(p['ch_bg'])
        ax.text(0.91, 0.955, f'제{num}장', ha='right', va='top', fontsize=13,
                color=p['white'], fontproperties=self.BOLD)
        ax.plot([0.95, 0.95], [0.90, 0.975], color=p['white'], lw=0.8)
        ax.plot([0.09, 0.62], [0.865, 0.865], color=p['white'], lw=0.8)
        ax.plot([0.62, 0.62], [0.865, 0.70], color=p['white'], lw=0.8)
        ax.text(0.07, 0.80, f'{num:02d}', ha='left', va='center', fontsize=110,
                color=p['ch_watermark'], alpha=0.55, fontproperties=self.BOLD)
        fs = 26.5 if max(len(t) for t in title_lines) <= 10 else 22
        y = 0.575 + (len(title_lines) - 1) * 0.042
        for i, t in enumerate(title_lines):
            ax.text(0.91, y - i * 0.084 * fs / 26.5, t, ha='right', va='center',
                    fontsize=fs, color=p['white'], fontproperties=self.BOLD)
        rule_y = y - (len(title_lines) - 1) * 0.084 * fs / 26.5 - 0.040
        ax.plot([0.53, 0.91], [rule_y, rule_y], color=p['gold'], lw=1.4)
        ax.text(0.91, rule_y - 0.048, intro, ha='right', va='top', fontsize=9.2,
                color=p['ch_intro'], linespacing=1.9)
        ax.plot([0.91, 0.91], [0.30, 0.155], color=p['white'], lw=0.8)
        ax.plot([0.91, 0.45], [0.155, 0.155], color=p['white'], lw=0.8)
        ax.plot([0.09, 0.125], [0.062, 0.062], color=p['gold'], lw=1.6)
        ax.text(0.148, 0.062, self.s['book']['footer'], ha='left', va='center',
                fontsize=6.8, color=p['gold'], fontproperties=self.SEMI)
        self.save(fig, f'ch{num:02d}_opener.png')

    # --- 부 간지: 밝은 배경 + PART 넘버 ---
    def part_opener(self, num, title, intro):
        p = self.pal
        fig, ax = self.blank(p['part_bg'])
        ax.text(0.09, 0.90, title, ha='left', va='top', fontsize=21.5,
                color=p['part_fg'], fontproperties=self.BOLD)
        ax.plot([0.09, 0.22], [0.852, 0.852], color=p['gold'], lw=2.2)
        ax.plot([0.09, 0.60], [0.52, 0.52], color=p['gold'], lw=1.2)
        ax.add_patch(mp.Rectangle((0.085, 0.512), 0.022, 0.016,
                                  facecolor=p['gold'], edgecolor='none'))
        ax.text(0.635, 0.522, 'PART', ha='left', va='center', fontsize=13,
                color=p['part_fg'], fontproperties=self.BOLD)
        ax.text(0.775, 0.525, str(num), ha='left', va='center', fontsize=88,
                color=p['part_fg'], fontproperties=self.BOLD)
        ax.text(0.09, 0.16, intro, ha='left', va='top', fontsize=8.4,
                color=p['part_fg'], linespacing=2.0, fontproperties=self.SEMI)
        self.save(fig, f'part{num}_opener.png')

    # --- 반표지(title_front)·속표지(title_inner): 부제 + 골드 대제목 ---
    def title_page(self, name, bg, fg_sub, author_line=None, tick=False):
        p = self.pal
        b = self.s['book']
        fig, ax = self.blank(bg)
        if tick:  # 반표지 우상단 세로 틱
            ax.plot([0.915, 0.915], [0.870, 0.935], color=p['ch_watermark'], lw=2.0)
        ax.text(0.915, 0.828, b['subtitle'], ha='right', va='center', fontsize=13.5,
                color=fg_sub, fontproperties=self.BOLD)
        ax.plot([0.70, 0.915], [0.793, 0.793], color=p['gold'], lw=2.0)
        n = len(b['title_lines'])
        fs = 46
        y0 = 0.700
        for i, t in enumerate(b['title_lines']):
            ax.text(0.915, y0 - i * 0.105, t, ha='right', va='center',
                    fontsize=fs, color=p['gold'], fontproperties=self.DISPLAY)
        if author_line:
            ax.text(0.915, 0.368, author_line, ha='right', va='center', fontsize=12.5,
                    color=fg_sub, fontproperties=self.BOLD)
            ax.plot([0.80, 0.915], [0.340, 0.340], color=fg_sub, lw=1.2)
        ax.plot([0.085, 0.150], [0.093, 0.093], color=p['gold'], lw=1.6)
        ax.text(0.178, 0.093, b['series_label'], ha='left', va='center', fontsize=11,
                color=(p['gold'] if tick else p['part_fg']), fontproperties=self.SEMI)
        self.save(fig, f'{name}.png')

    def run(self):
        t0 = time.time()
        made = []
        for it in self.s.get('parts', []):
            self.part_opener(it['num'], it['title'], '\n'.join(it['intro']))
            made.append(f"part{it['num']}")
        for it in self.s.get('chapters', []):
            self.chapter_opener(it['num'], it['title_lines'], '\n'.join(it['intro']))
            made.append(f"ch{it['num']:02d}")
        tp = self.s.get('title_pages', {})
        if tp.get('front', True):
            self.title_page('title_front', self.pal['ch_bg'], self.pal['ch_intro'], tick=True)
            made.append('title_front')
        if tp.get('inner', True):
            self.title_page('title_inner', self.pal['part_bg'], self.pal['part_fg'],
                            author_line=self.s['book'].get('author_line'))
            made.append('title_inner')
        print(f'{len(made)}종 생성 ({time.time()-t0:.1f}s) -> {self.out}')
        print('  ' + ', '.join(made))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    spec_path = sys.argv[1]
    spec = json.load(open(spec_path, encoding='utf-8'))
    outdir = sys.argv[2] if len(sys.argv) > 2 else \
        os.path.join(os.path.dirname(os.path.abspath(spec_path)), 'openers_out')
    OpenerGen(spec, outdir).run()
