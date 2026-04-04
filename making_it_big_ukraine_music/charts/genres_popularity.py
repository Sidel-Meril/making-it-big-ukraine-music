"""Genre popularity table (matches notebooks/eda.ipynb listeners-per-artist logic)."""

from __future__ import annotations

from typing import Any

import pandas as pd


def build_genres_long_df(artists_df: pd.DataFrame) -> pd.DataFrame:
    """One row per (artist_id, genre token) from comma-separated ``genre`` field."""
    rows: list[dict[str, Any]] = []
    for row in artists_df.itertuples():
        raw = getattr(row, "genre", None)
        if raw is None or (isinstance(raw, float) and pd.isna(raw)):
            continue
        s = str(raw).strip()
        if not s:
            continue
        aid = int(row.artist_id)
        aname = str(row.artist_name)
        for token in s.split(","):
            g = token.strip()
            if g:
                rows.append({"artist_id": aid, "artist_name": aname, "genre": g})
    if not rows:
        return pd.DataFrame(columns=["artist_id", "artist_name", "genre"])
    return pd.DataFrame(rows).sort_values(["artist_id", "genre"]).reset_index(drop=True)


def build_genre_popularity_table(
    genres_df: pd.DataFrame,
    listeners_df: pd.DataFrame,
    *,
    metric: str = "listeners_per_artist",
    top_n: int | None = 40,
) -> pd.DataFrame:
    """Aggregate by genre; drop genres with no summed listeners (notebook parity)."""
    if metric not in ("listeners_per_artist", "listeners_sum", "artist_count"):
        raise ValueError(f"unknown metric: {metric!r}")
    if genres_df.empty:
        return pd.DataFrame(
            columns=[
                "genre",
                "artist_count",
                "listeners_sum",
                "listeners_per_artist",
                "pack_value",
                "top_artist_names",
            ]
        )

    stats = genres_df["genre"].value_counts().reset_index()
    stats = stats.rename(columns={"count": "artist_count"})

    gwl = genres_df.merge(
        listeners_df[["artist_id", "listeners"]],
        on="artist_id",
        how="outer",
    )[["artist_id", "artist_name", "genre", "listeners"]]
    gwl = gwl.dropna(subset=["genre"])
    gwl["listeners"] = pd.to_numeric(gwl["listeners"], errors="coerce").fillna(0.0)
    by_artist_genre = (
        gwl.groupby(["genre", "artist_id", "artist_name"], sort=False)["listeners"]
        .sum()
        .reset_index()
    )
    by_artist_genre = by_artist_genre.sort_values(
        ["genre", "listeners"],
        ascending=[True, False],
    )
    top3 = (
        by_artist_genre.groupby("genre", sort=False)
        .head(3)
        .groupby("genre", sort=False)["artist_name"]
        .apply(lambda s: [str(x).strip() for x in s if str(x).strip()])
    )
    top3_map: dict[Any, list[str]] = top3.to_dict() if len(top3) else {}
    sums = gwl.groupby("genre", sort=False)["listeners"].sum()
    stats["listeners_sum"] = stats["genre"].map(lambda x: float(sums.get(x, 0.0)))
    stats = stats.loc[stats["listeners_sum"] > 0].copy()
    stats["top_artist_names"] = stats["genre"].map(lambda g: list(top3_map.get(g, [])))
    stats["listeners_per_artist"] = stats["listeners_sum"] / stats["artist_count"].replace(0, pd.NA)
    stats["listeners_per_artist"] = stats["listeners_per_artist"].astype(float)

    if metric == "listeners_per_artist":
        stats["pack_value"] = stats["listeners_per_artist"]
    elif metric == "listeners_sum":
        stats["pack_value"] = stats["listeners_sum"]
    else:
        stats["pack_value"] = stats["artist_count"].astype(float)

    stats = stats.sort_values("pack_value", ascending=False).reset_index(drop=True)
    if top_n is not None and top_n > 0:
        stats = stats.head(int(top_n)).reset_index(drop=True)
    return stats
