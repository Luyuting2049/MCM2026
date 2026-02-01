import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from mpl_toolkits.mplot3d import Axes3D

# ==========================================
# 1. 硬件配置与物理参数 (保持不变)
# ==========================================
class HardwareConfig:
    BIG = {'a': 1.15e-05, 'b': 1.05e-03, 'c': 20.61}
    GPU = {'a': 8.50e-06, 'b': 1.20e-03, 'c': 15.0}
    C_STATIC = 20.61 + 15.0 + 7.8 

def get_soc_current(f_c, mu_c, f_g, mu_g):
    conf_c = HardwareConfig.BIG
    conf_g = HardwareConfig.GPU
    i_cpu_dynamic = mu_c * (conf_c['a'] * f_c**2 + conf_c['b'] * f_c)
    i_gpu_dynamic = mu_g * (conf_g['a'] * f_g**2 + conf_g['b'] * f_g)
    return i_cpu_dynamic + i_gpu_dynamic + HardwareConfig.C_STATIC

# ==========================================
# 2. 三合一可视化 (布局深度优化版)
# ==========================================
# 增加 figsize 宽度
fig = plt.figure(figsize=(22, 7)) 
f_axis = np.linspace(0, 2200, 100)

# --- 图 A: GPU 物理分量拆解 (优化纵轴文字) ---
ax1 = fig.add_subplot(1, 3, 1)
gpu_p = HardwareConfig.GPU
i_gpu_total = gpu_p['a']*f_axis**2 + gpu_p['b']*f_axis + gpu_p['c']
ax1.plot(f_axis, i_gpu_total, 'm-', linewidth=2, label='GPU Total (100% Load)')
ax1.fill_between(f_axis, gpu_p['c'], i_gpu_total, color='magenta', alpha=0.1, label='GPU Dynamic')
ax1.axhline(y=gpu_p['c'], color='g', linestyle='--', label='GPU Static Baseline')
ax1.set_title("GPU Power Component Analysis", fontsize=15, pad=20)
ax1.set_xlabel("GPU Frequency (MHz)", fontsize=12, labelpad=10)
# 使用 labelpad 增加纵轴文字与数字的距离
ax1.set_ylabel("Current Consumption (mA)", fontsize=12, labelpad=15) 
ax1.legend(loc='upper left', fontsize=10)
ax1.grid(True, linestyle=':', alpha=0.6)

# --- 图 B: CPU & GPU 并发负载灵敏度 ---
ax2 = fig.add_subplot(1, 3, 2)
f_gpu_fixed = 675  
for mu_dual in [0.2, 0.5, 0.8, 1.0]:
    i_sim = get_soc_current(f_axis, mu_dual, f_gpu_fixed, mu_dual)
    ax2.plot(f_axis, i_sim, label=f'CPU&GPU Load {int(mu_dual*100)}%')
ax2.set_title(f"Impact of Concurrent Load (GPU@{f_gpu_fixed}MHz)", fontsize=15, pad=20)
ax2.set_xlabel("CPU Frequency (MHz)", fontsize=12, labelpad=10)
ax2.set_ylabel("Total System Current (mA)", fontsize=12, labelpad=15)
ax2.legend(loc='upper left', fontsize=10)
ax2.grid(True, linestyle=':', alpha=0.6)

# --- 图 C: CPU vs GPU 负载响应面 (优化 3D 纵轴文字) ---
ax3 = fig.add_subplot(1, 3, 3, projection='3d')
MU_C, MU_G = np.meshgrid(np.linspace(0, 1, 30), np.linspace(0, 1, 30))
F_C_CONST, F_G_CONST = 1800, 675 
Z = get_soc_current(F_C_CONST, MU_C, F_G_CONST, MU_G)

surf = ax3.plot_surface(MU_C, MU_G, Z, cmap='inferno', edgecolor='none', alpha=0.9)
ax3.set_title(f"SoC Response Surface\n(CPU:{F_C_CONST}MHz, GPU:{F_G_CONST}MHz)", fontsize=14, pad=30)

# 3D 标签优化：labelpad 强制向外推，同时调整视角
ax3.set_xlabel(r'CPU Load $\mu_c$', fontsize=12, labelpad=15)
ax3.set_ylabel(r'GPU Load $\mu_g$', fontsize=12, labelpad=15)
ax3.set_zlabel('Total Current (mA)', fontsize=12, labelpad=20)

# 视角调整：稍微调高俯视角度(elev)和旋转角度(azim)，让 Z 轴标签不被遮挡
ax3.view_init(elev=25, azim=-45)

# 颜色条调整
cb = fig.colorbar(surf, ax=ax3, shrink=0.5, aspect=12, pad=0.15)
cb.set_label('Current (mA)', fontsize=11, labelpad=10)

# 强制设置子图之间的水平间距 (left, right, wspace 可微调)
plt.subplots_adjust(left=0.08, right=0.95, wspace=0.35, top=0.85, bottom=0.15)

plt.show()