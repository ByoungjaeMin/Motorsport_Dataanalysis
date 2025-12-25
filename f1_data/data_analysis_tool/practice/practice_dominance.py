# -*- coding: utf-8 -*-
import fastf1
import fastf1.plotting
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os
# Setup
fastf1.plotting.setup_mpl()
pd.options.mode.chained_assignment = None 
CUSTOM_COLORS = {
    # Red Bull Racing (Deep Blue)
    'VER': '#0600EF', 
    'TSU': '#0600EF', 

    # Ferrari (Scuderia Red)
    'LEC': '#E8002D', 
    'HAM': '#E8002D', # Hamilton to Ferrari

    # McLaren (Papaya Orange)
    'NOR': '#FF8000', 
    'PIA': '#FF8000',

    # Mercedes (Petronas Cyan / Silver)
    'RUS': '#00D2BE', 
    'ANT': '#00D2BE', # Antonelli to Mercedes

    # Aston Martin (British Racing Green)
    'ALO': '#229971', 
    'STR': '#229971',

    # Alpine (Alpine Blue / Pink)
    'GAS': '#0093CC', 
    'DOO': '#0093CC', # Doohan to Alpine
    'COL': '#0093CC',

    # Williams (Williams Blue)
    'ALB': '#64C4FF', 
    'SAI': '#64C4FF', # Sainz to Williams

    # RB / VCARB (Blue & White)
    'LAW': '#6692FF', 
    'HAD': '#6692FF', # Hadjar (Candidate)

    # Sauber / Kick (Neon Green) - Becoming Audi later
    'HUL': '#52E252', # Hulkenberg to Sauber
    'BOR': '#52E252', # Bortoleto to Sauber

    # Haas (Red, White, Black)
    'OCO': '#B6BABD', # Ocon to Haas
    'BEA': '#B6BABD', # Bearman to Haas
}

def plot_track_dominance(session):
    """
    [Feature] Track Dominance Analysis (Auto Top 3 Teams)
    - Automatically selects the top 3 drivers from unique teams
    - Generates a track dominance map showing where each driver was fastest
    """
    print(f"\n[Dominance Analysis] Selecting Top 3 Unique Teams from the session...")

    # 1. Extract fastest laps for all drivers
    drivers = session.drivers
    valid_laps = []

    for drv in drivers:
        try:
            # FIXED: pick_driver -> pick_drivers
            lap = session.laps.pick_drivers(drv).pick_fastest()
            # Only add if valid (exclude NaT)
            if pd.notna(lap['LapTime']):
                valid_laps.append(lap)
        except Exception as e:
            # print(f"Skip {drv}: {e}") # Debugging
            continue

    # 2. Sort by lap time (fastest first)
    valid_laps.sort(key=lambda x: x['LapTime'])

    # 3. Select top 3 unique teams
    selected_laps = []
    selected_teams = set()
    
    print("\n--- [Selected Top 3 Drivers (Unique Teams)] ---")
    rank = 1
    for lap in valid_laps:
        team = lap['Team']
        driver = lap['Driver']
        lap_time = str(lap['LapTime']).split()[-1][:-3]
        
        # Skip if team already selected
        if team in selected_teams:
            pass
        else:
            # Select if new team
            selected_teams.add(team)
            selected_laps.append(lap)
            print(f" Rank {rank}: {driver} ({team}) - {lap_time}")
        
        rank += 1
        if len(selected_laps) == 3:
            break
    
    if len(selected_laps) < 3:
        print(f"[Error] Found only {len(selected_laps)} unique teams. Need at least 3.")
        return

    # 4. Merge telemetry data
    print("\n[Processing] Analyzing track mini-sectors...")
    
    telemetry_list = list()
    for lap in selected_laps:
        tel = lap.get_telemetry().add_distance()
        tel['Driver'] = lap['Driver']
        telemetry_list.append(tel)

    # Reference telemetry for plotting the map
    ref_tel = telemetry_list[0]
    total_distance = max(ref_tel['Distance'])
    
    # Divide into mini-sectors (approx. 25)
    num_minisectors = 25
    sector_len = total_distance / num_minisectors

    # Prepare plot
    fig, ax = plt.subplots(sharex=True, sharey=True, figsize=(12, 7))
    
    # Find fastest driver per mini-sector and color the track
    for i in range(num_minisectors):
        start_dist = i * sector_len
        end_dist = (i + 1) * sector_len
        
        sector_speeds = {}
        for tel in telemetry_list:
            mask = (tel['Distance'] >= start_dist) & (tel['Distance'] < end_dist)
            if mask.sum() > 0:
                avg_speed = tel.loc[mask, 'Speed'].mean()
                sector_speeds[tel['Driver'].iloc[0]] = avg_speed
        
        if not sector_speeds:
            continue

        # Winner of the sector
        fastest_driver = max(sector_speeds, key=sector_speeds.get)
        
        # Plot track segment
        segment = ref_tel[(ref_tel['Distance'] >= start_dist) & (ref_tel['Distance'] < end_dist)]
        if len(segment) < 2: continue
            
        # FIXED: driver_color -> get_driver_color
        color = fastf1.plotting.get_driver_color(fastest_driver, session=session)
        ax.plot(segment['X'], segment['Y'], color=color, linewidth=5, label=fastest_driver)

    # Handle legend
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), title="Sector Dominance", loc='best')
    
    drivers_str = ", ".join([l['Driver'] for l in selected_laps])
    ax.set_title(f"Track Dominance Map (Top 3 Unique Teams): {drivers_str}")
    ax.axis('off')
    
    # 5. Save to File
    save_dir = 'saved_photos'
    
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
        
    event_name = session.event.EventName.replace(" ", "_")
    filename = f"{session.event.year}_{event_name}_{session.name}_DominanceMap.png"
    save_path = os.path.join(save_dir, filename)
    
    plt.savefig(save_path, dpi=300)
    print(f"[System] Image saved to: {save_path}")

    plt.tight_layout()
    plt.show()