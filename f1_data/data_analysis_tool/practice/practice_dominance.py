# -*- coding: utf-8 -*-
import fastf1
import fastf1.plotting
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import pandas as pd
import numpy as np
import os
import warnings

# --- Setup ---
plt.style.use(['dark_background'])
fastf1.plotting.setup_mpl(mpl_timedelta_support=True, color_scheme=None, misc_mpl_mods=True)
warnings.simplefilter(action='ignore', category=FutureWarning)
pd.options.mode.chained_assignment = None 

# Custom Colors (Team/Driver mappings)
from practice.f1_colors import get_driver_color, get_driver_style
from practice.save_utils import make_filename, save_figure

# =========================================================
# 1. Helper Functions
# =========================================================

def get_driver_color_custom(driver_code, session):
    """Proxy to centralized driver color helper."""
    try:
        return get_driver_color(session, driver_code)
    except Exception:
        return fastf1.plotting.get_driver_color(driver_code, session=session)

def analyze_lap_sections(lap, telemetry):
    """Calculates Full/Partial Throttle, Braking, and Coasting ratios."""
    if 'Time' not in telemetry.columns:
        telemetry = lap.get_telemetry()

    time_deltas = telemetry['Time'].diff().dt.total_seconds().fillna(0)
    total_time = lap.LapTime.total_seconds()

    full_throttle_time = time_deltas[telemetry['Throttle'] >= 99].sum()
    braking_time = time_deltas[telemetry['Brake'] > 0.05].sum()
    lift_time = time_deltas[(telemetry['Throttle'] < 5) & (telemetry['Brake'] < 0.05)].sum()

    partial_time = total_time - full_throttle_time - braking_time - lift_time

    return {
        'Full Throttle': (full_throttle_time / total_time) * 100,
        'Partial Throttle': (partial_time / total_time) * 100,
        'Braking': (braking_time / total_time) * 100,
        'Lift (Coasting)': (lift_time / total_time) * 100
    }

def analyze_drs_effect(lap, telemetry):
    """Calculates top speeds and delta for DRS On/Off."""
    if 'DRS' not in telemetry.columns:
        telemetry = lap.get_telemetry()
        if 'DRS' not in telemetry.columns:
            return {'DRS On Speed': 0, 'DRS Off Speed': 0, 'DRS Delta': 0}

    speed_drs_on = telemetry[telemetry['DRS'] >= 10]['Speed'].max()
    speed_drs_off = telemetry[telemetry['DRS'] < 10]['Speed'].max()

    # Handle NaNs or Infs
    if pd.isna(speed_drs_on) or pd.isna(speed_drs_off) or \
       speed_drs_on == -np.inf or speed_drs_off == -np.inf:
        max_speed = telemetry['Speed'].max()
        if pd.isna(speed_drs_on) or speed_drs_on == -np.inf: speed_drs_on = max_speed
        if pd.isna(speed_drs_off) or speed_drs_off == -np.inf: speed_drs_off = max_speed

    return {
        'DRS On Speed': speed_drs_on,
        'DRS Off Speed': speed_drs_off,
        'DRS Delta': speed_drs_on - speed_drs_off
    }

# =========================================================
# 2. Main Logic
# =========================================================

