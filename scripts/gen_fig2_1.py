"""Generate fig2-1: underlay/overlay layer diagram (no baked-in caption)."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

FIGURES = 'docs/01_intro/figures'

fig, ax = plt.subplots(figsize=(10, 6))
ax.set_xlim(0, 10)
ax.set_ylim(0, 6)
ax.axis('off')

DARK = '#2C3E50'
GRAY = '#555555'

# Top annotation: source command for overlay
ax.text(0.3, 5.6, 'source ~/ros2_ws/install/setup.bash',
        ha='left', va='center', fontsize=9.5, color=GRAY)

# Overlay box
ov_x, ov_y, ov_w, ov_h = 0.5, 3.6, 9.0, 1.8
rect_ov = patches.Rectangle((ov_x, ov_y), ov_w, ov_h,
                              linewidth=2, edgecolor=DARK, facecolor='white')
ax.add_patch(rect_ov)
ax.text(ov_x + ov_w / 2, ov_y + 1.35, '오버레이 (overlay)',
        ha='center', va='center', fontsize=15, fontweight='bold', color=DARK)
ax.text(ov_x + ov_w / 2, ov_y + 0.9, '~/ros2_ws/install/setup.bash',
        ha='center', va='center', fontsize=10, color=GRAY)
ax.text(ov_x + ov_w / 2, ov_y + 0.4, 'my_py_pkg    my_cpp_pkg    (직접 빌드한 패키지)',
        ha='center', va='center', fontsize=9.5, color=GRAY)

# Arrow upward between the boxes
ax.annotate('', xy=(5.0, 3.6), xytext=(5.0, 2.4),
            arrowprops=dict(arrowstyle='->', color=DARK, lw=2.0))
ax.text(5.5, 3.0, '위에 얹힘 — 같은 이름이면 오버레이 우선',
        ha='left', va='center', fontsize=9, color=GRAY)

# Underlay box
ul_x, ul_y, ul_w, ul_h = 0.5, 0.6, 9.0, 1.8
rect_ul = patches.Rectangle((ul_x, ul_y), ul_w, ul_h,
                              linewidth=2, edgecolor=DARK, facecolor='white')
ax.add_patch(rect_ul)
ax.text(ul_x + ul_w / 2, ul_y + 1.35, '언더레이 (underlay)',
        ha='center', va='center', fontsize=15, fontweight='bold', color=DARK)
ax.text(ul_x + ul_w / 2, ul_y + 0.9, '/opt/ros/jazzy/setup.bash',
        ha='center', va='center', fontsize=10, color=GRAY)
ax.text(ul_x + ul_w / 2, ul_y + 0.4, 'rclpy    rclcpp    demo_nodes    ...',
        ha='center', va='center', fontsize=9.5, color=GRAY)

# Bottom annotation: source command for underlay (split to avoid monospace Korean glyphs)
ax.text(0.3, 0.25, 'source /opt/ros/jazzy/setup.bash',
        ha='left', va='center', fontsize=9.5, color=GRAY)
ax.text(4.5, 0.25, '(보통 ~/.bashrc 에서 자동 소싱)',
        ha='left', va='center', fontsize=9.5, color=GRAY)

plt.savefig(f'{FIGURES}/fig2-1.png', dpi=150, bbox_inches='tight',
            facecolor='white', pad_inches=0.15)
plt.close()
print('fig2-1.png done')
