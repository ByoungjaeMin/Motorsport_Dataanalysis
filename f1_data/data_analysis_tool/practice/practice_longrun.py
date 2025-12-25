# -*- coding: utf-8 -*-
import fastf1
import fastf1.plotting
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import numpy as np
import os

# Setup FastF1 plotting
fastf1.plotting.setup_mpl()

# [2025 Season Custom Colors]
CUSTOM_COLORS = {
    'VER': '#0600EF', 'TSU': '#0600EF', 
    'LEC': '#E8002D', 'HAM': '#E8002D',
    'NOR': '#FF8000', 'PIA': '#FF8000',
    'RUS': '#00D2BE', 'ANT': '#00D2BE',
    'ALO': '#229971', 'STR': '#229971',
    'GAS': '#0093CC', 'DOO': '#0093CC', 'COL': '#0093CC',
    'ALB': '#64C4FF', 'SAI': '#64C4FF',
    'LAW': '#6692FF', 'HAD': '#6692FF',
    'HUL': '#52E252', 'BOR': '#52E252',
    'OCO': '#B6BABD', 'BEA': '#B6BABD',
}

def get_driver_color_safe(abb, session):
    if abb in CUSTOM_COLORS: return CUSTOM_COLORS[abb]
    try: return fastf1.plotting.get_driver_color(abb, session=session)
    except: return 'gray'

def style_dark_plot(fig, ax):
    """Apply consistent dark theme"""
    fig.patch.set_facecolor('#1e1e1e')
    ax.set_facecolor('#1e1e1e')
    ax.grid(True, linestyle='--', alpha=0.2, color='white')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color('white')
    ax.spines['left'].set_color('white')
    ax.tick_params(colors='white')
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white')
    ax.title.set_color('white')

