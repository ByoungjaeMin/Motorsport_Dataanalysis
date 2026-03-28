# practice/config.py
# Centralised constants for F1 analysis modules.
# All magic numbers that affect analysis logic live here.

# ---------------------------------------------------------------------------
# Long Run Analysis (practice_longrun.py)
# ---------------------------------------------------------------------------

# B-3: Outlier filter — percentage ceiling (104 % of median pace per stint)
# Replaces the 107 % rule-of-thumb that was borrowed from the F1 qualifying
# regulation and was too permissive for practice long-run filtering.
LONG_RUN_OUTLIER_THRESHOLD: float = 1.04

# B-3: Outlier filter — absolute ceiling (median + N seconds per stint)
# AND-combined with the percentage ceiling so that a single very slow lap
# cannot survive just because the median is already high.
LONG_RUN_OUTLIER_ABS_DELTA: float = 3.0

# Minimum valid laps per stint (applied before AND after outlier removal)
LONG_RUN_MIN_STINT_LAPS: int = 5
