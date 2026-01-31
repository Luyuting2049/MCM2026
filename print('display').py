import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp

# --- 1. 参数定义 ---
V_SYS = 3.7
I_BASE = 7.8 / V_SYS  # ~2.11 mA
I_MAX = 414.0 / V_SYS # ~111.89 mA
K_BRIGHT = (I_MAX - I_BASE) / 100.0

Q_NOMINAL = 3700.0 # Pixel 3 XL [SPECS]
ETA = 0.85         # 效率 [CITATION CARROLL]

# --- 2. 模拟函数 ---
def get_i_disp(L):
    return K_BRIGHT * L + I_BASE

def battery_ode(t, y, L, i_other):
    soc = y[0]
    if soc <= 0: return 0
    i_total = get_i_disp(L) + i_other
    return -(ETA * i_total) / (Q_NOMINAL * 3600)

# --- 3. 绘图设置 ---
fig = plt.figure(figsize=(15, 5))

# 图 A: 静态特性曲线 (I vs L)
plt.subplot(1, 3, 1)
L_vals = np.linspace(0, 100, 100)
I_vals = get_i_disp(L_vals)
plt.plot(L_vals, I_vals, 'b-', linewidth=2, label='Model Curve')
plt.scatter([0, 100], [I_BASE, I_MAX], color='red', label=' extreme value')
plt.title("A: Display Current vs. Brightness\n(Linear Calibration)")
plt.xlabel("Brightness (%)")
plt.ylabel("Current (mA)")
plt.legend()
plt.grid(True, alpha=0.3)

# 图 B: 动态 SOC 掉电对比 (不同亮度)
plt.subplot(1, 3, 2)
time_hours = 12
t_eval = np.linspace(0, time_hours * 3600, 500)
i_other_standby = 50.0 # 假设其他组件底电流为 50mA [ASSUMPTION]

for L_level in [10, 25, 50, 75, 100]:
    sol = solve_ivp(fun=lambda t, y: battery_ode(t, y, L_level, i_other_standby),
                    t_span=[0, time_hours * 3600], y0=[1.0], t_eval=t_eval)
    plt.plot(sol.t/3600, sol.y[0]*100, label=f'Brightness {L_level}%')

plt.title("B: SOC Depletion Trace\nat Different Brightness")
plt.xlabel("Time (Hours)")
plt.ylabel("SOC (%)")
plt.legend()
plt.grid(True, alpha=0.3)

# 图 C: 功耗占比分析 (中等负载模式)
plt.subplot(1, 3, 3)
L_test = 80.0
i_disp_test = get_i_disp(L_test)
i_proc_test = 120.0  # 假设 CPU 负载电流 [ASSUMPTION/AOSP]
i_other_test = 30.0  # 其他 [ASSUMPTION]

components = ['Display', 'Processor', 'Others']
currents = [i_disp_test, i_proc_test, i_other_test]
colors = ['#ff9999','#66b3ff','#99ff99']
plt.pie(currents, labels=components, autopct='%1.1f%%', startangle=140, colors=colors, explode=(0.1, 0, 0))
plt.title(f"C: Power Breakdown\n(at {L_test}% Brightness)")

plt.tight_layout()
plt.show()