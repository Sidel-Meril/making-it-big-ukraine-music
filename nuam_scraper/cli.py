from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .config import ScraperSettings
from .pipeline import scrape_artists_to_parquet


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    p = argparse.ArgumentParser(
        description="Download NUAM artist base (Google Sheets CSV) to Parquet.",
    )
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("nuam_artists.parquet"),
        help="Output Parquet path",
    )
    p.add_argument(
        "--snapshot",
        type=Path,
        default=None,
        help="Optional saved Wix HTML (e.g. 'NUAM Base.html') to discover CSV URLs",
    )
    p.add_argument(
        "--csv-url",
        default=None,
        help="Override artist CSV URL (skips discovery)",
    )
    args = p.parse_args(argv)

    settings = ScraperSettings(
        snapshot_html_path=str(args.snapshot) if args.snapshot else None,
        artists_csv_url=args.csv_url,
    )
    path, url, n = scrape_artists_to_parquet(args.output, settings)
    print(f"Wrote {n} rows to {path} (source: {url})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
