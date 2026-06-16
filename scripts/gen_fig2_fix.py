"""Generate fig2-2 (fixed) and fig2-4 (new workspace tree diagram)."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

FIGURES = 'docs/01_intro/figures'

# ──────────────────────────────────────────
# fig2-2  (fixed): colcon label moved LEFT
# ──────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 5.5))
ax.set_xlim(0, 10)
ax.set_ylim(0, 5.5)
ax.axis('off')

# colcon build box
colcon_x, colcon_y, colcon_w, colcon_h = 2.0, 3.6, 6.0, 1.1
rect_top = patches.Rectangle((colcon_x, colcon_y), colcon_w, colcon_h,
                               linewidth=2, edgecolor='#333333', facecolor='#E8F4FD')
ax.add_patch(rect_top)
ax.text(colcon_x + colcon_w / 2, colcon_y + 0.72, 'colcon build',
        ha='center', va='center', fontsize=14, fontweight='bold', color='#1A5276')
ax.text(colcon_x + colcon_w / 2, colcon_y + 0.28, '(Collective Construction)',
        ha='center', va='center', fontsize=9, color='#555555')

# annotation text LEFT of the branch lines
ax.text(0.15, 2.55,
        '의존성 순서 정렬 후\n각 패키지를 순차 빌드',
        ha='left', va='center', fontsize=9, color='#555555',
        style='italic',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#FDFEFE', edgecolor='#AAAAAA', linewidth=0.8))

# branch: vertical line down from colcon box center
cx = colcon_x + colcon_w / 2  # 5.0
ax.annotate('', xy=(cx, 2.85), xytext=(cx, colcon_y),
            arrowprops=dict(arrowstyle='-', color='#555555', lw=1.5))

# horizontal line to two branches
ax.plot([3.0, 7.0], [2.85, 2.85], color='#555555', lw=1.5)

# left branch arrow
ax.annotate('', xy=(3.0, 2.1), xytext=(3.0, 2.85),
            arrowprops=dict(arrowstyle='->', color='#555555', lw=1.5))

# right branch arrow
ax.annotate('', xy=(7.0, 2.1), xytext=(7.0, 2.85),
            arrowprops=dict(arrowstyle='->', color='#555555', lw=1.5))

# left box: ament_python
py_x, py_y, py_w, py_h = 1.5, 0.55, 3.0, 1.55
rect_py = patches.Rectangle((py_x, py_y), py_w, py_h,
                              linewidth=1.5, edgecolor='#27AE60', facecolor='#EAFAF1')
ax.add_patch(rect_py)
ax.plot([py_x, py_x + py_w], [py_y + 0.95, py_y + 0.95], color='#27AE60', lw=0.8)
ax.text(py_x + py_w / 2, py_y + 1.25, 'ament_python',
        ha='center', va='center', fontsize=11, fontweight='bold', color='#1D8348')
ax.text(py_x + py_w / 2, py_y + 0.65, 'my_py_pkg',
        ha='center', va='center', fontsize=9.5, color='#333333')
ax.text(py_x + py_w / 2, py_y + 0.25, 'setup.py / setup.cfg',
        ha='center', va='center', fontsize=8.5, color='#555555')

# right box: ament_cmake
cpp_x, cpp_y, cpp_w, cpp_h = 5.5, 0.55, 3.0, 1.55
rect_cpp = patches.Rectangle((cpp_x, cpp_y), cpp_w, cpp_h,
                               linewidth=1.5, edgecolor='#E67E22', facecolor='#FEF9E7')
ax.add_patch(rect_cpp)
ax.plot([cpp_x, cpp_x + cpp_w], [cpp_y + 0.95, cpp_y + 0.95], color='#E67E22', lw=0.8)
ax.text(cpp_x + cpp_w / 2, cpp_y + 1.25, 'ament_cmake',
        ha='center', va='center', fontsize=11, fontweight='bold', color='#784212')
ax.text(cpp_x + cpp_w / 2, cpp_y + 0.65, 'my_cpp_pkg',
        ha='center', va='center', fontsize=9.5, color='#333333')
ax.text(cpp_x + cpp_w / 2, cpp_y + 0.25, 'CMakeLists.txt',
        ha='center', va='center', fontsize=8.5, color='#555555')

plt.savefig(f'{FIGURES}/fig2-2.png', dpi=150, bbox_inches='tight',
            facecolor='white', pad_inches=0.15)
plt.close()
print('fig2-2.png done')


# ──────────────────────────────────────────
# fig2-4: workspace folder tree
# ──────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 5.5))
ax.set_xlim(0, 10)
ax.set_ylim(0, 5.5)
ax.axis('off')

# Root box
root_x, root_y, root_w, root_h = 3.5, 4.2, 3.0, 0.85
rect_root = patches.Rectangle((root_x, root_y), root_w, root_h,
                                linewidth=2, edgecolor='#2C3E50', facecolor='#D6EAF8')
ax.add_patch(rect_root)
ax.text(root_x + root_w / 2, root_y + root_h / 2, 'ros2_ws/',
        ha='center', va='center', fontsize=13, fontweight='bold', color='#1A252F')

# vertical trunk
trunk_cx = root_x + root_w / 2  # 5.0
ax.plot([trunk_cx, trunk_cx], [root_y, 3.6], color='#555555', lw=1.5)

# horizontal bar
ax.plot([1.2, 8.8], [3.6, 3.6], color='#555555', lw=1.5)

# four child positions
children = [
    (1.2, 'src/',     '#EAFAF1', '#27AE60', '#1D8348',
     '내가 관리하는 소스 코드\ngit 관리 대상'),
    (3.5, 'build/',   '#FEF9E7', '#E67E22', '#784212',
     '중간 빌드 산출물\n(자동 생성)'),
    (5.8, 'install/', '#FEF5E4', '#D35400', '#6E2F00',
     '실행에 필요한 최종 결과물\nsetup.bash 포함 (자동 생성)'),
    (8.1, 'log/',     '#F4ECF7', '#8E44AD', '#4A235A',
     '빌드 로그\n(자동 생성)'),
]

box_w, box_h = 1.55, 0.75
desc_h = 1.0
for cx, label, fc, ec, tc, desc in children:
    bx = cx - box_w / 2
    by = 2.65

    # vertical drop
    ax.plot([cx, cx], [3.6, by + box_h], color='#555555', lw=1.5)

    # folder box
    rect = patches.Rectangle((bx, by), box_w, box_h,
                               linewidth=1.5, edgecolor=ec, facecolor=fc)
    ax.add_patch(rect)
    ax.text(cx, by + box_h / 2, label,
            ha='center', va='center', fontsize=10, fontweight='bold', color=tc)

    # description text below
    ax.text(cx, by - 0.15, desc,
            ha='center', va='top', fontsize=7.5, color='#444444',
            linespacing=1.5)

plt.savefig(f'{FIGURES}/fig2-4.png', dpi=150, bbox_inches='tight',
            facecolor='white', pad_inches=0.15)
plt.close()
print('fig2-4.png done')
