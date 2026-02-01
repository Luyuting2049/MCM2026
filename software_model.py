"""
software_model.py
软件层参数和五类App的行为定义
核心公式：I_total = Σ [硬件电流 × 活跃度(t) × 效率系数]
"""

import numpy as np

# 新增参数定义 ====================================
class SoftwareParams:
    """软件层新增的参数"""
    
    # 1. 效率系数表（η值，越大越耗电）
    EFFICIENCY_FACTORS = {
        'network': {
            'video_stream': 1.2,      # 大块数据传输，效率高
            'social_media': 2.5,      # HTTP小请求多，效率低
            'navigation': 1.5,        # 地图数据下载，中等
            'web_browse': 1.8,        # 混合大小请求
            'music': 1.3,             # 偶尔下载，效率较高
            'idle': 1.0,              # 网络休眠
        },
        'screen': {
            'video_watch': 1.3,       # 视频播放，亮度高
            'social_scroll': 1.8,     # 频繁刷新，UI复杂
            'map_view': 1.5,          # 地图渲染
            'reading': 1.2,           # 阅读模式，较省电
            'off': 1.0,               # 屏幕关闭
        },
        'gps': {
            'continuous': 1.0,        # 持续追踪
            'periodic': 1.5,          # 间歇定位
            'off': 1.0,
        },
        'cpu': {
            'video_decode': 1.3,      # 视频解码
            'ui_render': 1.5,         # UI渲染
            'audio_decode': 1.1,      # 音频解码
            'idle': 1.0,
        },
    }
    
# 2. 活跃度模式（时间函数）
    @staticmethod
    def get_activity(t_seconds, app_type, hardware):
        """返回t时刻某硬件的活跃度（0-1）"""
        if hardware == 'screen':
            if app_type == 'video_stream':
                # 看视频时屏幕一直亮
                return 1.0 if t_seconds % 600 < 590 else 0.0  # 每10分钟休息10秒
            elif app_type == 'social_media':
                # 刷社交：亮45秒，熄15秒循环
                return 1.0 if t_seconds % 60 < 45 else 0.0
            elif app_type == 'navigation':
                # 导航时屏幕常亮
                return 1.0
            elif app_type == 'web_browse':
                # 浏览网页：亮50秒，熄10秒
                return 1.0 if t_seconds % 60 < 50 else 0.0
            else:  # music
                # 听音乐时屏幕偶尔亮 - 改为基本不亮
                return 0.0  # 改为0.0，音乐播放时屏幕基本关闭
        
        elif hardware == 'network':
            if app_type == 'video_stream':
                # 视频流：前5秒高速下载，然后稳定
                cycle = t_seconds % 30  # 每30秒一个缓冲周期
                return 1.0 if cycle < 5 else 0.3
            elif app_type == 'social_media':
                # 社交：每10秒一个小请求
                return 1.0 if t_seconds % 10 < 0.5 else 0.1
            elif app_type == 'navigation':
                # 导航：每60秒更新地图
                return 1.0 if t_seconds % 60 < 2 else 0.2
            elif app_type == 'web_browse':
                # 浏览：随机请求
                return np.random.choice([0.0, 0.3, 1.0], p=[0.7, 0.2, 0.1])
            else:  # music
                # 音乐：每30秒一个极小心跳包
                return 0.01 if t_seconds % 30 < 0.1 else 0.0  # 改为心跳包模式
        
        elif hardware == 'cpu':
            # CPU活跃度跟随屏幕
            screen_act = SoftwareParams.get_activity(t_seconds, app_type, 'screen')
            if app_type == 'music':
                # 音乐：持续低活跃度解码
                return 0.3  # 改为固定30%活跃度
            return screen_act * 0.7 + 0.1  # 基础10%，屏幕亮时再加
        
        elif hardware == 'gps':
            if app_type == 'navigation':
                return 1.0  # 导航时GPS一直开
            else:
                return 0.0
        
        elif hardware == 'memory':
            # 内存活跃度跟随CPU
            cpu_act = SoftwareParams.get_activity(t_seconds, app_type, 'cpu')
            if app_type == 'music':
                return cpu_act * 0.3  # 音乐内存使用更低
            return cpu_act * 0.5
        
        elif hardware == 'storage':
            # 存储偶尔活跃
            if app_type == 'social_media':
                return 1.0 if t_seconds % 30 < 1 else 0.0  # 每30秒缓存一次
            else:
                return 0.0
        
        return 0.0  # 默认


