# config.py
# 所有参数统一分类存放在这里

class HardwareConfig:
    SYSTEM = {
    'voltage': 3.7,  # 系统电压 (V)
    'Q': 3700.0,      # 电池容量 (mAh)
    'eta': 0.85       # 充放电效率，体现损耗
    }

    DISPLAY = {
        'current_base': 7.8,      # 基础功率 (mW)
        'current_max': 414.0,     # 最大功率 (mW)
        'brightness_min': 0,      # 最小亮度 (%)
        'brightness_max': 100,    # 最大亮度 (%)
        'k_bright': (414.0 - 7.8) / 100.0,  # 亮度系数 (mW/%)，表示亮度每增加1%，电流增加多少mA
    }

# 处理器模块参数 (基于物理拟合 I = af^2 + bf + c)
    PROCESSOR = {
        # 大核簇 (Big Cluster: Cores 6-7)
        'big': {
            'a': 1.15e-05,   # 非线性因子 (mA/MHz^2)，反映 DVFS 电压爬升带来的平方级惩罚
            'b': 1.05e-03,   # 线性因子 (mA/MHz)，反映 CMOS 基础翻转损耗
            'c': 20.61,      # 静态漏电 (mA)，代表处理器的基准静默电流
        },
        # 小核簇 (Little Cluster: Cores 0-5)
        'little': {
            'a': 4.12e-06,   # 小核非线性因子，通常远小于大核
            'b': 6.84e-03,   # 小核线性因子
            'c': 13.52,      # 小核静态漏电
        },
        'gpu': {
            'a': 8.50e-06,   # GPU 非线性因子 (受电压域动态调节影响)
            'b': 1.20e-03,   # GPU 线性因子 (大规模并行单元翻转损耗)
            'c': 15.0,       # GPU 静态漏电 (mA)
            'freq_max': 675, # GPU 最大工作频率 (MHz)
        },
    }

class Signaling:
    COMMON = {
        'rssi_min': -100,    # 最小信号强度 (dB)
        'rssi_max': -50,     # 最大信号强度 (dB)
        'temp_coeff': 0.01,  # 温度系数 (mA/℃)
        'default_temp': 25,  # 默认工作温度 (℃)
    }
    BLUETOOTH = {
        'ble_idle': 1.2,
        'ble_tx': 8.0,
        'class_currents': {'1': 30.0, '2': 8.0, '3': 2.0},
        'classic_tx': 25.0,  # 传统蓝牙发射额外电流(mA)
    }

    CELLULAR = {
        # 静态电流 (mA)
        '2g_static': 20.0,
        '3g_static': 45.0,
        '4g_static': 70.0,
        
        # 信号强度参数
        'k_rssi': 50.0,      # 信号补偿系数
        'alpha': 0.05,       # 信号衰减系数
        
        # 基站切换参数
        'k_handoff': 15.0,   # 每次切换增加的电流(mA)
    }

    WIFI = {
        # 扫描阶段电流 (mA)
        'scan_peak': 120.0,
        
        # 连接阶段参数
        'sleep_current': 8.0,     # 最低待机电流
        
        # 频段系数 (mA)
        'k_24ghz': 50.0,          # 2.4GHz频段系数
        'k_5ghz': 85.0,           # 5GHz频段系数
        
        # 信号衰减系数
        'beta': 0.04,             # 信号强度影响系数
    }

    HOTSPOT = {
        # AP静态电流 (mA)
        'ap_static': 20.0,
        
        # 频段动态电流系数 (mA)
        'k_24ghz': 45.0,          # 2.4GHz频段基础电流
        'k_5ghz': 75.0,           # 5GHz频段基础电流
        
        # 设备数影响系数
        'device_coeff': 0.3,      # 每多一台设备增加的系数
    }


"""统一配置"""
class ConfigAll:
    def __init__(self, scenario_name='BLUETOOTH_SCENARIO_1'):
        self.hw = HardwareConfig()
        self.sgl = Signaling()

# 创建全局实例
cfg = ConfigAll()  # 默认
# 要换场景：cfg = ConfigAll('BLUETOOTH_SCENARIO_2')
