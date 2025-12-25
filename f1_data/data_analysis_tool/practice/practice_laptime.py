# -*- coding: utf-8 -*-
import fastf1
import fastf1.plotting
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import os

# Setup FastF1 plotting
fastf1.plotting.setup_mpl()

# [2025 Season Custom Colors]
CUSTOM_COLORS = {
    # Red Bull Racing (Deep Blue)
    'VER': '#0600EF', 'TSU': '#0600EF', 

    # Ferrari (Scuderia Red)
    'LEC': '#E8002D', 'HAM': '#E8002D',

    # McLaren (Papaya Orange)
    'NOR': '#FF8000', 'PIA': '#FF8000',

    # Mercedes (Petronas Cyan / Silver)
    'RUS': '#00D2BE', 'ANT': '#00D2BE',

    # Aston Martin (British Racing Green)
    'ALO': '#229971', 'STR': '#229971',

    # Alpine (Alpine Blue / Pink)
    'GAS': '#0093CC', 'DOO': '#0093CC', 'COL': '#0093CC',

    # Williams (Williams Blue)
    'ALB': '#64C4FF', 'SAI': '#64C4FF',

    # RB / VCARB (Blue & White)
    'LAW': '#6692FF', 'HAD': '#6692FF',

    # Sauber / Kick (Neon Green)
    'HUL': '#52E252', 'BOR': '#52E252',

    # Haas (Red, White, Black)
    'OCO': '#B6BABD', 'BEA': '#B6BABD',
}

def get_driver_color_safe(abb, session):
    """Helper to get driver color safely"""
    if abb in CUSTOM_COLORS:
        return CUSTOM_COLORS[abb]
    try:
        return fastf1.plotting.get_driver_color(abb, session=session)
    except:
        return 'gray'

def plot_lap_gap_dark(session):
    """
    [Analysis 1] Lap Delta (Dark Mode)
    """
    print(f"\n[1/2] Calculating Whole Grid Lap Delta...")

    drivers = session.drivers
    results = []

    for drv in drivers:
        try:
            driver_info = session.get_driver(drv)
            abb = driver_info['Abbreviation']
            lap = session.laps.pick_drivers(drv).pick_fastest()
            
            if pd.notna(lap['LapTime']):
                color = get_driver_color_safe(abb, session)
                results.append({
                    'Driver': abb,
                    'LapTime': lap['LapTime'],
                    'Color': color
                })
        except:
            continue
    
    if not results:
        print("[Error] No valid lap data found.")
        return

    # Data Processing
    df = pd.DataFrame(results)
    df = df.sort_values(by='LapTime').reset_index(drop=True)
    p1_time = df.loc[0, 'LapTime']
    df['Gap'] = (df['LapTime'] - p1_time).dt.total_seconds()
    
    # --- Plotting (Dark Theme) ---
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(12, 8))
    fig.patch.set_facecolor('#1e1e1e')
    ax.set_facecolor('#1e1e1e')

    bars = ax.barh(df.index, df['Gap'], color=df['Color'], edgecolor='white', linewidth=0.5)
    
    ax.invert_yaxis()
    ax.set_yticks(df.index)
    ax.set_yticklabels(df['Driver'], fontsize=12, fontweight='bold', color='white')
    ax.set_xlabel("Gap to Leader (seconds)", color='white', fontsize=11)
    
    session_name = f"{session.event.year} {session.event.EventName} {session.name}"
    ax.set_title(f"{session_name} - Lap Delta", fontsize=16, fontweight='bold', color='white', pad=20)
    
    ax.grid(axis='x', linestyle='--', alpha=0.3, color='white')
    ax.grid(axis='y', visible=False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color('white')
    ax.spines['left'].set_color('white')
    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')

    for i, bar in enumerate(bars):
        gap_val = df.loc[i, 'Gap']
        if i > 0:
            label = f"+{gap_val:.3f}s"
        else:
            t = df.loc[i, 'LapTime']
            minutes, remainder = divmod(t.seconds, 60)
            label = f"{minutes:02d}:{remainder:02d}.{t.microseconds // 1000:03d}"
        ax.text(bar.get_width() + 0.02, bar.get_y() + bar.get_height()/2, 
                label, va='center', fontsize=10, color='white', fontweight='bold')

    save_dir = 'Saved_photos'
    if not os.path.exists(save_dir): os.makedirs(save_dir)
    filename = f"{session.event.year}_{session.event.EventName.replace(' ', '_')}_{session.name}_LapDelta_Dark.png"
    save_path = os.path.join(save_dir, filename)
    plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor())
    print(f"[System] Lap Delta saved to: {save_path}")
    plt.style.use('default') 

