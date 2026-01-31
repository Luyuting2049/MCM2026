import numpy as np
import matplotlib.pyplot as plt

def calculate_bluetooth_current(t, V_ble_seq, D_seq, C_seq):
  
    # -------------------------- 1. 插值获取t时刻的连续变量 --------------------------
   
    V_ble_t = interpolate_time_series(t, V_ble_seq, is_numeric=False)
    D_t = interpolate_time_series(t, D_seq, is_numeric=True)
    C_t = interpolate_time_series(t, C_seq, is_numeric=False)
    
    # -------------------------- 2. BLE电流项（V_ble=1时） --------------------------
    I_ble_idle = 1.2
    I_ble_tx = 8
    I_ble = I_ble_idle + D_t * (I_ble_tx - I_ble_idle)
    
    # -------------------------- 3. 传统蓝牙电流项（V_ble=0时） --------------------------
    I_class_map = {
        '1': 30,   # Class 1：发射功率100mW（20dBm），基础功耗最高
        '2': 8,    # Class 2：发射功率2.5mW（4dBm），手机常用，功耗中等
        '3': 2     # Class 3：发射功率1mW（0dBm），功耗最低
    }
    I_classic_tx = 25
    I_classic = I_class_map[C_t] + D_t * (I_classic_tx - I_class_map[C_t])
    
    # -------------------------- 4. 蓝牙总电流（按版本切换） --------------------------
   
    I_bluetooth = I_ble if V_ble_t == '1' else I_classic
    return I_bluetooth

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
    # 1. 蓝牙版本时间序列：0~2小时用BLE（连智能手表），2~5小时用传统蓝牙（连旧音箱）
    V_ble_seq = [
        [0, '1'], [2, '1'], [2.1, '0'], [5, '0']
    ]
    # 2. 占空比时间序列：0~1小时传文件（占空比0.8），1~2小时闲置（0.05），2~3小时听歌（0.6），3~5小时闲置（0.1）
    D_seq = [
        [0, 0.8], [1, 0.8], [1.1, 0.05], [2, 0.05],
        [2.1, 0.6], [3, 0.6], [3.1, 0.1], [5, 0.1]
    ]
    # 3. 传统蓝牙Class等级时间序列：2~5小时用Class 2（手机常用）
    C_seq = [
        [2, '2'], [5, '2']
    ]
    
    # 生成连续时间点（0~5小时，每0.01小时一个点，保证连续特性）
    t_range = np.linspace(0, 5, 500)
    # 计算每个时刻的蓝牙电流
    I_bluetooth_range = [calculate_bluetooth_current(t, V_ble_seq, D_seq, C_seq) for t in t_range]
    
    # 画图展示结果（直观呈现电流随时间的连续变化）
    plt.figure(figsize=(10, 6))
    plt.plot(t_range, I_bluetooth_range, label='I_bluetooth(t) (mA)', color='#ff7f0e')
    plt.xlabel('Time (hours)')
    plt.ylabel('Bluetooth Current (mA)')
    plt.title('Bluetooth Power Consumption Over 5-Hour Scenario')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.show()