def analyze_long_runs(session):
    """
    [Feature 5] Long Run Analysis (Matches Reference Style)
    1. Plots separate Trend and Consistency charts.
    2. Uses 'Laps into Stint' (Relative X-axis) to align drivers.
    3. Filters out outliers (Slow laps) to show only valid race pace.
    """
    print(f"\n[Long Run Analysis] Extracting and Cleaning race pace data...")

    laps = session.laps.pick_accurate()
    drivers = session.drivers
    long_run_data = []

    for drv in drivers:
        try:
            driver_info = session.get_driver(drv)
            abb = driver_info['Abbreviation']
            
            # Get driver's laps
            drv_laps = laps.pick_drivers(drv)
            if drv_laps.empty: continue
            
            # Group by stint
            for stint, stint_data in drv_laps.groupby('Stint'):
                # 1. Length Check: Minimum 5 laps
                if len(stint_data) >= 5:
                    
                    # 2. Advanced Filtering (Clean-up Logic)
                    # Calculate median to find the "normal" pace for this stint
                    median_pace = stint_data['LapTime'].median()
                    
                    # Filter: Keep laps within 107% of median (Removes cool-down/mistake laps)
                    # This makes the graph tight and clean like the reference
                    threshold = median_pace * 1.07
                    clean_stint = stint_data[stint_data['LapTime'] < threshold]
                    
                    # Check length again after cleaning
                    if len(clean_stint) >= 5:
                        compound = clean_stint['Compound'].iloc[0]
                        color = get_driver_color_safe(abb, session)
                        
                        # 3. Relative Lap Count (1, 2, 3...) for X-axis alignment
                        clean_stint = clean_stint.reset_index(drop=True)
                        
                        for idx, lap in clean_stint.iterrows():
                            long_run_data.append({
                                'Driver': abb, 
                                'Stint': stint,
                                'StintLap': idx + 1,   # KEY FIX: 1st lap of stint, 2nd lap...
                                'LapTimeSeconds': lap['LapTime'].total_seconds(),
                                'Compound': compound,
                                'Color': color
                            })
        except:
            continue

    if not long_run_data:
        print("[Error] No valid long run data found.")
        return

    df = pd.DataFrame(long_run_data)
    
    # Save Directory
    save_dir = 'Saved_photos'
    if not os.path.exists(save_dir): os.makedirs(save_dir)
    base_filename = f"{session.event.year}_{session.event.EventName.replace(' ', '_')}_{session.name}"

    # Palette
    unique_drivers = df['Driver'].unique()
    palette_dict = {d: df[df['Driver'] == d]['Color'].iloc[0] for d in unique_drivers}
    plt.style.use('dark_background')

    # =================================================================
    # GRAPH 1: Race Pace Evolution (Trend Line)
    # =================================================================
    fig1, ax1 = plt.subplots(figsize=(14, 8))
    style_dark_plot(fig1, ax1)

    # Plot Lines using 'StintLap' (Relative X-axis)
    sns.lineplot(
        data=df, x='StintLap', y='LapTimeSeconds', hue='Driver', 
        palette=palette_dict, ax=ax1, linewidth=2.5, marker='o', markersize=6, legend=False
    )
    
    # Legend Logic (Drivers + Mean Pace)
    driver_means = df.groupby('Driver')['LapTimeSeconds'].mean().sort_values()
    legend_handles, legend_labels = [], []
    
    for drv_name in driver_means.index:
        mean_val = driver_means[drv_name]
        minutes, seconds = divmod(mean_val, 60)
        time_str = f"{int(minutes)}:{seconds:06.3f}"
        
        # Create legend item
        line = plt.Line2D([0], [0], color=palette_dict[drv_name], lw=2, marker='o')
        legend_handles.append(line)
        legend_labels.append(f"{drv_name}\nMean: {time_str}")

    # Add Legend to the Right
    ax1.legend(handles=legend_handles, labels=legend_labels, 
               bbox_to_anchor=(1.02, 1), loc='upper left', 
               facecolor='#1e1e1e', edgecolor='none', labelcolor='white', fontsize=10)

    ax1.set_title(f"{session.event.year} {session.event.EventName} - Long Run Pace Trend", fontsize=16, fontweight='bold', pad=15)
    ax1.set_ylabel("Lap Time (s)", fontsize=12)
    ax1.set_xlabel("Laps into Stint", fontsize=12) # Changed label

    # Save Graph 1
    save_path1 = os.path.join(save_dir, f"{base_filename}_Longrun_Trend.png")
    plt.savefig(save_path1, dpi=300, bbox_inches='tight', facecolor='#1e1e1e')
    print(f"[System] Trend graph saved to: {save_path1}")


    # =================================================================
    # GRAPH 2: Pace Consistency (Box Plot)
    # =================================================================
    fig2, ax2 = plt.subplots(figsize=(14, 8))
    style_dark_plot(fig2, ax2)

    # Prepare detailed X-axis labels (Driver + Compound + Lap Count)
    # e.g., "NOR (M) (8)"
    stats = df.groupby('Driver').agg({
        'LapTimeSeconds': 'median',
        'Compound': 'first', # Usually one compound per main stint
        'Driver': 'count'
    }).rename(columns={'Driver': 'Count'}).sort_values('LapTimeSeconds')
    
    # Map Driver Name to "Driver\n(Comp) (Count)" format
    label_map = {}
    for drv in stats.index:
        comp = stats.loc[drv, 'Compound'][0] if stats.loc[drv, 'Compound'] else '?' # Take first letter (S/M/H)
        count = stats.loc[drv, 'Count']
        label_map[drv] = f"{drv}\n({comp}) ({count})"
    
    # Add a formatted column for plotting
    df['Label'] = df['Driver'].map(label_map)
    order_labels = [label_map[d] for d in stats.index] # Order by median pace
    
    # Create Box Plot
    sns.boxplot(
        data=df, x='Label', y='LapTimeSeconds', hue='Driver', # Hue used for coloring
        palette=palette_dict, order=order_labels, 
        ax=ax2, showfliers=False, dodge=False, boxprops=dict(alpha=0.7)
    )
    # Add Dots
    sns.stripplot(
        data=df, x='Label', y='LapTimeSeconds', color='white', size=3, alpha=0.5, 
        order=order_labels, ax=ax2
    )
    
    # Remove legend from boxplot (colors are self-explanatory)
    if ax2.get_legend(): ax2.get_legend().remove()

    ax2.set_title("Long Run Consistency (Cleaned Data)", fontsize=16, fontweight='bold', pad=15)
    ax2.set_ylabel("Lap Time (s)", fontsize=12)
    ax2.set_xlabel("Driver (Compound) (Laps)", fontsize=12)

    # Save Graph 2
    save_path2 = os.path.join(save_dir, f"{base_filename}_Longrun_Consistency.png")
    plt.savefig(save_path2, dpi=300, bbox_inches='tight', facecolor='#1e1e1e')
    print(f"[System] Consistency graph saved to: {save_path2}")

    # Show All
    print("[System] Displaying graphs...")
    plt.show()
    plt.style.use('default')