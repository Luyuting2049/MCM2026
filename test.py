"""
test_scenarios.py
测试五种App在不同SOC下的续航时间
输出：5种App × 5种SOC = 25个续航时间
"""

import numpy as np
from config import ConfigAll
from core_model import (
    Display, Memory, Storage, Sensors, Processor,
    Bluetooth, Cellular, WiFi, Hotspot
)
from software_model import get_app


class BatterySimulator:
    """电池续航模拟器"""
    
    def __init__(self):
        # 加载硬件模型
        self.cfg = ConfigAll()
        
        # 初始化所有硬件模块
        self.display = Display(self.cfg)
        self.memory = Memory(self.cfg)
        self.storage = Storage(self.cfg)
        self.sensors = Sensors(self.cfg)
        self.processor = Processor(self.cfg)
        self.cellular = Cellular(self.cfg)
        self.wifi = WiFi(self.cfg)
        
        # 电池参数
        self.battery_capacity = self.cfg.hardware.SYSTEM['Q']  # mAh
        self.voltage = self.cfg.hardware.SYSTEM['voltage']
        
    def calculate_current(self, t_seconds, app):
        """计算t时刻的总电流（应用公式）"""
        # 获取App在当前时刻的参数
        params = app.get_params(t_seconds)
        
        total_current = 0.0
        
        # 1. 显示屏电流（考虑活跃度和效率）
        screen_params = params['screen']
        if screen_params['activity'] > 0:
            base_current = self.display.I(screen_params['brightness'])
            total_current += base_current * screen_params['activity'] * screen_params['eta']
        
        # 2. CPU电流
        cpu_params = params['cpu']
        if cpu_params['activity'] > 0:
            # 简化：只使用大核
            base_current = self.processor.I(
                f_cpu=cpu_params['freq'],
                mu_cpu=cpu_params['load'],
                f_gpu=0,  # GPU单独计算
                mu_gpu=0
            )
            # 减去GPU部分（因为上面计算了CPU+GPU，我们只要CPU）
            base_cpu_only = base_current * 0.7  # 估计CPU占70%
            total_current += base_cpu_only * cpu_params['activity'] * cpu_params['eta']
        
        # 3. GPU电流（如果有）
        gpu_params = params['gpu']
        if gpu_params['activity'] > 0:
            base_gpu = self.processor.I(
                f_cpu=0,
                mu_cpu=0,
                f_gpu=gpu_params['freq'],
                mu_gpu=gpu_params['load']
            )
            total_current += base_gpu * gpu_params['activity'] * gpu_params['eta']
        
        # 4. 内存电流
        mem_params = params['memory']
        if mem_params['activity'] > 0:
            base_current = self.memory.I(
                bw_r=mem_params['bw_r'],
                bw_w=mem_params['bw_w']
            )
            total_current += base_current * mem_params['activity'] * mem_params['eta']
        
        # 5. 存储电流
        store_params = params['storage']
        if store_params['activity'] > 0:
            base_current = self.storage.I(store_params['is_active'])
            total_current += base_current * store_params['activity'] * store_params['eta']
        
        # 6. 网络电流（蜂窝）
        net_params = params['network']
        if net_params['activity'] > 0:
            base_current = self.cellular.I(
                network_type=net_params['network_type'],
                rssi_db=net_params['rssi_db'],
                handoff_rate=0.1  # 假设切换频率
            )
            total_current += base_current * net_params['activity'] * net_params['eta']
        
        # 7. GPS电流
        gps_params = params['gps']
        if gps_params['activity'] > 0:
            base_current = self.sensors.I(gps_mode=gps_params['mode'])
            total_current += base_current * gps_params['activity'] * gps_params['eta']
        
        return total_current
    
    def simulate(self, start_soc, app_name, max_hours=24):
        """
        模拟从start_soc开始使用app，直到电量耗尽
        start_soc: 初始电量百分比（0-100）
        app_name: 'video', 'social', 'navigation', 'browser', 'music'
        max_hours: 最大模拟时间（防止无限循环）
        """
        # 获取App实例
        app = get_app(app_name)
        if app is None:
            print(f"错误：未知的App类型 '{app_name}'")
            return 0
        
        # 初始电量（mAh）
        initial_charge = self.battery_capacity * (start_soc / 100.0)
        remaining_charge = initial_charge
        
        # 时间步长（秒）
        dt = 1.0  # 1秒步长
        current_time = 0.0  # 秒
        
        # 每小时记录一次
        hourly_records = []
        
        while remaining_charge > 0 and current_time < max_hours * 3600:
            # 计算当前电流（mA）
            current_current = self.calculate_current(current_time, app)
            
            # 电量变化（mAh = mA × 小时）
            # 注意：电流是mA，dt是秒，需要转换为小时
            delta_charge = current_current * (dt / 3600.0)
            remaining_charge -= delta_charge
            
            # 记录每小时数据
            if current_time % 3600 < dt:
                hour = current_time / 3600.0
                soc = (remaining_charge / self.battery_capacity) * 100
                hourly_records.append({
                    'hour': hour,
                    'soc': soc,
                    'current': current_current,
                    'remaining_mAh': remaining_charge
                })
            
            current_time += dt
            
            # 每10分钟打印一次进度
            if current_time % 600 < dt:
                print(f"  {app_name}: {current_time/3600:.1f}h, "
                      f"剩余电量: {remaining_charge:.0f}mAh ({soc:.0f}%)")
        
        # 计算总续航时间（小时）
        total_hours = current_time / 3600.0
        
        return {
            'app_name': app_name,
            'start_soc': start_soc,
            'end_soc': (remaining_charge / self.battery_capacity) * 100 if remaining_charge > 0 else 0,
            'total_hours': total_hours,
            'total_minutes': total_hours * 60,
            'avg_current': (initial_charge - remaining_charge) / total_hours if total_hours > 0 else 0,
            'hourly_data': hourly_records
        }


