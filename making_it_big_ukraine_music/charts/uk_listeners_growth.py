"""Monthly summed Spotify listeners (NUAM export) for story opener chart."""

from __future__ import annotations

from typing import Any

import pandas as pd


def build_uk_listeners_growth_payload(
    listeners_df: pd.DataFrame,
    *,
    start_year: int = 2024,
    current_year_split: int = 2026,
) -> dict[str, Any]:
    """Sum ``listeners`` by calendar month (all artist–month rows in export).

    Interprets the series as aggregate monthly-listener counts on the NUAM roster
    (Ukrainian-music–focused catalog), not unique national listeners.
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
        # 95 % CI half-width for the sum:  z₀.₀₂₅ × σ_sum  where σ_sum = std × √n
        ci_band = 1.96 * float(r["std"]) * (artist_count ** 0.5)
        points.append(
            {
                "monthIso": m.isoformat(),
                "year": int(m.year),
                "monthIndex": int(m.month),
                "total": total,
                "ciBand": round(ci_band),
                "deltaPrev": delta,
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
    }
    return {"meta": meta, "points": points}
