# -*- coding: utf-8 -*-
import fastf1
import fastf1.plotting
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Setup
fastf1.plotting.setup_mpl()

from practice.f1_colors import get_driver_color, get_driver_style
from practice.save_utils import make_filename, save_figure


def analyze_grid_aero(session):
    """
    [Feature 4] Downforce Positioning — Mean Speed vs Top Speed

    Axes:
      X-axis: Mean Speed — average speed over fastest-lap telemetry
      Y-axis: Top Speed  — maximum speed in fastest-lap telemetry

    Quadrants:
      Top-Left     Low MeanSpeed  + High TopSpeed  → "High Downforce"
      Top-Right    High MeanSpeed + High TopSpeed  → "Balanced"
      Bottom-Right High MeanSpeed + Low TopSpeed   → "Low Downforce"
      Bottom-Left  Low MeanSpeed  + Low TopSpeed   → "Underperforming"

    Centre axes: median of MeanSpeed and median of TopSpeed across teams.
    Best-driver selection per team: highest TopSpeed.
    """
    print(f"\n[Aero Analysis] Calculating Team Downforce Positioning "
          f"(Mean Speed vs Top Speed)...")

    teams      = session.results['TeamName'].unique()
    team_stats = []

    for team in teams:
        drivers = session.laps.pick_team(team)['Driver'].unique()
        if len(drivers) == 0:
            continue

        drivers_in_team = []

        for drv in drivers:
            try:
                lap = session.laps.pick_drivers(drv).pick_fastest()
                tel = lap.get_car_data().add_distance()

                # X-axis: Mean Speed — average over full lap telemetry
                mean_speed = tel['Speed'].mean()

                # Y-axis: Top Speed — maximum speed in lap telemetry
                top_speed = tel['Speed'].max()

                if not np.isnan(mean_speed) and not np.isnan(top_speed):
                    drivers_in_team.append({
                        'Driver':    drv,
                        'MeanSpeed': mean_speed,
                        'TopSpeed':  top_speed,
                    })
            except Exception:
                continue

        # Select best driver per team by highest TopSpeed
        if len(drivers_in_team) > 0:
            best_drv = sorted(
                drivers_in_team, key=lambda x: x['TopSpeed'], reverse=True)[0]
            color = get_driver_color(session, best_drv['Driver'])

            team_stats.append({
                'Team':      team,
                'Driver':    best_drv['Driver'],
                'MeanSpeed': best_drv['MeanSpeed'],
                'TopSpeed':  best_drv['TopSpeed'],
                'Color':     color,
            })
            print(f" -> {team} ({best_drv['Driver']}): "
                  f"MeanSpeed {best_drv['MeanSpeed']:.1f}  "
                  f"TopSpeed {best_drv['TopSpeed']:.1f}")

    df = pd.DataFrame(team_stats)

    # --- Visualization ---
    fig, ax = plt.subplots(figsize=(16, 10))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')

    # Centre point = median of each axis
    median_mean  = df['MeanSpeed'].median()
    median_top   = df['TopSpeed'].median()

    # Axis limits with padding
    x_span = df['MeanSpeed'].max() - df['MeanSpeed'].min()
    y_span = df['TopSpeed'].max()  - df['TopSpeed'].min()
    x_pad  = x_span * 0.4
    y_pad  = y_span * 0.4

    x_min = df['MeanSpeed'].min() - x_pad
    x_max = df['MeanSpeed'].max() + x_pad
    y_min = df['TopSpeed'].min()  - y_pad
    y_max = df['TopSpeed'].max()  + y_pad

    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)

    # --- Diagonal arrows & quadrant labels ---
    arrow_props = dict(color='lightgray', alpha=0.5, lw=1.5, head_width=0, zorder=1)

    # Top-right: Balanced
    ax.arrow(median_mean, median_top,
             (x_max - median_mean) * 0.9, (y_max - median_top) * 0.9,
             **arrow_props)
    ax.text(x_max * 0.995, y_max * 0.995, "Balanced",
            color='black', ha='right', va='top',
            fontsize=12, fontweight='bold')

    # Top-left: High Downforce
    ax.arrow(median_mean, median_top,
             (x_min - median_mean) * 0.9, (y_max - median_top) * 0.9,
             **arrow_props)
    ax.text(x_min * 1.005, y_max * 0.995, "High\nDownforce",
            color='black', ha='left', va='top',
            fontsize=12, fontweight='bold')

    # Bottom-right: Low Downforce
    ax.arrow(median_mean, median_top,
             (x_max - median_mean) * 0.9, (y_min - median_top) * 0.9,
             **arrow_props)
    ax.text(x_max * 0.995, y_min * 1.005, "Low\nDownforce",
            color='black', ha='right', va='bottom',
            fontsize=12, fontweight='bold')

    # Bottom-left: Underperforming
    ax.arrow(median_mean, median_top,
             (x_min - median_mean) * 0.9, (y_min - median_top) * 0.9,
             **arrow_props)
    ax.text(x_min * 1.005, y_min * 1.005, "Under-\nperforming",
            color='black', ha='left', va='bottom',
            fontsize=12, fontweight='bold')

    # --- Axis-direction labels ---
    ax.arrow(median_mean, median_top,
             0, (y_max - median_top) * 0.95,
             color='gray', alpha=0.3, lw=3, head_width=0.05)
    ax.text(median_mean, y_max * 0.995, "High Top Speed ↑",
            color='gray', ha='center', va='top', fontsize=10)

    ax.arrow(median_mean, median_top,
             0, (y_min - median_top) * 0.95,
             color='gray', alpha=0.3, lw=3, head_width=0.05)
    ax.text(median_mean, y_min * 1.005, "Low Top Speed ↓",
            color='gray', ha='center', va='bottom', fontsize=10)

    ax.arrow(median_mean, median_top,
             (x_max - median_mean) * 0.95, 0,
             color='gray', alpha=0.3, lw=3, head_width=0.2)
    ax.text(x_max * 0.995, median_top, "High Mean Speed →",
            color='gray', ha='right', va='center', fontsize=10)

    ax.arrow(median_mean, median_top,
             (x_min - median_mean) * 0.95, 0,
             color='gray', alpha=0.3, lw=3, head_width=0.2)
    ax.text(x_min * 1.005, median_top, "← Low Mean Speed",
            color='gray', ha='left', va='center', fontsize=10)

    # --- Scatter points ---
    ax.scatter(df['MeanSpeed'], df['TopSpeed'],
               c=df['Color'], s=120,
               edgecolors='black', linewidth=0.8,
               alpha=1.0, zorder=10)

    # --- Team labels ---
    for _, row in df.iterrows():
        ax.text(row['MeanSpeed'], row['TopSpeed'] + 0.4,
                row['Team'],
                ha='center', va='bottom',
                fontsize=10, fontweight='bold',
                color=row['Color'], zorder=11)

    # Grid
    ax.grid(True, linestyle=':', alpha=0.2)

    # A-4: Axis labels & title
    session_name = f"{session.event.year} {session.event.EventName} {session.name}"
    ax.set_title(
        f"{session_name} — Downforce Positioning — Mean Speed vs Top Speed",
        fontsize=18, fontweight='bold', color='black', pad=20)
    ax.set_xlabel("Mean Speed (km/h)", fontsize=12, color='black')
    ax.set_ylabel("Top Speed (km/h)", fontsize=12, color='black')

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color('black')
    ax.spines['left'].set_color('black')
    ax.tick_params(colors='black')

    # Save
    filename = make_filename(session, suffix='Downforce')
    save_figure(fig, filename, facecolor='white', show=False)
