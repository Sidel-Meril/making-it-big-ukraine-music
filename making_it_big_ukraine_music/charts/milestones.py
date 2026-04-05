"""Milestone booleans for the flower chart; label lists and listener thresholds."""

from __future__ import annotations

import pandas as pd

# Six petals — notebooks/eda.ipynb check__* columns; clockwise from top in the chart.
MILESTONE_COLUMNS: list[str] = [
    "m_spotify_link",
    "m_instagram",
    "m_listeners_1m",
    "m_debut_recent",
    "m_signed_peer_label",
    "m_payout_300",
]

FLOWER_MILESTONES: list[dict[str, str]] = [
    {"id": "spotify_link", "label": "Spotify profile linked"},
    {"id": "instagram", "label": "Instagram linked"},
    {"id": "listeners_1m", "label": "1M+ peak monthly listeners"},
    {"id": "debut_recent", "label": "Debut recorded (last 3 yrs)"},
    {"id": "signed_peer_label", "label": "On label shared with high-listener peers"},
    {"id": "payout_300", "label": "Earned $300+ total (est. streaming)"},
]

# USD per 1 000 paid streams — mirrors money_about.py / JS RATE_PER_1K default.
_PAID_RATE_PER_1K = 1.33


def listeners_threshold_from_quantile(listeners_df: pd.DataFrame, q: float = 0.995) -> int:
    import math

    last_month = listeners_df["month"].max()
    last_month_listeners = listeners_df.loc[listeners_df["month"] == last_month, "listeners"]
    qv = float(last_month_listeners.quantile(q))
    return int(100_000 * math.ceil(qv / 100_000))


def top_artist_ids_at_threshold(listeners_df: pd.DataFrame, listeners_thresh: float) -> pd.Series:
    return (
        listeners_df.loc[listeners_df["listeners"] >= listeners_thresh, "artist_id"]
        .drop_duplicates()
        .reset_index(drop=True)
    )


def compute_top_rated_labels(
    labels_df: pd.DataFrame,
    top_artist_ids: pd.Series,
    *,
    min_signings: int = 2,
) -> list[str]:
    """Labels that sign at least ``min_signings`` distinct top-listener artists (>= threshold)."""
    pool = labels_df[labels_df["artist_id"].isin(top_artist_ids)]
    uniq = pd.DataFrame({"label": pool["label"].unique()})
    top_set = set(top_artist_ids)

    def count_signings(lab: str) -> int:
        return int(
            len(labels_df[(labels_df["label"] == lab) & labels_df["artist_id"].isin(top_set)])
        )

    uniq["signed_top_artists"] = uniq["label"].map(count_signings)
    uniq = uniq.sort_values("signed_top_artists", ascending=False).reset_index(drop=True)
    # Match notebooks/eda.ipynb: keep labels with more than one top artist → signed_top_artists >= 2.
    return uniq.loc[uniq["signed_top_artists"] >= min_signings, "label"].tolist()


def build_achievement_frame(
    artists_df: pd.DataFrame,
    listeners_df: pd.DataFrame,
    debut_df: pd.DataFrame,
    labels_df: pd.DataFrame,
    top_rated_labels: list[str],
    *,
    spotify_listeners_criteria: float = 1_000_000,
    paid_rate_per_1k: float = _PAID_RATE_PER_1K,
    payout_threshold_usd: float = 300.0,
) -> pd.DataFrame:
    ref_year = int(listeners_df["month"].max().year)
    max_listeners = listeners_df.groupby("artist_id")["listeners"].max()

    out = artists_df.copy()
    out["listeners"] = out["artist_id"].map(max_listeners)

    label_set = set(top_rated_labels)
    signed_ids = labels_df.loc[labels_df["label"].isin(label_set), "artist_id"].drop_duplicates()
    signed_mask = out["artist_id"].isin(set(signed_ids))

    debut_ok = debut_df.loc[
        debut_df["is_debuted"] & (debut_df["year"] >= ref_year - 3), "artist_id"
    ].drop_duplicates()
    debut_mask = out["artist_id"].isin(set(debut_ok))

    # Mirrors notebooks/eda.ipynb check__has_300_dollars_payout:
    # sum monthly listeners × rate/1 000 across all snapshot months.
    payout_by_artist = (
        listeners_df.groupby("artist_id")["listeners"].sum() * paid_rate_per_1k / 1000
    )
    payout_mask = out["artist_id"].map(payout_by_artist >= payout_threshold_usd).fillna(False)

    bits = {
        "m_spotify_link": out["spotify"].notna(),
        "m_instagram": out["instagram"].notna(),
        "m_listeners_1m": out["listeners"] >= spotify_listeners_criteria,
        "m_debut_recent": debut_mask,
        "m_signed_peer_label": signed_mask,
        "m_payout_300": payout_mask,
    }
    assert set(bits) == set(MILESTONE_COLUMNS)
    for k in MILESTONE_COLUMNS:
        out[k] = bits[k]

    mcols = MILESTONE_COLUMNS
    out["achievement_count"] = out[mcols].sum(axis=1)
    out["achievement_total"] = len(mcols)

    return out


def achievement_frame_sorted_by_peak_listeners(achievement_df: pd.DataFrame) -> pd.DataFrame:
    """Descending peak listeners; NaN listeners last (matches listener-rank order in the chart)."""
    return achievement_df.sort_values("listeners", ascending=False, na_position="last").reset_index(drop=True)


def select_artists_by_listener_rank(
    achievement_df: pd.DataFrame,
    *,
    shift: int = 0,
    n: int = 50,
) -> pd.DataFrame:
    order = achievement_frame_sorted_by_peak_listeners(achievement_df)
    return order.iloc[shift : shift + n]
