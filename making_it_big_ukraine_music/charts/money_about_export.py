"""Write money-about chart-data.js."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_money_about_js_bundle(path: str | Path, payload: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    dumped = json.dumps(payload, ensure_ascii=False)
    path.write_text(f"window.__NUAM_MONEY_ABOUT__ = {dumped};\n", encoding="utf-8")
