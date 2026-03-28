import fastf1
import fastf1.plotting
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# Setup FastF1 plotting
fastf1.plotting.setup_mpl()

# Try importing custom modules from the 'practice' package
# If running standalone or files missing, use basic fallbacks
try:
    from practice.f1_colors import get_driver_color
    from practice.save_utils import make_filename, save_figure
except ImportError:
    # Fallback if custom modules are not found
    def get_driver_color(session, abb): return fastf1.plotting.driver_color(abb)
    def make_filename(session, suffix): return f"{session.event.year}_{session.event.EventName}_{suffix}.png"
    def save_figure(fig, filename, facecolor, show): 
        fig.savefig(filename, facecolor=facecolor)
        if show: plt.show()

# ==========================================
# 1. Lap Delta Analysis (Gap to Leader)
# ==========================================
def plot_lap_gap(session):
    """
    Calculates and plots the gap to the leader for the fastest lap of each driver.
    """
    print(f"\n[1/3] Calculating Whole Grid Lap Delta...")

    drivers = session.drivers
    results = []

    for drv in drivers:
        try:
            driver_info = session.get_driver(drv)
            abb = driver_info['Abbreviation']
            
            # Get fastest lap
            lap = session.laps.pick_drivers(drv).pick_fastest()
            
            if pd.notna(lap['LapTime']):
                color = get_driver_color(session, abb)
                results.append({
                    'Driver': abb,
                    'LapTime': lap['LapTime'],
                    'Color': color
                })
        except Exception:
            continue
    
    if not results:
        print("[Error] No valid lap data found.")
        return

    # Create DataFrame and calculate gap
    df = pd.DataFrame(results)
    df = df.sort_values(by='LapTime').reset_index(drop=True)
    p1_time = df.loc[0, 'LapTime']
    df['Gap'] = (df['LapTime'] - p1_time).dt.total_seconds()
    
    fig, ax = plt.subplots(figsize=(12, 8))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')

    # Horizontal Bar Chart
    bars = ax.barh(df.index, df['Gap'], color=df['Color'], edgecolor='white', linewidth=0.5)

    # Axis formatting
    ax.invert_yaxis()
    ax.set_yticks(df.index)
    ax.set_yticklabels(df['Driver'], fontsize=12, fontweight='bold', color='black')
    ax.set_xlabel("Gap to Leader (seconds)", color='black', fontsize=11)

    session_name = f"{session.event.year} {session.event.EventName} {session.name}"
    ax.set_title(f"{session_name} - Lap Delta", fontsize=16, fontweight='bold', color='black', pad=20)

    # Styling
    ax.grid(axis='x', linestyle='--', alpha=0.3, color='gray')
    ax.grid(axis='y', visible=False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color('black')
    ax.spines['left'].set_color('black')
    ax.tick_params(colors='black')

    # Add text labels
    for i, bar in enumerate(bars):
        gap_val = df.loc[i, 'Gap']
        if i > 0:
            label = f"+{gap_val:.3f}s"
        else:
            t = df.loc[i, 'LapTime']
            minutes, remainder = divmod(t.seconds, 60)
            label = f"{minutes:02d}:{remainder:02d}.{t.microseconds // 1000:03d}"

        ax.text(bar.get_width() + 0.02, bar.get_y() + bar.get_height()/2,
                label, va='center', fontsize=10, color='black', fontweight='bold')

    filename = make_filename(session, suffix='LapDelta')
    save_figure(fig, filename, facecolor='white', show=False)

# ==========================================
# 2. Sector Ranking Analysis
# ==========================================
def plot_sector_ranking(session):
    """
    Plots the fastest sector times for each driver.
    """
    print(f"\n[2/3] Calculating Best Sector Times...")
    
    drivers = session.drivers
    s1_data, s2_data, s3_data = [], [], []

    # Collect sector times
    for drv in drivers:
        try:
            driver_info = session.get_driver(drv)
            abb = driver_info['Abbreviation']
            color = get_driver_color(session, abb)
            laps = session.laps.pick_drivers(drv)
            
            s1 = laps['Sector1Time'].min()
            s2 = laps['Sector2Time'].min()
            s3 = laps['Sector3Time'].min()
            
            if pd.notna(s1): s1_data.append({'Driver': abb, 'Time': s1, 'Color': color})
            if pd.notna(s2): s2_data.append({'Driver': abb, 'Time': s2, 'Color': color})
            if pd.notna(s3): s3_data.append({'Driver': abb, 'Time': s3, 'Color': color})
        except Exception:
            continue

    s1_df = pd.DataFrame(s1_data).sort_values('Time').reset_index(drop=True)
    s2_df = pd.DataFrame(s2_data).sort_values('Time').reset_index(drop=True)
    s3_df = pd.DataFrame(s3_data).sort_values('Time').reset_index(drop=True)

    # Plot Setup
    fig, axes = plt.subplots(1, 3, figsize=(18, 11))
    fig.patch.set_facecolor('white')

    sectors = [('Sector 1', s1_df), ('Sector 2', s2_df), ('Sector 3', s3_df)]
    fig.suptitle(f"FASTEST SECTOR TIMES IN {session.event.year} {session.event.EventName} {session.name}".upper(),
                 fontsize=20, fontweight='bold', color='black', y=0.90)

    for i, (title, df) in enumerate(sectors):
        ax = axes[i]
        ax.set_facecolor('white')
        ax.set_title(title, fontsize=18, color='black', pad=20, fontweight='bold')
        ax.axis('off')
        
        top_n = min(len(df), 20)
        
        # Calculate visualization scaling
        if top_n > 0:
            min_sector_time = df['Time'].min().total_seconds()
            time_floor = min_sector_time - 0.5 
            max_visual_width = df['Time'].max().total_seconds() - time_floor
        else:
            time_floor = 0
            max_visual_width = 1.0

        bar_start_x = 0.35 
        y_positions = range(top_n, 0, -1) 
        
        for idx in range(top_n):
            row = df.iloc[idx]
            y_pos = y_positions[idx]
            real_time = row['Time'].total_seconds()
            visual_width = real_time - time_floor
            
            # Driver Name
            ax.text(0.0, y_pos, f"{row['Driver']}", 
                    fontsize=13, fontweight='bold', color=row['Color'], ha='left', va='center')
            
            # Time Bar
            ax.barh(y_pos, width=visual_width, left=bar_start_x, 
                    color=row['Color'], edgecolor='none', height=0.6, alpha=0.9)
            
            # Time Text
            time_str = f"{real_time:.3f}s"
            text_x = bar_start_x + visual_width + 0.05
            ax.text(text_x, y_pos, time_str,
                    fontsize=13, fontweight='bold', color='black', ha='left', va='center')

        ax.set_xlim(0, bar_start_x + max_visual_width + 0.8) 
        ax.set_ylim(0, 22)

    plt.tight_layout()
    plt.subplots_adjust(top=0.75)
    
    filename = make_filename(session, suffix='SectorRanks')
    save_figure(fig, filename, facecolor='white', show=False)

# ==========================================
# 3. Telemetry Metrics (Top Speed & Throttle) - Separate & Zoomed
# ==========================================
def plot_telemetry_metrics(session):
    """
    [Analysis 3] Top Speed & Full Throttle % (Separated & Zoomed)
    """
    print(f"\n[3/3] Calculating Telemetry Metrics (Speed & Throttle)...")
    
    drivers = session.drivers
    results = []

    for drv in drivers:
        try:
            driver_info = session.get_driver(drv)
            abb = driver_info['Abbreviation']
            color = get_driver_color(session, abb)
            
            # Fastest Lap & Telemetry
            lap = session.laps.pick_drivers(drv).pick_fastest()
            telemetry = lap.get_car_data().add_distance()
            
            if not telemetry.empty:
                # 1. Top Speed
                max_speed = telemetry['Speed'].max()
                
                # 2. Full Throttle % (Threshold > 98%)
                full_throttle_count = telemetry[telemetry['Throttle'] > 98]['Throttle'].count()
                total_count = telemetry['Throttle'].count()
                throttle_pct = (full_throttle_count / total_count) * 100 if total_count > 0 else 0
                
                results.append({
                    'Driver': abb,
                    'TopSpeed': max_speed,
                    'ThrottlePct': throttle_pct,
                    'Color': color
                })
        except Exception:
            continue
            
    if not results:
        print("[Error] No telemetry data found.")
        return

    # Create DataFrame
    df = pd.DataFrame(results)
    
    # ---------------------------------------------------------
    # settings for each metric
    # ---------------------------------------------------------
    metrics_config = [
        {
            'title': 'Top Speed Analysis',
            'col': 'TopSpeed',
            'unit': 'km/h',
            'suffix': 'TopSpeed',
            'pad_min': 10,  # start from 10 km/h below min value
            'pad_max': 5
        },
        {
            'title': 'Full Throttle % Analysis',
            'col': 'ThrottlePct',
            'unit': '%',
            'suffix': 'Throttle',
            'pad_min': 5,   # start from 5% below min value
            'pad_max': 2
        }
    ]

    # 각각 별도의 이미지로 생성 및 저장
    for config in metrics_config:
        col_name = config['col']
        unit = config['unit']
        
        # 데이터 정렬 (내림차순)
        sub_df = df.sort_values(by=col_name, ascending=False).reset_index(drop=True)
        
        # --- Plotting Setup ---
        fig, ax = plt.subplots(figsize=(12, 8))
        fig.patch.set_facecolor('white')
        ax.set_facecolor('white')
        
        # --- Dynamic Y-Axis Limit (Zoom In) ---
        data_min = sub_df[col_name].min()
        data_max = sub_df[col_name].max()
        
        # set y-limits with padding
        ylim_bottom = max(0, data_min - config['pad_min']) 
        ylim_top = data_max + config['pad_max']
        
        # Barplot
        bars = ax.bar(sub_df['Driver'], sub_df[col_name], 
                      color=sub_df['Color'], 
                      width=0.6, 
                      edgecolor='white', 
                      linewidth=0.5)
        
        # set axis limits
        ax.set_ylim(ylim_bottom, ylim_top)
        
        # --- Styling ---
        session_title = f"{session.event.year} {session.event.EventName} - {session.name}"
        full_title = f"{session_title}\n{config['title']} ({unit})"

        ax.set_title(full_title, fontsize=18, fontweight='bold', color='black', pad=20)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_color('black')
        ax.tick_params(axis='x', colors='black', labelsize=12, labelrotation=0)
        ax.get_yaxis().set_visible(False)

        # --- Annotations (Values on Top) ---
        for bar in bars:
            height = bar.get_height()
            if unit == '%':
                label = f"{height:.1f}"
            else:
                label = f"{int(height)}"

            ax.text(bar.get_x() + bar.get_width()/2.,
                    height + (ylim_top - ylim_bottom) * 0.01,
                    label,
                    ha='center', va='bottom',
                    fontsize=13, fontweight='bold', color='black')

        # --- Save ---
        plt.tight_layout()
        filename = make_filename(session, suffix=config['suffix'])
        save_figure(fig, filename, facecolor='white', show=False)

# ==========================================
# Main Entry Point
# ==========================================
def analyze_all_drivers(session):
    """
    Main function called from main.py
    Executes all analysis plots in sequence.
    """
    plot_lap_gap(session)
    plot_sector_ranking(session)
    plot_telemetry_metrics(session)