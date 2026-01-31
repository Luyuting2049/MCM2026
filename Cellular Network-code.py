import numpy as np
import matplotlib.pyplot as plt

def calculate_cellular_current(t, T_net_seq, RSSI_seq, H_seq):
   
    # -------------------------- 1. 静态电流项 I_cell_static(T_net(t)) --------------------------
 
  
    static_current_map = {
        '2G': 20,    # GSM网络：低带宽，射频电路基础功耗低
        '3G': 45,    # WCDMA网络：中等带宽，调制方式更复杂，功耗提升
        '4G': 70     # LTE网络：高带宽，OFDM技术，射频电路工作强度高
    }
   
    T_net_t = interpolate_time_series(t, T_net_seq)
    I_static = static_current_map[T_net_t]
    
    # -------------------------- 2. 动态电流项 I_cell_dynamic --------------------------
    # 2.1 信号强度相关电流：k_tx * exp(-α * RSSI(t))
    
    k_tx = 50
    alpha = 0.05
    RSSI_t = interpolate_time_series(t, RSSI_seq, is_numeric=True)
    I_signal = k_tx * np.exp(-alpha * RSSI_t)
   
    # 2.2 基站切换相关电流：k_handoff * H(t)
    k_handoff = 15
    H_t = interpolate_time_series(t, H_seq, is_numeric=True)
    I_handoff = k_handoff * H_t
    I_dynamic = I_signal + I_handoff
    
    # -------------------------- 3. 蜂窝网络总电流 --------------------------
    I_cellular = I_static + I_dynamic
    return I_cellular

def interpolate_time_series(t, seq, is_numeric=True):
    """
    时间序列插值函数：根据已知时间点的数值，获取任意时刻t的连续值
    （保证模型的连续时间特性，符合题目核心要求）
    
    参数：
    t: 目标时刻
    seq: 时间序列，格式为[[t0, v0], [t1, v1], ..., [tn, vn]]
    is_numeric: 是否为数值型序列（True：数值插值；False：字符串类型（如网络类型）近邻匹配）
    
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

# -------------------------- 示例：模拟真实场景计算（可替换为实际数据） --------------------------
if __name__ == "__main__":
    # 模拟5小时通勤场景的时间序列（0~5小时）
    # 【注意：以下时间序列数据为杜撰的合理值，需后续替换为实测/公开数据】
    # 1. 网络类型时间序列：[时间(小时), 网络类型]
    T_net_seq = [
        [0, '4G'],    # 0小时（家里）：4G满格
        [1, '3G'],    # 1小时（郊区路段）：4G信号弱，切换为3G
        [2, '2G'],    # 2小时（地铁隧道）：仅2G信号
        [3, '3G'],    # 3小时（出地铁）：切换为3G
        [4, '4G'],    # 4小时（公司）：4G信号恢复
        [5, '4G']
    ]
    # 2. RSSI信号强度时间序列：[时间(小时), RSSI(dBm)]（数值越大，信号越强）
    RSSI_seq = [
        [0, -60],     # 家里：强信号
        [1, -85],     # 郊区：中等信号
        [2, -100],    # 地铁：弱信号
        [3, -80],     # 出地铁：中等信号
        [4, -55],     # 公司：强信号
        [5, -58]
    ]
    # 3. 基站切换频率时间序列：[时间(小时), 切换频率(次/小时)]
    H_seq = [
        [0, 1],       # 家里：静止，切换少
        [1, 12],      # 郊区通勤：移动中，切换频繁
        [2, 8],       # 地铁：隧道内基站少，切换减少
        [3, 15],      # 出地铁换乘：移动快，切换频繁
        [4, 2],       # 公司：静止，切换少
        [5, 1]
    ]
    
    # 生成连续时间点（0~5小时，每0.01小时一个点，保证连续特性）
    t_range = np.linspace(0, 5, 500)
    # 计算每个时刻的蜂窝网络电流
    I_cellular_range = [calculate_cellular_current(t, T_net_seq, RSSI_seq, H_seq) for t in t_range]
    
    # 画图展示结果（直观呈现电流随时间的连续变化）
    plt.figure(figsize=(10, 6))
    plt.plot(t_range, I_cellular_range, label='I_cellular(t) (mA)', color='#1f77b4')
    plt.xlabel('Time (hours)')
    plt.ylabel('Cellular Network Current (mA)')
    plt.title('Cellular Network Power Consumption Over 5-Hour Commute Scenario')
    plt.grid(True, alpha=0.3)
    plt.legend()

    plt.show()
