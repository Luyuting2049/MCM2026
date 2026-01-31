import numpy as np
import matplotlib.pyplot as plt

def calculate_wifi_current(t, S_wifi_seq, RSSI_seq, F_wifi_seq, scan_duration=3):
   
    # -------------------------- 1. 插值获取t时刻的连续变量 --------------------------
   
    S_wifi_t = interpolate_time_series(t, S_wifi_seq, is_numeric=False)
    RSSI_t = interpolate_time_series(t, RSSI_seq, is_numeric=True)
    F_wifi_t = interpolate_time_series(t, F_wifi_seq, is_numeric=False)
    
    # -------------------------- 2. 扫描阶段电流（短时高功耗） --------------------------
   
    I_scan_peak = 120
    scan_start = S_wifi_seq[0][0] 
    scan_end = scan_start + scan_duration / 3600
    I_scan = I_scan_peak if (scan_start <= t <= scan_end) else 0
    
    # -------------------------- 3. 连接阶段电流（低功耗） --------------------------
   
    I_wifi_sleep = 8
   
    k_wifi_map = {
        '2.4GHz': 50, 
        '5GHz': 85     
    }
    k_wifi_t = k_wifi_map[F_wifi_t]
  
    beta = 0.04
    I_conn_dynamic = k_wifi_t / np.exp(beta * np.abs(RSSI_t))
    I_conn = I_wifi_sleep + I_conn_dynamic
    
    # -------------------------- 4. Wi-Fi总电流（开关状态控制） --------------------------
  
    I_wifi = (I_scan + I_conn) if S_wifi_t == '1' else 0
    return I_wifi

def interpolate_time_series(t, seq, is_numeric=True):
 
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
    # 1. Wi-Fi开关状态时间序列：0~1小时关闭，1~5小时开启（1小时时首次开启，触发扫描）
    S_wifi_seq = [
        [0, '0'], [1, '0'], [1.00083, '1'], [5, '1']  # 1.00083小时=1小时+3秒（扫描持续时间）
    ]
    # 2. Wi-Fi信号强度时间序列：1~2小时弱信号（-85dBm），2~3小时强信号（-50dBm），3~5小时中等信号（-65dBm）
    RSSI_seq = [
        [1, -85], [2, -85], [2.1, -50], [3, -50], [3.1, -65], [5, -65]
    ]
    # 3. Wi-Fi频段时间序列：1~3小时2.4GHz，3~5小时5GHz（切换频段）
    F_wifi_seq = [
        [1, '2.4GHz'], [3, '2.4GHz'], [3.1, '5GHz'], [5, '5GHz']
    ]
    
    # 生成连续时间点（0~5小时，每0.01小时一个点，保证连续特性）
    t_range = np.linspace(0, 5, 500)
    # 计算每个时刻的Wi-Fi电流
    I_wifi_range = [calculate_wifi_current(t, S_wifi_seq, RSSI_seq, F_wifi_seq) for t in t_range]
    
    # 画图展示结果（直观呈现电流随时间的连续变化）
    plt.figure(figsize=(10, 6))
    plt.plot(t_range, I_wifi_range, label='I_wifi(t) (mA)', color='#d62728')
    plt.xlabel('Time (hours)')
    plt.ylabel('Wi-Fi Current (mA)')
    plt.title('Wi-Fi Power Consumption Over 5-Hour Scenario')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.show()

