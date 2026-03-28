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

from practice.f1_colors import get_driver_color, get_driver_style
from practice.save_utils import make_filename, save_figure
from practice import config

# Linestyle cycle for distinguishing multiple stints of the same driver
_LINESTYLES = ['-', '--', ':', '-.']


def style_plot(fig, ax):
    """Apply consistent light theme"""
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    ax.grid(True, linestyle='--', alpha=0.3, color='gray')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color('black')
    ax.spines['left'].set_color('black')
    ax.tick_params(colors='black')
    ax.xaxis.label.set_color('black')
    ax.yaxis.label.set_color('black')
    ax.title.set_color('black')


def analyze_long_runs(session):
    """
    [Feature 5] Long Run Analysis

    Changes vs. original:
    B-1  Session filter strengthened: pick_accurate() + pick_quicklaps(1.05)
    B-2  Compound extracted via mode() over dropna() — tolerates NaN/dirty data
    B-3  Dual-threshold outlier removal: 104 % AND median+3 s (AND condition)
         Constants live in practice/config.py
    B-4  Driver_Stint granularity: one line per stint, not per driver
         Legend format: "VER S1 (SOFT)  Mean: 1:32.456"
         Same-driver stints share colour; linestyle cycles solid/dash/dot/dashdot
    """
    print(f"\n[Long Run Analysis] Extracting and cleaning race pace data...")

    # B-1: strengthen session filter
    laps = session.laps.pick_accurate().pick_quicklaps(threshold=1.05)

    drivers = session.drivers
    long_run_data = []

    for drv in drivers:
        try:
            driver_info = session.get_driver(drv)
            abb = driver_info['Abbreviation']

            drv_laps = laps.pick_drivers(drv)
            if drv_laps.empty:
                continue

            for stint, stint_data in drv_laps.groupby('Stint'):

                # Pre-filter length check
                if len(stint_data) < config.LONG_RUN_MIN_STINT_LAPS:
                    continue

                # B-2: Compound — mode over dropna (robust against NaN / carry-over)
                _c = stint_data['Compound'].dropna().mode()
                compound = _c.iloc[0] if not _c.empty else '?'

                # B-3: Dual-threshold outlier removal (AND condition)
                median_pace      = stint_data['LapTime'].median()
                threshold_pct    = median_pace * config.LONG_RUN_OUTLIER_THRESHOLD
                threshold_abs    = median_pace + pd.Timedelta(
                                       seconds=config.LONG_RUN_OUTLIER_ABS_DELTA)
                clean_stint = stint_data[
                    (stint_data['LapTime'] < threshold_pct) &
                    (stint_data['LapTime'] < threshold_abs)
                ]

                # Post-filter length check
                if len(clean_stint) < config.LONG_RUN_MIN_STINT_LAPS:
                    continue

                color      = get_driver_color(session, abb)
                clean_stint = clean_stint.reset_index(drop=True)

                # B-4: StintKey for per-stint separation
                stint_key = f"{abb} S{int(stint)}"

                for idx, lap in clean_stint.iterrows():
                    long_run_data.append({
                        'Driver':         abb,
                        'Stint':          int(stint),
                        'StintKey':       stint_key,
                        'StintLap':       idx + 1,
                        'LapTimeSeconds': lap['LapTime'].total_seconds(),
                        'Compound':       compound,
                        'Color':          color,
                    })
        except Exception:
            continue

    if not long_run_data:
        print("[Error] No valid long run data found.")
        return

    df = pd.DataFrame(long_run_data)

    # B-4: Build per-StintKey lookup dicts
    unique_stintkeys     = df['StintKey'].unique()
    stintkey_color       = {sk: df[df['StintKey'] == sk]['Color'].iloc[0]    for sk in unique_stintkeys}
    stintkey_stint_num   = {sk: df[df['StintKey'] == sk]['Stint'].iloc[0]    for sk in unique_stintkeys}
    stintkey_ls          = {sk: _LINESTYLES[(stintkey_stint_num[sk] - 1) % len(_LINESTYLES)]
                               for sk in unique_stintkeys}
    stintkey_compound    = {sk: df[df['StintKey'] == sk]['Compound'].iloc[0] for sk in unique_stintkeys}

    # =====================================================================
    # GRAPH 1: Race Pace Evolution (Trend) — one line per StintKey   [B-4]
    # =====================================================================
    fig1, ax1 = plt.subplots(figsize=(14, 8))
    style_plot(fig1, ax1)

    for stint_key, group in df.groupby('StintKey'):
        g = group.sort_values('StintLap')
        ax1.plot(
            g['StintLap'], g['LapTimeSeconds'],
            color=stintkey_color[stint_key],
            linestyle=stintkey_ls[stint_key],
            linewidth=2.5, marker='o', markersize=6,
        )

    # Legend: StintKey + compound + per-stint mean
    stint_means = df.groupby('StintKey')['LapTimeSeconds'].mean().sort_values()
    legend_handles, legend_labels = [], []
    for sk in stint_means.index:
        mean_val          = stint_means[sk]
        minutes, seconds  = divmod(mean_val, 60)
        time_str          = f"{int(minutes)}:{seconds:06.3f}"
        comp              = stintkey_compound[sk]
        line = plt.Line2D([0], [0],
                          color=stintkey_color[sk],
                          linestyle=stintkey_ls[sk],
                          lw=2, marker='o')
        legend_handles.append(line)
        legend_labels.append(f"{sk} ({comp})\nMean: {time_str}")

    ax1.legend(handles=legend_handles, labels=legend_labels,
               bbox_to_anchor=(1.02, 1), loc='upper left',
               facecolor='white', edgecolor='lightgray',
               labelcolor='black', fontsize=10)

    ax1.set_title(
        f"{session.event.year} {session.event.EventName} — Long Run Pace Trend",
        fontsize=16, fontweight='bold', pad=15)
    ax1.set_ylabel("Lap Time (s)", fontsize=12)
    ax1.set_xlabel("Laps into Stint", fontsize=12)

    filename1 = make_filename(session, suffix='Longrun_Trend')
    save_figure(fig1, filename1, facecolor='white', show=False)

    # =====================================================================
    # GRAPH 2: Pace Consistency (Box Plot) — per StintKey              [B-4]
    # =====================================================================
    fig2, ax2 = plt.subplots(figsize=(14, 8))
    style_plot(fig2, ax2)

    stats = (
        df.groupby('StintKey')
          .agg(Median=('LapTimeSeconds', 'median'),
               Compound=('Compound', 'first'),
               Count=('LapTimeSeconds', 'count'))
          .sort_values('Median')
    )

    label_map = {}
    for sk in stats.index:
        comp  = stats.loc[sk, 'Compound'][0] if stats.loc[sk, 'Compound'] else '?'
        count = stats.loc[sk, 'Count']
        label_map[sk] = f"{sk}\n({comp}) ({count})"

    df['Label']  = df['StintKey'].map(label_map)
    order_labels = [label_map[sk] for sk in stats.index]

    sns.boxplot(
        data=df, x='Label', y='LapTimeSeconds', hue='StintKey',
        palette=stintkey_color, order=order_labels,
        ax=ax2, showfliers=False, dodge=False,
        boxprops=dict(alpha=0.7),
    )
    sns.stripplot(
        data=df, x='Label', y='LapTimeSeconds',
        color='gray', size=3, alpha=0.5,
        order=order_labels, ax=ax2,
    )

    if ax2.get_legend():
        ax2.get_legend().remove()

    ax2.set_title("Long Run Consistency (Cleaned Data)",
                  fontsize=16, fontweight='bold', pad=15)
    ax2.set_ylabel("Lap Time (s)", fontsize=12)
    ax2.set_xlabel("Stint (Compound) (Laps)", fontsize=12)

    filename2 = make_filename(session, suffix='Longrun_Consistency')
    save_figure(fig2, filename2, facecolor='white', show=False)

    print("[System] Long run analysis complete.")
