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
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for _, r in df.iterrows():
        bits = [bool(r[c]) for c in MILESTONE_COLUMNS]
        achieved_tracked = sum(bits)
        tracked_total = len(bits)
        rows.append(
            {
                "artistId": int(r["artist_id"]),
                "name": str(r["artist_name"]),
                "ruLang": bool(r["ru_lang_flag"]),
                "listenersMax": float(r["listeners"]) if pd.notna(r["listeners"]) else None,
                "bits": [1 if b else 0 for b in bits],
                "achievedTracked": achieved_tracked,
                "trackedTotal": tracked_total,
            }
        )

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
