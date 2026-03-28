import fastf1
import os
import shutil
import difflib

from practice import practice_export
from practice import practice_downforce
from practice import practice_laptime
from practice import practice_dominance
from practice import practice_longrun

# Create cache directory if it doesn't exist
if not os.path.exists('cache'):
    os.makedirs('cache')
fastf1.Cache.enable_cache('cache')

# 2-1. FastF1 진행 상태 로그 활성화
fastf1.set_log_level('INFO')

# 1-2. 허용 세션 타입 상수
VALID_SESSION_TYPES = ['FP1', 'FP2', 'FP3', 'Q', 'SQ', 'R', 'S']

def _get_valid_year() -> int | None:
    """연도 입력 — 유효한 정수가 입력될 때까지 반복."""
    while True:
        year_input = input("Year (e.g. 2024): ").strip()
        try:
            return int(year_input)
        except ValueError:
            print("[Error] 숫자로 입력해 주세요 (예: 2024).")


def _get_valid_gp(year: int) -> str | None:
    """
    1-1. GP 이름 검증
    - get_event_schedule(year)로 유효 이벤트 목록 조회
    - difflib fuzzy 매칭(n=3, cutoff=0.6)으로 후보 제안
    - 유효 이름이 입력될 때까지 재입력 루프
    """
    print(f"\n[System] {year} 이벤트 일정을 불러오는 중...")
    try:
        schedule = fastf1.get_event_schedule(year, include_testing=False)
    except Exception as e:
        print(f"[Error] 이벤트 일정 조회 실패: {e}")
        return None

    event_names = schedule['EventName'].tolist()
    # 대소문자·공백 무시 비교용 정규화 맵  {normalized: original}
    name_map = {n.lower().strip(): n for n in event_names}

    print("\n[사용 가능한 Grand Prix 목록]")
    for idx, name in enumerate(event_names, 1):
        print(f"  {idx:2}. {name}")

    while True:
        gp_input = input("\nGrand Prix (e.g. Brazil): ").strip()
        normalized = gp_input.lower().strip()

        # 정확 매칭 (대소문자 무시)
        if normalized in name_map:
            return name_map[normalized]

        # Fuzzy 매칭
        close = difflib.get_close_matches(normalized, name_map.keys(), n=3, cutoff=0.6)
        if close:
            print(f"[Warning] '{gp_input}'을(를) 찾을 수 없습니다. 혹시 이 중 하나인가요?")
            for c in close:
                print(f"  → {name_map[c]}")
        else:
            print(f"[Warning] '{gp_input}'을(를) 찾을 수 없습니다. 위 목록에서 정확히 입력해 주세요.")


def _get_valid_session_type() -> str:
    """
    1-2. 세션 타입 검증
    - VALID_SESSION_TYPES 외 입력 시 목록 출력 후 재입력
    """
    while True:
        session_input = input(f"Session {VALID_SESSION_TYPES}: ").strip().upper()
        if session_input in VALID_SESSION_TYPES:
            return session_input
        print(f"[Error] '{session_input}'은(는) 유효하지 않습니다. 다음 중 하나를 입력하세요: {VALID_SESSION_TYPES}")


def load_session_data():
    """
    Prompts user for session details and loads the FastF1 session.
    """
    print("========================================")
    print("       F1 Grid Analysis Tool         ")
    print("========================================")

    year = _get_valid_year()
    if year is None:
        return None

    gp = _get_valid_gp(year)
    if gp is None:
        return None

    session_type = _get_valid_session_type()

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
            shutil.rmtree('cache', ignore_errors=True)
            print("[System] Cache deleted successfully.")

            print("Exiting...")
            break
        else:
            print("Invalid input. Please try again.")

if __name__ == "__main__":
    main()