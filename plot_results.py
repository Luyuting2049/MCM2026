# plot_results.py
"""
Visualization for MCM 2026 Results
Clean, professional academic style
"""
import json
import matplotlib.pyplot as plt
import numpy as np
import matplotlib

# Set clean academic style
matplotlib.rcParams.update({
    'font.size': 10,
    'font.family': 'sans-serif',
    'figure.autolayout': True
})

def plot_static_results():
    """Plot Section 5.1 results - 4 App Categories (excluding Music), 3 SOC levels"""
    try:
        with open('static_benchmark_results.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Error: static_benchmark_results.json not found")
        return
    
    results = data['results']
    
    # Exclude music category as requested
    app_keys = ['video', 'social', 'navigation', 'browser']  # Skip 'music'
    
    # App name mapping for display
    app_display_names = {
        'video': 'Video Streaming',
        'social': 'Social Media', 
        'navigation': 'Navigation',
        'browser': 'Web Browsing'
    }
    
    app_names = [app_display_names[key] for key in app_keys]
    soc_levels = ['100%', '50%', '20%']
    
    # Extract TTE values
    tte_data = np.zeros((len(soc_levels), len(app_keys)))
    for i, soc in enumerate(soc_levels):
        for j, app_key in enumerate(app_keys):
            tte_data[i, j] = results[app_key]['tte'][soc]
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # Bar positions
    x = np.arange(len(app_names))
    width = 0.25
    colors = ['#2c7bb6', '#abd9e9', '#fdae61']  # Clean blue-orange palette
    
    # Plot grouped bars
    for i, (soc, color) in enumerate(zip(soc_levels, colors)):
        offset = (i - 1) * width
        bars = ax.bar(x + offset, tte_data[i], width, label=f'{soc} SOC',
                     color=color, edgecolor='black', linewidth=0.8)
        
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                   f'{height:.1f}', ha='center', va='bottom', fontsize=9)
    
    # Customize plot
    ax.set_xlabel('Application Category', fontsize=12)
    ax.set_ylabel('Time To Empty (hours)', fontsize=12)
    ax.set_title('Static TTE Benchmarking: Battery Life Across Different Usage Scenarios',
                fontsize=14, pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(app_names, fontsize=11)
    ax.legend(title='Initial State of Charge', fontsize=10)
    ax.grid(True, alpha=0.2, linestyle='--', axis='y')
    ax.set_axisbelow(True)
    
    # Add horizontal reference lines
    y_max = np.max(tte_data)
    for y in np.arange(2, y_max + 2, 2):
        ax.axhline(y=y, color='gray', linestyle=':', alpha=0.15, linewidth=0.5)
    
    plt.tight_layout()
    plt.savefig('static_benchmark.png', dpi=300)
    print("Static benchmark plot saved as 'static_benchmark.png'")
    plt.show()

def plot_dynamic_journeys():
    """Plot Section 5.2 results - 4 Journeys"""
    try:
        with open('dynamic_journey_results.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Error: dynamic_journey_results.json not found")
        return
    
    journeys = data['journeys']
    journey_ids = list(journeys.keys())
    
    # Create figure with 4 subplots
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()
    
    # Color scheme for apps
    app_colors = {
        'video': '#e41a1c',
        'social': '#377eb8',
        'navigation': '#4daf4a',
        'browser': '#984ea3',
        'music': '#ff7f00',
        'end': '#999999'
    }
    
    # Plot each journey
    for idx, journey_id in enumerate(journey_ids):
        if idx >= len(axes):
            break
            
        journey = journeys[journey_id]
        ax = axes[idx]
        
        # Plot SOC curve
        time_hours = journey['time_hours']
        soc_percent = journey['soc_percent']
        ax.plot(time_hours, soc_percent, 'k-', linewidth=2.0, label='Battery SOC')
        
        # Highlight app segments with background colors
        current_app = None
        segment_start = 0
        
        for i, (t, app) in enumerate(zip(time_hours, journey['current_app'])):
            if app != current_app:
                if current_app is not None:
                    # Fill previous segment
                    ax.axvspan(segment_start, t, alpha=0.15, 
                              color=app_colors.get(current_app, 'gray'))
                    
                    # Add label at segment middle
                    mid_point = (segment_start + t) / 2
                    ax.text(mid_point, 15, current_app.title(), 
                           ha='center', va='center', fontsize=9)
                
                current_app = app
                segment_start = t
        
        # Fill last segment
        if current_app and len(time_hours) > 0:
            ax.axvspan(segment_start, time_hours[-1], alpha=0.15,
                      color=app_colors.get(current_app, 'gray'))
            
            if current_app != 'end':
                mid_point = (segment_start + time_hours[-1]) / 2
                ax.text(mid_point, 15, current_app.title(),
                       ha='center', va='center', fontsize=9)
        
        # Customize subplot
        ax.set_xlabel('Time (hours)', fontsize=11)
        ax.set_ylabel('State of Charge (%)', fontsize=11)
        ax.set_title(journey['journey_name'], fontsize=12)
        ax.grid(True, alpha=0.2, linestyle='--')
        ax.set_xlim(0, max(time_hours) * 1.02)
        ax.set_ylim(0, 105)
        
        # Add final SOC annotation
        final_soc = journey['final_soc']
        ax.text(time_hours[-1], final_soc, f'{final_soc:.1f}%',
               fontsize=10, ha='right', va='bottom')
    
    plt.suptitle('Dynamic Journey Simulations: 4 Different Usage Scenarios',
                fontsize=14, y=1.02)
    plt.tight_layout()
    plt.savefig('dynamic_journeys.png', dpi=300)
    print("Dynamic journeys plot saved as 'dynamic_journeys.png'")
    plt.show()

def plot_comparison():
    """Create comparison plot of all journeys"""
    try:
        with open('dynamic_journey_results.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Error: dynamic_journey_results.json not found")
        return
    
    journeys = data['journeys']
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Prepare data
    journey_names = []
    final_socs = []
    energy_useds = []
    
    for journey_id, journey_data in journeys.items():
        journey_names.append(journey_data['journey_name'])
        final_socs.append(journey_data['final_soc'])
        energy_useds.append(journey_data['energy_used'])
    
    # Plot 1: Final SOC comparison
    x = range(len(journey_names))
    colors = ['#66c2a5', '#fc8d62', '#8da0cb', '#e78ac3']
    
    bars1 = ax1.bar(x, final_socs, color=colors, edgecolor='black')
    ax1.set_xlabel('Journey', fontsize=11)
    ax1.set_ylabel('Final SOC (%)', fontsize=11)
    ax1.set_title('Final Battery State After 4-Hour Journeys', fontsize=12)
    ax1.set_xticks(x)
    ax1.set_xticklabels(journey_names, rotation=15, ha='right')
    ax1.grid(True, alpha=0.2, axis='y')
    
    # Add values on bars
    for bar in bars1:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                f'{height:.1f}%', ha='center', va='bottom', fontsize=10)
    
    # Plot 2: Energy used comparison
    bars2 = ax2.bar(x, energy_useds, color=colors, edgecolor='black')
    ax2.set_xlabel('Journey', fontsize=11)
    ax2.set_ylabel('Energy Used (mAh)', fontsize=11)
    ax2.set_title('Total Energy Consumption', fontsize=12)
    ax2.set_xticks(x)
    ax2.set_xticklabels(journey_names, rotation=15, ha='right')
    ax2.grid(True, alpha=0.2, axis='y')
    
    # Add values on bars
    for bar in bars2:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 5,
                f'{height:.0f}', ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    plt.savefig('journey_comparison.png', dpi=300)
    print("Journey comparison plot saved as 'journey_comparison.png'")
    plt.show()

def main():
    """Main plotting function"""
    print("=" * 60)
    print("MCM 2026 - Results Visualization")
    print("=" * 60)
    
    try:
        # Plot static results
        print("\n1. Plotting Static Benchmark Results (Section 5.1)...")
        plot_static_results()
        
        # Plot dynamic results
        print("\n2. Plotting Dynamic Journey Results (Section 5.2)...")
        plot_dynamic_journeys()
        
        # Plot comparison
        print("\n3. Plotting Journey Comparison...")
        plot_comparison()
        
        print("\n" + "=" * 60)
        print("All plots generated successfully!")
        print("\nGenerated files:")
        print("  - static_benchmark.png")
        print("  - dynamic_journeys.png")
        print("  - journey_comparison.png")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nError during plotting: {e}")
        print("Please ensure both simulation programs have been executed first.")

if __name__ == "__main__":
    main()