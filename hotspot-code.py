import numpy as np
import matplotlib.pyplot as plt

def calculate_hotspot_current(t, F_wifi_seq, N_seq, I_cellular_seq):
   
    # -------------------------- 1. 插值获取t时刻的连续变量 --------------------------
  
    F_wifi_t = interpolate_time_series(t, F_wifi_seq, is_numeric=False)
    N_t = interpolate_time_series(t, N_seq, is_numeric=True)
   
    # （实际应调用之前的calculate_cellular_current函数，此处为简化用时间序列插值）
    I_cellular_t = interpolate_time_series(t, I_cellular_seq, is_numeric=True)
    
    # -------------------------- 2. Wi-Fi AP动态电流（数据输出） --------------------------
  
    k_ap_map = {
        '2.4GHz': 45,  # 2.4GHz发射功率17dBm（50mW），叠加射频损耗后取45mA
        '5GHz': 75     # 5GHz发射功率20dBm（100mW），叠加射频损耗后取75mA
    }
    k_ap_t = k_ap_map[F_wifi_t]
    device_coeff = 0.3
    I_ap = k_ap_t * (1 + device_coeff * N_t)
    
    # -------------------------- 3. Wi-Fi AP静态电流（基带基础功耗） --------------------------
   
    I_ap_static = 20
    
    # -------------------------- 4. 热点总电流（双角色功耗叠加） --------------------------
    I_hotspot = I_cellular_t + I_ap + I_ap_static
    return I_hotspot

def interpolate_time_series(t, seq, is_numeric=True):
    """
    时间序列插值函数：保证模型的连续时间特性（题目核心要求）
    数值型变量（设备数、蜂窝电流）用线性插值，字符串型变量（频段）用近邻匹配
    
    参数：
    t: 目标时刻
    seq: 时间序列，格式为[[t0, v0], [t1, v1], ..., [tn, vn]]
    is_numeric: 是否为数值型序列（True=线性插值，False=近邻匹配）
    
    返回值：
    v_t: t时刻的插值结果
    """
    times = np.array([item[0] for item in seq])
    values = np.array([item[1] for item in seq])
    
    if is_numeric:
        return np.interp(t, times, values)  
    else:
        idx = np.argmin(np.abs(times - t)) 
        return values[idx]

# -------------------------- 示例：模拟5小时使用场景（可替换为实测数据） --------------------------
if __name__ == "__main__":
    # 【需后续填充】以下时间序列为杜撰的合理场景，需替换为实测数据
    # 1. Wi-Fi频段时间序列：0~2小时通勤（2.4GHz），2~5小时家庭（5GHz）
    F_wifi_seq = [
        [0, '2.4GHz'], [2, '2.4GHz'], [2.1, '5GHz'], [5, '5GHz']
    ]
    # 2. 连接设备数时间序列：0~2小时通勤（1台手机），2~3小时家庭（3台设备），3~5小时家庭（2台设备）
    N_seq = [
        [0, 1], [2, 1], [2.1, 3], [3, 3], [3.1, 2], [5, 2]
    ]
    # 3. 蜂窝网络电流时间序列：0~1小时信号弱（80mA），1~2小时信号中等（70mA），2~5小时信号强（60mA）
    I_cellular_seq = [
        [0, 80], [1, 80], [1.1, 70], [2, 70], [2.1, 60], [5, 60]
    ]
    
    # 生成连续时间点（0~5小时，每0.01小时一个点，保证连续特性）
    t_range = np.linspace(0, 5, 500)
   
    I_hotspot_range = [calculate_hotspot_current(t, F_wifi_seq, N_seq, I_cellular_seq) for t in t_range]
    
    # 画图展示结果（直观呈现电流随时间的连续变化）
    plt.figure(figsize=(10, 6))
    plt.plot(t_range, I_hotspot_range, label='I_hotspot(t) (mA)', color='#2ca02c')
    plt.xlabel('Time (hours)')
    plt.ylabel('Hotspot Current (mA)')
    plt.title('Hotspot Power Consumption Over 5-Hour Scenario')
    plt.grid(True, alpha=0.3)
    plt.legend()

    plt.show()
