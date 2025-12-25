# -*- coding: utf-8 -*-
import fastf1
import fastf1.plotting
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os

# Setup
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

def get_team_color_safe(team, drv, session):
    if drv in CUSTOM_COLORS: return CUSTOM_COLORS[drv]
    try: return fastf1.plotting.get_team_color(team, session=session)
    except: return 'gray'

def analyze_grid_aero(session):
    """
    [Feature 4] Downforce vs Drag Analysis (Best Driver per Team)
    - Instead of averaging both drivers, select the faster driver (Higher Avg Speed)
    - Represents the team's peak performance potential
    """
    print(f"\n[Aero Analysis] Calculating Team Peak Aero Data (Selecting faster driver)...")

    teams = session.results['TeamName'].unique()
    team_stats = []

    for team in teams:
        drivers = session.laps.pick_team(team)['Driver'].unique()
        if len(drivers) == 0: continue
        
        # Store stats for each driver in the team
        drivers_in_team = []
        
        for drv in drivers:
            try:
                lap = session.laps.pick_drivers(drv).pick_fastest()
                tel = lap.get_car_data().add_distance()
                
                t_speed = tel['Speed'].max()
                a_speed = tel['Speed'].mean() # Average Lap Speed
                
                if not np.isnan(t_speed) and not np.isnan(a_speed):
                    drivers_in_team.append({
                        'Driver': drv,
                        'TopSpeed': t_speed,
                        'AvgSpeed': a_speed
                    })
            except:
                continue
        
        # [Logic Change] Select the BEST driver for the team (Max Avg Speed)
        if len(drivers_in_team) > 0:
            # Sort by Avg Speed descending and pick the first one
            best_drv = sorted(drivers_in_team, key=lambda x: x['AvgSpeed'], reverse=True)[0]
            
            color = get_team_color_safe(team, best_drv['Driver'], session)
            
            team_stats.append({
                'Team': team,
                'Driver': best_drv['Driver'], # Keep track of who was faster
                'TopSpeed': best_drv['TopSpeed'],
                'AvgSpeed': best_drv['AvgSpeed'],
                'Color': color
            })
            print(f" -> {team} ({best_drv['Driver']}): Top {best_drv['TopSpeed']:.1f}, Avg {best_drv['AvgSpeed']:.1f}")

    df = pd.DataFrame(team_stats)
    
    # --- Visualization ---
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(16, 10))
    
    fig.patch.set_facecolor('#1e1e1e')
    ax.set_facecolor('#1e1e1e')
    
    # Center Point (Grid Mean)
    mean_top = df['TopSpeed'].mean()
    mean_avg = df['AvgSpeed'].mean()

    # Calculate Limits with Padding
    x_span = df['AvgSpeed'].max() - df['AvgSpeed'].min()
    y_span = df['TopSpeed'].max() - df['TopSpeed'].min()
    x_pad = x_span * 0.4
    y_pad = y_span * 0.4
    
    x_min, x_max = df['AvgSpeed'].min() - x_pad, df['AvgSpeed'].max() + x_pad
    y_min, y_max = df['TopSpeed'].min() - y_pad, df['TopSpeed'].max() + y_pad
    
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)

    # --- Draw Arrows ---
    arrow_props = dict(color='lightgray', alpha=0.5, lw=1.5, head_width=0, zorder=1)
    
    # 1. Diagonal Arrows
    ax.arrow(mean_avg, mean_top, (x_max-mean_avg)*0.9, (y_max-mean_top)*0.9, **arrow_props)
    ax.text(x_max*0.995, y_max*0.995, "High\nEfficiency", color='white', ha='right', va='top', fontsize=12, fontweight='bold')
    
    ax.arrow(mean_avg, mean_top, (x_min-mean_avg)*0.9, (y_max-mean_top)*0.9, **arrow_props)
    ax.text(x_min*1.005, y_max*0.995, "Low\nDownforce", color='white', ha='left', va='top', fontsize=12, fontweight='bold')
    
    ax.arrow(mean_avg, mean_top, (x_max-mean_avg)*0.9, (y_min-mean_top)*0.9, **arrow_props)
    ax.text(x_max*0.995, y_min*1.005, "High\nDownforce", color='white', ha='right', va='bottom', fontsize=12, fontweight='bold')
    
    ax.arrow(mean_avg, mean_top, (x_min-mean_avg)*0.9, (y_min-mean_top)*0.9, **arrow_props)
    ax.text(x_min*1.005, y_min*1.005, "Low\nEfficiency", color='white', ha='left', va='bottom', fontsize=12, fontweight='bold')

    # 2. Axis Arrows
    ax.arrow(mean_avg, mean_top, 0, (y_max-mean_top)*0.95, color='gray', alpha=0.3, lw=3, head_width=0.05)
    ax.text(mean_avg, y_max*0.995, "Low Drag", color='gray', ha='center', va='top', fontsize=10)
    
    ax.arrow(mean_avg, mean_top, 0, (y_min-mean_top)*0.95, color='gray', alpha=0.3, lw=3, head_width=0.05)
    ax.text(mean_avg, y_min*1.005, "High Drag", color='gray', ha='center', va='bottom', fontsize=10)
    
    ax.arrow(mean_avg, mean_top, (x_max-mean_avg)*0.95, 0, color='gray', alpha=0.3, lw=3, head_width=0.2)
    ax.text(x_max*0.995, mean_top, "High Speed", color='gray', ha='right', va='center', fontsize=10)
    
    ax.arrow(mean_avg, mean_top, (x_min-mean_avg)*0.95, 0, color='gray', alpha=0.3, lw=3, head_width=0.2)
    ax.text(x_min*1.005, mean_top, "Low Speed", color='gray', ha='left', va='center', fontsize=10)

    # 3. Draw Scatter Points
    # s=120 size for dots
    ax.scatter(df['AvgSpeed'], df['TopSpeed'], c=df['Color'], s=120, edgecolors='white', linewidth=0.8, alpha=1.0, zorder=10)
    
    # 4. Label Teams (Team Name + Driver Abbreviation if needed)
    for i, row in df.iterrows():
        # Label: "Red Bull"
        ax.text(row['AvgSpeed'], row['TopSpeed'] + 0.4, 
                row['Team'], ha='center', va='bottom', fontsize=10, fontweight='bold', color=row['Color'], zorder=11)

    # Grid styling
    ax.grid(True, linestyle=':', alpha=0.2)
    
    # Titles
    session_name = f"{session.event.year} {session.event.EventName} {session.name}"
    ax.set_title(f"{session_name} - Downforce Map (Best Driver per Team)", fontsize=20, fontweight='bold', color='white', pad=20)
    ax.set_xlabel("Average Speed (km/h)", fontsize=12, color='white')
    ax.set_ylabel("Top Speed (km/h)", fontsize=12, color='white')

    # Remove spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color('white')
    ax.spines['left'].set_color('white')
    ax.tick_params(colors='white')

    # Save
    save_dir = 'Saved_photos'
    if not os.path.exists(save_dir): os.makedirs(save_dir)
    filename = f"{session.event.year}_{session.event.EventName.replace(' ', '_')}_{session.name}_Downforce_Dark.png"
    save_path = os.path.join(save_dir, filename)
    
    plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='#1e1e1e')
    print(f"[System] Image saved to: {save_path}")
    plt.show()
    plt.style.use('default')