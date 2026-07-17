"""Generate figures for chapter 6 (파라미터와 커스텀 인터페이스)."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os

import matplotlib.font_manager as fm
_available = {f.name for f in fm.fontManager.ttflist}
plt.rcParams['font.family'] = 'NanumGothic' if 'NanumGothic' in _available else 'Malgun Gothic'

plt.rcParams['axes.unicode_minus'] = False

FIGURES = 'docs/02_basics/figures'
os.makedirs(FIGURES, exist_ok=True)

# Colors
BLUE_BG  = '#E8F4FD'
BLUE_EC  = '#2980B9'
BLUE_TC  = '#1A5276'
GREEN_BG = '#EAFAF1'
GREEN_EC = '#27AE60'
GREEN_TC = '#1D8348'
ORANGE_BG = '#FEF9E7'
ORANGE_EC = '#E67E22'
ORANGE_TC = '#784212'
PURPLE_BG = '#F4ECF7'
PURPLE_EC = '#8E44AD'
PURPLE_TC = '#4A235A'
RED_BG   = '#FDEDEC'
RED_EC   = '#E74C3C'
RED_TC   = '#922B21'
GRAY     = '#555555'
DARK     = '#2C3E50'

def rounded_box(ax, x, y, w, h, label, fc, ec, tc, fontsize=10, sublabel=None, sub_fs=8):
    rect = patches.FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.08',
                                   linewidth=1.8, edgecolor=ec, facecolor=fc)
    ax.add_patch(rect)
    if sublabel:
        ax.text(x + w/2, y + h*0.62, label, ha='center', va='center',
                fontsize=fontsize, fontweight='bold', color=tc)
        ax.text(x + w/2, y + h*0.28, sublabel, ha='center', va='center',
                fontsize=sub_fs, color=GRAY)
    else:
        ax.text(x + w/2, y + h/2, label, ha='center', va='center',
                fontsize=fontsize, fontweight='bold', color=tc)

def arrow(ax, x1, y1, x2, y2, color=GRAY, style='->', lw=1.5):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle=style, color=color, lw=lw))


# ══════════════════════════════════════════
# fig6-1: Parameter lifecycle
# declare → get/set (runtime) → YAML file
# ══════════════════════════════════════════
fig, ax = plt.subplots(figsize=(11, 5.5))
ax.set_xlim(-0.2, 11)
ax.set_ylim(0, 5.5)
ax.axis('off')

# Title — well above the dashed box
ax.text(5.5, 5.2, '파라미터 생명주기', ha='center', va='center',
        fontsize=14, fontweight='bold', color=DARK)

# Step 1: declare
rounded_box(ax, 0.3, 2.8, 2.4, 1.2, 'declare_parameter', BLUE_BG, BLUE_EC, BLUE_TC,
            fontsize=12, sublabel='선언 + 기본값', sub_fs=10)

# Step 2: get (code)
rounded_box(ax, 3.5, 3.2, 2.2, 0.8, 'get_parameter', GREEN_BG, GREEN_EC, GREEN_TC,
            fontsize=12)

# Step 3: set (runtime)
rounded_box(ax, 3.5, 2.0, 2.2, 0.8, 'ros2 param set', ORANGE_BG, ORANGE_EC, ORANGE_TC,
            fontsize=12)

# Step 4: YAML
rounded_box(ax, 6.6, 2.8, 2.2, 1.2, 'params.yaml', PURPLE_BG, PURPLE_EC, PURPLE_TC,
            fontsize=12, sublabel='--params-file', sub_fs=10)

# Arrows
arrow(ax, 2.7, 3.4, 3.5, 3.55)
arrow(ax, 2.7, 3.3, 3.5, 2.5)
arrow(ax, 5.7, 3.4, 6.6, 3.4)

# CLI injection box at top
rounded_box(ax, 3.2, 0.5, 5.8, 0.9, '--ros-args  -p name:=value', '#FEF5E4', '#D35400', '#6E2F00',
            fontsize=11, sublabel='CLI 주입', sub_fs=10)
arrow(ax, 5.0, 1.4, 4.6, 2.0)

# Node box encompassing
node_rect = patches.FancyBboxPatch((0.1, 1.7), 5.8, 2.7, boxstyle='round,pad=0.12',
                                    linewidth=2, edgecolor=DARK, facecolor='none',
                                    linestyle='--')
ax.add_patch(node_rect)
ax.text(0.3, 4.2, 'Node', fontsize=12, fontweight='bold', color=DARK)

plt.savefig(f'{FIGURES}/fig6-1.png', dpi=150, bbox_inches='tight',
            facecolor='white', pad_inches=0.15)
plt.close()
print('fig6-1.png done')


# ══════════════════════════════════════════
# fig6-2: Custom interface build pipeline
# .msg/.srv/.action → rosidl → Python/C++ code
# ══════════════════════════════════════════
fig, ax = plt.subplots(figsize=(11, 5.5))
ax.set_xlim(0, 11)
ax.set_ylim(0, 5.5)
ax.axis('off')

ax.text(5.5, 5.15, '커스텀 인터페이스 빌드 파이프라인', ha='center', va='center',
        fontsize=14, fontweight='bold', color=DARK)

# Source files (left column)
src_items = [
    (0.3, 3.8, '.msg', '메시지 정의', GREEN_BG, GREEN_EC, GREEN_TC),
    (0.3, 2.6, '.srv', '서비스 정의', BLUE_BG, BLUE_EC, BLUE_TC),
    (0.3, 1.4, '.action', '액션 정의', ORANGE_BG, ORANGE_EC, ORANGE_TC),
]
for x, y, label, sub, fc, ec, tc in src_items:
    rounded_box(ax, x, y, 1.8, 0.9, label, fc, ec, tc, fontsize=11, sublabel=sub)

# rosidl generator (middle)
rounded_box(ax, 3.2, 2.2, 2.8, 1.8, 'rosidl_generate\n_interfaces', PURPLE_BG, PURPLE_EC, PURPLE_TC,
            fontsize=11)
ax.text(4.6, 2.35, 'CMakeLists.txt', fontsize=8, color=GRAY)

# Arrows from source to rosidl
for y in [4.25, 3.05, 1.85]:
    arrow(ax, 2.1, y, 3.2, 3.1)

# Generated output (right column)
out_items = [
    (7.0, 3.5, 'Python', 'from pkg.msg import X', GREEN_BG, GREEN_EC, GREEN_TC),
    (7.0, 2.1, 'C++', '#include <pkg/msg/x.hpp>', ORANGE_BG, ORANGE_EC, ORANGE_TC),
]
for x, y, label, sub, fc, ec, tc in out_items:
    rounded_box(ax, x, y, 3.5, 1.0, label, fc, ec, tc, fontsize=11, sublabel=sub, sub_fs=8)

# Arrows from rosidl to outputs
arrow(ax, 6.0, 3.4, 7.0, 3.9)
arrow(ax, 6.0, 2.9, 7.0, 2.7)

# colcon build wrapping
wrap = patches.FancyBboxPatch((2.9, 1.9, ), 3.4, 2.4, boxstyle='round,pad=0.12',
                               linewidth=2, edgecolor=DARK, facecolor='none',
                               linestyle='--')
ax.add_patch(wrap)
ax.text(3.1, 4.15, 'colcon build', fontsize=10, fontweight='bold', color=DARK)

# package.xml note
ax.text(5.5, 0.6,
        'package.xml:  <buildtool_depend>rosidl_default_generators</buildtool_depend>\n'
        '              <member_of_group>rosidl_interface_packages</member_of_group>',
        ha='center', va='center', fontsize=8.5, color=GRAY, family='monospace',
        bbox=dict(boxstyle='round,pad=0.4', facecolor='#F8F9F9', edgecolor='#CCCCCC'))

plt.savefig(f'{FIGURES}/fig6-2.png', dpi=150, bbox_inches='tight',
            facecolor='white', pad_inches=0.15)
plt.close()
print('fig6-2.png done')


# ══════════════════════════════════════════
# fig6-3: Interface package dependency
# my_robot_interfaces ← my_py_pkg / my_cpp_pkg
# ══════════════════════════════════════════
fig, ax = plt.subplots(figsize=(10, 4.5))
ax.set_xlim(0, 10)
ax.set_ylim(0, 4.5)
ax.axis('off')

ax.text(5.0, 4.15, '인터페이스 패키지 의존 관계', ha='center', va='center',
        fontsize=14, fontweight='bold', color=DARK)

# Interface package (center bottom)
rounded_box(ax, 2.8, 0.4, 4.4, 1.2, 'my_robot_interfaces', PURPLE_BG, PURPLE_EC, PURPLE_TC,
            fontsize=12, sublabel='ament_cmake  (msg/srv/action)')

# Python package (left top)
rounded_box(ax, 0.3, 2.5, 3.2, 1.1, 'my_py_pkg', GREEN_BG, GREEN_EC, GREEN_TC,
            fontsize=11, sublabel='<depend>my_robot_interfaces</depend>', sub_fs=7)

# C++ package (right top)
rounded_box(ax, 6.5, 2.5, 3.2, 1.1, 'my_cpp_pkg', ORANGE_BG, ORANGE_EC, ORANGE_TC,
            fontsize=11, sublabel='<depend>my_robot_interfaces</depend>', sub_fs=7)

# Arrows (depends on)
import numpy as np
# Left arrow: my_py_pkg → my_robot_interfaces
x1L, y1L, x2L, y2L = 1.9, 2.5, 4.0, 1.6
arrow(ax, x1L, y1L, x2L, y2L, color=GREEN_EC)
# Right arrow: my_cpp_pkg → my_robot_interfaces
x1R, y1R, x2R, y2R = 8.1, 2.5, 6.0, 1.6
arrow(ax, x1R, y1R, x2R, y2R, color=ORANGE_EC)

# Label on arrows — parallel to arrow direction
angle_L = np.degrees(np.arctan2(y2L - y1L, x2L - x1L))
angle_R = np.degrees(np.arctan2(y1R - y2R, x1R - x2R))
ax.text((x1L+x2L)/2, (y1L+y2L)/2 + 0.12, 'import', fontsize=9, color=GREEN_TC,
        rotation=angle_L, ha='center', va='bottom', rotation_mode='anchor')
ax.text((x1R+x2R)/2, (y1R+y2R)/2 + 0.12, '#include', fontsize=9, color=ORANGE_TC,
        rotation=angle_R, ha='center', va='bottom', rotation_mode='anchor')

plt.savefig(f'{FIGURES}/fig6-3.png', dpi=150, bbox_inches='tight',
            facecolor='white', pad_inches=0.15)
plt.close()
print('fig6-3.png done')
