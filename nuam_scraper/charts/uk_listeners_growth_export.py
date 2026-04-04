"""Write UK listeners growth chart-data.js."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_uk_listeners_growth_js_bundle(path: str | Path, payload: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    dumped = json.dumps(payload, ensure_ascii=False)
    path.write_text(f"window.__NUAM_UK_LISTENERS_GROWTH__ = {dumped};\n", encoding="utf-8")
