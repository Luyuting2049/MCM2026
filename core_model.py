import config
import numpy as np


"""显示器模块"""
# 输入:亮度L(%)，输出:电流值(mA)
# 核心公式/解释：特定亮度下电流值 = 基础电流 + 每度亮度增加的电流*亮度 （对比CPU那个，这种就可以用自然语言描述公式含义）
class Display:
    """类的初始化"""
    def __init__(self, cfg):
        self.cfg = cfg.hardware
        self.V = self.cfg.SYSTEM['voltage']
        self.Q = self.cfg.SYSTEM['Q']
        self.eta = self.cfg.SYSTEM['eta']
        disp = self.cfg.DISPLAY
        self.Pb = disp['current_base']
        self.k = disp['k_bright']
        self.I_max = disp['current_max'] / self.V
    
    # 计算相应亮度下的电流
    def I(self, L):
        return (self.Pb + self.k * L) / self.V


"""处理器模块 (CPU & GPU)"""
# 输入: CPU频率(MHz), CPU负载(0-1), GPU频率(MHz), GPU负载(0-1)
# 输出: 总电流值(mA)
# 核心公式/解释：
# 处理器电流 = [μ_cpu * (a_c*f_c^2 + b_c*f_c) + μ_gpu * (a_g*f_g^2 + b_g*f_g) + C_static] / η
# 1. 动态部分：负载(μ)乘以频率(f)的多项式，体现了由于频率升高导致电压强制爬升(DVFS)带来的非线性功耗激增。
# 2. 静态部分：C_static 代表芯片通电即存在的静态漏电流，与频率和负载无关。
# 3. 效率转换：最终除以系统效率 η，得到电池端实际输出的电流。

class Processor:
    """类的初始化"""
    def __init__(self, cfg):
        self.cfg = cfg.hardware
        self.V = self.cfg.SYSTEM['voltage']
        self.Q = self.cfg.SYSTEM['Q_nominal']
        self.eta = self.cfg.SYSTEM['eta']
        
        # 载入大核(CPU)物理参数
        cpu_cfg = self.cfg.PROCESSOR['big']
        self.a_c = cpu_cfg['a']
        self.b_c = cpu_cfg['b']
        self.c_c = cpu_cfg['c']
        
        # 载入GPU物理参数
        gpu_cfg = self.cfg.PROCESSOR['gpu']
        self.a_g = gpu_cfg['a']
        self.b_g = gpu_cfg['b']
        self.c_g = gpu_cfg['c']

    # 计算相应频率与负载下的总电流
    def I(self, f_cpu, mu_cpu, f_gpu, mu_gpu):
        """
        f_cpu/f_gpu: 频率 (MHz)
        mu_cpu/mu_gpu: 负载率 (0.0 到 1.0)
        """
        # 1. 计算CPU动态电流分量
        i_cpu_dynamic = mu_cpu * (self.a_c * f_cpu**2 + self.b_c * f_cpu)
        
        # 2. 计算GPU动态电流分量
        i_gpu_dynamic = mu_gpu * (self.a_g * f_gpu**2 + self.b_g * f_gpu)
        
        # 3. 静态电流分量 (CPU与GPU静态漏电之和)
        i_static = self.c_c + self.c_g
        
        # 4. 汇总并考虑能量转换效率 η
        total_current = (i_cpu_dynamic + i_gpu_dynamic + i_static) / self.eta
        
        return total_current



"""蓝牙模块"""
# 输入:模式mode('ble'或'classic')，类别class_type('1','2','3')，占空比duty_cycle(0~1)
# 输出:电流值(mA)
# 核心公式和原理解释（最好通俗易懂地说明一下）
class Bluetooth:
    def __init__(self, cfg):
        self.phy = cfg.sgl.BLUETOOTH
    
    def I(self, mode='ble', class_type='2', duty_cycle=0.1):
        if mode == 'ble':
            idle = self.phy['ble_idle']
            tx = self.phy['ble_tx']
        else:  # classic
            idle = self.phy['classic_idle'][class_type]
            tx = self.phy['classic_tx']
        
        # 线性插值：I = I_idle + D*(I_tx - I_idle)
        return idle + duty_cycle * (tx - idle)
    

