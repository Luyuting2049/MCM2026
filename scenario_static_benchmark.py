# scenario_static_benchmark.py
"""
Section 5.1: Static TTE Benchmarking - Based on 5 App Categories
"""
import json
import sys
import os

# Ensure current directory is in Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from core_model import Display, Processor, Memory, Storage, Sensors, Cellular
    from software_model import get_app
    from config import cfg
except ImportError as e:
    print(f"Import Error: {e}")
    print("Please ensure all required files are in the same directory:")
    print("  - config.py")
    print("  - core_model.py (contains all hardware classes)")
    print("  - software_model.py")
    sys.exit(1)

class StaticBenchmark:
    def __init__(self):
        # Initialize hardware models
        self.display = Display(cfg)
        self.processor = Processor(cfg)
        self.memory = Memory(cfg)
        self.storage = Storage(cfg)
        self.sensors = Sensors(cfg)
        self.cellular = Cellular(cfg)
        
        # Battery parameters
        self.Q_total = cfg.hardware.SYSTEM['Q']  # Battery capacity (mAh)
        
        # Define 5 app categories from your model
        self.app_categories = {
            'video': 'Video Streaming (TikTok/YouTube)',
            'social': 'Social Media (WeChat/Weibo)',
            'navigation': 'Navigation (Gaode Maps)',
            'browser': 'Web Browsing (Chrome)',
            'music': 'Music Playback (NetEase Cloud Music)'
        }
    
    def calculate_current_for_app(self, app_name, t_seconds):
        """
        Calculate total current for a specific app at time t
        Based on your software_model's app parameters
        """
        app = get_app(app_name)
        if not app:
            return 0.0
        
        params = app.get_params(t_seconds)
        I_total = 0.0
        
        # Display current
        if params['screen']['activity'] > 0:
            I_display = self.display.I(params['screen']['brightness'])
            I_total += I_display * params['screen']['activity'] * params['screen']['eta']
        
        # Processor current
        if params['cpu']['activity'] > 0:
            I_cpu = self.processor.I(
                f_cpu=params['cpu']['freq'],
                mu_cpu=params['cpu']['load'],
                f_gpu=params['gpu']['freq'],
                mu_gpu=params['gpu']['load']
            )
            I_total += I_cpu * params['cpu']['activity'] * params['cpu']['eta']
        
        # Memory current
        if params['memory']['activity'] > 0:
            I_mem = self.memory.I(
                bw_r=params['memory']['bw_r'],
                bw_w=params['memory']['bw_w']
            )
            I_total += I_mem * params['memory']['activity'] * params['memory']['eta']
        
        # Storage current
        if params['storage']['activity'] > 0:
            I_storage = self.storage.I(params['storage']['is_active'])
            I_total += I_storage * params['storage']['activity'] * params['storage']['eta']
        
        # GPS current
        if params['gps']['activity'] > 0:
            I_gps = self.sensors.I(gps_mode=params['gps']['mode'])
            I_total += I_gps * params['gps']['activity'] * params['gps']['eta']
        
        # Cellular network current
        if params['network']['activity'] > 0:
            I_net = self.cellular.I(
                network_type=params['network']['network_type'],
                rssi_db=params['network']['rssi_db']
            )
            I_total += I_net * params['network']['activity'] * params['network']['eta']
        
        return I_total
    
    def simulate_single_scenario(self, app_name, soc_initial=1.0, max_hours=48):
        """
        Simulate until battery empty for a single app
        """
        Q_current = soc_initial * self.Q_total
        dt = 10.0  # Time step: 10 seconds (for speed)
        max_seconds = max_hours * 3600
        t_seconds = 0
        elapsed_time = 0
        
        while t_seconds < max_seconds and Q_current > 0:
            # Calculate current
            I_now = self.calculate_current_for_app(app_name, t_seconds)
            
            # Update battery charge
            Q_current -= I_now * (dt / 3600.0)  # Convert mA·s to mAh
            
            # Advance time
            t_seconds += dt
            elapsed_time = t_seconds
        
        # Calculate TTE in hours
        if Q_current <= 0:
            tte_hours = elapsed_time / 3600.0
        else:
            tte_hours = max_hours  # Didn't deplete within simulation limit
        
        return round(tte_hours, 2)
    
    def run_benchmarks(self):
        """
        Run TTE benchmarks for all 5 app categories at 3 SOC levels
        """
        soc_levels = [1.0, 0.5, 0.2]  # 100%, 50%, 20%
        results = {}
        
        print("Running Static TTE Benchmarks for 5 App Categories...")
        print("=" * 70)
        
        for app_key, app_desc in self.app_categories.items():
            print(f"\nTesting: {app_desc}")
            app_results = {}
            
            for soc in soc_levels:
                soc_percent = int(soc * 100)
                print(f"  - SOC {soc_percent}%: ", end="", flush=True)
                
                tte = self.simulate_single_scenario(app_key, soc_initial=soc)
                app_results[f'{soc_percent}%'] = tte
                
                print(f"{tte:.1f} hours")
            
            results[app_key] = {
                'description': app_desc,
                'tte': app_results
            }
        
        # Save results
        output_data = {
            'battery_capacity': self.Q_total,
            'units': 'hours',
            'results': results
        }
        
        with open('static_benchmark_results.json', 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print("\n" + "=" * 70)
        print(f"Results saved to 'static_benchmark_results.json'")
        
        return output_data

def main():
    """Main execution function"""
    print("=" * 70)
    print("MCM 2026 - Section 5.1: Static TTE Benchmarking")
    print("Using 5 App Categories from Software Model")
    print("=" * 70)
    
    try:
        benchmark = StaticBenchmark()
        results = benchmark.run_benchmarks()
        
        # Print summary table
        print("\n" + "=" * 70)
        print("SUMMARY TABLE: Time To Empty (hours)")
        print("=" * 70)
        print(f"{'App Category':<25} | {'100%':>8} | {'50%':>8} | {'20%':>8}")
        print("-" * 70)
        
        for app_key, data in results['results'].items():
            desc_short = data['description'].split('(')[0].strip()
            tte_data = data['tte']
            print(f"{desc_short:<25} | {tte_data['100%']:8.1f} | "
                  f"{tte_data['50%']:8.1f} | {tte_data['20%']:8.1f}")
        
        print("=" * 70)
        
    except Exception as e:
        print(f"\nError during simulation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()