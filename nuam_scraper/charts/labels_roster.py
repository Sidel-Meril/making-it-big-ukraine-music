"""Label roster rows for the tick chart (top-listener artists per label)."""

from __future__ import annotations

from typing import Any

import pandas as pd


def peak_listeners_by_artist(listeners_df: pd.DataFrame) -> pd.Series:
    return listeners_df.groupby("artist_id", sort=False)["listeners"].max()


def build_label_roster_entries(
    labels_df: pd.DataFrame,
    top_artist_ids: pd.Series,
    artists_df: pd.DataFrame,
    listeners_df: pd.DataFrame,
    *,
    min_top_artists_on_label: int = 2,
) -> list[dict[str, Any]]:
    """One entry per distinct label in ``labels_df``.

    * ``artistCountOnLabel`` — distinct artists on that label in NUAM (drives center circle size / number).
    * ``artists`` — only high-listener-pool artists on the label (one export tick each).
    * ``topRated`` — True when at least ``min_top_artists_on_label`` pool artists appear on the label.
    """
    top_set = set(top_artist_ids.tolist())
    peaks = peak_listeners_by_artist(listeners_df)
    id_name = artists_df.drop_duplicates("artist_id").set_index("artist_id")["artist_name"]

    all_labels = sorted(
        labels_df["label"].dropna().unique().tolist(),
        key=lambda x: str(x).lower(),
    )

    entries: list[dict[str, Any]] = []
    for lab in all_labels:
        sub_all = labels_df[labels_df["label"] == lab]
        artist_count = int(sub_all["artist_id"].nunique())

        sub_top = sub_all[sub_all["artist_id"].isin(top_set)]
        aids = sub_top["artist_id"].drop_duplicates().tolist()
        roster: list[dict[str, Any]] = []
        for aid in aids:
            aid = int(aid)
            lm = peaks.get(aid)
            roster.append(
                {
                    "artistId": aid,
                    "name": str(id_name.get(aid, "")),
                    "listenersMax": float(lm) if lm is not None and pd.notna(lm) else None,
                }
            )
        roster.sort(key=lambda r: (-(r["listenersMax"] or 0), r["name"].lower()))
        top_rated = len(roster) >= min_top_artists_on_label
        entries.append(
            {
                "key": lab,
                "name": lab,
                "artistCountOnLabel": artist_count,
                "topRated": top_rated,
                "artists": roster,
            }
        )

    entries.sort(
        key=lambda e: (
            -int(e["topRated"]),
            -e["artistCountOnLabel"],
            -len(e["artists"]),
            e["name"].lower(),
        )
    )
    return entries
