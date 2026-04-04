"""Serialize label roster tick chart data to JS."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def label_roster_entries_to_payload(
    entries: list[dict[str, Any]],
    *,
    ref_month_iso: str,
    listeners_rank_threshold: int | None,
    min_top_artists_on_label: int,
) -> dict[str, Any]:
    max_cat = max((e["artistCountOnLabel"] for e in entries), default=1)
    top_rated_n = sum(1 for e in entries if e.get("topRated"))
    meta: dict[str, Any] = {
        "refMonth": ref_month_iso,
        "listenersRankThreshold": listeners_rank_threshold,
        "minTopArtistsOnLabel": min_top_artists_on_label,
        "labelCount": len(entries),
        "maxArtistCountOnLabel": int(max_cat),
        "topRatedLabelCount": int(top_rated_n),
    }
    return {"meta": meta, "labels": entries}


def write_label_roster_js_bundle(path: str | Path, payload: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    dumped = json.dumps(payload, ensure_ascii=False)
    path.write_text(f"window.__NUAM_LABEL_ROSTER_DATA__ = {dumped};\n", encoding="utf-8")
