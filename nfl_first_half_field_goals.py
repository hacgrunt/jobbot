"""
NFL First-Half Field Goal Analysis using nflfastR data (via nfl_data_py).

Compares field goal attempts and makes in the first half of games
across recent NFL seasons, with a focus on the 2024 season.
"""

import nfl_data_py as nfl
import pandas as pd
import time

# Load play-by-play data for 2014-2024 (gives us a decade+ of context)
SEASONS = list(range(2014, 2025))
print(f"Loading play-by-play data for seasons {SEASONS[0]}-{SEASONS[-1]}...")

# Retry with exponential backoff if any seasons fail
frames = []
for season in SEASONS:
    for attempt in range(4):
        try:
            df = nfl.import_pbp_data([season], downcast=False)
            frames.append(df)
            break
        except Exception as e:
            wait = 2 ** (attempt + 1)
            print(f"  Retry {attempt+1} for {season} after error: {e}. Waiting {wait}s...")
            time.sleep(wait)
    else:
        print(f"  WARNING: Could not load {season} after 4 retries, skipping.")

pbp = pd.concat(frames, ignore_index=True)

# ── Filter to field goal plays in the first half ──
# nflfastR uses play_type == "field_goal" for FG attempts
# First half = quarter 1 or 2 (qtr <= 2)
fg = pbp[pbp["play_type"] == "field_goal"].copy()
fg_first_half = fg[fg["qtr"] <= 2].copy()
fg_second_half = fg[fg["qtr"] > 2].copy()

# field_goal_result: "made" or "missed" (includes blocked)
fg_first_half["made"] = (fg_first_half["field_goal_result"] == "made").astype(int)
fg_second_half["made"] = (fg_second_half["field_goal_result"] == "made").astype(int)

# ── Per-season summary: first half ──
first_half_summary = (
    fg_first_half.groupby("season")
    .agg(
        attempts=("play_id", "count"),
        makes=("made", "sum"),
        avg_distance=("kick_distance", "mean"),
    )
    .reset_index()
)
first_half_summary["pct"] = (
    first_half_summary["makes"] / first_half_summary["attempts"] * 100
)

# ── Per-season summary: second half + OT ──
second_half_summary = (
    fg_second_half.groupby("season")
    .agg(
        attempts=("play_id", "count"),
        makes=("made", "sum"),
        avg_distance=("kick_distance", "mean"),
    )
    .reset_index()
)
second_half_summary["pct"] = (
    second_half_summary["makes"] / second_half_summary["attempts"] * 100
)

# ── Total FGs per season (for share calculation) ──
total_summary = (
    fg.groupby("season")
    .agg(total_attempts=("play_id", "count"))
    .reset_index()
)

combined = first_half_summary.merge(total_summary, on="season")
combined["first_half_share"] = (
    combined["attempts"] / combined["total_attempts"] * 100
)

# ── Per-game averages ──
games_per_season = (
    pbp[pbp["play_type"].notna()]
    .groupby("season")["game_id"]
    .nunique()
    .reset_index()
    .rename(columns={"game_id": "games"})
)
combined = combined.merge(games_per_season, on="season")
combined["fg_per_game_1h"] = combined["attempts"] / combined["games"]

# ── Print results ──
print("\n" + "=" * 85)
print("NFL FIRST-HALF FIELD GOAL ATTEMPTS BY SEASON (nflfastR data)")
print("=" * 85)
print(
    f"{'Season':<8} {'1H Att':>7} {'1H Made':>8} {'1H Pct':>7} "
    f"{'Avg Dist':>9} {'Total Att':>10} {'1H Share':>9} {'1H FG/Gm':>9}"
)
print("-" * 85)

for _, row in combined.iterrows():
    print(
        f"{int(row['season']):<8} {int(row['attempts']):>7} {int(row['makes']):>8} "
        f"{row['pct']:>6.1f}% {row['avg_distance']:>8.1f} "
        f"{int(row['total_attempts']):>10} {row['first_half_share']:>8.1f}% "
        f"{row['fg_per_game_1h']:>9.2f}"
    )

