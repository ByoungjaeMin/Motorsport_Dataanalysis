# -*- coding: utf-8 -*-
import fastf1
import os
import pandas

from practice import practice_export 
from practice import practice_downforce
from practice import practice_laptime
from practice import practice_dominance
from practice import practice_longrun

# Create cache directory if it doesn't exist
if not os.path.exists('cache'):
    os.makedirs('cache')
fastf1.Cache.enable_cache('cache')

def load_session_data():
    """
    Prompts user for session details and loads the FastF1 session.
    """
    print("========================================")
    print("       F1 Grid Analysis Tool v4         ")
    print("========================================")
    
    try:
        year_input = input("Year (e.g. 2024): ")
        year = int(year_input)
    except ValueError:
        print("Invalid year format.")
        return None

    gp = input("Grand Prix (e.g. Brazil): ")
    session_type = input("Session (Q, R, FP1...): ").upper()
    
    print(f"\n[System] Loading data for {year} {gp} - {session_type}...")
    try:
        session = fastf1.get_session(year, gp, session_type)
        session.load()
        return session
    except Exception as e:
        print(f"[Error] Failed to download/load session: {e}")
        return None

def main():
    session = load_session_data()
    if session is None:
        return

    while True:
        print("\n---------------- MENU ----------------")
        print("1. Lap Delta")
        print("2. Track Domination")
        print("3. Export Data")
        print("4. Downforce Map")
        print("5. Long Runs")
        print("q. Quit")
        
        choice = input("Select >> ")

        if choice == '1':
            practice_laptime.analyze_all_drivers(session)
            
        elif choice == '2':
            practice_dominance.plot_track_dominance(session)
            
        elif choice == '3':
            # Updated: calls practice_export instead of practice
            team = input("Team Name: ")
            practice_export.export_telemetry_data(session, team)
            
        elif choice == '4':
            practice_downforce.analyze_grid_aero(session)
            
        elif choice == '5':
            practice_longrun.analyze_long_runs(session)
            
        elif choice.lower() == 'q':
            print("Exiting...")
            break
        else:
            print("Invalid input. Please try again.")

if __name__ == "__main__":
    main()