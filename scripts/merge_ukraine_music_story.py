#!/usr/bin/env python3
"""Merge standalone NUAM chart pages into ukraine-music-story/index.html (inline, dark theme)."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CH = ROOT / "data" / "charts"
OUT = CH / "ukraine-music-story" / "index.html"

CHARTS: list[tuple[str, str, str]] = [
    ("uk_listeners_growth", "uklg", "nuam-b-uklg"),
    ("listeners_dist", "ld", "nuam-b-ld"),
    ("label_rosters", "lr", "nuam-b-lr"),
    ("milestones", "ms", "nuam-b-ms"),
    ("genres_popularity", "gp", "nuam-b-gp"),
    ("signed_deals", "sd", "nuam-b-sd"),
    ("money_about", "ma", "nuam-b-ma"),
]


def extract_style(html: str) -> str:
    m = re.search(r"<style>(.*?)</style>", html, re.DOTALL)
    return m.group(1).strip() if m else ""


def extract_body_fragment(html: str) -> str:
    m = re.search(r"<body>(.*?)</body>", html, re.DOTALL)
    if not m:
        return ""
    frag = m.group(1)
    frag = re.sub(r"<script\b[^>]*>.*?</script>", "", frag, flags=re.DOTALL | re.IGNORECASE)
    frag = re.sub(
        r"<script\b[^>]*src=[^>]+>\s*</script>", "", frag, flags=re.DOTALL | re.IGNORECASE
    )
    return frag.strip()


def extract_inline_script(html: str) -> str:
    scripts = re.findall(r"<script>(.*?)</script>", html, re.DOTALL)
    for s in scripts:
        if "d3" in s and ("function" in s or "=>" in s):
            return s.strip()
    return ""


def prefix_ids(html: str, pfx: str, ids: list[str]) -> str:
    for i in sorted(ids, key=len, reverse=True):
        ip = f"{pfx}-{i}"
        html = re.sub(rf'\bid="{re.escape(i)}"', f'id="{ip}"', html)
        html = re.sub(rf'\bfor="{re.escape(i)}"', f'for="{ip}"', html)
        html = re.sub(rf'aria-labelledby="{re.escape(i)}"', f'aria-labelledby="{ip}"', html)
        html = re.sub(rf"getElementById\(\s*['\"]{re.escape(i)}['\"]\s*\)", f'getElementById("{ip}")', html)
        html = re.sub(rf'd3\.select\(\s*["\']#{re.escape(i)}["\']\s*\)', f'd3.select("#{ip}")', html)
        html = re.sub(rf'#{re.escape(i)}\b', f"#{ip}", html)
    return html


def scope_css(css: str, scope: str, pfx: str, ids: list[str]) -> str:
    css = css.replace(":root", scope, 1)
    css = re.sub(
        r"^\s*\*\s*\{\s*box-sizing:\s*border-box;\s*\}",
        f"{scope}, {scope} * {{ box-sizing: border-box; }}",
        css,
        flags=re.MULTILINE,
    )
    # 'body {' alone → component root class
    css = re.sub(r"^\s*body\s*\{", f"{scope} {{", css, flags=re.MULTILINE)
    # 'body .selector' used as a descendant prefix → 'scope .selector'
    # (source files use `body .pack-host` etc. so they also work standalone)
    css = re.sub(r"(?m)^(\s*)body\s+(?!\{)", rf"\1{scope} ", css)
    for i in sorted(ids, key=len, reverse=True):
        css = re.sub(rf"#{re.escape(i)}\b", f"#{pfx}-{i}", css)
    return css


def chart_css_preserve_dark(css: str) -> str:
    """Keep original chart palette (standalone pages are already dark)."""
    return css


def patch_script(script: str, block_id: str) -> str:
    script = script.replace(
        "getComputedStyle(document.documentElement)",
        "getComputedStyle(root)",
    )
    script = re.sub(
        r"\(function\s*\(\)\s*\{\s*",
        '(function () {\n  const root = document.getElementById("' + block_id + '");\n  ',
        script,
        count=1,
    )
    return script


def strip_regenerate_notes(frag: str) -> str:
    # Paragraph that is only Regenerate / CLI instructions
    frag = re.sub(
        r'<p class="note">\s*Regenerate:.*?</p>\s*',
        "",
        frag,
        flags=re.DOTALL,
    )
    # Trailing "Regenerate: …" clause inside a longer <p class="note">…</p>
    frag = re.sub(
        r'(<p class="note">[\s\S]*?)\s*Regenerate:[\s\S]*?(</p>)',
        r"\1\2",
        frag,
    )
    return frag


def collect_ids(html: str) -> list[str]:
    return sorted(set(re.findall(r'\bid="([^"]+)"', html)))


def main() -> None:
    prose_head = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>The Unlikely Odds of Making it Big in Ukraine — a NUAM data story</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,500;0,9..144,700;1,9..144,500&family=Source+Sans+3:ital,wght@0,400;0,600;0,700;1,400&display=swap" rel="stylesheet" />
  <style>
"""

    story_css = """
    :root {
      --paper: #0a0a0a;
      --paper2: #121212;
      --ink: #e8e8e8;
      --ink-muted: #9aa0a6;
      --rule: #2a2a2a;
      --accent: #c084fc;
      --accent-soft: rgba(192, 132, 252, 0.13);
      --max-prose: 40rem;
      --max-chart: 72rem;
      --font-serif: "Fraunces", Georgia, "Times New Roman", serif;
      --font-sans: "Source Sans 3", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
    }
    * { box-sizing: border-box; }
    html { scroll-behavior: smooth; color-scheme: dark; }
    body {
      margin: 0;
      color: var(--ink);
      background: var(--paper);
      font-family: var(--font-sans);
      font-size: 1.05rem;
      line-height: 1.65;
    }
    .ambient {
      position: fixed;
      inset: 0;
      pointer-events: none;
      z-index: 0;
      background:
        radial-gradient(ellipse 80% 50% at 50% -10%, rgba(100, 40, 180, 0.30), transparent 55%),
        radial-gradient(ellipse 55% 40% at 100% 20%, rgba(251, 191, 36, 0.07), transparent 45%),
        var(--paper);
    }
    .story { position: relative; z-index: 1; }
    .story-hero {
      padding: clamp(2.5rem, 8vw, 5rem) 1.5rem clamp(2rem, 5vw, 3.5rem);
      text-align: center;
      border-bottom: 1px solid var(--rule);
      background: linear-gradient(180deg, var(--paper2) 0%, var(--paper) 100%);
    }
    .story-hero .kicker {
      font-family: var(--font-sans);
      font-size: 0.78rem;
      font-weight: 600;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      color: var(--accent);
      margin: 0 0 1rem;
    }
    .story-hero h1 {
      font-family: var(--font-serif);
      font-size: clamp(1.85rem, 5vw, 2.75rem);
      font-weight: 700;
      line-height: 1.12;
      letter-spacing: -0.02em;
      max-width: 18ch;
      margin: 0 auto 1rem;
    }
    .story-hero .lede {
      max-width: var(--max-prose);
      margin: 0 auto;
      font-size: 1.08rem;
      color: var(--ink-muted);
      line-height: 1.6;
    }
    .prose-block {
      max-width: var(--max-prose);
      margin: 0 auto;
      padding: clamp(2rem, 5vw, 3rem) 1.5rem;
    }
    .prose-block h2 {
      font-family: var(--font-serif);
      font-size: clamp(1.35rem, 3.2vw, 1.75rem);
      font-weight: 700;
      line-height: 1.2;
      margin: 0 0 1rem;
      letter-spacing: -0.02em;
    }
    .prose-block h3 {
      font-family: var(--font-serif);
      font-size: 1.15rem;
      font-weight: 700;
      margin: 2rem 0 0.75rem;
    }
    .prose-block p { margin: 0 0 1rem; }
    .prose-block p:last-child { margin-bottom: 0; }
    .prose-block strong { font-weight: 700; color: var(--ink); }
    .prose-block ol, .prose-block ul { margin: 0 0 1rem; padding-left: 1.35rem; }
    .prose-block li { margin-bottom: 0.5rem; }
    .prose-block li::marker { color: var(--ink-muted); }
    .prose-block a {
      color: var(--accent);
      text-decoration-thickness: 1px;
      text-underline-offset: 3px;
    }
    .prose-block code {
      font-size: 0.92em;
      padding: 0.12em 0.4em;
      border-radius: 4px;
      background: #1a1a1a;
      color: #d4d4d4;
      border: 1px solid #333;
    }
    .section-label {
      font-size: 0.72rem;
      font-weight: 700;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: var(--ink-muted);
      margin-bottom: 0.35rem;
    }
    .chart-section { padding: 0 0 clamp(2rem, 5vw, 3.5rem); }
    .chart-dek {
      max-width: var(--max-prose);
      margin: 0 auto 1rem;
      padding: 0 1.5rem;
      font-size: 0.95rem;
      color: var(--ink-muted);
      line-height: 1.5;
    }
    .chart-frame {
      max-width: var(--max-chart);
      margin: 0 auto;
      padding: 0 1rem 0.5rem;
    }
    .chart-frame-inner {
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 12px 40px rgba(0, 0, 0, 0.45);
      border: 1px solid #1f1f1f;
    }
    .nuam-ch {
      position: relative;
    }
    .story-aside {
      max-width: var(--max-prose);
      margin: 1.5rem auto 0;
      padding: 1.1rem 1.25rem;
      background: var(--accent-soft);
      border-left: 3px solid var(--accent);
      border-radius: 0 8px 8px 0;
      font-size: 0.98rem;
      color: var(--ink-muted);
    }
    .story-aside p { margin: 0 0 0.75rem; }
    .story-aside p:last-child { margin-bottom: 0; }
    .sources-footer {
      max-width: var(--max-prose);
      margin: 0 auto;
      padding: 2.5rem 1.5rem 4rem;
      border-top: 1px solid var(--rule);
      font-size: 0.88rem;
      color: var(--ink-muted);
    }
    .sources-footer h2 {
      font-family: var(--font-serif);
      font-size: 1.1rem;
      margin: 0 0 0.75rem;
      color: var(--ink);
    }
    .sources-footer ul { margin: 0; padding-left: 1.2rem; }
    .sources-footer li { margin-bottom: 0.4rem; }
    .sources-footer a { color: var(--accent); }
    .note-callout {
      max-width: var(--max-prose);
      margin: 1.25rem auto 0;
      padding: 0 1.5rem;
      font-size: 0.9rem;
      color: var(--ink-muted);
      font-style: italic;
    }
"""

    chart_css_parts: list[str] = []
    chart_blocks: list[str] = []

    for folder, pfx, block_id in CHARTS:
        path = CH / folder / "index.html"
        html = path.read_text(encoding="utf-8")
        ids = collect_ids(html)
        scope = f".nuam-ch-{pfx}"
        css = extract_style(html)
        css = scope_css(css, scope, pfx, ids)
        css = chart_css_preserve_dark(css)
        chart_css_parts.append(f"    /* === {folder} === */\n{css}\n")

        frag = extract_body_fragment(html)
        frag = strip_regenerate_notes(frag)
        frag = prefix_ids(frag, pfx, ids)
        script = extract_inline_script(html)
        script = prefix_ids(script, pfx, ids)
        script = patch_script(script, block_id)

        chart_blocks.append(
            f"""      <div class="chart-frame"><div class="chart-frame-inner">
        <div class="nuam-ch nuam-ch-{pfx}" id="{block_id}">
{frag}
        <script>{script}</script>
        </div>
      </div></div>"""
        )

    data_scripts = "\n".join(
        f'  <script src="../{folder}/chart-data.js"></script>' for folder, _, _ in CHARTS
    )

    middle = (
        """
  </style>
"""
        + data_scripts
        + """
  <script src="https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js"></script>
</head>
<body>
  <div class="ambient" aria-hidden="true"></div>
  <article class="story">
    <header class="story-hero">
      <p class="kicker">Ukrainian music market · NUAM</p>
      <h1>The unlikely odds of making it big in Ukraine</h1>
      <p class="lede">
        How listening stacks up on Spotify, which labels cluster serious reach, what “career signals” look like in the data, where genres lean, and what early label appearances can mean — drawn from NUAM’s public catalogue.
      </p>
    </header>

    <section class="chart-section" aria-labelledby="sec-listeners">
      <div class="prose-block" style="padding-bottom:1rem">
        <p class="section-label">Section 1 · Time series</p>
        <h2 id="sec-listeners">Total listeners over time (2024–2026)</h2>
      </div>
      <p class="chart-dek">
        Summed monthly listeners across artists in NUAM. The vertical scale is trimmed to the visible range (not zero); month-to-month change is labeled on the chart.
      </p>
"""
    )

    s1 = chart_blocks[0]
    s2_ld = chart_blocks[1]

    listeners_followup = """
      <div class="prose-block">
        <p>
          The chart illustrates the growth in total listeners in the Ukrainian music scene from 2024 to early 2026, based on data from <strong>NUAM (New UA Music)</strong> — a leading Ukrainian online music resource. The dataset, with a snapshot from April 2026, shows a steady rise in listener engagement, reflecting the ongoing transformation of the local music market.
        </p>
        <p>
          <a href="https://www.nuam.club/stat">NUAM</a> is one of the largest publicly accessible databases of Ukrainian musicians, maintaining detailed profiles of tens of thousands of artists and their releases. It allows users to explore and filter music by genre, popularity, release date, and more. The platform also provides playlists, yearly charts, and genre collections. Through its web app, <strong>NUAM Base</strong>, it offers analytics for both artists and fans.
        </p>
        <p>In recent months, the number of listeners has been consistently growing. Several factors may explain this trend:</p>
        <ol>
          <li><strong>Increasing number of artists.</strong> As more artists join the scene and release music, the total number of listeners naturally increases. Since NUAM began tracking the platform, the number of active Ukrainian musicians has surged, with over 16,500 artists and more than 9,200 releasing music in 2025 alone.</li>
          <li><strong>Aggregation across artists.</strong> The listener count aggregates data across all artists, which means that if the same listener discovers multiple artists, this could inflate the total listener count.</li>
          <li><strong>Genuine growth in audience.</strong> If the listener bases of artists significantly do not overlap, the chart might reflect real growth in the number of unique listeners.</li>
        </ol>
        <p>
          Regardless of these technical nuances, all signs point to a <strong>growing interest in local music</strong>. The rise of streaming platforms such as <a href="https://www.spotify.com/">Spotify</a> and <a href="https://www.apple.com/apple-music/">Apple Music</a> has played a significant role in amplifying this growth.
        </p>
      </div>
    </section>

    <div class="prose-block">
      <p>
        The Ukrainian music market is relatively young and has undergone dramatic transformations over the past century. Under the Soviet Union, Ukrainian culture — including music — existed within a framework that often favored Russian‑language cultural production and tightly controlled local cultural expression. After independence in 1991, Ukrainian pop and contemporary music gradually revived, but Russian‑language songs remained common in the market because they reached larger audiences across the post‑Soviet space.
      </p>
      <p>
        In the 2000s and early 2010s, Ukrainian artists increasingly built local followings through domestic festivals and television, and social media expanded opportunities for promotion and audience building. However, many musicians still recorded in Russian to gain wider reach within the larger Russian‑speaking market.
      </p>
      <p>
        <strong>The turning point came after 2014</strong> and <strong>especially after Russia’s full‑scale invasion in February 2022</strong>. Following these events, both cultural identity and language began reshaping the industry — Ukrainian‑language music surged in popularity and became mainstream. By 2025, Ukrainian‑language content accounted for a majority of music consumption in Ukraine, up significantly from before the invasion.
      </p>
      <p>
        At the same time, new legislation in 2022 restricted public performance and broadcast of many Russian‑language songs and increased Ukrainian content quotas on radio and television, further accelerating the shift toward Ukrainian music as the dominant cultural force.
      </p>
      <p>
        Despite this cultural revitalization, <strong>economic realities for most musicians remain tough</strong>. Earlier research showed that for over four‑fifths of Ukrainian artists, income from music alone often does not cover basic living costs, highlighting the challenges of professional success within the local market.
      </p>
      <p>
        Today, the Ukrainian music scene is experiencing a renaissance shaped by war, national identity, digital platforms, and evolving audience preferences. This period — from 2022 through 2026 — represents a generation‑defining decade for artists striving to break through in a market that’s simultaneously becoming more local and more global.
      </p>
    </div>

    <section class="chart-section" aria-labelledby="sec-distribution">
      <div class="prose-block" style="padding-bottom:1rem">
        <p class="section-label">Section 2 · Distribution</p>
        <h2 id="sec-distribution">How many listeners do Ukrainian artists have?</h2>
      </div>
      <div class="prose-block">
        <p>
          The distribution is sharply skewed. A large share of artists in the NUAM catalogue attract only a handful of streams; the curve drops off steeply, and only a small slice ever breaks through to significant listener counts. The histogram below makes that shape visible — drag the slider to see where any top‑percentile cutoff lands in actual listener count terms.
        </p>
        <p>
          For the analysis in this piece, we focus on artists who’ve crossed the <strong>400,000 monthly listener</strong> mark — a threshold that puts them among the most visible acts in the Ukrainian market today.
        </p>
      </div>
      <p class="chart-dek">
        Log-scaled histogram of monthly listeners across the full NUAM catalogue. Drag the blue band to see where any top-N% cutoff falls in real listener count.
      </p>
"""

    dist_close = """
    </section>

    <section class="chart-section" aria-labelledby="sec-labels">
      <div class="prose-block" style="padding-bottom:1rem">
        <p class="section-label">Section 3 · Labels</p>
        <h2 id="sec-labels">Top‑rated Ukrainian labels</h2>
      </div>
      <p class="chart-dek">
        Each glyph is a label: the center scales with how many artists sit on that imprint; green marks labels with several high-listener acts. Legend and sort sit with the graphic.
      </p>
"""

    s3 = chart_blocks[2]

    block4 = """
      <div class="prose-block">
        <p>
          For many artists, record labels can be an important step in building a professional career in music. In the global industry, traditional label contracts are legal agreements in which an artist typically grants a label <strong>exclusive rights</strong> to record, market and distribute their music for a defined period of time, often tied to multiple albums or defined contract terms; during that period, artists generally cannot release music through other labels without the original label’s permission.
        </p>
        <p>
          In Ukraine, however, the label ecosystem operates <strong>differently from these dominant international models</strong>. Many local labels function less like exclusive commercial partners and more like <strong>supportive artistic communities</strong> — offering promotion, distribution help, curated releases, shared networks and collaborative audiences without strictly locking artists into traditional exclusivity. Because most agreements are private and governed by nondisclosure clauses, there is no single public standard defining whether an artist is fully bound to one label or free to work with others. Nonetheless, many Ukrainian labels emphasize <strong>support and exposure</strong> — assisting with distribution, sharing audiences between their roster, and sometimes coordinating live events or promotional opportunities — rather than imposing hard legal exclusivity.
        </p>
        <p>
          There are labels that have become known for <strong>creating successful artists</strong> and pushing them into larger markets. We define a <strong>top‑rated label</strong> as one that has at least <strong>two artists who each reached 270,960+ monthly Spotify listeners</strong> — roughly <strong>$300</strong> in estimated streaming payout per artist.
        </p>
        <p>A few stand out from the rest:</p>
        <ul>
          <li><strong>ENKO Music</strong> — pop releases; artists such as Jerry Hail, Alyona Alyona, KALUSH, YAKTAK, and Шугар; strong Spotify presence.</li>
          <li><strong>PLAN</strong> — very high signing volume (<strong>379 deals in two years</strong>); mainstream breakout still an open story.</li>
          <li><strong>UA Phonk Community</strong> — community‑driven, phonk‑focused; high performers inside a niche.</li>
        </ul>
        <p>Top‑rated labels on NUAM also include, among others:</p>
        <ul>
          <li>BEST MUSIC</li>
          <li>YATOMI HOUSE RECORDS</li>
          <li>Comp Music</li>
          <li>МУЛЬТИТРЕК</li>
          <li>pomitni</li>
          <li>CVRSED</li>
          <li>House of Culture and Дім Звукозапису</li>
          <li>Mayak Music</li>
          <li>SUNDAY</li>
          <li>TAVR Records</li>
          <li>AURORA RECORDS</li>
          <li style="color:#9aa0a6;list-style:none;padding-top:0.25rem">— and 13 more labels visible on the chart above</li>
        </ul>
        <p>
          <strong>pomitni</strong> has only been active since <strong>2022</strong> but is already growing quickly, with artists like Nadya Dorofeyeva and Кажанна. Getting a deal with one of these <strong>26 top‑rated labels</strong> is both an opportunity and a signal that an artist is on a credible path.
        </p>
      </div>
    </section>

    <section class="chart-section" aria-labelledby="sec-milestones">
      <div class="prose-block" style="padding-bottom:1rem">
        <p class="section-label">Section 4 · Careers</p>
        <h2 id="sec-milestones">How mature is Ukraine’s music market?</h2>
      </div>
      <div class="prose-block">
        <p>
          To get a sense of what it really means for an artist to move from early attention to a career with some traction,
          we took inspiration from a fascinating visual essay by
          <a href="https://pudding.cool/2022/07/tiktok-story/"><em>The Pudding</em></a>.
          In that piece, the authors looked at a group of artists who went viral on TikTok and checked how many of them
          hit a set of real‑world milestones that often come with “making it” — things like charting on Spotify,
          playing live shows, signing record deals, gaining followers on social platforms, or reaching 1 million monthly listeners.
        </p>
        <p>
          We wanted to adapt that idea for Ukrainian artists, but we also only have certain kinds of data available for analysis.
          So instead of tracking eight different milestones, we picked a handful that are meaningful signals for where an artist
          stands today and that we can actually measure:
        </p>
        <ul>
          <li><strong>Signed with a top‑rated label</strong> — a signal that other music professionals see promise in your work and that you’ve got access to support from experienced people in the industry — from wider distribution to connections that can help your career grow.</li>
          <li><strong>Spotify profile</strong> — you’re available to listeners everywhere in the world</li>
          <li><strong>Instagram account</strong> — you have a social presence where fans can connect with you</li>
          <li><strong>Debuted in the last three years</strong> — you’re part of the currently rising cohort of musicians</li>
          <li><strong>Spotify monthly listeners ≥ 1 million</strong> — a clear indicator of audience reach beyond local borders</li>
          <li><strong>Earned over $300</strong> — showing that your music is generating real streaming income (not just plays)</li>
        </ul>
      </div>
      <p class="chart-dek">
        Each tile is one artist. Triangular rays are five catalogue signals; the number in the center is how many are true. A gold border marks Russian-language rows in NUAM. Use the listener band to narrow who appears in the grid.
      </p>
"""

    s5 = chart_blocks[3]

    block6 = """
      <div class="prose-block">
        <p>
          Artists in our listener band view range from about ~240 000 up to around ~1.8 million monthly listeners —
          and that difference tells a story.
        </p>
        <p>
          To make this more interactive for readers, our dynamic visualization lets you configure the listener band yourself.
          The view highlighted here shows where
          <a href="https://open.spotify.com/search/Ziferblat/artists" target="_blank" rel="noopener"><strong>Ziferblat</strong></a>
          sits in the landscape — as a recent Ukrainian representative at the Eurovision Song Contest 2025 with their song
          “Bird of Pray.”
        </p>
        <p>
          By comparison,
          <a href="https://open.spotify.com/search/Go_A/artists" target="_blank" rel="noopener"><strong>Go_A</strong></a>,
          who represented Ukraine at Eurovision in 2021, followed a different growth path. Though they had strong international
          attention, their listener growth under the conditions of the early 2020s looks different in our data than
          Ziferblat’s during the broader surge in global interest in Ukrainian music after 2022.
        </p>
        <p>
          Another interesting pattern in the chart is
          <a href="https://open.spotify.com/search/Carpetman/artists" target="_blank" rel="noopener"><strong>Carpetman</strong></a>,
          who sits to the left of Ziferblat — meaning he has more monthly listeners in this view. Before launching his
          solo career, Carpetman was part of
          <a href="https://open.spotify.com/search/Kalush%20Orchestra/artists" target="_blank" rel="noopener"><strong>Kalush Orchestra</strong></a>,
          the Ukrainian group that won the Eurovision Song Contest 2022, and both Carpetman and Kalush Orchestra appear
          in our listener band — though Kalush Orchestra sits with a significantly lower listener rate than Carpetman’s
          current solo numbers, highlighting how his recent international growth stands apart.
        </p>

      </div>
    </section>

    <section class="chart-section" aria-labelledby="sec-genres">
      <div class="prose-block" style="padding-bottom:1rem">
        <p class="section-label">Section 5 · Genres</p>
        <h2 id="sec-genres">Genres</h2>
      </div>
      <p class="chart-dek">
        Circle area reflects the chosen size metric from NUAM; color shows listeners per artist on a logarithmic scale. The gradient key and range sliders sit with the pack.
      </p>
"""

    s7 = chart_blocks[4]

    block8 = """
      <div class="prose-block">
        <p>
          I also looked at music from the listeners’ side — in particular <strong>which genres attract the most listeners</strong> and which ones are <em>under‑represented</em> compared to their audience size. Not every genre is proportional: some styles have way more ears listening than artists making that music. Below are genres that <strong>have a lot of listeners but fewer artists creating in them</strong> — one way to spot opportunities on the scene.
        </p>
        <p>
          One of the most listened‑to but under‑represented genres on our charts is <strong>Ukrainian phonk</strong> — a style rooted in phonk and internet‑driven beats that’s finding real traction with listeners even though there aren’t many artists producing it. This means demand far outpaces the number of creators right now, so phonk shows up strong in listenership compared to its small roster.
        </p>
        <p>
          By contrast, well‑known genres like <strong>rap</strong> have enough artists to satisfy audience demand, so listener attention and streams are spread more evenly across performers and competition is higher in that field.
        </p>
        <p>
          At the same time, experimental corners and classic styles (like <strong>emo, opera, blues</strong>) don’t have a wide market in Ukraine; they’re interesting to specific listeners but don’t attract large audiences here, so their growth potential is limited in this context.
        </p>
        <aside class="story-aside">
          <p>
            Ukrainian phonk grew out of the global phonk wave — Memphis‑rooted loops and trap energy that blew up on SoundCloud and short‑video feeds — and took on a local accent through collectives such as <strong>Ukrainian Phonk Community</strong>. Today it’s often independent, bass‑heavy, and unmistakably “late night internet,” with listeners both at home and abroad.
          </p>
        </aside>
      </div>
    </section>

    <section class="chart-section" aria-labelledby="sec-deals">
      <div class="prose-block" style="padding-bottom:1rem">
        <p class="section-label">Section 6 · Signings</p>
        <h2 id="sec-deals">Strange deals</h2>
      </div>
      <p class="chart-dek">
        Roster growth, then a peak-listener histogram (orange band), a genre pack for the low-listener signing subset, and label totals — read as one continuous thread.
      </p>
"""

    s9 = chart_blocks[5]
    s10 = chart_blocks[6]

    # Strange-deals prose closes section 6; must come *after* s9 (chart follows chart-dek).
    block_deals_prose = r"""
      <div class="prose-block">
        <p>
          Have you noticed the small details on the chart about signed deals? We definitely did.
        </p>
        <p>
          Some of the deals you see are what we call <strong>“zero‑shot” deals</strong> — an artist signs with a label and releases music with no real prior background or track record on the platform. It’s a blunt metaphor, but it gets the idea across.
        </p>
        <p>
          That does not prove the contract closed at that instant; it shows how often the <strong>first NUAM snapshot on a top‑rated label</strong> still sits in a low‑listener band — worth contrasting with majors that tend to show up after streaming scale. The histogram, genre pack, and label bars in the chart above are there to explore that tail.
        </p>
      </div>
    </section>

"""

    block_money = """
    <section class="chart-section" aria-labelledby="sec-money">
      <div class="prose-block" style="padding-bottom:1rem">
        <p class="section-label">Section 7 · Money</p>
        <h2 id="sec-money">Where's the money, Lebowski?</h2>
      </div>
      <div class="prose-block">
        <p>
          Listener counts do not translate directly into bank deposits. In the last couple of years, trade press and artist statements have often linked the same frustration to two threads:
          <strong>per‑stream payouts that stay small</strong> for many acts, and worry that <strong>AI‑generated or bulk‑uploaded catalog</strong> could dilute attention (and, indirectly, how royalty pools are shared)—part of the backdrop to <strong>high‑profile pullbacks or threats to leave Spotify</strong> that surfaced around 2024–2026. None of that shows up line‑by‑line in NUAM; it is context for why “streams up” and “rent paid” are different questions.
        </p>
        <p>
          The views below apply one <strong>Ukraine premium‑stream shortcut</strong> (~$1.33 per 1,000 paid streams, from third‑party royalty tables such as Dynamoi)
          to <strong>each month in the NUAM export</strong>. That yields a rough <em>lower‑bound style</em> estimate — not an official Spotify statement, and not a split between free and premium plays.
        </p>
        <p>
          The <strong>histogram</strong> doesn’t ask about theory or technical charts — it <strong>reveals how streaming money is actually distributed among artists</strong>. It shows the number of artists earning at each level of total estimated payout from streams, and one thing is clear at a glance: <strong>most artists aren’t making enough to live on</strong>. Approximately <strong>93 % of artists receive less than $300</strong> in total payouts from streaming alone — meaning most have to work full‑time jobs alongside their music.
        </p>
        <p>
          Below that, we’ve treated each artist’s payout trends like a <strong>stock performance chart</strong>, because for many musicians streaming income <em>is like an investment in their own career</em>. You can see how their estimated monthly earnings change over time. If you type, for example, “Кажанна,” you’ll see her journey: from a relatively underpaid artist to one of the rare few who crossed the $300 boundary with her hit <em>“Boy.”</em> Her line rises just like a breakout stock — showing how a viral moment can change an artist’s income dynamics.
        </p>
      </div>
      <p class="chart-dek">
        Log-scaled payout histogram with a sub-$300 band; interactive monthly payout lines with a peak-listener range (min/max) and hover for exact month estimates.
      </p>
"""

    block_money_close = """
      <div class="prose-block" style="margin-top:1.5rem">
        <h3 id="sec-royalties">Spotify royalty rate estimates for Ukraine (Dec&nbsp;2025)</h3>
        <p>According to <a href="https://dynamoi.com/data/royalties/spotify/ua">Dynamoi</a> data, Spotify pays roughly:</p>
        <ul>
          <li><strong>~$1.33 per 1,000 paid (premium) streams</strong> in Ukraine</li>
          <li><strong>~$0.35 per 1,000 free / ad‑supported streams</strong> in Ukraine</li>
        </ul>
        <p class="note-callout" style="padding:0;margin-top:0.5rem">
          These numbers come from a royalty dataset, not an official Spotify payout table — treat them as a market estimate. Lower local subscription prices and ad revenue often mean smaller per‑stream rates than in larger markets.
        </p>
      </div>
    </section>

"""

    article_end = r"""    <footer class="sources-footer">
      <h2>Sources &amp; references</h2>
      <ul>
        <li><a href="https://www.nuam.club/stat">NUAM — statistics and catalog</a> (data source for all graphics)</li>
        <li><a href="https://pudding.cool/2022/07/tiktok-story/">The Pudding — emerging artists on TikTok</a> (visual essay reference for milestones)</li>
        <li><a href="https://dynamoi.com/data/royalties/spotify/ua">Dynamoi — Spotify Ukraine royalty estimates</a></li>
        <li><a href="https://www.spotify.com/">Spotify</a> · <a href="https://www.apple.com/apple-music/">Apple Music</a></li>
      </ul>
    </footer>
  </article>
"""

    tail2 = """
</body>
</html>
"""

    # Each chart block follows its section chart-dek; prose (if any) follows the chart inside the same section.
    full = (
        prose_head
        + story_css
        + "".join(chart_css_parts)
        + middle
        + s1
        + listeners_followup
        + s2_ld
        + dist_close
        + s3
        + block4
        + s5
        + block6
        + s7
        + block8
        + s9
        + block_deals_prose
        + block_money
        + s10
        + block_money_close
        + article_end
        + tail2
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(full, encoding="utf-8")
    print("Wrote", OUT)


if __name__ == "__main__":
    main()
