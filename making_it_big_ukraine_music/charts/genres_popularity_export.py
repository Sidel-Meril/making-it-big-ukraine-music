"""Serialize genre circle-pack chart data to JS."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


def genre_table_to_payload(
    df: pd.DataFrame,
    *,
    metric: str,
    top_n: int | None,
) -> dict[str, Any]:
    genres: list[dict[str, Any]] = []
    for _, r in df.iterrows():
        raw_list = r.get("top_artist_names")
        if raw_list is None or (isinstance(raw_list, float) and pd.isna(raw_list)):
            top_names: list[str] = []
        elif isinstance(raw_list, list):
            top_names = [str(x).strip() for x in raw_list if str(x).strip()]
        else:
            top_names = [str(raw_list).strip()] if str(raw_list).strip() else []
        top_names = top_names[:3]
        genres.append(
            {
                "name": str(r["genre"]),
                "value": float(r["pack_value"]),
                "artistCount": int(r["artist_count"]),
                "listenersSum": float(r["listeners_sum"]),
                "listenersPerArtist": float(r["listeners_per_artist"])
                if pd.notna(r["listeners_per_artist"])
                else None,
                "topArtistNames": top_names,
            }
        )
    meta: dict[str, Any] = {
        "metric": metric,
        "topN": top_n,
        "genreCount": len(genres),
        "metricLabel": {
            "listeners_per_artist": "Listeners per artist (sum of monthly listener counts ÷ artist rows in genre)",
            "listeners_sum": "Sum of monthly listener counts (all artist–month rows tagged with genre)",
            "artist_count": "Artist–genre rows in NUAM (comma-split genres)",
        }.get(metric, metric),
    }
    return {"meta": meta, "genres": genres}


def write_genres_pack_js_bundle(path: str | Path, payload: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    dumped = json.dumps(payload, ensure_ascii=False)
    path.write_text(f"window.__NUAM_GENRES_PACK_DATA__ = {dumped};\n", encoding="utf-8")
