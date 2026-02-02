# scenario_dynamic_journey.py
"""
Section 5.2: Dynamic Time-Series Simulation - Multiple Journeys
Each journey uses different combinations of the 5 app categories
"""
import json
import sys
import os
import numpy as np

# Ensure current directory is in Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from core_model import Display, Processor, Memory, Storage, Sensors, Cellular
    from software_model import get_app
    from config import cfg
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

class DynamicJourneySimulator:
    def __init__(self):
        # Initialize hardware models
        self.display = Display(cfg)
        self.processor = Processor(cfg)
        self.memory = Memory(cfg)
        self.storage = Storage(cfg)
        self.sensors = Sensors(cfg)
        self.cellular = Cellular(cfg)
        
        # Battery parameters
        self.Q_total = cfg.hardware.SYSTEM['Q']
        
        # Define 4 different journeys (each 4 hours total)
        self.journeys = {
            'journey_1': {
                'name': 'Weekend Entertainment',
                'description': 'Video streaming followed by music',
                'segments': [
                    {'app': 'video', 'duration': 120},    # 2 hours video
                    {'app': 'music', 'duration': 120},    # 2 hours music
                ]
            },
            'journey_2': {
                'name': 'Commute & Work',
                'description': 'Navigation, social media, and browsing',
                'segments': [
                    {'app': 'navigation', 'duration': 60},   # 1 hour navigation
                    {'app': 'social', 'duration': 60},       # 1 hour social
                    {'app': 'browser', 'duration': 120},     # 2 hours browsing
                ]
            },
            'journey_3': {
                'name': 'Mixed Daily Usage',
                'description': 'Balanced mix of all app categories',
                'segments': [
                    {'app': 'navigation', 'duration': 30},   # 0.5 hour navigation
                    {'app': 'social', 'duration': 60},       # 1 hour social
                    {'app': 'video', 'duration': 60},        # 1 hour video
                    {'app': 'music', 'duration': 90},        # 1.5 hours music
                    {'app': 'browser', 'duration': 60},      # 1 hour browsing
                ]
            },
            'journey_4': {
                'name': 'Business Travel',
                'description': 'Extended navigation with media',
                'segments': [
                    {'app': 'navigation', 'duration': 180},  # 3 hours navigation
                    {'app': 'music', 'duration': 60},        # 1 hour music
                ]
            }
        }
    
    def calculate_current(self, app_name, t_seconds):
        """Calculate current for specific app at time t"""
        app = get_app(app_name)
        if not app:
            return 0.0
        
        params = app.get_params(t_seconds)
        I_total = 0.0
        
        # Display
        if params['screen']['activity'] > 0:
            I_display = self.display.I(params['screen']['brightness'])
            I_total += I_display * params['screen']['activity'] * params['screen']['eta']
        
        # Processor
        if params['cpu']['activity'] > 0:
            I_cpu = self.processor.I(
                f_cpu=params['cpu']['freq'],
                mu_cpu=params['cpu']['load'],
                f_gpu=params['gpu']['freq'],
                mu_gpu=params['gpu']['load']
            )
            I_total += I_cpu * params['cpu']['activity'] * params['cpu']['eta']
        
        # Memory
        if params['memory']['activity'] > 0:
            I_mem = self.memory.I(
                bw_r=params['memory']['bw_r'],
                bw_w=params['memory']['bw_w']
            )
            I_total += I_mem * params['memory']['activity'] * params['memory']['eta']
        
        # Storage
        if params['storage']['activity'] > 0:
            I_storage = self.storage.I(params['storage']['is_active'])
            I_total += I_storage * params['storage']['activity'] * params['storage']['eta']
        
        # GPS
        if params['gps']['activity'] > 0:
            I_gps = self.sensors.I(gps_mode=params['gps']['mode'])
            I_total += I_gps * params['gps']['activity'] * params['gps']['eta']
        
        # Cellular
        if params['network']['activity'] > 0:
            I_net = self.cellular.I(
                network_type=params['network']['network_type'],
                rssi_db=params['network']['rssi_db']
            )
            I_total += I_net * params['network']['activity'] * params['network']['eta']
        
        return I_total
    
    def simulate_journey(self, journey_id, soc_initial=1.0):
        """
        Simulate a complete journey
        Returns: time-series data
        """
        journey = self.journeys[journey_id]
        total_duration = sum(seg['duration'] for seg in journey['segments']) * 60  # Convert to seconds
        
        # Initialize
        Q_current = soc_initial * self.Q_total
        dt = 15.0  # 15-second time step (for speed)
        t_seconds = 0
        
        # Recording arrays
        time_points = []
        soc_points = []
        current_points = []
        app_points = []
        segment_points = []
        
        # Helper: Get current app based on elapsed time
        def get_current_app(elapsed_seconds):
            elapsed_minutes = elapsed_seconds / 60.0
            cumulative = 0
            for seg in journey['segments']:
                cumulative += seg['duration']
                if elapsed_minutes <= cumulative:
                    return seg['app'], cumulative - seg['duration']
            return 'music', 0  # Default
        
        # Main simulation loop
        segment_index = 0
        current_segment_start = 0
        
        while t_seconds <= total_duration and Q_current > 0:
            current_app, segment_start = get_current_app(t_seconds)
            
            # Detect segment change
            if t_seconds == 0 or (t_seconds - segment_start * 60) < dt:
                if segment_start > current_segment_start:
                    current_segment_start = segment_start
                    segment_index += 1
            
            # Calculate current
            I_now = self.calculate_current(current_app, t_seconds)
            
            # Update battery
            Q_current -= I_now * (dt / 3600.0)
            
            # Record data (every 2 minutes)
            if t_seconds % 120 == 0:
                time_points.append(t_seconds / 3600.0)  # Hours
                soc_points.append(max(0, Q_current / self.Q_total * 100))
                current_points.append(I_now)
                app_points.append(current_app)
                segment_points.append(segment_index)
            
            # Advance time
            t_seconds += dt
        
        # Ensure we record the end state
        if len(time_points) == 0 or time_points[-1] < total_duration/3600:
            final_time = min(t_seconds, total_duration) / 3600.0
            time_points.append(final_time)
            soc_points.append(max(0, Q_current / self.Q_total * 100))
            current_points.append(0)
            app_points.append('end')
            segment_points.append(segment_index)
        
        return {
            'journey_id': journey_id,
            'journey_name': journey['name'],
            'description': journey['description'],
            'time_hours': time_points,
            'soc_percent': soc_points,
            'current_mA': current_points,
            'current_app': app_points,
            'segments': segment_points,
            'final_soc': max(0, Q_current / self.Q_total * 100),
            'energy_used': (soc_initial * 100 - max(0, Q_current / self.Q_total * 100)) / 100 * self.Q_total,
            'total_duration': total_duration / 3600.0,
            'segments_detail': journey['segments']
        }
    
    def simulate_all_journeys(self, soc_initial=1.0):
        """
        Simulate all 4 journeys
        """
        print(f"\nSimulating 4 journeys (each 4 hours, SOC={int(soc_initial*100)}%)...")
        print("=" * 70)
        
        all_results = {}
        
        for journey_id in self.journeys.keys():
            print(f"\nJourney: {self.journeys[journey_id]['name']}")
            print(f"Description: {self.journeys[journey_id]['description']}")
            print("Progress: [", end="", flush=True)
            
            result = self.simulate_journey(journey_id, soc_initial)
            all_results[journey_id] = result
            
            print(f"] - Final SOC: {result['final_soc']:.1f}%")
        
        # Save all results
        output_data = {
            'soc_initial': soc_initial,
            'battery_capacity': self.Q_total,
            'journeys': all_results
        }
        
        with open('dynamic_journey_results.json', 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print("\n" + "=" * 70)
        print("All journeys simulated successfully!")
        print(f"Results saved to 'dynamic_journey_results.json'")
        
        return output_data

def main():
    """Main execution function"""
    print("=" * 70)
    print("MCM 2026 - Section 5.2: Dynamic Time-Series Simulation")
    print("4 Different Journeys Using 5 App Categories")
    print("=" * 70)
    
    try:
        simulator = DynamicJourneySimulator()
        results = simulator.simulate_all_journeys(soc_initial=1.0)
        
        # Print summary
        print("\n" + "=" * 70)
        print("JOURNEY SIMULATION SUMMARY")
        print("=" * 70)
        print(f"{'Journey Name':<25} | {'Final SOC':>10} | {'Energy Used':>12} | {'Avg Current':>12}")
        print("-" * 70)
        
        for journey_id, data in results['journeys'].items():
            energy_used = data['energy_used']
            avg_current = np.mean(data['current_mA']) if data['current_mA'] else 0
            print(f"{data['journey_name']:<25} | {data['final_soc']:9.1f}% | "
                  f"{energy_used:11.0f} mAh | {avg_current:11.0f} mA")
        
        print("=" * 70)
        
    except Exception as e:
        print(f"\nError during simulation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()