# 五类App定义 ====================================
class VideoStreamApp:
    """视频流媒体App（如抖音、YouTube）"""
    
    def __init__(self):
        self.app_type = 'video_stream'
        
    def get_params(self, t_seconds):
        """返回t时刻的所有参数"""
        return {
            'screen': {
                'brightness': 0.8,  # 亮度80%
                'activity': SoftwareParams.get_activity(t_seconds, self.app_type, 'screen'),
                'eta': SoftwareParams.EFFICIENCY_FACTORS['screen']['video_watch'],
            },
            'network': {
                'network_type': '4G',
                'rssi_db': -70,
                'activity': SoftwareParams.get_activity(t_seconds, self.app_type, 'network'),
                'eta': SoftwareParams.EFFICIENCY_FACTORS['network'][self.app_type],
            },
            'cpu': {
                'freq': 1800,  # MHz
                'load': 0.6,   # 60%负载
                'activity': SoftwareParams.get_activity(t_seconds, self.app_type, 'cpu'),
                'eta': SoftwareParams.EFFICIENCY_FACTORS['cpu']['video_decode'],
            },
            'gpu': {
                'freq': 500,
                'load': 0.4,
                'activity': SoftwareParams.get_activity(t_seconds, self.app_type, 'cpu') * 0.8,
                'eta': 1.2,
            },
            'gps': {'activity': 0.0, 'mode': 'off', 'eta': 1.0},
            'memory': {
                'bw_r': 0.5,  # GB/s
                'bw_w': 0.1,
                'activity': SoftwareParams.get_activity(t_seconds, self.app_type, 'memory'),
                'eta': 1.0,
            },
            'storage': {
                'is_active': SoftwareParams.get_activity(t_seconds, self.app_type, 'storage') > 0.5,
                'activity': SoftwareParams.get_activity(t_seconds, self.app_type, 'storage'),
                'eta': 1.0,
            },
        }


class SocialMediaApp:
    """社交媒体App（如微信、微博）"""
    
    def __init__(self):
        self.app_type = 'social_media'
        
    def get_params(self, t_seconds):
        return {
            'screen': {
                'brightness': 0.6,
                'activity': SoftwareParams.get_activity(t_seconds, self.app_type, 'screen'),
                'eta': SoftwareParams.EFFICIENCY_FACTORS['screen']['social_scroll'],
            },
            'network': {
                'network_type': '4G',
                'rssi_db': -75,
                'activity': SoftwareParams.get_activity(t_seconds, self.app_type, 'network'),
                'eta': SoftwareParams.EFFICIENCY_FACTORS['network'][self.app_type],
            },
            'cpu': {
                'freq': 1400,
                'load': 0.4,
                'activity': SoftwareParams.get_activity(t_seconds, self.app_type, 'cpu'),
                'eta': SoftwareParams.EFFICIENCY_FACTORS['cpu']['ui_render'],
            },
            'gpu': {
                'freq': 300,
                'load': 0.3,
                'activity': SoftwareParams.get_activity(t_seconds, self.app_type, 'cpu') * 0.6,
                'eta': 1.5,
            },
            'gps': {'activity': 0.0, 'mode': 'off', 'eta': 1.0},
            'memory': {
                'bw_r': 0.2,
                'bw_w': 0.05,
                'activity': SoftwareParams.get_activity(t_seconds, self.app_type, 'memory'),
                'eta': 1.0,
            },
            'storage': {
                'is_active': SoftwareParams.get_activity(t_seconds, self.app_type, 'storage') > 0.5,
                'activity': SoftwareParams.get_activity(t_seconds, self.app_type, 'storage'),
                'eta': 1.0,
            },
        }


