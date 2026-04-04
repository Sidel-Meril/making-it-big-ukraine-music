"""Payloads for 'What About Money?' — payout histogram + per-artist monthly lines."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def listeners_with_min_payout_usd(
    listeners_df: pd.DataFrame,
    *,
    paid_premium_per_1k_streams: float = 1.33,
) -> pd.DataFrame:
    """estimated_min_payout style: listeners × (paid $/1k) / 1000 (premium-only shortcut)."""
    df = listeners_df.copy()
    df["payout_usd"] = df["listeners"].astype(float) * float(paid_premium_per_1k_streams) / 1000.0
    return df


def build_payout_histogram_payload(
    df: pd.DataFrame,
    *,
    threshold_usd: float = 300.0,
    bins: int = 72,
) -> dict[str, Any]:
    by_artist = df.groupby("artist_name", sort=False)["payout_usd"].sum()
    totals = by_artist.to_numpy(dtype=float)
    n_artists = int(len(totals))
    if n_artists == 0:
        return {
            "bars": [],
            "thresholdUsd": threshold_usd,
            "thresholdLog": float(np.log1p(threshold_usd)),
            "pctUnderThreshold": 0.0,
            "artistCount": 0,
        }

    logv = np.log1p(totals)
    counts, edges = np.histogram(logv, bins=bins)
    pct_under = float((totals < threshold_usd).sum()) / n_artists * 100.0

    bars: list[dict[str, Any]] = []
    for i in range(len(counts)):
        c = int(counts[i])
        if c == 0:
            continue
        bars.append(
            {
                "logX0": float(edges[i]),
                "logX1": float(edges[i + 1]),
                "count": c,
            }
        )

    return {
        "bars": bars,
        "thresholdUsd": threshold_usd,
        "thresholdLog": float(np.log1p(threshold_usd)),
        "pctUnderThreshold": pct_under,
        "artistCount": n_artists,
        "maxLog": float(logv.max()) if len(logv) else 0.0,
    }


def build_artist_payout_lines_payload(
    df: pd.DataFrame,
    *,
    start_month: str = "2025-01-01",
    max_artists: int = 0,
) -> dict[str, Any]:
    """One series per artist with any row in the window. Optional max_artists caps export size (>0)."""
    w = df[df["month"] >= pd.Timestamp(start_month)].copy()
    if w.empty:
        return {"series": [], "monthExtents": [], "meta": {"startMonth": start_month, "artistSeriesCount": 0}}

    totals = w.groupby("artist_name", sort=False)["payout_usd"].sum().sort_values(ascending=False)
    names = list(totals.index)
    if max_artists and max_artists > 0:
        names = names[: int(max_artists)]

    peak_by_name = df.groupby("artist_name", sort=False)["listeners"].max()

    months_sorted = sorted(w["month"].unique())
    month_iso = [pd.Timestamp(m).date().isoformat() for m in months_sorted]

    series: list[dict[str, Any]] = []
    for idx, name in enumerate(names):
        sub = w[w["artist_name"] == name].sort_values("month")
        points = [
            {"month": pd.Timestamp(r.month).date().isoformat(), "usd": round(float(r.payout_usd), 4)}
            for r in sub.itertuples(index=False)
        ]
        pl = int(peak_by_name.get(name, 0)) if name in peak_by_name.index else 0
        total_usd = float(sub["payout_usd"].sum())
        series.append(
            {
                "id": idx,
                "name": name,
                "peakListeners": pl,
                "totalUsd": round(total_usd, 2),
                "points": points,
            }
        )

    max_peak = max((s["peakListeners"] for s in series), default=0)
    max_usd = float(w["payout_usd"].max()) if len(w) else 0.0

    return {
        "series": series,
        "monthExtents": month_iso,
        "meta": {
            "startMonth": start_month,
            "artistSeriesCount": len(series),
            "paidPremiumPer1kStreams": 1.33,
            "sliderMaxPeakListeners": max_peak,
            "sliderMinPeakListeners": 0,
            "maxMonthlyUsd": max_usd,
        },
    }


def build_money_about_payload(
    listeners_df: pd.DataFrame,
    *,
    paid_premium_per_1k_streams: float = 1.33,
    hist_threshold_usd: float = 300.0,
    hist_bins: int = 72,
    lines_start_month: str = "2025-01-01",
    lines_max_artists: int = 0,
) -> dict[str, Any]:
    df = listeners_with_min_payout_usd(
        listeners_df, paid_premium_per_1k_streams=paid_premium_per_1k_streams
    )
    hist = build_payout_histogram_payload(df, threshold_usd=hist_threshold_usd, bins=hist_bins)
    lines = build_artist_payout_lines_payload(
        df, start_month=lines_start_month, max_artists=lines_max_artists
    )
    return {
        "histogram": hist,
        "lines": lines,
        "meta": {
            "paidPremiumPer1kStreams": paid_premium_per_1k_streams,
            "histThresholdUsd": hist_threshold_usd,
            "linesStartMonth": lines_start_month,
            "linesMaxArtistsExport": lines_max_artists,
            "subtitleMetric": (
                "Estimated Spotify payout using premium rate ≈ $"
                f"{paid_premium_per_1k_streams:.2f} per 1,000 streams (Ukraine market estimate)"
            ),
        },
    }