# Highlight 2024 vs historical average (2014-2023)
hist = combined[combined["season"] < 2024]
curr = combined[combined["season"] == 2024].iloc[0]
print("-" * 85)
print(
    f"{'2014-23':<8} {hist['attempts'].mean():>7.0f} {hist['makes'].mean():>8.0f} "
    f"{(hist['makes'].sum() / hist['attempts'].sum() * 100):>6.1f}% "
    f"{hist['avg_distance'].mean():>8.1f} "
    f"{hist['total_attempts'].mean():>10.0f} "
    f"{(hist['attempts'].sum() / hist['total_attempts'].sum() * 100):>8.1f}% "
    f"{hist['fg_per_game_1h'].mean():>9.2f}"
)
print(f"{'Avg':<8}")

print("\n" + "=" * 85)
print("2024 SEASON vs HISTORICAL AVERAGE (2014-2023)")
print("=" * 85)

delta_att = curr["attempts"] - hist["attempts"].mean()
delta_pct = curr["pct"] - (hist["makes"].sum() / hist["attempts"].sum() * 100)
delta_per_game = curr["fg_per_game_1h"] - hist["fg_per_game_1h"].mean()
delta_share = curr["first_half_share"] - (
    hist["attempts"].sum() / hist["total_attempts"].sum() * 100
)

print(f"  1H attempts:       {int(curr['attempts']):>5}  (avg {hist['attempts'].mean():.0f},  delta {delta_att:+.0f})")
print(f"  1H makes:          {int(curr['makes']):>5}  (avg {hist['makes'].mean():.0f})")
print(f"  1H make pct:       {curr['pct']:.1f}%  (avg {(hist['makes'].sum()/hist['attempts'].sum()*100):.1f}%,  delta {delta_pct:+.1f}pp)")
print(f"  1H avg distance:   {curr['avg_distance']:.1f} yds  (avg {hist['avg_distance'].mean():.1f} yds)")
print(f"  1H FG/game:        {curr['fg_per_game_1h']:.2f}  (avg {hist['fg_per_game_1h'].mean():.2f},  delta {delta_per_game:+.2f})")
print(f"  1H share of FGs:   {curr['first_half_share']:.1f}%  (avg {(hist['attempts'].sum()/hist['total_attempts'].sum()*100):.1f}%,  delta {delta_share:+.1f}pp)")

# ── Second half comparison ──
print("\n" + "=" * 85)
print("FIRST HALF vs SECOND HALF+OT FIELD GOALS BY SEASON")
print("=" * 85)
print(f"{'Season':<8} {'1H Att':>7} {'1H Made':>8} {'1H Pct':>7}  |  {'2H Att':>7} {'2H Made':>8} {'2H Pct':>7}")
print("-" * 85)

second_half_map = second_half_summary.set_index("season")
for _, row in first_half_summary.iterrows():
    s = int(row["season"])
    s2 = second_half_map.loc[s]
    print(
        f"{s:<8} {int(row['attempts']):>7} {int(row['makes']):>8} {row['pct']:>6.1f}%"
        f"  |  {int(s2['attempts']):>7} {int(s2['makes']):>8} {s2['pct']:>6.1f}%"
    )

# ── Year-over-year trend ──
print("\n" + "=" * 85)
print("YEAR-OVER-YEAR CHANGE IN 1H FG ATTEMPTS")
print("=" * 85)
combined_sorted = combined.sort_values("season")
prev_att = None
for _, row in combined_sorted.iterrows():
    s = int(row["season"])
    att = int(row["attempts"])
    if prev_att is not None:
        diff = att - prev_att
        print(f"  {s}: {att:>4} ({diff:+4} vs prior year)")
    else:
        print(f"  {s}: {att:>4}")
    prev_att = att

print("\n" + "=" * 85)
print("NOTE: Data sourced from nflfastR via nfl_data_py. 2024 = regular season only.")
print("=" * 85)
