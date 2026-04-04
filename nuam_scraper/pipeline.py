from __future__ import annotations

import logging
from pathlib import Path

from .config import ScraperSettings
from .discovery import load_html, resolve_artists_csv_url
from .http_client import build_client, fetch_text
from .transform import artists_csv_to_dataframe, dataframe_to_parquet

logger = logging.getLogger(__name__)


def scrape_artists_to_parquet(
    output_parquet: str | Path,
    settings: ScraperSettings | None = None,
) -> tuple[Path, str, int]:
    """
    Fetch artist CSV, normalize, write Parquet.

    Returns (output_path, csv_url_used, row_count).
    """
    settings = settings or ScraperSettings()
    out = Path(output_parquet)
    out.parent.mkdir(parents=True, exist_ok=True)

    snapshot = (
        Path(settings.snapshot_html_path)
        if settings.snapshot_html_path
        else None
    )

    with build_client(settings) as client:

        def fetch_base() -> str:
            return fetch_text(client, settings.base_page_url, settings)

        def fetch_github() -> str:
            return fetch_text(client, settings.github_app_url, settings)

        csv_url = resolve_artists_csv_url(
            explicit=settings.artists_csv_url,
            snapshot_path=snapshot,
            fetch_base_fn=fetch_base,
            fetch_github_fn=fetch_github,
        )
        logger.info("Using artist CSV URL: %s", csv_url)
        csv_body = fetch_text(client, csv_url, settings)

    df = artists_csv_to_dataframe(csv_body)
    dataframe_to_parquet(df, out)
    return out, csv_url, len(df)
