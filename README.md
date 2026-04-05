# NUAM scraper — data story tooling (Ukraine)

This project supports a **long, visual data story** in the spirit of [The Pudding — *The Unlikely Odds of Making it Big on TikTok*](https://pudding.cool/2022/07/tiktok-story/): scrolling narrative, clear milestones, and explorable graphics. The **Ukrainian edition** is framed around making it on the **local music scene**; working title: **The Unlikely Odds of Making it Big on Ukraine**.

## Data source

Public statistics and catalog context come from **NUAM** (*Нова українська музика*):

- [https://www.nuam.club/stat](https://www.nuam.club/stat) — statistical overview of the Ukrainian music scene (and linked NUAM databases).

This repository **scrapes and normalizes** NUAM sheet/catalog data (artists, milestones, listener history) for analysis and for chart exports—not a mirror of the whole NUAM site.

## Top-rated labels — how we drew the line

For the essay we wanted a plain-language rule: when does an imprint look like more than a one-off association with a big act? The charts and the “peer label” milestone use the same preprocessing.

**First, we fix a listener bar using the freshest month in the scrape.** We take every artist’s **monthly** Spotify listener count in that **reference month** and compute a high quantile of that snapshot (by default the **99.5th percentile**). We then round that value **up to the next hundred thousand** listeners. That yields a single cutoff—easy to repeat and to explain—anchored in “where the head of the Ukrainian scene sits right now” rather than in a hand-picked number.

**Then we form a pool of “high-listener” artists.** Anyone who **at least once** in our listener history reaches or clears that monthly cutoff counts in the pool. (The cutoff is calibrated on the latest month; eligibility still uses the full history we exported, so a career peak in an earlier month still qualifies.)

**Finally, a label is “top-rated” for the label-roster view (green glyph) when NUAM lists at least two distinct artists from that pool on the same imprint**—by default **two** or more, matching the idea in the notebook that a single overlap is fragile but a pair starts to look like a real cluster. You can change the quantile or the minimum count on the CLI (`nuam-chart label-rosters --quantile`, `--min-artists-on-label`); the milestone export uses the same quantile for building the pool that feeds the peer-label signal.

Every label in NUAM still appears in the roster chart; gray glyphs are simply “not top-rated” under this rule, even when the center is large because the catalog lists many artists on that name.

## What lives here

- **Python package** `nuam_scraper`: HTTP scrape → typed rows → Parquet (and related prep).
- **Charts**: milestone “sun” (D3), label roster ticks, and a **genre popularity** circle pack—static `index.html` + `chart-data.js` per view.
- **Notebooks**: exploratory analysis (`notebooks/`).

## Charts

- **Milestones** (`data/charts/milestones/`): six-signal sun (triangular rays).  
- **Label rosters** (`data/charts/label_rosters/`): **every** NUAM label; **center size and number** = artists on that label; **ticks** = high-listener-pool artists on the imprint; **green** = top-rated (definition in the section *Top-rated labels — how we drew the line*), **gray** otherwise.
- **Genres popularity** (`data/charts/genres_popularity/`): **circle pack** — **area ∝** export metric (default listeners per artist); **dual slider** (log-scaled listeners/artist) chooses which genres are packed; **d3.pack padding 0** for tight clusters. Default export is **all genres** (`--top 0`). The chart footnote links the R [packcircles](https://www.r-bloggers.com/2017/04/packcircles-version-0-2-0-released/) approach as a related reference.

Regenerate (and optionally sync HTML from bundled templates):

```bash
uv sync
uv run nuam-chart milestones
uv run nuam-chart label-rosters
uv run nuam-chart genres-popularity
# optional: overwrite pages from package templates
uv run nuam-chart milestones --sync-html
uv run nuam-chart label-rosters --sync-html
uv run nuam-chart genres-popularity --sync-html
```

The milestone page explains how to read the glyph and cites NUAM and The Pudding reference piece in-page.

## Scrape CLI

```bash
uv run nuam-scrape --help
```

(Network access and any credentials follow your local `.env` / settings as implemented in `nuam_scraper`.)

## Requirements

Python **3.12+**, dependencies in `pyproject.toml` / `uv.lock`.
