"""Payload for the log-transformed listener distribution chart."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def build_listeners_dist_payload(
    listeners_df: pd.DataFrame,
    *,
    bins: int = 30,
) -> dict[str, Any]:
    """Histogram of log1p(listeners) for the most recent month + precomputed quantile table."""
    last_month = listeners_df["month"].max()
    subset = listeners_df[listeners_df["month"] == last_month]["listeners"].dropna()
    vals = subset.values.astype(float)

    if len(vals) == 0:
        return {
            "bars": [],
            "quantiles": {},
            "maxLog": 0.0,
            "minLog": 0.0,
            "totalArtists": 0,
            "month": str(pd.Timestamp(last_month).date()),
            "meta": {},
        }

    log_vals = np.log1p(vals)
    counts, edges = np.histogram(log_vals, bins=bins)

    bars: list[dict[str, Any]] = [
        {
            "logX0": float(edges[i]),
            "logX1": float(edges[i + 1]),
            "count": int(counts[i]),
        }
        for i in range(len(counts))
        if counts[i] > 0
    ]

    # Precompute integer percentile thresholds 0..100 so the frontend can do
    # instant lookups without raw data.
    quantiles: dict[str, float] = {
        str(p): float(np.percentile(log_vals, p)) for p in range(101)
    }

    return {
        "bars": bars,
        "quantiles": quantiles,
        "maxLog": float(log_vals.max()),
        "minLog": float(log_vals.min()),
        "totalArtists": int(len(vals)),
        "month": str(pd.Timestamp(last_month).date()),
        "meta": {
            "description": (
                "Log₁₊-transformed monthly listener distribution "
                "for the most recent month in the NUAM export."
            ),
        },
    }
