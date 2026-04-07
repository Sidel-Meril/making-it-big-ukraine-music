"""Monthly summed Spotify listeners (NUAM export) for story opener chart."""

from __future__ import annotations

from typing import Any

import pandas as pd

# Audience tier definitions (rank-based per month, descending by listeners)
TIERS: list[tuple[str, int, int]] = [
    ("top10",  1,   10),
    ("mid1",  11,   50),
    ("mid2",  51,  200),
    ("rest",  201, 999_999),
]


def _tier_sums(month_df: pd.DataFrame) -> dict[str, float]:
    """Return summed listeners per tier for a single month's artist rows.

    Artists are ranked by their listeners in that month (highest first).
    Tier boundaries are rank-based (1-10, 11-50, 51-200, 201+).
    """
    ranked = (
        month_df[month_df["listeners"] > 0]
        .sort_values("listeners", ascending=False)
        .reset_index(drop=True)
    )
    ranked["rank"] = ranked.index + 1
    result: dict[str, float] = {}
    for key, lo, hi in TIERS:
        mask = (ranked["rank"] >= lo) & (ranked["rank"] <= hi)
        result[key] = float(ranked.loc[mask, "listeners"].sum())
    return result


def build_uk_listeners_growth_payload(
    listeners_df: pd.DataFrame,
    *,
    start_year: int = 2024,
    current_year_split: int = 2026,
) -> dict[str, Any]:
    """Sum ``listeners`` by calendar month with per-tier breakdowns.

    Each point includes a ``tiers`` object with four keys (top10, mid1, mid2,
    rest) that sum to ``total``.  Tiers are ranked per-month by listener count.
    """
    if listeners_df.empty or "month" not in listeners_df.columns:
        return {
            "meta": {
                "startYear": start_year,
                "currentYearSplit": current_year_split,
                "note": "No listener rows",
            },
            "points": [],
        }

    df = listeners_df.copy()
    df["month"] = pd.to_datetime(df["month"])
    df = df[df["listeners"].notna()]
    start = pd.Timestamp(year=start_year, month=1, day=1)
    df = df.loc[df["month"] >= start]
    if df.empty:
        return {
            "meta": {
                "startYear": start_year,
                "currentYearSplit": current_year_split,
                "note": "No rows after start filter",
            },
            "points": [],
        }

    monthly = (
        df.groupby(pd.Grouper(key="month", freq="MS"), sort=True)["listeners"]
        .agg(**{"total": "sum", "std": "std", "artistCount": "count"})
        .reset_index()
    )
    monthly["std"] = monthly["std"].fillna(0.0)
    monthly = monthly.loc[monthly["total"] > 0].reset_index(drop=True)

    points: list[dict[str, Any]] = []
    prev: float | None = None
    for _, r in monthly.iterrows():
        m = r["month"]
        total = float(r["total"])
        delta = None if prev is None else total - prev
        artist_count = int(r["artistCount"])
        ci_band = 1.96 * float(r["std"]) * (artist_count ** 0.5)
        tiers = _tier_sums(df[df["month"] == m])
        points.append(
            {
                "monthIso": m.isoformat(),
                "year": int(m.year),
                "monthIndex": int(m.month),
                "total": total,
                "ciBand": round(ci_band),
                "deltaPrev": delta,
                "tiers": {k: round(v) for k, v in tiers.items()},
            }
        )
        prev = total

    last_m = monthly["month"].max()
    meta = {
        "startYear": start_year,
        "currentYearSplit": current_year_split,
        "lastMonthIso": pd.Timestamp(last_m).isoformat(),
        "pointCount": len(points),
        "subtitleMetric": "Σ monthly Spotify listener counts on NUAM artist rows (same months as export)",
        "tiers": [{"key": k, "rankLo": lo, "rankHi": hi} for k, lo, hi in TIERS],
    }
    return {"meta": meta, "points": points}
