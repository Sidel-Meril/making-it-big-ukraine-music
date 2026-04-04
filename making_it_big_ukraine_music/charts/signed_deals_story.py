"""Build payload for signed-deals story charts (histogram, strange-genre pack, label bars)."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from making_it_big_ukraine_music.charts.genres_popularity import build_genre_popularity_table, build_genres_long_df
from making_it_big_ukraine_music.charts.genres_popularity_export import genre_table_to_payload
from making_it_big_ukraine_music.charts.milestones import (
    compute_top_rated_labels,
    listeners_threshold_from_quantile,
    top_artist_ids_at_threshold,
)


def build_signed_deals_story_payload(
    artists_df: pd.DataFrame,
    listeners_df: pd.DataFrame,
    labels_df: pd.DataFrame,
    *,
    quantile: float = 0.995,
    min_signings: int = 2,
    strange_max_listeners: float = 1000.0,
    label_min_peak_listeners: float = 10_000.0,
    hist_bins: int = 40,
    label_bar_top_n: int = 10,
) -> dict[str, Any]:
    ref_month = listeners_df["month"].max()
    listeners_thresh = float(listeners_threshold_from_quantile(listeners_df, q=quantile))
    top_ids = top_artist_ids_at_threshold(listeners_df, listeners_thresh)
    top_labels_list = compute_top_rated_labels(labels_df, top_ids, min_signings=min_signings)
    top_label_set = set(top_labels_list)

    peaks = listeners_df.groupby("artist_id", sort=False)["listeners"].max()

    valid_labels: set[str] = set()
    _ldf = labels_df.dropna(subset=["label"])
    for lab, grp in _ldf.groupby("label", sort=False):
        aids = grp["artist_id"].unique()
        sub = peaks.reindex(aids.astype(object))
        mx = float(sub.max()) if len(sub) else float("nan")
        if np.isfinite(mx) and mx >= label_min_peak_listeners:
            valid_labels.add(str(lab))

    signed_mask = labels_df["label"].isin(top_label_set)
    signed_artist_ids = labels_df.loc[signed_mask, "artist_id"].drop_duplicates().astype(int)
    signed_set = set(signed_artist_ids.tolist())

    ach = artists_df.loc[artists_df["artist_id"].isin(signed_set)].copy()
    ach["listeners"] = ach["artist_id"].map(peaks)

    L = ach["listeners"].fillna(0).clip(lower=0).astype(float)
    log_l = np.log1p(L.to_numpy(dtype=float))
    hi = float(max(log_l.max(), np.log1p(strange_max_listeners) + 1e-6, 0.01))
    counts, bin_edges = np.histogram(log_l, bins=hist_bins, range=(0.0, hi))
    strange_log_end = float(np.log1p(strange_max_listeners))

    strange_ids = set(
        ach.loc[
            ach["listeners"].notna() & (ach["listeners"] < strange_max_listeners),
            "artist_id",
        ]
        .astype(int)
        .tolist()
    )

    def peak_val(aid: int) -> float:
        v = peaks.get(aid)
        return float(v) if v is not None and pd.notna(v) else 0.0

    candidate_labels = sorted(top_label_set & valid_labels, key=lambda x: str(x).lower())
    bar_rows: list[dict[str, Any]] = []
    for lab in candidate_labels:
        sub = labels_df[labels_df["label"] == lab]
        aids_on = {int(x) for x in sub["artist_id"].unique()} & signed_set
        n_sig = len(aids_on)
        n_str = sum(1 for a in aids_on if peak_val(a) < strange_max_listeners)
        bar_rows.append({"label": str(lab), "signedCount": n_sig, "strangeCount": n_str})
    bar_rows.sort(key=lambda r: (-r["signedCount"], r["label"].lower()))
    bar_top = bar_rows[: int(label_bar_top_n)]

    genres_long = build_genres_long_df(artists_df)
    gl = genres_long[genres_long["artist_id"].isin(strange_ids)]
    if gl.empty:
        strange_genres_payload: dict[str, Any] = {
            "meta": {
                "metric": "listeners_sum",
                "genreCount": 0,
                "topN": None,
                "metricLabel": "No strange-deal artists with genre tags",
            },
            "genres": [],
        }
    else:
        t = build_genre_popularity_table(gl, listeners_df, metric="listeners_sum", top_n=None)
        strange_genres_payload = genre_table_to_payload(t, metric="listeners_sum", top_n=None)

    return {
        "meta": {
            "refMonthIso": ref_month.isoformat(),
            "listenersRankThreshold": listeners_thresh,
            "topRatedLabelCount": len(top_labels_list),
            "strangeMaxListeners": strange_max_listeners,
            "labelMinPeakListeners": label_min_peak_listeners,
            "signedArtistCount": len(signed_set),
            "strangeArtistCount": len(strange_ids),
            "quantile": quantile,
            "minSignings": min_signings,
        },
        "histogram": {
            "binEdges": [float(x) for x in bin_edges],
            "counts": [int(x) for x in counts],
            "strangeBandLogEnd": strange_log_end,
            "xIsLog1p": True,
        },
        "strangeGenrePack": strange_genres_payload,
        "labelBars": bar_top,
    }
