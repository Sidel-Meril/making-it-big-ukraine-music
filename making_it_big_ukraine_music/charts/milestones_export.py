"""Serialize milestone flower chart data to JS for D3."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from making_it_big_ukraine_music.charts.milestones import FLOWER_MILESTONES, MILESTONE_COLUMNS


def achievement_frame_to_chart_payload(
    df: pd.DataFrame,
    *,
    ref_month_iso: str,
    spotify_listeners_threshold: float,
    listeners_rank_threshold: int | None,
    min_peak_listeners_export: float | None = None,
    listeners_df: pd.DataFrame | None = None,
    labels_df: pd.DataFrame | None = None,
) -> dict[str, Any]:
    # Build optional lookup maps for latest listeners and last label per artist
    latest_listeners_map: dict[int, float] = {}
    if listeners_df is not None:
        last_month = listeners_df["month"].max()
        latest_rows = listeners_df[listeners_df["month"] == last_month][["artist_id", "listeners"]]
        latest_listeners_map = {int(aid): float(v) for aid, v in zip(latest_rows["artist_id"], latest_rows["listeners"])}

    last_label_map: dict[int, str] = {}
    if labels_df is not None:
        last_label_series = labels_df.groupby("artist_id")["label"].last()
        last_label_map = {int(aid): str(lab) for aid, lab in last_label_series.items() if pd.notna(lab)}

    rows: list[dict[str, Any]] = []
    for _, r in df.iterrows():
        bits = [bool(r[c]) for c in MILESTONE_COLUMNS]
        achieved_tracked = sum(bits)
        tracked_total = len(bits)
        artist_id = int(r["artist_id"])
        row: dict[str, Any] = {
            "artistId": artist_id,
            "name": str(r["artist_name"]),
            "ruLang": bool(r["ru_lang_flag"]),
            "listenersMax": float(r["listeners"]) if pd.notna(r["listeners"]) else None,
            "bits": [1 if b else 0 for b in bits],
            "achievedTracked": achieved_tracked,
            "trackedTotal": tracked_total,
        }
        if latest_listeners_map:
            v = latest_listeners_map.get(artist_id)
            row["latestListeners"] = float(v) if v is not None else None
        if last_label_map:
            row["label"] = last_label_map.get(artist_id) or None
        rows.append(row)

    meta: dict[str, Any] = {
        "refMonth": ref_month_iso,
        "spotifyListenersThreshold": spotify_listeners_threshold,
        "listenersRankThreshold": listeners_rank_threshold,
        "petalCount": len(FLOWER_MILESTONES),
        "listenerRankOrder": "listenersMax_desc",
        "listenerRankCount": len(rows),
    }
    if min_peak_listeners_export is not None and min_peak_listeners_export > 0:
        meta["minPeakListenersInExport"] = float(min_peak_listeners_export)

    return {
        "meta": meta,
        "milestones": FLOWER_MILESTONES,
        "artists": rows,
    }


def write_chart_js_bundle(path: str | Path, payload: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    dumped = json.dumps(payload, ensure_ascii=False)
    path.write_text(f"window.__NUAM_MILESTONE_DATA__ = {dumped};\n", encoding="utf-8")