"""蜂窝网络模块"""
# 输入：network_type, rssi_db, handoff_rate
# 输出：当前蜂窝网络电流(mA)
# 原理：总电流 = 静态电流(网络类型) + 信号补偿电流 + 切换开销电流
# 核心公式：I_total = I_static(network_type) + k_rssi * exp(-α * RSSI) + k_handoff * H（看不懂，config里每个参数的注释要加个通俗易懂的说明，不要只有术语）
class Cellular:
    def __init__(self, cfg):
        self.phy = cfg.sgl.CELLULAR
        
    def I(self, network_type='4G', rssi_db=-70, handoff_rate=1):
        # 1. 静态电流（网络类型决定）
        static_currents = {
            '2G': self.phy.get('2g_static', 20.0),
            '3G': self.phy.get('3g_static', 45.0),
            '4G': self.phy.get('4g_static', 70.0)
        }
        I_static = static_currents[network_type]
        
        # 2. 信号强度补偿电流（信号越差，发射功率越高）
        k_rssi = self.phy.get('k_rssi', 50.0)
        alpha = self.phy.get('alpha', 0.05)
        I_signal = k_rssi * np.exp(-alpha * rssi_db)
        
        # 3. 基站切换开销电流
        k_handoff = self.phy.get('k_handoff', 15.0)
        I_handoff = k_handoff * handoff_rate
        
        return I_static + I_signal + I_handoff
    

"""WiFi模块"""
# 输入：is_on, rssi_db, freq, is_scanning
# 输出：当前WiFi电流(mA)
# 原理：总电流 = (WiFi开启 ? (扫描电流 or 连接电流) : 0) （这里依旧看不懂，需要能用通俗语言解释）
"""
计算当前WiFi电流   
物理公式：
if not is_on: return 0
elif is_scanning: return I_scan_peak
else: return I_sleep + k_freq * exp(-β * |RSSI|)
"""
class WiFi:
    def __init__(self, cfg):
        # 物理参数从config读取（需要你在config里添加）
        self.phy = cfg.sgl.WIFI  # 假设你在config里加了WIFI
        
    def I(self, is_on=True, rssi_db=-70, freq='2.4GHz', is_scanning=False):
        # WiFi关闭时电流为0
        if not is_on:
            return 0.0
        
        # 扫描阶段（高功耗）
        if is_scanning:
            return self.phy.get('scan_peak', 120.0)
        
        # 正常连接阶段
        I_sleep = self.phy.get('sleep_current', 8.0)
        
        # 频段系数
        k_freq_map = {
            '2.4GHz': self.phy.get('k_24ghz', 50.0),
            '5GHz': self.phy.get('k_5ghz', 85.0)
        }
        k_freq = k_freq_map.get(freq, 50.0)
        
        # 信号强度影响（信号越差，发射功率越高）
        beta = self.phy.get('beta', 0.04)
        I_dynamic = k_freq / np.exp(beta * abs(rssi_db))
        
        return I_sleep + I_dynamic
    

    """热点模块（手机作为WiFi热点）"""
# 输入：is_active, cellular_current, freq, device_count
# 输出：当前热点模式总电流(mA)
# 原理：热点总电流 = (热点开启 ? (蜂窝电流 + AP静态电流 + AP动态电流) : 0)
"""
计算热点模式总电流
物理公式：
if not is_active: return 0
else: return I_cellular + I_ap_static + k_freq * (1 + α * N)
"""
class Hotspot:
    def __init__(self, cfg):
        self.phy = cfg.sgl.HOTSPOT
        
    def I(self, is_active=True, cellular_current=70.0, freq='2.4GHz', device_count=1):
        # 热点关闭时电流为0
        if not is_active:
            return 0.0
        
        # 1. 蜂窝网络电流（从蜂窝模块传入）
        I_cell = cellular_current
        
        # 2. AP静态电流（基带基础功耗）
        I_ap_static = self.phy.get('ap_static', 20.0)
        
        # 3. AP动态电流（与频段和设备数相关）
        k_freq_map = {
            '2.4GHz': self.phy.get('k_24ghz', 45.0),
            '5GHz': self.phy.get('k_5ghz', 75.0)
        }
        k_freq = k_freq_map.get(freq, 45.0)
        
        # 设备数影响系数（每多一台设备增加α倍基础电流）
        alpha = self.phy.get('device_coeff', 0.3)
        I_ap_dynamic = k_freq * (1 + alpha * device_count)
        
        return I_cell + I_ap_static + I_ap_dynamic