def plot_sector_ranking(session):
    """
    [Analysis 2] Fastest Sector Times Ranking (Top 20)
    * Visual Update: "Zoomed-in" Bars
    * Logic: Subtract (Min_Time - 0.5s) from all times so bars represent ONLY the differences.
    """
    print(f"\n[2/2] Calculating Best Sector Times...")
    
    drivers = session.drivers
    s1_data, s2_data, s3_data = [], [], []

    for drv in drivers:
        try:
            driver_info = session.get_driver(drv)
            abb = driver_info['Abbreviation']
            color = get_driver_color_safe(abb, session)
            laps = session.laps.pick_drivers(drv)
            
            s1 = laps['Sector1Time'].min()
            s2 = laps['Sector2Time'].min()
            s3 = laps['Sector3Time'].min()
            
            if pd.notna(s1): s1_data.append({'Driver': abb, 'Time': s1, 'Color': color})
            if pd.notna(s2): s2_data.append({'Driver': abb, 'Time': s2, 'Color': color})
            if pd.notna(s3): s3_data.append({'Driver': abb, 'Time': s3, 'Color': color})
        except:
            continue

    s1_df = pd.DataFrame(s1_data).sort_values('Time').reset_index(drop=True)
    s2_df = pd.DataFrame(s2_data).sort_values('Time').reset_index(drop=True)
    s3_df = pd.DataFrame(s3_data).sort_values('Time').reset_index(drop=True)

    # --- Plotting ---
    plt.style.use('dark_background')
    fig, axes = plt.subplots(1, 3, figsize=(18, 11))
    fig.patch.set_facecolor('black')
    
    sectors = [('Sector 1', s1_df), ('Sector 2', s2_df), ('Sector 3', s3_df)]
    fig.suptitle(f"FASTEST SECTOR TIMES IN {session.event.year} {session.event.EventName} {session.name}".upper(), 
                 fontsize=20, fontweight='bold', color='white', y=0.96)

    for i, (title, df) in enumerate(sectors):
        ax = axes[i]
        ax.set_facecolor('black')
        ax.set_title(title, fontsize=18, color='white', pad=20, fontweight='bold')
        ax.axis('off')
        
        top_n = min(len(df), 20)
        
        # [Visual Logic] Calculate "Zoom" offset
        # We want the fastest bar to have a minimal length (e.g., 0.5s visual width)
        # So we subtract (min_time - 0.5) from everyone.
        if top_n > 0:
            min_sector_time = df['Time'].min().total_seconds()
            # This "floor" is what we subtract from the absolute time
            time_floor = min_sector_time - 0.5 
            
            # For layout spacing
            max_visual_width = df['Time'].max().total_seconds() - time_floor
        else:
            time_floor = 0
            max_visual_width = 1.0

        # Layout Settings
        name_x_pos = 0.0
        bar_start_x = 0.35  # Gap for driver name
        
        y_positions = range(top_n, 0, -1) 
        
        for idx in range(top_n):
            row = df.iloc[idx]
            y_pos = y_positions[idx]
            
            # Absolute time
            real_time = row['Time'].total_seconds()
            
            # Visual width (Zoomed in difference)
            # Example: Time 17.0, Floor 16.5 -> Width 0.5
            # Example: Time 17.5, Floor 16.5 -> Width 1.0 (2x visual length!)
            visual_width = real_time - time_floor
            
            # 1. Driver Name (Left Aligned)
            ax.text(name_x_pos, y_pos, f"{row['Driver']}", 
                    fontsize=13, fontweight='bold', color=row['Color'], ha='left', va='center')
            
            # 2. Color Bar (Scaled by Relative Difference)
            ax.barh(y_pos, width=visual_width, left=bar_start_x, 
                    color=row['Color'], edgecolor='none', height=0.6, alpha=0.9)
            
            # 3. Time Text (Right of the bar)
            time_str = f"{real_time:.3f}s"
            text_x = bar_start_x + visual_width + 0.05
            ax.text(text_x, y_pos, time_str, 
                    fontsize=13, fontweight='bold', color='white', ha='left', va='center')

        # Set X limits to fit everything
        # Limit = bar start + max visual width + text space
        ax.set_xlim(0, bar_start_x + max_visual_width + 0.8) 
        ax.set_ylim(0, 22)

    plt.tight_layout()
    plt.subplots_adjust(top=0.9)
    
    save_dir = 'Saved_photos'
    if not os.path.exists(save_dir): os.makedirs(save_dir)
    filename = f"{session.event.year}_{session.event.EventName.replace(' ', '_')}_{session.name}_SectorRanks.png"
    save_path = os.path.join(save_dir, filename)
    plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='black')
    print(f"[System] Sector Ranks saved to: {save_path}")
    plt.style.use('default')

def analyze_all_drivers(session):
    """
    Execute both Lap Delta analysis and Sector Ranking analysis.
    """
    plot_lap_gap_dark(session)
    plot_sector_ranking(session)
    print("[System] Displaying all graphs...")
    plt.show()