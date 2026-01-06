import fastf1
import os
import pandas
import seaborn
import shutil

# `keyboard` is optional on some platforms (may require privileges on macOS).
try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except Exception:
    KEYBOARD_AVAILABLE = False

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
    print("       F1 Grid Analysis Tool         ")
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

def clear_saved_photos():
    """
    Clears all files and subdirectories inside the Saved_photos folder.
    """
    # Saved_photos is located at repository root alongside data_analysis_tool
    saved_photos_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Saved_photos')

    if not os.path.exists(saved_photos_path):
        print(f"[Warning] Saved_photos directory not found at {saved_photos_path}")
        return

    try:
        items_deleted = 0
        for name in os.listdir(saved_photos_path):
            path = os.path.join(saved_photos_path, name)
            if os.path.isfile(path) or os.path.islink(path):
                os.remove(path)
                items_deleted += 1
            elif os.path.isdir(path):
                shutil.rmtree(path)
                items_deleted += 1

        print(f"[System] Deleted {items_deleted} item(s) from Saved_photos.")
    except Exception as e:
        print(f"[Error] Failed to clear Saved_photos: {e}")

def main():
    session = load_session_data()
    if session is None:
        return
    print("\n[Tip] Press 'c' in the menu to clear Saved_photos.")
    if KEYBOARD_AVAILABLE:
        try:
            keyboard.add_hotkey('c', clear_saved_photos)
            print("[System] Global hotkey 'c' registered (keyboard module).")
        except Exception as e:
            print(f"[Warning] Could not register global hotkey: {e}")

    while True:
        print("\n---------------- MENU ----------------")
        print("1. Lap Delta")
        print("2. Track Domination")
        print("3. Export Data")
        print("4. Downforce Map")
        print("5. Long Runs")
        print("c. Clear Saved_photos")
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
            
        elif choice == 'c':
            clear_saved_photos()
            
        elif choice == 'q':
            print("Exiting...")
            print("Cleaning up cache...")
            try:
                # disable fastf1 cache and delete cache folder
                fastf1.Cache.clear_cache('cache') 
                # or delete entire cache folder
                if os.path.exists('cache'):
                    shutil.rmtree('cache')
                    print("[System] Cache deleted successfully.")
            except Exception as e:
                print(f"[Warning] Could not delete cache: {e}")

            print("Exiting...")
            break
        else:
            print("Invalid input. Please try again.")

if __name__ == "__main__":
    main()