def plot_track_dominance(session):
    """
    [Feature] Track Dominance & Telemetry Dashboard (Top 3 Unique Teams)
    - Selects top 3 drivers from different teams.
    - Generates comprehensive dashboard + 3 secondary charts.
    """
    print(f"\n[Dominance Analysis] Selecting Top 3 Unique Teams from the session...")

    # --- 1. Filter Drivers ---
    drivers = session.drivers
    valid_laps = []

    for drv in drivers:
        try:
            lap = session.laps.pick_drivers(drv).pick_fastest()
            if pd.notna(lap['LapTime']):
                valid_laps.append(lap)
        except:
            continue

    # Sort by lap time
    valid_laps.sort(key=lambda x: x['LapTime'])

    # Select Top 3 Unique Teams
    selected_laps = []
    selected_teams = set()
    
    print("\n--- [Selected Top 3 Drivers (Unique Teams)] ---")
    rank = 1
    for lap in valid_laps:
        team = lap['Team']
        driver = lap['Driver']
        lap_time_str = str(lap['LapTime']).split()[-1][:-3]
        
        if team in selected_teams:
            pass
        else:
            selected_teams.add(team)
            selected_laps.append(lap)
            print(f" Rank {rank}: {driver} ({team}) - {lap_time_str}")
        
        if len(selected_laps) == 3:
            break
    
    if len(selected_laps) < 3:
        print(f"[Error] Found only {len(selected_laps)} unique teams. Need at least 3 to generate comparison.")
        return

    # --- 2. Variable Mapping ---
    bestlap_24 = selected_laps[0]  # Baseline (Fastest)
    bestlap_25 = selected_laps[1]  # Comparison 1
    bestlap_26 = selected_laps[2]  # Comparison 2

    # Assign Colors
    color_24 = get_driver_color_custom(bestlap_24['Driver'], session)
    color_25 = get_driver_color_custom(bestlap_25['Driver'], session)
    color_26 = get_driver_color_custom(bestlap_26['Driver'], session)

    # Event metadata
    event_name = session.event.EventName
    year = session.event.year
    # Ensure standardized save directory exists (handled by save_figure)

    # Standardized base filename prefix: Year_GrandPrix_session_practice_domination
    base_prefix = f"{year}_{event_name.replace(' ', '_')}_{session.name}_practice_domination"

    # =========================================================
    # 3. [Graph 1] Comprehensive Dashboard
    # =========================================================
    try:
        print("\n--- 1. Generating Comprehensive Dashboard... ---")

        # Load Telemetry
        tel_24 = bestlap_24.get_telemetry().add_distance()
        tel_25 = bestlap_25.get_telemetry().add_distance()
        tel_26 = bestlap_26.get_telemetry().add_distance()

        # Calculate Deltas
        # [FIXED] Changed 'ff1.utils' to 'fastf1.utils'
        delta_t_ver_nor, ref_tel_ver_nor, comp_tel_ver_nor = fastf1.utils.delta_time(bestlap_24, bestlap_25)
        delta_t_sai_nor, ref_tel_sai_nor, comp_tel_sai_nor = fastf1.utils.delta_time(bestlap_24, bestlap_26)

        # Interpolate Deltas
        orig_distance = tel_24['Distance']
        delta_ver_nor_interpolated = np.interp(orig_distance, ref_tel_ver_nor['Distance'], delta_t_ver_nor.fillna(0))
        delta_sai_nor_interpolated = np.interp(orig_distance, ref_tel_sai_nor['Distance'], delta_t_sai_nor.fillna(0))

        # Setup Layout
        fig = plt.figure(figsize=(15, 20))
        gs = fig.add_gridspec(6, 1, height_ratios=[1.5, 1, 1, 1, 1, 1])
        ax_map = fig.add_subplot(gs[0])
        ax_speed = fig.add_subplot(gs[1])
        ax_throttle = fig.add_subplot(gs[2], sharex=ax_speed)
        ax_brake = fig.add_subplot(gs[3], sharex=ax_speed)
        ax_gear = fig.add_subplot(gs[4], sharex=ax_speed) # Gear subplot
        ax_delta = fig.add_subplot(gs[5], sharex=ax_speed)

        # Draw Track Map (Dominance based on instantaneous delta)
        drivers_label = f"{bestlap_24.Driver} vs {bestlap_25.Driver} vs {bestlap_26.Driver}"
        ax_map.set_title(f"Track Dominance: {drivers_label}", fontsize=14)
        
        d_delta_ver_nor = np.diff(delta_ver_nor_interpolated)
        d_delta_sai_nor = np.diff(delta_sai_nor_interpolated)

        colors_map = []
        for i in range(len(d_delta_ver_nor)):
            # Determine who gained time in this segment
            pace_gains = [0, d_delta_ver_nor[i], d_delta_sai_nor[i]]
            min_pace_idx = np.argmin(pace_gains)
            
            if min_pace_idx == 0: colors_map.append(color_24)
            elif min_pace_idx == 1: colors_map.append(color_25)
            else: colors_map.append(color_26)

        x = tel_24['X'].values
        y = tel_24['Y'].values
        points = np.array([x, y]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)
        lc = LineCollection(segments, colors=colors_map, linewidth=2.5)
        ax_map.add_collection(lc)
        ax_map.axis('equal'); ax_map.set_xticks([]); ax_map.set_yticks([]); ax_map.axis('off')

        # Calculate Sector Positions
        track_end_dist = tel_24['Distance'].max()
        s1_dist, s2_dist = None, None
        try:
            s1_time = bestlap_24.Sector1Time.total_seconds()
            s2_time = bestlap_24.Sector2Time.total_seconds() + s1_time
            tel_time = tel_24['Time'].dt.total_seconds()
            tel_dist = tel_24['Distance']
            s1_dist = np.interp(s1_time, tel_time, tel_dist)
            s2_dist = np.interp(s2_time, tel_time, tel_dist)
            print(f"Sector Split: {s1_dist:.0f}m, {s2_dist:.0f}m")
        except:
            s1_dist, s2_dist = None, None

        # Plot Data
        fig.suptitle(f"Telemetry Comparison: {drivers_label} - {year} {event_name}", fontsize=16, y=1.02)

        # Speed
        ax_speed.plot(tel_24['Distance'], tel_24['Speed'], label=bestlap_24.Driver, color=color_24)
        ax_speed.plot(tel_25['Distance'], tel_25['Speed'], label=bestlap_25.Driver, color=color_25)
        ax_speed.plot(tel_26['Distance'], tel_26['Speed'], label=bestlap_26.Driver, color=color_26)
        ax_speed.set_ylabel('Speed (km/h)'); ax_speed.legend()
        plt.setp(ax_speed.get_xticklabels(), visible=False)

        # Throttle
        ax_throttle.plot(tel_24['Distance'], tel_24['Throttle'], label=bestlap_24.Driver, color=color_24)
        ax_throttle.plot(tel_25['Distance'], tel_25['Throttle'], label=bestlap_25.Driver, color=color_25)
        ax_throttle.plot(tel_26['Distance'], tel_26['Throttle'], label=bestlap_26.Driver, color=color_26)
        ax_throttle.set_ylabel('Throttle (%)')
        plt.setp(ax_throttle.get_xticklabels(), visible=False)

        # Brake
        ax_brake.plot(tel_24['Distance'], tel_24['Brake'].astype(int), label=bestlap_24.Driver, color=color_24)
        ax_brake.plot(tel_25['Distance'], tel_25['Brake'].astype(int), label=bestlap_25.Driver, color=color_25)
        ax_brake.plot(tel_26['Distance'], tel_26['Brake'].astype(int), label=bestlap_26.Driver, color=color_26)
        ax_brake.set_ylabel('Brake')
        plt.setp(ax_brake.get_xticklabels(), visible=False)

        # Gear
        ax_gear.plot(tel_24['Distance'], tel_24['nGear'], label=bestlap_24.Driver, color=color_24)
        ax_gear.plot(tel_25['Distance'], tel_25['nGear'], label=bestlap_25.Driver, color=color_25)
        ax_gear.plot(tel_26['Distance'], tel_26['nGear'], label=bestlap_26.Driver, color=color_26)
        ax_gear.set_ylabel('Gear')
        plt.setp(ax_gear.get_xticklabels(), visible=False)

        # Delta
        ax_delta.plot(tel_24['Distance'], np.zeros_like(tel_24['Distance']), label=f'{bestlap_24.Driver} (Base)', color=color_24)
        ax_delta.plot(tel_24['Distance'], delta_ver_nor_interpolated, label=f'{bestlap_25.Driver} vs Base', color=color_25)
        ax_delta.plot(tel_24['Distance'], delta_sai_nor_interpolated, label=f'{bestlap_26.Driver} vs Base', color=color_26)
        ax_delta.axhline(0, color='grey', linestyle='-')
        ax_delta.set_ylabel('Delta (s)')
        ax_delta.set_xlabel('Distance (m)')
        ax_delta.legend()

        # Grid and Ticks
        major_ticks = np.arange(0, track_end_dist, 500)
        minor_ticks = np.arange(0, track_end_dist, 250)

        for ax in [ax_speed, ax_throttle, ax_brake, ax_gear, ax_delta]:
            ax.set_xticks(major_ticks)
            ax.set_xticks(minor_ticks, minor=True)
            ax.grid(which='major', axis='x', linestyle=':', linewidth=0.5, color='#888888')
            ax.grid(which='minor', axis='x', linestyle=':', linewidth=0.5, color='#555555')
            if s1_dist and s2_dist:
                ax.axvline(s1_dist, color='grey', linestyle='--', linewidth=1.0)
                ax.axvline(s2_dist, color='grey', linestyle='--', linewidth=1.0)

        # Sector Background Colors (Based on Fastest Sector)
        if s1_dist and s2_dist:
            laps_list = [bestlap_24, bestlap_25, bestlap_26]
            colors_list = [color_24, color_25, color_26]

            def get_fastest_color(sector_attr):
                times = [getattr(lap, sector_attr) for lap in laps_list]
                # Handle None times
                valid_times = [t for t in times if t is not None]
                if not valid_times: return 'grey'
                min_t = min(valid_times)
                idx = times.index(min_t)
                return colors_list[idx]

            c_s1 = get_fastest_color('Sector1Time')
            c_s2 = get_fastest_color('Sector2Time')
            c_s3 = get_fastest_color('Sector3Time')

            ax_speed.axvspan(0, s1_dist, color=c_s1, alpha=0.2)
            ax_speed.axvspan(s1_dist, s2_dist, color=c_s2, alpha=0.2)
            ax_speed.axvspan(s2_dist, track_end_dist, color=c_s3, alpha=0.2)
            
            # Sector Labels
            y_pos = ax_speed.get_ylim()[1] * 0.95
            ax_speed.text(s1_dist/2, y_pos, 'S1', ha='center', color='white', fontweight='bold')
            ax_speed.text((s1_dist+s2_dist)/2, y_pos, 'S2', ha='center', color='white', fontweight='bold')
            ax_speed.text((s2_dist+track_end_dist)/2, y_pos, 'S3', ha='center', color='white', fontweight='bold')

        # Save Dashboard (centralized)
        filename_dash = f"{session.event.year}_{event_name.replace(' ','_')}_Dashboard.png"
        save_figure(fig, filename_dash, dpi=300, show=True, tight_rect=[0, 0, 1, 0.98])

    except Exception as e:
        print(f"[Error] Graph 1 Failed: {e}")

    # =========================================================
    # 4. Calculate Data for Secondary Charts
    # =========================================================
    try:
        # Top Speed
        max_speed_24 = tel_24['Speed'].max()
        max_speed_25 = tel_25['Speed'].max()
        max_speed_26 = tel_26['Speed'].max()

        # Driving Style
        sections_24 = analyze_lap_sections(bestlap_24, tel_24)
        sections_25 = analyze_lap_sections(bestlap_25, tel_25)
        sections_26 = analyze_lap_sections(bestlap_26, tel_26)
        df_sections = pd.DataFrame({
            bestlap_24.Driver: sections_24, 
            bestlap_25.Driver: sections_25, 
            bestlap_26.Driver: sections_26
        })

        # DRS Stats
        drs_24 = analyze_drs_effect(bestlap_24, tel_24)
        drs_25 = analyze_drs_effect(bestlap_25, tel_25)
        drs_26 = analyze_drs_effect(bestlap_26, tel_26)
        
        print("\n--- Secondary Charts Data Calculated ---")

    except Exception as e:
        print(f"[Error] Data Calculation Failed: {e}")
        return # Exit if data calculation fails

    # =========================================================
    # 5. [Graph 2] Top Speed Comparison
    # =========================================================
    try:
        drivers = [bestlap_24.Driver, bestlap_25.Driver, bestlap_26.Driver]
        speeds = [max_speed_24, max_speed_25, max_speed_26]
        colors = [color_24, color_25, color_26]

        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(drivers, speeds, color=colors)
        ax.set_title('Top Speed Comparison (Fastest Lap)', fontsize=16)
        ax.set_ylabel('Top Speed (km/h)')
        ax.set_ylim(min(speeds)*0.95, max(speeds)*1.05) 

        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2.0, height + 0.5, f'{height:.1f}', ha='center', va='bottom', fontsize=12)

        plt.grid(axis='y', linestyle='--', alpha=0.3)
        filename = make_filename(session, suffix='TopSpeed')
        save_figure(fig, filename, dpi=300, show=True)
    except Exception as e:
        print(f"[Error] Graph 2 Failed: {e}")

    # =========================================================
    # 6. [Graph 3] Driving Style Analysis
    # =========================================================
    try:
        categories = ['Full Throttle', 'Partial Throttle', 'Braking', 'Lift (Coasting)']
        data_24 = df_sections[bestlap_24.Driver]
        data_25 = df_sections[bestlap_25.Driver]
        data_26 = df_sections[bestlap_26.Driver]

        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        fig.suptitle('% of Lap Time Analysis', fontsize=18)

        drivers_list = [bestlap_24.Driver, bestlap_25.Driver, bestlap_26.Driver]
        colors_list = [color_24, color_25, color_26]

        for i, (ax, category) in enumerate(zip(axes.flat, categories)):
            values = [data_24[category], data_25[category], data_26[category]]
            bars = ax.bar(drivers_list, values, color=colors_list)

            ax.set_title(category, fontsize=14)
            ax.set_ylabel('% of Lap Time')

            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2.0, height, f'{height:.1f}%', ha='center', va='bottom', fontsize=10)

            # Auto-scale Y axis
            max_val = max(values) if values else 0
            if max_val > 0:
                ax.set_ylim(top=max_val * 1.25)
            else:
                ax.set_ylim(top=10)
            
            ax.grid(axis='y', linestyle='--', alpha=0.3)

        filename = make_filename(session, suffix='DrivingStyle')
        save_figure(fig, filename, dpi=300, show=True, tight_rect=[0, 0.03, 1, 0.95])
    except Exception as e:
        print(f"[Error] Graph 3 Failed: {e}")

    # =========================================================
    # 7. [Graph 4] DRS Effect Analysis
    # =========================================================
    try:
        categories = [bestlap_24.Driver, bestlap_25.Driver, bestlap_26.Driver]
        drs_off_speeds = [drs_24['DRS Off Speed'], drs_25['DRS Off Speed'], drs_26['DRS Off Speed']]
        drs_deltas = [drs_24['DRS Delta'], drs_25['DRS Delta'], drs_26['DRS Delta']]
        drs_on_speeds = [drs_24['DRS On Speed'], drs_25['DRS On Speed'], drs_26['DRS On Speed']]
        
        colors_bottom = [color_24, color_25, color_26] 
        colors_top = ['orange', 'cyan', 'lime'] # Distinct colors for delta

        fig, ax = plt.subplots(figsize=(10, 7))
        ax.bar(categories, drs_off_speeds, label='DRS Off', color=colors_bottom, alpha=0.7)
        ax.bar(categories, drs_deltas, bottom=drs_off_speeds, label='DRS Delta', color=colors_top)

        ax.set_title('DRS Effect Comparison (Top Speed)', fontsize=16)
        ax.set_ylabel('Speed (km/h)')
        
        # Scale Y axis
        min_y = min(drs_off_speeds) * 0.95
        max_y = max(drs_on_speeds) * 1.05
        ax.set_ylim(min_y, max_y)
        ax.legend()

        for i, cat in enumerate(categories):
            on_speed = drs_on_speeds[i]
            off_speed = drs_off_speeds[i]
            delta = drs_deltas[i]
            
            delta_pos = off_speed + (delta / 2) if delta > 0 else off_speed
            off_pos = off_speed / 2 if off_speed > 0 else 0

            ax.text(cat, on_speed + 1, f"{on_speed:.0f}", ha='center', va='bottom', fontsize=12, weight='bold')
            ax.text(cat, delta_pos, f"[+{delta:.0f}]", ha='center', va='center', fontsize=11, color='black') 
            ax.text(cat, off_pos, f"{off_speed:.0f}", ha='center', va='center', fontsize=11, color='white')

        plt.grid(axis='y', linestyle='--', alpha=0.3)
        filename = make_filename(session, suffix='DRS')
        save_figure(fig, filename, dpi=300, show=True)
    except Exception as e:
        print(f"[Error] Graph 4 Failed: {e}")