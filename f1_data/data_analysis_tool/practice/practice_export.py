# -*- coding: utf-8 -*-
import fastf1
import pandas as pd
import os

def export_telemetry_data(session, team_name):
    """
    [Feature 3] Export Team Telemetry Data to CSV
    - Extracts Speed, RPM, Gear, Throttle, Brake, DRS data
    - Saves as CSV file in the current directory
    """
    print(f"\n[Export] Extracting telemetry data for {team_name}...")
    
    try:
        # Get drivers from the specific team
        drivers = session.laps.pick_team(team_name)['Driver'].unique()
        
        if len(drivers) == 0:
            print(f"[Error] No drivers found for team: {team_name}")
            return

        for drv in drivers:
            try:
                # Get fastest lap and telemetry
                lap = session.laps.pick_drivers(drv).pick_fastest()
                tel = lap.get_car_data().add_distance()
                
                # Select columns
                save_df = tel[['Date', 'RPM', 'Speed', 'nGear', 'Throttle', 'Brake', 'DRS', 'Distance']]
                
                # Save to CSV
                filename = f"{team_name}_{drv}_telemetry.csv"
                save_df.to_csv(filename, index=False)
                print(f" -> Saved: {filename}")
                
            except Exception as e:
                print(f" -> Failed to export {drv}: {e}")
                
        print("[System] Data export complete.")

    except Exception as e:
        print(f"[Error] Export process failed: {e}")