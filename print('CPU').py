import numpy as np
import matplotlib.pyplot as plt

# ==========================================
# 1. 提取 AOSP 原始数据 (Data Extraction)
# ==========================================
# 小核簇 (Cores 0-5) - 频率转换为 MHz
freq_little = np.array([300000, 576000, 748800, 998400, 1209600, 1324800, 1516800, 1708800]) / 1000 
curr_little = np.array([15.246, 18.216, 20.186, 23.29, 25.011, 28.485, 31.686, 35.79])

# 大核簇 (Cores 6-7) - 频率转换为 MHz
freq_big = np.array([300000, 652800, 825600, 979200, 1132800, 1363200, 1536000, 1747200, 1843200, 1996800, 2016000]) / 1000 
curr_big = np.array([24.06, 27.56, 29.0, 31.675, 34.53, 38.885, 43.075, 48.705, 64.57, 69.805, 76.545])

# ==========================================
# 2. 拟合与 R^2 计算 (Numpy Only)
# ==========================================
p_little = np.polyfit(freq_little, curr_little, 2)
p_big = np.polyfit(freq_big, curr_big, 2)

def get_r2(x, y, p):
    y_pred = np.polyval(p, x)
    return 1 - (np.sum((y - y_pred)**2) / np.sum((y - np.mean(y))**2))

r2_l, r2_b = get_r2(freq_little, curr_little, p_little), get_r2(freq_big, curr_big, p_big)

print(f"Little Core Fit: I = {p_little[0]:.2e}*f^2 + {p_little[1]:.2e}*f + {p_little[2]:.2f} (R²={r2_l:.4f})")
print(f"Big Core Fit:    I = {p_big[0]:.2e}*f^2 + {p_big[1]:.2e}*f + {p_big[2]:.2f} (R²={r2_b:.4f})")

# ==========================================
# 3. 三合一可视化 (Visualizations)
# ==========================================
fig = plt.figure(figsize=(16, 5))

# 图 A: 拟合验证图 (Physics vs. Empirical)
plt.subplot(1, 3, 1)
f_axis = np.linspace(300, 2100, 100)
plt.scatter(freq_big, curr_big, color='red', label='AOSP Data (Big)', alpha=0.6)
plt.plot(f_axis, np.polyval(p_big, f_axis), 'r--', label=f'Model ($R^2$={r2_b:.3f})')
plt.scatter(freq_little, curr_little, color='blue', label='AOSP Data (Little)', alpha=0.6)
plt.plot(f_axis, np.polyval(p_little, f_axis), 'b--', label=f'Model ($R^2$={r2_l:.3f})')
plt.title("CPU Model Calibration (bonito)")
plt.xlabel("Frequency (MHz)"); plt.ylabel("Current (mA)"); plt.legend(); plt.grid(True, alpha=0.3)

# 图 B: 功耗分解 (Power Sensitivity)
plt.subplot(1, 3, 2)
for mu in [0.2, 0.5, 0.8, 1.0]:
    plt.plot(f_axis, mu * np.polyval(p_big, f_axis), label=f'Utilization {int(mu*100)}%')
plt.title("Impact of CPU Load on Current")
plt.xlabel("Frequency (MHz)"); plt.ylabel("Current (mA)"); plt.legend(); plt.grid(True, alpha=0.3)

# 图 C: 3D 响应面 (3D Map)
from mpl_toolkits.mplot3d import Axes3D
ax = fig.add_subplot(1, 3, 3, projection='3d')
F, M = np.meshgrid(np.linspace(300, 2000, 20), np.linspace(0, 1, 20))
Z = M * (p_big[0]*F**2 + p_big[1]*F + p_big[2])
ax.plot_surface(F, M, Z, cmap='magma')
ax.set_title("3D CPU Power Surface")
ax.set_xlabel('f (MHz)'); ax.set_ylabel('Load ($\mu$)'); ax.set_zlabel('I (mA)')

plt.tight_layout()
plt.show()