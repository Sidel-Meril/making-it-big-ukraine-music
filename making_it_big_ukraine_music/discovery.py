from __future__ import annotations

import re
from pathlib import Path

from .config import DEFAULT_ARTISTS_CSV_URL

# Google Sheets "publish to web" CSV links embedded in the NUAM Base web app
SHEETS_CSV_RE = re.compile(
    r'https://docs\.google\.com/spreadsheets/d/e/[A-Za-z0-9_-]+/pub\?[^"\'\s<>]+output=csv',
    re.IGNORECASE,
)


def extract_sheet_csv_urls(html: str) -> list[str]:
    """Return unique Google Sheets CSV export URLs found in HTML/JS."""
    found = SHEETS_CSV_RE.findall(html)
    # de-dupe preserving order
    seen: set[str] = set()
    out: list[str] = []
    for u in found:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def pick_artists_csv_url(urls: list[str]) -> str | None:
    """Heuristic: main artist table is gid=0 on the primary multi-tab document."""
    for u in urls:
        if "gid=0&" in u or "gid=0" in u:
            return u
    return urls[0] if urls else None


def discover_artists_csv_url_from_texts(*html_chunks: str) -> str | None:
    for chunk in html_chunks:
        if not chunk:
            continue
        urls = extract_sheet_csv_urls(chunk)
        picked = pick_artists_csv_url(urls)
        if picked:
            return picked
    return None


def load_html(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def resolve_artists_csv_url(
    *,
    explicit: str | None,
    snapshot_path: Path | None,
    fetch_base_fn,
    fetch_github_fn,
) -> str:
    """Pick CSV URL: explicit > snapshot > live discovery > default constant."""
    if explicit:
        return explicit
    chunks: list[str] = []
    if snapshot_path and snapshot_path.is_file():
        chunks.append(load_html(snapshot_path))
    try:
        chunks.append(fetch_base_fn())
    except Exception:
        pass
    try:
        chunks.append(fetch_github_fn())
    except Exception:
        pass
    discovered = discover_artists_csv_url_from_texts(*chunks)
    return discovered or DEFAULT_ARTISTS_CSV_URL
