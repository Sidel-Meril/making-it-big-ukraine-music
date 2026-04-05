"""CLI for exporting charts under data/charts/."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from making_it_big_ukraine_music.charts.genres_popularity import build_genre_popularity_table, build_genres_long_df
from making_it_big_ukraine_music.charts.genres_popularity_export import genre_table_to_payload, write_genres_pack_js_bundle
from making_it_big_ukraine_music.charts.signed_deals_story import build_signed_deals_story_payload
from making_it_big_ukraine_music.charts.signed_deals_story_export import write_signed_deals_story_js_bundle
from making_it_big_ukraine_music.charts.uk_listeners_growth import build_uk_listeners_growth_payload
from making_it_big_ukraine_music.charts.uk_listeners_growth_export import write_uk_listeners_growth_js_bundle
from making_it_big_ukraine_music.charts.money_about import build_money_about_payload
from making_it_big_ukraine_music.charts.money_about_export import write_money_about_js_bundle
from making_it_big_ukraine_music.charts.listeners_dist import build_listeners_dist_payload
from making_it_big_ukraine_music.charts.listeners_dist_export import write_listeners_dist_js_bundle
from making_it_big_ukraine_music.charts.labels_roster import build_label_roster_entries
from making_it_big_ukraine_music.charts.labels_roster_export import (
    label_roster_entries_to_payload,
    write_label_roster_js_bundle,
)
from making_it_big_ukraine_music.charts.milestones_export import achievement_frame_to_chart_payload, write_chart_js_bundle
from making_it_big_ukraine_music.charts.nuam_frames import load_nuam_parquet
from making_it_big_ukraine_music.charts.paths import charts_root, repo_root
from making_it_big_ukraine_music.charts.milestones import (
    achievement_frame_sorted_by_peak_listeners,
    build_achievement_frame,
    compute_top_rated_labels,
    listeners_threshold_from_quantile,
    top_artist_ids_at_threshold,
)

_ASSET_MILESTONES_INDEX = Path(__file__).resolve().parent / "assets" / "milestones" / "index.html"
_ASSET_LABEL_ROSTERS_INDEX = Path(__file__).resolve().parent / "assets" / "label_rosters" / "index.html"
_ASSET_GENRES_PACK_INDEX = Path(__file__).resolve().parent / "assets" / "genres_popularity" / "index.html"
_ASSET_SIGNED_DEALS_INDEX = Path(__file__).resolve().parent / "assets" / "signed_deals" / "index.html"
_ASSET_UK_LISTENERS_GROWTH_INDEX = Path(__file__).resolve().parent / "assets" / "uk_listeners_growth" / "index.html"
_ASSET_MONEY_ABOUT_INDEX = Path(__file__).resolve().parent / "assets" / "money_about" / "index.html"
_ASSET_LISTENERS_DIST_INDEX = Path(__file__).resolve().parent / "assets" / "listeners_dist" / "index.html"


def _cmd_milestones(args: argparse.Namespace) -> None:
    out_dir = Path(args.out_dir) if args.out_dir else charts_root() / "milestones"
    out_js = Path(args.out_js) if args.out_js else out_dir / "chart-data.js"

    if args.sync_html:
        out_dir.mkdir(parents=True, exist_ok=True)
        if not _ASSET_MILESTONES_INDEX.is_file():
            raise FileNotFoundError(f"Missing bundled template: {_ASSET_MILESTONES_INDEX}")
        shutil.copyfile(_ASSET_MILESTONES_INDEX, out_dir / "index.html")

    frames = load_nuam_parquet(args.parquet)
    listeners_thresh = listeners_threshold_from_quantile(frames.listeners_df, q=args.quantile)
    top_ids = top_artist_ids_at_threshold(frames.listeners_df, listeners_thresh)
    top_labels = compute_top_rated_labels(frames.labels_df, top_ids, min_signings=2)

    full = build_achievement_frame(
        frames.artists_df,
        frames.listeners_df,
        frames.debut_df,
        frames.labels_df,
        top_labels,
        spotify_listeners_criteria=args.spotify_listeners_min,
    )
    min_export = float(args.min_export_listeners)
    if min_export > 0:
        full = full.loc[full["listeners"].notna() & (full["listeners"] >= min_export)]

    ordered = achievement_frame_sorted_by_peak_listeners(full)
    if args.max_artists is not None:
        ordered = ordered.head(int(args.max_artists))
    if args.shift is not None or args.n is not None:
        shift = 0 if args.shift is None else int(args.shift)
        n = len(ordered) if args.n is None else int(args.n)
        ordered = ordered.iloc[shift : shift + n]

    ref_m = frames.listeners_df["month"].max()
    payload = achievement_frame_to_chart_payload(
        ordered,
        ref_month_iso=ref_m.isoformat(),
        spotify_listeners_threshold=args.spotify_listeners_min,
        listeners_rank_threshold=listeners_thresh,
        min_peak_listeners_export=min_export if min_export > 0 else None,
    )
    write_chart_js_bundle(out_js, payload)
    print(f"Wrote {out_js} ({len(payload['artists'])} artists)")


def _cmd_label_rosters(args: argparse.Namespace) -> None:
    out_dir = Path(args.out_dir) if args.out_dir else charts_root() / "label_rosters"
    out_js = Path(args.out_js) if args.out_js else out_dir / "chart-data.js"

    if args.sync_html:
        out_dir.mkdir(parents=True, exist_ok=True)
        if not _ASSET_LABEL_ROSTERS_INDEX.is_file():
            raise FileNotFoundError(f"Missing bundled template: {_ASSET_LABEL_ROSTERS_INDEX}")
        shutil.copyfile(_ASSET_LABEL_ROSTERS_INDEX, out_dir / "index.html")

    frames = load_nuam_parquet(args.parquet)
    listeners_thresh = (
        int(args.listeners_min)
        if args.listeners_min is not None and args.listeners_min > 0
        else listeners_threshold_from_quantile(frames.listeners_df, q=args.quantile)
    )
    top_ids = top_artist_ids_at_threshold(frames.listeners_df, listeners_thresh)
    entries = build_label_roster_entries(
        frames.labels_df,
        top_ids,
        frames.artists_df,
        frames.listeners_df,
        min_top_artists_on_label=int(args.min_artists_on_label),
    )
    ref_m = frames.listeners_df["month"].max()
    payload = label_roster_entries_to_payload(
        entries,
        ref_month_iso=ref_m.isoformat(),
        listeners_rank_threshold=listeners_thresh,
        min_top_artists_on_label=int(args.min_artists_on_label),
    )
    write_label_roster_js_bundle(out_js, payload)
    n_roster = sum(len(e["artists"]) for e in entries)
    tr = payload["meta"].get("topRatedLabelCount", 0)
    print(f"Wrote {out_js} ({len(entries)} labels, {n_roster} pool-on-label links, {tr} top-rated)")


def _cmd_genres_pack(args: argparse.Namespace) -> None:
    out_dir = Path(args.out_dir) if args.out_dir else charts_root() / "genres_popularity"
    out_js = Path(args.out_js) if args.out_js else out_dir / "chart-data.js"

    if args.sync_html:
        out_dir.mkdir(parents=True, exist_ok=True)
        if not _ASSET_GENRES_PACK_INDEX.is_file():
            raise FileNotFoundError(f"Missing bundled template: {_ASSET_GENRES_PACK_INDEX}")
        shutil.copyfile(_ASSET_GENRES_PACK_INDEX, out_dir / "index.html")

    frames = load_nuam_parquet(args.parquet)
    genres_long = build_genres_long_df(frames.artists_df)
    top_n = None if int(args.top) == 0 else int(args.top)
    metric = str(args.metric)
    table = build_genre_popularity_table(
        genres_long,
        frames.listeners_df,
        metric=metric,
        top_n=top_n,
    )
    payload = genre_table_to_payload(table, metric=metric, top_n=top_n)
    write_genres_pack_js_bundle(out_js, payload)
    print(f"Wrote {out_js} ({len(payload['genres'])} genres, metric={metric})")


def _cmd_signed_deals(args: argparse.Namespace) -> None:
    out_dir = Path(args.out_dir) if args.out_dir else charts_root() / "signed_deals"
    out_js = Path(args.out_js) if args.out_js else out_dir / "chart-data.js"

    if args.sync_html:
        out_dir.mkdir(parents=True, exist_ok=True)
        if not _ASSET_SIGNED_DEALS_INDEX.is_file():
            raise FileNotFoundError(f"Missing bundled template: {_ASSET_SIGNED_DEALS_INDEX}")
        shutil.copyfile(_ASSET_SIGNED_DEALS_INDEX, out_dir / "index.html")

    frames = load_nuam_parquet(args.parquet)
    payload = build_signed_deals_story_payload(
        frames.artists_df,
        frames.listeners_df,
        frames.labels_df,
        quantile=float(args.quantile),
        listeners_min=float(args.listeners_min) if args.listeners_min is not None else 0.0,
        min_signings=int(args.min_signings),
        strange_max_listeners=float(args.strange_max_listeners),
        label_min_peak_listeners=float(args.label_min_peak_listeners),
        hist_bins=int(args.hist_bins),
        label_bar_top_n=int(args.label_bar_top),
    )
    write_signed_deals_story_js_bundle(out_js, payload)
    m = payload["meta"]
    print(
        f"Wrote {out_js} (signed={m['signedArtistCount']}, strange={m['strangeArtistCount']}, "
        f"labelBars={len(payload['labelBars'])})"
    )


def _cmd_uk_listeners_growth(args: argparse.Namespace) -> None:
    out_dir = Path(args.out_dir) if args.out_dir else charts_root() / "uk_listeners_growth"
    out_js = Path(args.out_js) if args.out_js else out_dir / "chart-data.js"

    if args.sync_html:
        out_dir.mkdir(parents=True, exist_ok=True)
        if not _ASSET_UK_LISTENERS_GROWTH_INDEX.is_file():
            raise FileNotFoundError(f"Missing bundled template: {_ASSET_UK_LISTENERS_GROWTH_INDEX}")
        shutil.copyfile(_ASSET_UK_LISTENERS_GROWTH_INDEX, out_dir / "index.html")

    frames = load_nuam_parquet(args.parquet)
    payload = build_uk_listeners_growth_payload(
        frames.listeners_df,
        start_year=int(args.start_year),
        current_year_split=int(args.current_year_split),
    )
    write_uk_listeners_growth_js_bundle(out_js, payload)
    n = len(payload["points"])
    print(f"Wrote {out_js} ({n} month(s))")


def _cmd_money_about(args: argparse.Namespace) -> None:
    out_dir = Path(args.out_dir) if args.out_dir else charts_root() / "money_about"
    out_js = Path(args.out_js) if args.out_js else out_dir / "chart-data.js"

    if args.sync_html:
        out_dir.mkdir(parents=True, exist_ok=True)
        if not _ASSET_MONEY_ABOUT_INDEX.is_file():
            raise FileNotFoundError(f"Missing bundled template: {_ASSET_MONEY_ABOUT_INDEX}")
        shutil.copyfile(_ASSET_MONEY_ABOUT_INDEX, out_dir / "index.html")

    frames = load_nuam_parquet(args.parquet)
    payload = build_money_about_payload(
        frames.listeners_df,
        paid_premium_per_1k_streams=float(args.paid_per_1k),
        hist_threshold_usd=float(args.hist_threshold),
        hist_bins=int(args.hist_bins),
        lines_start_month=str(args.lines_start),
        lines_max_artists=int(args.lines_max_artists),
    )
    write_money_about_js_bundle(out_js, payload)
    nlines = len(payload.get("lines", {}).get("series", []))
    print(f"Wrote {out_js} (hist bars + {nlines} line series)")


def _cmd_listeners_dist(args: argparse.Namespace) -> None:
    out_dir = Path(args.out_dir) if args.out_dir else charts_root() / "listeners_dist"
    out_js = Path(args.out_js) if args.out_js else out_dir / "chart-data.js"

    if args.sync_html:
        out_dir.mkdir(parents=True, exist_ok=True)
        if not _ASSET_LISTENERS_DIST_INDEX.is_file():
            raise FileNotFoundError(f"Missing bundled template: {_ASSET_LISTENERS_DIST_INDEX}")
        shutil.copyfile(_ASSET_LISTENERS_DIST_INDEX, out_dir / "index.html")

    frames = load_nuam_parquet(args.parquet)
    payload = build_listeners_dist_payload(frames.listeners_df, bins=int(args.bins))
    write_listeners_dist_js_bundle(out_js, payload)
    nbars = len(payload.get("bars", []))
    print(f"Wrote {out_js} ({payload['totalArtists']} artists, {nbars} histogram bars)")


def main(argv: list[str] | None = None) -> None:
    root = repo_root()
    p = argparse.ArgumentParser(prog="nuam-chart", description="Export NUAM charts to data/charts/.")
    sub = p.add_subparsers(dest="command", required=True)

    m = sub.add_parser("milestones", help="Milestone flower (D3) data + optional HTML sync")
    m.add_argument(
        "--parquet",
        type=Path,
        default=root / "nuam_artists.parquet",
        help="Path to nuam_artists.parquet",
    )
    m.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Chart folder (default: <repo>/data/charts/milestones)",
    )
    m.add_argument(
        "--out-js",
        type=Path,
        default=None,
        help="Output JS path (default: <out-dir>/chart-data.js)",
    )
    m.add_argument(
        "--max-artists",
        type=int,
        default=None,
        metavar="K",
        help="After listener sort, keep only the top K rows (default: all, for rank window in the page)",
    )
    m.add_argument(
        "--shift",
        type=int,
        default=None,
        help="Optional server-side slice start (0-based) after sort — omit to export full range for the UI slider",
    )
    m.add_argument(
        "--n",
        type=int,
        default=None,
        help="Optional server-side slice length (use with --shift) for smaller chart-data.js",
    )
    m.add_argument("--spotify-listeners-min", type=float, default=1_000_000)
    m.add_argument(
        "--min-export-listeners",
        type=float,
        default=1_000,
        help="Export only artists whose peak monthly listeners (max over months) are >= this (use 0 to include everyone)",
    )
    m.add_argument("--quantile", type=float, default=0.995)
    m.add_argument(
        "--sync-html",
        action="store_true",
        help="Copy bundled index.html into out-dir (overwrites if present)",
    )
    m.set_defaults(func=_cmd_milestones)

    lr = sub.add_parser(
        "label-rosters",
        help="All labels: center = catalog size; ticks = pool artists; green if top-rated",
    )
    lr.add_argument(
        "--parquet",
        type=Path,
        default=root / "nuam_artists.parquet",
        help="Path to nuam_artists.parquet",
    )
    lr.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Chart folder (default: <repo>/data/charts/label_rosters)",
    )
    lr.add_argument(
        "--out-js",
        type=Path,
        default=None,
        help="Output JS path (default: <out-dir>/chart-data.js)",
    )
    lr.add_argument("--quantile", type=float, default=0.995)
    lr.add_argument(
        "--listeners-min",
        type=int,
        default=270960,
        help=(
            "Absolute monthly-listeners threshold for a 'top artist' "
            "(default: 270960 ≈ $300 streaming payout). "
            "Set to 0 to fall back to the --quantile-based threshold."
        ),
    )
    lr.add_argument(
        "--min-artists-on-label",
        type=int,
        default=2,
        help="Include labels that sign at least this many distinct top-listener artists (default: 2, matches eda.ipynb > 1)",
    )
    lr.add_argument(
        "--sync-html",
        action="store_true",
        help="Copy bundled index.html into out-dir (overwrites if present)",
    )
    lr.set_defaults(func=_cmd_label_rosters)

    gp = sub.add_parser(
        "genres-popularity",
        help="Genre circle pack (area ∝ popularity; compact d3.pack, padding 0)",
    )
    gp.add_argument(
        "--parquet",
        type=Path,
        default=root / "nuam_artists.parquet",
        help="Path to nuam_artists.parquet",
    )
    gp.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Chart folder (default: <repo>/data/charts/genres_popularity)",
    )
    gp.add_argument(
        "--out-js",
        type=Path,
        default=None,
        help="Output JS path (default: <out-dir>/chart-data.js)",
    )
    gp.add_argument(
        "--metric",
        choices=["listeners_per_artist", "listeners_sum", "artist_count"],
        default="listeners_per_artist",
        help="What drives circle area (default: listeners_per_artist, matches eda.ipynb)",
    )
    gp.add_argument(
        "--top",
        type=int,
        default=0,
        metavar="N",
        help="Keep top N genres by metric after sorting (0 = all; default 0 for on-page LPA band)",
    )
    gp.add_argument(
        "--sync-html",
        action="store_true",
        help="Copy bundled index.html into out-dir (overwrites if present)",
    )
    gp.set_defaults(func=_cmd_genres_pack)

    sd = sub.add_parser(
        "signed-deals",
        help="Signed-deals story: listener histogram, strange-genre pack, top labels bar+line",
    )
    sd.add_argument(
        "--parquet",
        type=Path,
        default=root / "nuam_artists.parquet",
        help="Path to nuam_artists.parquet",
    )
    sd.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Chart folder (default: <repo>/data/charts/signed_deals)",
    )
    sd.add_argument(
        "--out-js",
        type=Path,
        default=None,
        help="Output JS path (default: <out-dir>/chart-data.js)",
    )
    sd.add_argument("--quantile", type=float, default=0.995)
    sd.add_argument(
        "--listeners-min",
        type=int,
        default=270960,
        help=(
            "Absolute monthly-listeners threshold for a 'top-rated label' artist "
            "(default: 270960 ≈ $300 streaming payout). "
            "Set to 0 to fall back to the --quantile-based threshold."
        ),
    )
    sd.add_argument(
        "--min-signings",
        type=int,
        default=2,
        help="Min top-pool artists on a label to count as peer-rated (default 2)",
    )
    sd.add_argument(
        "--strange-max-listeners",
        type=float,
        default=1000,
        help="Peak listeners below this = strange deal (default 1000)",
    )
    sd.add_argument(
        "--label-min-peak-listeners",
        type=float,
        default=10_000,
        help="Bar chart: keep labels with at least one artist at this peak (default 10000)",
    )
    sd.add_argument("--hist-bins", type=int, default=40)
    sd.add_argument("--label-bar-top", type=int, default=0, help="Top N labels by signed count (0 = all top-rated)")
    sd.add_argument(
        "--sync-html",
        action="store_true",
        help="Copy bundled index.html into out-dir (overwrites if present)",
    )
    sd.set_defaults(func=_cmd_signed_deals)

    uk = sub.add_parser(
        "uk-listeners-growth",
        help="Story opener: Σ monthly listeners on NUAM roster by month (2024+)",
    )
    uk.add_argument(
        "--parquet",
        type=Path,
        default=root / "nuam_artists.parquet",
        help="Path to nuam_artists.parquet",
    )
    uk.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Chart folder (default: <repo>/data/charts/uk_listeners_growth)",
    )
    uk.add_argument(
        "--out-js",
        type=Path,
        default=None,
        help="Output JS path (default: <out-dir>/chart-data.js)",
    )
    uk.add_argument("--start-year", type=int, default=2024)
    uk.add_argument(
        "--current-year-split",
        type=int,
        default=2026,
        help="Line color switches for months in this calendar year and later",
    )
    uk.add_argument(
        "--sync-html",
        action="store_true",
        help="Copy bundled index.html into out-dir (overwrites if present)",
    )
    uk.set_defaults(func=_cmd_uk_listeners_growth)

    mo = sub.add_parser(
        "money-about",
        help="Money section: payout histogram + per-artist monthly lines (listener band + hover)",
    )
    mo.add_argument(
        "--parquet",
        type=Path,
        default=root / "nuam_artists.parquet",
        help="Path to nuam_artists.parquet",
    )
    mo.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Chart folder (default: <repo>/data/charts/money_about)",
    )
    mo.add_argument(
        "--out-js",
        type=Path,
        default=None,
        help="Output JS path (default: <out-dir>/chart-data.js)",
    )
    mo.add_argument(
        "--paid-per-1k",
        type=float,
        default=1.33,
        help="Premium USD per 1,000 streams (default 1.33, Ukraine estimate)",
    )
    mo.add_argument(
        "--hist-threshold",
        type=float,
        default=300.0,
        help="Histogram shaded threshold in USD (default 300)",
    )
    mo.add_argument("--hist-bins", type=int, default=72)
    mo.add_argument("--lines-start", type=str, default="2025-01-01")
    mo.add_argument(
        "--lines-max-artists",
        type=int,
        default=0,
        metavar="K",
        help="Cap line series in export (0 = all artists with data in the window; use >0 to shrink chart-data.js)",
    )
    mo.add_argument(
        "--sync-html",
        action="store_true",
        help="Copy bundled index.html into out-dir (overwrites if present)",
    )
    mo.set_defaults(func=_cmd_money_about)

    ld = sub.add_parser(
        "listeners-dist",
        help="Log-transformed listener distribution histogram with interactive top-N% highlight",
    )
    ld.add_argument(
        "--parquet",
        type=Path,
        default=root / "nuam_artists.parquet",
    )
    ld.add_argument("--out-dir", type=Path, default=None)
    ld.add_argument("--out-js",  type=Path, default=None)
    ld.add_argument("--bins", type=int, default=30, help="Number of histogram bins (default 30)")
    ld.add_argument(
        "--sync-html",
        action="store_true",
        help="Copy bundled index.html into out-dir (overwrites if present)",
    )
    ld.set_defaults(func=_cmd_listeners_dist)

    args = p.parse_args(argv)
    args.func(args)


def milestones_legacy_main() -> None:
    """Entry point for nuam-milestones-export (forwards to 'milestones' subcommand)."""
    main(["milestones", *sys.argv[1:]])


if __name__ == "__main__":
    main()
