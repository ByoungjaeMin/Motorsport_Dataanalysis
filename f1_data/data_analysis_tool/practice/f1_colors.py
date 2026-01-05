"""
f1_colors.py
F1 Team/Driver Color Mapping Module for FastF1 Analysis.
Handles historical livery changes and mid-season driver transfers automatically.
"""

import fastf1

# -----------------------------------------------------------------------------
# 1. Team Name & Color Mapping (2018 ~ 2025+)
# -----------------------------------------------------------------------------
# Key: Identification keyword included in team name (lowercase)
# Value: Representative Hex Color for the team
# *Note*: Search order matters; place specific names before general ones.

TEAM_COLORS_MAP = {
    # --- The Big 4 (Relatively Stable) ---
    'red bull': '#0600EF',   # Red Bull Racing
    'ferrari': '#E8002D',    # Scuderia Ferrari
    'mercedes': '#00D2BE',   # Mercedes-AMG
    'mclaren': '#FF8000',    # McLaren

    # --- Enstone Team (Renault -> Alpine) ---
    'alpine': '#0093CC',     # 2021~ (Blue)
    'renault': '#FFF500',    # ~2020 (Yellow)

    # --- Silverstone Team (Force India -> RP -> Aston Martin) ---
    'aston martin': '#229971', # 2021~ (British Racing Green)
    'racing point': '#F596C8', # 2019~2020 (Pink)
    'force india': '#F596C8',  # ~2018 (Pink)

    # --- Faenza Team (Toro Rosso -> AlphaTauri -> RB) ---
    'visa cash app': '#6692FF', # 2024~ (VCARB/RB) - Unique keyword to avoid matching errors
    'rb': '#6692FF',            # 2024~ (Short name fallback)
    'alphatauri': '#2B4562',    # 2020~2023 (Navy/White)
    'toro rosso': '#469BFF',    # ~2019 (Blue/Silver)

    # --- Hinwil Team (Sauber -> Alfa Romeo -> Stake/Kick) ---
    'stake': '#52E252',         # 2024~ (Neon Green)
    'kick': '#52E252',          # 2024~ (Neon Green)
    'alfa romeo': '#900000',    # 2019~2023 (Dark Red)
    'sauber': '#9B0000',        # 2018 (Red/White) - Used for 2018 mapping until Audi in 2026

    # --- Others ---
    'williams': '#64C4FF',      # Williams (Blue)
    'haas': '#B6BABD',          # Haas (Grey/White/Black)
}

DEFAULT_COLOR = '#808080'  # Grey color for failed matches


# -----------------------------------------------------------------------------
# 2. Helper Functions
# -----------------------------------------------------------------------------

def get_team_color(team_name: str) -> str:
    """
    Returns the color code based on the team name string.
    Uses substring matching.
    """
    if not team_name:
        return DEFAULT_COLOR
    
    name_lower = team_name.lower()
    
    # Check if keyword is in team name
    for keyword, color in TEAM_COLORS_MAP.items():
        if keyword in name_lower:
            return color
            
    return DEFAULT_COLOR


def get_driver_color(session, driver: str) -> str:
    """
    [Core Function]
    Returns the team color for a specific driver in a given session.
    
    Usage: 
    >>> color = get_driver_color(session, 'VER')
    """
    try:
        # Load driver info from FastF1 session
        drv_info = session.get_driver(driver)
        team_name = drv_info['TeamName']
        return get_team_color(team_name)
    except Exception as e:
        print(f"[Color Error] Could not find color for driver {driver}: {e}")
        return DEFAULT_COLOR

def get_driver_style(session, driver: str):
    """
    (Optional)
    Returns a style dictionary including color.
    Useful for unpacking into Matplotlib (**kwargs).
    """
    color = get_driver_color(session, driver)
    return {
        'color': color,
        'label': driver,
        'alpha': 0.8
    }