def run_all_scenarios():
    """运行所有测试场景"""
    print("="*60)
    print("智能手机续航测试模拟")
    print(f"电池容量: {ConfigAll().hardware.SYSTEM['Q']}mAh")
    print("="*60)
    
    simulator = BatterySimulator()
    
    # 测试的SOC值
    soc_values = [100, 80, 60, 40, 20]  # 百分比
    
    # 测试的App类型
    app_types = ['video', 'social', 'navigation', 'browser', 'music']
    app_names = {
        'video': '视频流媒体',
        'social': '社交媒体',
        'navigation': '导航应用',
        'browser': '网页浏览',
        'music': '音乐播放'
    }
    
    # 结果表格
    results_table = {}
    
    for app in app_types:
        print(f"\n测试App: {app_names[app]}")
        print("-"*40)
        
        app_results = []
        for soc in soc_values:
            print(f"  开始SOC: {soc}%")
            result = simulator.simulate(start_soc=soc, app_name=app)
            app_results.append(result)
            
            print(f"    结果: 续航 {result['total_hours']:.1f}小时 "
                  f"({result['total_minutes']:.0f}分钟)")
            print(f"    平均电流: {result['avg_current']:.0f}mA")
        
        results_table[app] = app_results
    
    # 打印汇总表格
    print("\n" + "="*60)
    print("续航时间汇总表（小时）")
    print("="*60)
    print(f"{'App类型':<12}", end="")
    for soc in soc_values:
        print(f"{soc}%".center(10), end="")
    print()
    print("-"*60)
    
    for app in app_types:
        print(f"{app_names[app]:<12}", end="")
        for result in results_table[app]:
            hours = result['total_hours']
            print(f"{hours:>8.1f}  ", end="")
        print()
    
    # 额外信息：每小时耗电百分比
    print("\n" + "="*60)
    print("每小时耗电百分比（从100%开始）")
    print("="*60)
    
    for app in app_types:
        result = results_table[app][0]  # 从100%开始的结果
        if result['hourly_data']:
            print(f"\n{app_names[app]}:")
            for i, record in enumerate(result['hourly_data'][:6]):  # 前6小时
                if i < len(result['hourly_data']):
                    print(f"  第{i+1}小时: SOC={record['soc']:.0f}%, "
                          f"电流={record['current']:.0f}mA")
    
    return results_table


# 主程序入口
if __name__ == "__main__":
    print("正在启动续航模拟测试...")
    results = run_all_scenarios()
    
    print("\n" + "="*60)
    print("测试完成！")
    print("="*60)