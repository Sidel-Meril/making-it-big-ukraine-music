"""Monthly summed Spotify listeners (NUAM export) for story opener chart."""

from __future__ import annotations

from typing import Any

import pandas as pd

# Audience tier definitions — fixed listener-count thresholds (lo inclusive, hi exclusive).
# Listed top-to-bottom; stack order in the chart is bottom-to-top (reversed).
TIERS: list[tuple[str, int, int | None]] = [
    ("mega",      1_000_000, None),        # 1 M+
    ("large",       500_000, 1_000_000),   # 500 K – 1 M
    ("big",         250_000,   500_000),   # 250 K – 500 K
    ("medium",      100_000,   250_000),   # 100 K – 250 K
    ("small_hi",     10_000,   100_000),   # 10 K – 100 K
    ("small_lo",      1_000,    10_000),   # 1 K – 10 K
    ("tiny",              0,     1_000),   # < 1 K
]


def _tier_sums(month_df: pd.DataFrame) -> dict[str, float]:
    """Return summed listeners per fixed-threshold tier for a single month."""
    result: dict[str, float] = {}
    listeners = month_df["listeners"]
    for key, lo, hi in TIERS:
        mask = listeners >= lo
        if hi is not None:
            mask &= listeners < hi
        result[key] = float(listeners[mask].sum())
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
        "tiers": [{"key": k, "minListeners": lo, "maxListeners": hi} for k, lo, hi in TIERS],
    }
    return {"meta": meta, "points": points}
