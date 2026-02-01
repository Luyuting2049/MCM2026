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


"""内存模块 (Memory - LPDDR)"""
# 输入: 读带宽 BW_r (GB/s), 写带宽 BW_w (GB/s)
# 输出: 电流值 (mA)
# 核心公式/解释：I_mem = (delta_r * BW_r + delta_w * BW_w) + I_static
# 1. 动态功耗：由数据总线（Data Bus）翻转引起。读取和写入的电流系数（delta）略有不同，
#    通常写入操作因为需要驱动存储颗粒电容，功耗略高于读取。
# 2. 静态功耗：即自刷新电流（Self-Refresh Current），用于在无读写操作时维持电荷不流失。

class Memory:
    """类的初始化"""
    def __init__(self, cfg):
        self.cfg = cfg.hardware
        self.V = self.cfg.SYSTEM['voltage']
        self.eta = self.cfg.SYSTEM['eta']
        
        # 内存特定参数 (以 LPDDR4x 为例)
        mem_cfg = self.cfg.MEMORY
        self.delta_r = mem_cfg['delta_read']   # 每 GB/s 消耗的电流 (mA/(GB/s))
        self.delta_w = mem_cfg['delta_write']  # 每 GB/s 消耗的电流
        self.I_static = mem_cfg['static_mA']   # 基础刷新电流

    # 计算相应带宽下的电流
    def I(self, bw_r, bw_w):
        """
        bw_r: 读取带宽 (GB/s)
        bw_w: 写入带宽 (GB/s)
        """
        # 1. 动态读写分量
        i_dynamic = (self.delta_r * bw_r) + (self.delta_w * bw_w)
        
        # 2. 叠加静态功耗并考虑转换效率
        return (i_dynamic + self.I_static) / self.eta


"""存储模块 (Storage - UFS/eMMC)"""
# 输入: 读写状态 (is_active: True/False)
# 输出: 电流值 (mA)
# 核心公式/解释：I_store = I_io (Active) 或 I_sleep (Idle)
# 1. Active 状态：当闪存控制器进行电荷泵操作、读写寻址及 ECC 纠错时，会产生显著电流。
# 2. Idle 状态：存储模块进入深度休眠（Deep Sleep），电流极低，通常可忽略不计。

class Storage:
    """类的初始化"""
    def __init__(self, cfg):
        self.cfg = cfg.hardware
        self.V = self.cfg.SYSTEM['voltage']
        self.eta = self.cfg.SYSTEM['eta']
        
        # 存储特定参数 (参考 UFS 3.1 标准)
        store_cfg = self.cfg.STORAGE
        self.I_io = store_cfg['current_active']  # 活跃读写电流 (mA)
        self.I_sleep = store_cfg['current_idle'] # 静态待机电流 (mA)

    # 计算相应状态下的电流
    def I(self, is_active=False):
        """
        is_active: 布尔值，代表当前是否有 I/O 操作
        """
        # 根据状态切换电流值
        i_raw = self.I_io if is_active else self.I_sleep
        
        # 考虑效率转换
        return i_raw / self.eta


"""
处理器模块 (CPU & GPU)
输入: CPU频率 f_c, CPU负载 μ_c; GPU频率 f_g, GPU负载 μ_g
输出: 总电流值 I_total (mA)

--- 核心公式推导 ---
1. 功率方程: 根据 CMOS 电路原理，总功耗由动态翻转功耗和静态漏电功耗组成：
   $$P_{total} = P_{dyn} + P_{stat} = \alpha C V^2 f + V I_{leak}$$
2. 电压-频率耦合 (DVFS): 在现代处理器中，电压与频率近似呈线性关系：
   $$V \approx k_v f + V_{min}$$
3. 电流方程推导: 利用 I = P/V，代入 V 的表达式：
   $$I(f) = \frac{\alpha C V^2 f}{V} + \frac{V I_{leak}}{V} = \alpha C V f + I_{leak}$$
   $$I(f) = \alpha C (k_v f + V_{min}) f + I_{leak} = (\alpha C k_v)f^2 + (\alpha C V_{min})f + I_{leak}$$
4. 最终形式: 
   $$I = a f^2 + b f + c$$
   - a 代表动态电容特性与电压爬升速率的耦合。
   - b 代表基础开关损耗。
   - c 代表静态漏电流 (Leakage Current)。
"""

class Processor:
    """类的初始化"""
    def __init__(self, cfg):
        self.cfg = cfg.hardware
        self.V = self.cfg.SYSTEM['voltage']
        self.eta = self.cfg.SYSTEM['eta']
        
        # --- 大核(Big Cluster) 拟合数值 [基于 AOSP bonito 数据] ---
        # 拟合优度 R² = 0.962
        self.a_c = 1.15e-05  # 非线性因子 (mA/MHz^2)
        self.b_c = 1.05e-03  # 线性因子 (mA/MHz)
        self.c_c = 20.61     # 静态漏电 (mA)
        
        # --- GPU 标定数值 ---
        self.a_g = 8.50e-06
        self.b_g = 1.20e-03
        self.c_g = 15.00

    # 计算相应频率与负载下的总电流
    def I(self, f_cpu, mu_cpu, f_gpu, mu_gpu):
        """
        核心物理逻辑：
        I_total = [μ_cpu * (a_c*f_c^2 + b_c*f_c) + μ_gpu * (a_g*f_g^2 + b_g*f_g) + (c_c + c_g)] / η
        """
        # 1. CPU 动态贡献 (受负载 mu 调节)
        i_cpu_dyn = mu_cpu * (self.a_c * f_cpu**2 + self.b_c * f_cpu)
        
        # 2. GPU 动态贡献
        i_gpu_dyn = mu_gpu * (self.a_g * f_gpu**2 + self.b_g * f_gpu)
        
        # 3. 系统静态漏电 (常驻电量消耗)
        i_static = self.c_c + self.c_g
        
        # 4. 考虑转换效率计算最终电池端电流
        return (i_cpu_dyn + i_gpu_dyn + i_static) / self.eta


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