class NavigationApp:
    """导航App（如高德地图）"""
    
    def __init__(self):
        self.app_type = 'navigation'
        
    def get_params(self, t_seconds):
        return {
            'screen': {
                'brightness': 0.7,
                'activity': SoftwareParams.get_activity(t_seconds, self.app_type, 'screen'),
                'eta': SoftwareParams.EFFICIENCY_FACTORS['screen']['map_view'],
            },
            'network': {
                'network_type': '4G',
                'rssi_db': -80,
                'activity': SoftwareParams.get_activity(t_seconds, self.app_type, 'network'),
                'eta': SoftwareParams.EFFICIENCY_FACTORS['network'][self.app_type],
            },
            'cpu': {
                'freq': 1600,
                'load': 0.5,
                'activity': SoftwareParams.get_activity(t_seconds, self.app_type, 'cpu'),
                'eta': SoftwareParams.EFFICIENCY_FACTORS['cpu']['ui_render'],
            },
            'gpu': {
                'freq': 400,
                'load': 0.5,
                'activity': SoftwareParams.get_activity(t_seconds, self.app_type, 'cpu') * 0.9,
                'eta': 1.3,
            },
            'gps': {
                'activity': SoftwareParams.get_activity(t_seconds, self.app_type, 'gps'),
                'mode': 'track',
                'eta': SoftwareParams.EFFICIENCY_FACTORS['gps']['continuous'],
            },
            'memory': {
                'bw_r': 0.3,
                'bw_w': 0.1,
                'activity': SoftwareParams.get_activity(t_seconds, self.app_type, 'memory'),
                'eta': 1.0,
            },
            'storage': {
                'is_active': False,
                'activity': 0.0,
                'eta': 1.0,
            },
        }


class WebBrowserApp:
    """网页浏览器（如Chrome）"""
    
    def __init__(self):
        self.app_type = 'web_browse'
        
    def get_params(self, t_seconds):
        return {
            'screen': {
                'brightness': 0.5,
                'activity': SoftwareParams.get_activity(t_seconds, self.app_type, 'screen'),
                'eta': SoftwareParams.EFFICIENCY_FACTORS['screen']['reading'],
            },
            'network': {
                'network_type': '4G',
                'rssi_db': -72,
                'activity': SoftwareParams.get_activity(t_seconds, self.app_type, 'network'),
                'eta': SoftwareParams.EFFICIENCY_FACTORS['network'][self.app_type],
            },
            'cpu': {
                'freq': 1500,
                'load': 0.5,
                'activity': SoftwareParams.get_activity(t_seconds, self.app_type, 'cpu'),
                'eta': SoftwareParams.EFFICIENCY_FACTORS['cpu']['ui_render'],
            },
            'gpu': {
                'freq': 350,
                'load': 0.4,
                'activity': SoftwareParams.get_activity(t_seconds, self.app_type, 'cpu') * 0.7,
                'eta': 1.4,
            },
            'gps': {'activity': 0.0, 'mode': 'off', 'eta': 1.0},
            'memory': {
                'bw_r': 0.4,
                'bw_w': 0.08,
                'activity': SoftwareParams.get_activity(t_seconds, self.app_type, 'memory'),
                'eta': 1.0,
            },
            'storage': {
                'is_active': False,
                'activity': 0.0,
                'eta': 1.0,
            },
        }


class MusicApp:
    """音乐App（如网易云音乐）- 修正版"""
    
    def __init__(self):
        self.app_type = 'music'
        
    def get_params(self, t_seconds):
        return {
            'screen': {
                'brightness': 0.0,
                'activity': 0.0,  # 完全熄屏
                'eta': 1.0,
            },
            'network': {
                'network_type': '4G',
                'rssi_db': -70,
                'activity': 0.01 if t_seconds % 30 < 0.5 else 0.0,  # 每30秒心跳
                'eta': 1.0,  # 最低效率系数
            },
            'cpu': {
                'freq': 300,   # 极低频
                'load': 0.1,   # 极低负载
                'activity': 0.3,  # 持续后台运行
                'eta': 1.0,    # 高效解码
            },
            'gpu': {
                'freq': 0,
                'load': 0.0,
                'activity': 0.0,
                'eta': 1.0,
            },
            'gps': {'activity': 0.0, 'mode': 'off', 'eta': 1.0},
            'memory': {
                'bw_r': 0.01,  # 极低带宽
                'bw_w': 0.0,
                'activity': 0.1,
                'eta': 1.0,
            },
            'storage': {
                'is_active': False,
                'activity': 0.0,
                'eta': 1.0,
            },
        }


# App工厂函数
def get_app(app_name):
    """根据名称获取App实例"""
    apps = {
        'video': VideoStreamApp,
        'social': SocialMediaApp,
        'navigation': NavigationApp,
        'browser': WebBrowserApp,
        'music': MusicApp,
    }
    return apps[app_name]() if app_name in apps else None