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
    .story-byline {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.55rem;
      margin: 1rem auto 0;
      font-family: var(--font-sans);
      font-size: 0.8rem;
      color: var(--ink-muted);
      opacity: 0.6;
    }
    .story-byline img {
      width: 22px;
      height: 22px;
      border-radius: 50%;
      object-fit: cover;
      vertical-align: middle;
      opacity: 0.8;
    }
    .story-byline a { color: inherit; text-decoration: none; border-bottom: 1px dotted currentColor; }
    .story-byline a:hover { opacity: 1; }
    .story-byline .sep { opacity: 0.4; }
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
    sup.ref a { color: var(--accent); font-size: 0.75em; text-decoration: none; }
    sup.ref a:hover { text-decoration: underline; }
    .history-spoiler {
      border: 1px solid rgba(255,255,255,0.1);
      border-radius: 8px;
      overflow: hidden;
    }
    .history-spoiler summary {
      cursor: pointer;
      padding: 0.65rem 0.9rem;
      font-family: var(--font-serif);
      font-size: clamp(1.35rem, 3.2vw, 1.75rem);
      font-weight: 700;
      letter-spacing: -0.02em;
      color: var(--ink);
      list-style: none;
      display: flex;
      align-items: center;
      gap: 0.55rem;
      user-select: none;
    }
    .history-spoiler summary::-webkit-details-marker { display: none; }
    .history-spoiler summary::before {
      content: "▶";
      font-size: 0.65rem;
      transition: transform 0.2s;
      opacity: 0.5;
    }
    .history-spoiler[open] summary::before { transform: rotate(90deg); }
    .history-spoiler summary:hover { color: var(--ink); }
    .history-body {
      padding: 0.25rem 0.9rem 1rem;
      border-top: 1px solid rgba(255,255,255,0.07);
    }
    .history-body p { margin: 0.75rem 0 0; font-size: 0.95rem; color: var(--ink-muted); }
    .note-callout {
      max-width: var(--max-prose);
      margin: 1.25rem auto 0;
      padding: 0 1.5rem;
      font-size: 0.9rem;
      color: var(--ink-muted);
      font-style: italic;
    }
    /* === Bilingual toggle === */
    body.ua .en-only { display: none !important; }
    body:not(.ua) .ua-only { display: none !important; }
    .lang-toggle {
      display: flex;
      gap: 0.25rem;
      align-items: center;
      position: fixed;
      top: 0.9rem;
      right: 1.2rem;
      z-index: 200;
    }
    .lang-toggle button {
      background: rgba(255,255,255,0.07);
      border: 1px solid rgba(255,255,255,0.15);
      color: var(--ink-muted);
      border-radius: 0.3rem;
      padding: 0.2rem 0.65rem;
      font-size: 0.78rem;
      font-weight: 700;
      letter-spacing: 0.07em;
      cursor: pointer;
      transition: background 0.15s, color 0.15s, border-color 0.15s;
      font-family: var(--font-sans);
    }
    .lang-toggle button:hover { background: rgba(255,255,255,0.13); color: var(--ink); }
    .lang-toggle button.active {
      background: var(--accent-soft);
      border-color: var(--accent);
      color: var(--accent);
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
  <script>(function(){if(localStorage.getItem('nuam-lang')==='ua')document.body.classList.add('ua');})()</script>
"""
        + data_scripts
        + """
  <script src="https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js"></script>
</head>
<body>
  <div class="ambient" aria-hidden="true"></div>
  <div class="lang-toggle" aria-label="Language / Мова">
    <button id="btn-lang-en" onclick="setLang('en')">EN</button>
    <button id="btn-lang-ua" onclick="setLang('ua')">UA</button>
  </div>
  <article class="story">
    <header class="story-hero">
      <p class="kicker">
        <span class="en-only">Ukrainian music market · NUAM</span>
        <span class="ua-only">Музичний ринок України · NUAM</span>
      </p>
      <h1>
        <span class="en-only">The unlikely odds of making it big in Ukraine</span>
        <span class="ua-only">Неймовірні шанси стати відомим в Україні</span>
      </h1>
      <p class="lede">
        <span class="en-only">How much Jerry Heil earns, whether the Eurovision Song Contest actually pushes a career forward, and in which genres you need to make music if you want to build a business from music — drawn from NUAM’s public catalogue.</span>
        <span class="ua-only">Скільки заробляє Jerry Heil, чи справді Євробачення просуває кар’єру, і в яких жанрах варто творити музику, якщо хочеш зробити з неї бізнес — на основі публічного каталогу NUAM.</span>
      </p>
      <p class="story-byline">
        <img src="data:image/jpeg;base64,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" alt="" aria-hidden="true" />
        By <strong>Kateryna Siomina</strong>
        <span class="sep">&middot;</span>
        <span class="en-only">Data Scientist &amp; Artists Manager</span>
        <span class="ua-only">Data Scientist і менеджер артистів</span>
        <span class="sep">&middot;</span>
        <a href="https://www.instagram.com/sidel_meril/" target="_blank" rel="noopener">Instagram</a>
        <span class="sep">&middot;</span>
        <a href="https://t.me/sidel_meril" target="_blank" rel="noopener">Telegram</a>

      </p>
    </header>

    <section class="chart-section" aria-labelledby="sec-listeners">
      <div class="prose-block" style="padding-bottom:1rem">
        <p class="section-label">
          <span class="en-only">Section 1 · Time series</span>
          <span class="ua-only">Розділ 1 · Часовий ряд</span>
        </p>
        <h2 id="sec-listeners">
          <span class="en-only">Total listeners over time (2024–2026)</span>
          <span class="ua-only">Загальна кількість слухачів (2024–2026)</span>
        </h2>
      </div>
      <p class="chart-dek">
        <span class="en-only">Summed monthly listeners across artists in NUAM. The vertical scale is trimmed to the visible range (not zero); month-to-month change is labeled on the chart.</span>
        <span class="ua-only"></span>
      </p>
"""
    )

    s1 = chart_blocks[0]
    s2_ld = chart_blocks[1]

    listeners_followup = """
      <div class="prose-block">
        <div class="en-only">
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
        <div class="ua-only">
          <p>
            Графік ілюструє зростання загальної кількості слухачів на українській музичній сцені з 2024 до початку 2026 року — на основі даних <strong>NUAM (New UA Music)</strong>, провідного українського онлайн-музичного ресурсу. Датасет зі зрізом за квітень 2026 року фіксує стабільне зростання залученості слухачів, що відображає тривалу трансформацію локального музичного ринку.
          </p>
          <p>
            <a href="https://www.nuam.club/stat">NUAM</a> — одна з найбільших публічно доступних баз даних українських музикантів, яка зберігає детальні профілі десятків тисяч артистів та їхніх релізів. Платформа дозволяє шукати та фільтрувати музику за жанром, популярністю, датою релізу та іншими параметрами, а також пропонує плейлисти, щорічні чарти та жанрові добірки. Через вебдодаток <strong>NUAM Base</strong> вона надає аналітику як для артистів, так і для слухачів.
          </p>
          <p>Останніми місяцями кількість слухачів стабільно зростає. Кілька факторів можуть пояснити цю тенденцію:</p>
          <ol>
            <li><strong>Зростання кількості артистів.</strong> Що більше музикантів приєднується до сцени та випускає музику, то природньо зростає загальна кількість слухачів.  З початку відстеження NUAM кількість активних українських музикантів різко зросла — понад 16&thinsp;500 артистів, і більше 9&thinsp;200 з них випустили музику лише в 2025 році.</li>
            <li><strong>Агрегування даних по артистах.</strong> Кількість слухачів підсумовується по всіх артистах — якщо один слухач відкрив кількох виконавців, це може збільшувати загальний показник.</li>
            <li><strong>Реальне зростання аудиторії.</strong> Якщо аудиторії різних артистів суттєво не перетинаються, графік може відображати справжнє зростання кількості унікальних слухачів.</li>
          </ol>
          <p>
            Попри ці технічні нюанси, всі ознаки вказують на <strong>зростання інтересу до локальної музики</strong>. Стримінгові платформи — <a href="https://www.spotify.com/">Spotify</a> та <a href="https://www.apple.com/apple-music/">Apple Music</a> — відіграли значну роль у посиленні цього зростання.
          </p>
        </div>
      </div>
    </section>

    <div class="prose-block" style="padding-top:0.5rem">
      <details class="history-spoiler">
        <summary>
          <span class="en-only">How we got here</span>
          <span class="ua-only">Як ми сюди прийшли</span>
        </summary>
        <div class="history-body">
      <div class="en-only">
      <p>
        The Ukrainian music market is relatively young and has undergone dramatic transformations over the past century. Under the Soviet Union, Ukrainian culture — including music — existed within a framework that often favored Russian‑language cultural production and tightly controlled local cultural expression. After independence in 1991, Ukrainian pop and contemporary music gradually revived, but Russian‑language songs remained common in the market because they reached larger audiences across the post‑Soviet space.
      </p>
      <p>
        In the 2000s and early 2010s, Ukrainian artists increasingly built local followings through domestic festivals and television, and social media expanded opportunities for promotion and audience building. However, many musicians still recorded in Russian to gain wider reach within the larger Russian‑speaking market.
      </p>
      <p>
        <strong>The turning point came after 2014</strong> and <strong>especially after Russia's full‑scale invasion in February 2022</strong>. Following these events, both cultural identity and language began reshaping the industry — Ukrainian‑language music surged in popularity and became mainstream. By 2025, Ukrainian‑language content accounted for a majority of music consumption in Ukraine, up significantly from before the invasion.
      </p>
      <p>
        At the same time, new legislation in 2022 restricted public performance and broadcast of many Russian‑language songs and increased Ukrainian content quotas on radio and television, further accelerating the shift toward Ukrainian music as the dominant cultural force.
      </p>
      <p>
        Despite this cultural revitalization, <strong>economic realities for most musicians remain tough</strong>. Earlier research showed that for over four‑fifths of Ukrainian artists, income from music alone often does not cover basic living costs, highlighting the challenges of professional success within the local market.
      </p>
      <p>
        Today, the Ukrainian music scene is experiencing a renaissance shaped by war, national identity, digital platforms, and evolving audience preferences. This period — from 2022 through 2026 — represents a generation‑defining decade for artists striving to break through in a market that's simultaneously becoming more local and more global.
      </p>
      </div>
      <div class="ua-only">
      <p>
        Музичний ринок України відносно молодий і пройшов через кардинальні трансформації протягом останнього століття. За радянських часів українська культура — зокрема музика — існувала в умовах, що часто надавали перевагу російськомовному культурному виробництву та жорстко контролювали місцеве культурне самовираження. Після незалежності у 1991 році українська поп-музика та сучасна музика поступово відроджувалися, але російськомовні пісні залишалися поширеними на ринку, оскільки охоплювали ширшу аудиторію на пострадянському просторі.
      </p>
      <p>
        У 2000-х та на початку 2010-х українські артисти дедалі більше нарощували місцеву аудиторію завдяки вітчизняним фестивалям і телебаченню, а соціальні мережі відкрили нові можливості для просування та розбудови аудиторії. Проте багато музикантів усе ще записувалися російською, щоб охопити більший російськомовний ринок.
      </p>
      <p>
        <strong>Переломний момент настав після 2014 року</strong> і <strong>особливо після повномасштабного вторгнення Росії у лютому 2022 року</strong>. Після цих подій культурна ідентичність і мова почали переформатовувати індустрію — українськомовна музика різко зросла в популярності й стала мейнстримом. До 2025 року українськомовний контент становив більшість музичного споживання в Україні — значно більше, ніж до вторгнення.
      </p>
      <p>
        Водночас нове законодавство 2022 року обмежило публічне виконання та трансляцію багатьох російськомовних пісень і збільшило квоти на українськомовний контент на радіо та телебаченні, що ще більше прискорило перехід до української музики як домінуючої культурної сили.
      </p>
      <p>
        Попри це культурне відродження, <strong>економічні реалії для більшості музикантів залишаються складними</strong>. Раніші дослідження показали, що для понад чотирьох п'ятих українських артистів дохід лише від музики часто не покриває базових витрат на проживання — що підкреслює труднощі досягнення професійного успіху на місцевому ринку.
      </p>
      <p>
        Сьогодні українська музична сцена переживає ренесанс, формований війною, національною ідентичністю, цифровими платформами та мінливими вподобаннями аудиторії. Цей період — з 2022 до 2026 року — є десятиліттям, що визначить ціле покоління артистів, які прагнуть пробитися на ринку, що одночасно стає більш локальним і більш глобальним.
      </p>
      </div>
        </div>
      </details>
    </div>

    <section class="chart-section" aria-labelledby="sec-distribution">
      <div class="prose-block" style="padding-bottom:1rem">
        <p class="section-label">
          <span class="en-only">Section 2 · Distribution</span>
          <span class="ua-only">Розділ 2 · Розподіл</span>
        </p>
        <h2 id="sec-distribution">
          <span class="en-only">How many listeners do Ukrainian artists have?</span>
          <span class="ua-only">Скільки слухачів мають українські артисти?</span>
        </h2>
      </div>
      <div class="prose-block">
        <p class="en-only">
          The distribution is sharply skewed. A large share of artists in the NUAM catalogue attract only a handful of streams; the curve drops off steeply, and only a small slice ever breaks through to significant listener counts. The histogram below makes that shape visible — drag the slider to see where any top‑percentile cutoff lands in actual listener count terms.
        </p>
        <p class="ua-only">
          Розподіл різко скошений.  Велика доля артистів із каталогу NUAM отримує лише одиничні прослуховування; крива різко спадає, і лише невеликий відсоток коли-небудь досягає значної кількості слухачів. Гістограма нижче робить цю форму наочною — перетягніть повзунок, щоб побачити, де будь-який відсотковий поріг опиняється у фактичній кількості слухачів.
        </p>
      </div>
      <p class="chart-dek">
        <span class="en-only">Move the slider to watch how the highlighted frame changes — it shows how many artists are included once you set the listener threshold.</span>
        <span class="ua-only">Переміщуйте повзунок, щоб бачити, як змінюється підсвічений фрейм — він показує, скільки артистів потрапляє у вибраний поріг слухачів.</span>
      </p>
"""

    dist_close = """
    </section>

    <section class="chart-section" aria-labelledby="sec-labels">
      <div class="prose-block" style="padding-bottom:1rem">
        <p class="section-label">
          <span class="en-only">Section 3 · Labels</span>
          <span class="ua-only">Розділ 3 · Лейбли</span>
        </p>
        <h2 id="sec-labels">
          <span class="en-only">Top&#8209;rated Ukrainian labels</span>
          <span class="ua-only">Топові українські лейбли</span>
        </h2>
      </div>
"""

    s3 = chart_blocks[2]

    block4 = """
      <div class="prose-block">
        <div class="en-only">
        <p>
          For many artists, record labels can be an important step in building a professional career in music. In the global industry, traditional label contracts are legal agreements in which an artist typically grants a label <strong>exclusive rights</strong> to record, market and distribute their music for a defined period of time, often tied to multiple albums or defined contract terms; during that period, artists generally cannot release music through other labels without the original label's permission.
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
        <div class="ua-only">
        <p>
          Для багатьох артистів рекорд-лейбли можуть стати важливим кроком у побудові професійної кар'єри в музиці. У глобальній індустрії традиційні лейблові контракти — це юридичні угоди, за якими артист зазвичай надає лейблу <strong>виключні права</strong> на запис, маркетинг і дистрибуцію своєї музики на визначений термін, часто прив'язаний до кількох альбомів або чітко визначених умов контракту; протягом цього строку артисти загалом не можуть випускати музику через інші лейбли без дозволу первісного.
        </p>
        <p>
          В Україні, однак, лейблова екосистема функціонує <strong>інакше, ніж у домінуючих міжнародних моделях</strong>. Багато локальних лейблів є не стільки ексклюзивними комерційними партнерами, скільки <strong>підтримуючими артистичними спільнотами</strong> — вони пропонують просування, допомогу з дистрибуцією, кураторні релізи, спільні мережі й колаборативні аудиторії, не прив'язуючи артистів жорсткою ексклюзивністю. Оскільки більшість угод є приватними і регулюються NDA, єдиного публічного стандарту, що визначає, чи повністю прив'язаний артист до одного лейблу, не існує. Проте більшість українських лейблів наголошують на <strong>підтримці та просуванні</strong> — допомазі з дистрибуцією, поширенні аудиторій, а іноді й координації живих виступів або промо-заходів — замість жорсткої правової ексклюзивності.
        </p>
        <p>
          Є лейбли, відомі <strong>тим, що створюють успішних артистів</strong> і просувають їх на ширші ринки. Ми визначаємо <strong>Топ - лейбл</strong> як такий, що має щонайменше <strong>двох артистів, кожен із яких досяг 270&thinsp;960+ місячних слухачів Spotify</strong> — приблизно <strong>$300</strong> за підрахунками стримінгових виплат.
        </p>
        <p>Кілька виділяються серед інших:</p>
        <ul>
          <li><strong>ENKO Music</strong> — поп-релізи; артисти Jerry Hail, Alyona Alyona, KALUSH, YAKTAK, Шугар; сильна присутність на Spotify.</li>
          <li><strong>PLAN</strong> — дуже великий обсяг підписань (<strong>379 угод за два роки</strong>); мейнстримний прорив поки відкрита історія.</li>
          <li><strong>UA Phonk Community</strong> — орієнтований на спільноту фонк-лейбл; сильні виконавці в ніші.</li>
        </ul>
        <p>Топові лейбли на NUAM також включають, серед інших:</p>
        <ul>
          <li>BEST MUSIC</li>
          <li>YATOMI HOUSE RECORDS</li>
          <li>Comp Music</li>
          <li>МУЛЬТИТРЕК</li>
          <li>pomitni</li>
          <li>CVRSED</li>
          <li>House of Culture і Дім Звукозапису</li>
          <li>Mayak Music</li>
          <li>SUNDAY</li>
          <li>TAVR Records</li>
          <li>AURORA RECORDS</li>
          <li style="color:#9aa0a6;list-style:none;padding-top:0.25rem">— та ще 13 лейблів, видимих на графіку вище</li>
        </ul>
        <p>
          <strong>pomitni</strong> активний лише з <strong>2022 року</strong>, але вже швидко зростає — з артистами як Nadya Dorofeyeva та Кажанна. Підписання контракту з одним із цих <strong>26 топових лейблів</strong> — це і можливість, і сигнал того, що артист рухається по надійному шляху.
        </p>
        </div>
      </div>
    </section>

    <section class="chart-section" aria-labelledby="sec-milestones">
      <div class="prose-block" style="padding-bottom:1rem">
        <p class="section-label">
          <span class="en-only">Section 4 · Careers</span>
          <span class="ua-only">Розділ 4 · Кар'єри</span>
        </p>
        <h2 id="sec-milestones">
          <span class="en-only">How mature is Ukraine's music market?</span>
          <span class="ua-only">Наскільки зрілий музичний ринок України?</span>
        </h2>
      </div>
      <div class="prose-block">
        <div class="en-only">
        <p>
          To get a sense of what it really means for an artist to move from early attention to a career with some traction,
          we took inspiration from a fascinating visual essay by
          <a href="https://pudding.cool/2022/07/tiktok-story/"><em>The Pudding</em></a>.
          In that piece, the authors looked at a group of artists who went viral on TikTok and checked how many of them
          hit a set of real‑world milestones that often come with "making it" — things like charting on Spotify,
          playing live shows, signing record deals, gaining followers on social platforms, or reaching 1 million monthly listeners.
        </p>
        <p>
          We wanted to adapt that idea for Ukrainian artists, but we also only have certain kinds of data available for analysis.
          So instead of tracking eight different milestones, we picked a handful that are meaningful signals for where an artist
          stands today and that we can actually measure:
        </p>
        <ul>
          <li><strong>Signed with a top‑rated label</strong> — a signal that other music professionals see promise in your work and that you've got access to support from experienced people in the industry — from wider distribution to connections that can help your career grow.</li>
          <li><strong>Spotify profile</strong> — you're available to listeners everywhere in the world</li>
          <li><strong>Instagram account</strong> — you have a social presence where fans can connect with you</li>
          <li><strong>Debuted in the last three years</strong> — you're part of the currently rising cohort of musicians</li>
          <li><strong>Spotify monthly listeners ≥ 1 million</strong> — a clear indicator of audience reach beyond local borders</li>
          <li><strong>Earned over $300</strong> — showing that your music is generating real streaming income (not just plays)</li>
        </ul>
        </div>
        <div class="ua-only">
        <p>
          Щоб зрозуміти, що насправді означає для артиста перехід від першої уваги до кар'єри з певним імпульсом,
          ми надихнулися захопливим візуальним есе від
          <a href="https://pudding.cool/2022/07/tiktok-story/"><em>The Pudding</em></a>.
          У ньому автори розглядали групу артистів, що стали вірусними у TikTok, і перевіряли, скільки з них досягли
          набору реальних майлстоунів, пов'язаних із «прориванням» — потрапляння в чарти Spotify,
          виступи на живих концертах, підписання лейблових угод, набір підписників у соцмережах або мільйон місячних слухачів.
        </p>
        <p>
          Ми хотіли адаптувати цю ідею для українських артистів, але маємо лише певні типи даних для аналізу.
          Тому замість восьми різних майлстоунів ми вибрали кілька, які є значущими сигналами про те, де зараз перебуває артист
          і які ми можемо реально виміряти:
        </p>
        <ul>
          <li><strong>Підписання з топовим лейблом</strong> — сигнал того, що інші музичні профі вбачають у тобі потенціал і що ти маєш доступ до підтримки досвідчених людей у індустрії — від ширшої дистрибуції до зв'язків, що можуть допомогти кар'єрі.</li>
          <li><strong>Профіль на Spotify</strong> — ти доступний слухачам по всьому світу</li>
          <li><strong>Акаунт в Instagram</strong> — ти маєш соціальну присутність, де фани можуть тебе знайти</li>
          <li><strong>Дебют за останні три роки</strong> — ти частина когорти музикантів, що зараз зростає</li>
          <li><strong>Місячні слухачі Spotify ≥ 1 мільйон</strong> — чіткий показник охоплення аудиторії за межами кордонів</li>
          <li><strong>Зароблено понад $300</strong> — підтверджує, що твоя музика генерує реальний стримінговий дохід (не просто прослуховування)</li>
        </ul>
        </div>
      </div>
"""

    s5 = chart_blocks[3]

    block6 = """
      <div class="prose-block">
        <div class="en-only">
        <p>
          Artists in our listener band view range from about ~240 000 up to around ~1.8 million monthly listeners —
          and that difference tells a story.
        </p>
        <p>
          To make this more interactive for readers, our dynamic visualization lets you configure the listener band yourself.
          The view highlighted here shows where
          <a href="https://open.spotify.com/search/Ziferblat/artists" target="_blank" rel="noopener"><strong>Ziferblat</strong></a>
          sits in the landscape — as a recent Ukrainian representative at the Eurovision Song Contest 2025 with their song
          "Bird of Pray."
        </p>
        <p>
          By comparison,
          <a href="https://open.spotify.com/search/Go_A/artists" target="_blank" rel="noopener"><strong>Go_A</strong></a>,
          who represented Ukraine at Eurovision in 2021, followed a different growth path. Though they had strong international
          attention, their listener growth under the conditions of the early 2020s looks different in our data than
          Ziferblat's during the broader surge in global interest in Ukrainian music after 2022.
        </p>
        <p>
          Another interesting pattern in the chart is
          <a href="https://open.spotify.com/search/Carpetman/artists" target="_blank" rel="noopener"><strong>Carpetman</strong></a>,
          who sits to the left of Ziferblat — meaning he has more monthly listeners in this view. Before launching his
          solo career, Carpetman was part of
          <a href="https://open.spotify.com/search/Kalush%20Orchestra/artists" target="_blank" rel="noopener"><strong>Kalush Orchestra</strong></a>,
          the Ukrainian group that won the Eurovision Song Contest 2022, and both Carpetman and Kalush Orchestra appear
          in our listener band — though Kalush Orchestra sits with a significantly lower listener rate than Carpetman's
          current solo numbers, highlighting how his recent international growth stands apart.
        </p>
        </div>
        <div class="ua-only">
        <p>
          Артисти у нашому діапазоні слухачів охоплюють від ~240&thinsp;000 до ~1,8 мільйона місячних слухачів —
          і ця різниця розповідає свою історію.
        </p>
        <p>
          Щоб зробити це інтерактивнішим для читачів, наша динамічна візуалізація дозволяє самостійно налаштувати діапазон слухачів.
          Підсвічений тут діапазон показує, де знаходиться
          <a href="https://open.spotify.com/search/Ziferblat/artists" target="_blank" rel="noopener"><strong>Ziferblat</strong></a>
          — нещодавній представник України на Євробаченні 2025 з піснею "Bird of Pray."
        </p>
        <p>
          Для порівняння,
          <a href="https://open.spotify.com/search/Go_A/artists" target="_blank" rel="noopener"><strong>Go_A</strong></a>,
          хто представляв Україну на Євробаченні 2021, обрав інший шлях зростання. Попри сильну міжнародну увагу,
          зростання їхньої аудиторії в умовах початку 2020-х виглядає інакше в наших даних, ніж
          зростання Ziferblat під час ширшого сплеску глобального інтересу до української музики після 2022 року.
        </p>
        <p>
          Ще одна цікава закономірність на графіку —
          <a href="https://open.spotify.com/search/Carpetman/artists" target="_blank" rel="noopener"><strong>Carpetman</strong></a>,
          який розташований лівіше від Ziferblat — тобто має більше місячних слухачів у цьому вигляді. До початку
          сольної кар'єри Carpetman був частиною
          <a href="https://open.spotify.com/search/Kalush%20Orchestra/artists" target="_blank" rel="noopener"><strong>Kalush Orchestra</strong></a>,
          укр. групи, що виграла Євробачення 2022, і обидва — і Carpetman, і Kalush Orchestra — з'являються
          в нашому діапазоні, хоча Kalush Orchestra має значно менше слухачів, ніж сольні показники Carpetman,
          що підкреслює відокремленість його нещодавнього міжнародного зростання.
        </p>
        </div>

      </div>
    </section>

    <section class="chart-section" aria-labelledby="sec-genres">
      <div class="prose-block" style="padding-bottom:1rem">
        <p class="section-label">
          <span class="en-only">Section 5 · Genres</span>
          <span class="ua-only">Розділ 5 · Жанри</span>
        </p>
        <h2 id="sec-genres">
          <span class="en-only">Genres</span>
          <span class="ua-only">Жанри</span>
        </h2>
      </div>
"""

    s7 = chart_blocks[4]

    block8 = """
      <div class="prose-block">
        <div class="en-only">
        <p>
          I also looked at music from the listeners' side — in particular <strong>which genres attract the most listeners</strong> and which ones are <em>under‑represented</em> compared to their audience size. Not every genre is proportional: some styles have way more ears listening than artists making that music. Below are genres that <strong>have a lot of listeners but fewer artists creating in them</strong> — one way to spot opportunities on the scene.
        </p>
        <p>
          One of the most listened‑to but under‑represented genres on our charts is <strong>Ukrainian phonk</strong> — a style rooted in phonk and internet‑driven beats that's finding real traction with listeners even though there aren't many artists producing it. This means demand far outpaces the number of creators right now, so phonk shows up strong in listenership compared to its small roster.
        </p>
        <p>
          By contrast, well‑known genres like <strong>rap</strong> have enough artists to satisfy audience demand, so listener attention and streams are spread more evenly across performers and competition is higher in that field.
        </p>
        <p>
          At the same time, experimental corners and classic styles (like <strong>emo, opera, blues</strong>) don't have a wide market in Ukraine; they're interesting to specific listeners but don't attract large audiences here, so their growth potential is limited in this context.
        </p>
        <aside class="story-aside">
          <p>
            Ukrainian phonk grew out of the global phonk wave — Memphis‑rooted loops and trap energy that blew up on SoundCloud and short‑video feeds — and took on a local accent through collectives such as <strong>Ukrainian Phonk Community</strong>. Today it's often independent, bass‑heavy, and unmistakably "late night internet," with listeners both at home and abroad.
          </p>
        </aside>
        </div>
        <div class="ua-only">
        <p>
          Я також розглянула музику з боку слухачів — зокрема <strong>які жанри приваблюють найбільше слухачів</strong> і які з них є <em>недопредставленими</em> відносно розміру аудиторії. Не кожен жанр пропорційний: деякі стилі мають набагато більше вух, що їх слухають, ніж артистів, що їх створюють. Нижче — жанри, що <strong>мають багато слухачів, але мало артистів, які у них творять</strong> — один зі способів помітити можливості на сцені.
        </p>
        <p>
          Один із найбільш прослуховуваних, але недопредставлених жанрів на наших чартах — <strong>Ukrainian phonk</strong> — стиль на основі фонку та інтернет-біту, що знаходить реальну тягу в слухачів, попри невелику кількість артистів, які його створюють. Це означає, що попит значно перевищує кількість творців зараз, тому фонк виглядає сильним у прослуховуваннях порівняно зі своїм невеликим ростером.
        </p>
        <p>
          Для порівняння, добре відомі жанри, як-от <strong>реп</strong>, мають достатньо артистів для задоволення попиту аудиторії, тому увага слухачів і стрими розподілені рівномірніше серед виконавців, а конкуренція в цій сфері вища.
        </p>
        <p>
          Водночас, експериментальні напрями та класичні стилі (як-от <strong>емо, опера, блюз</strong>) не мають широкого ринку в Україні; вони цікаві певним слухачам, але не залучають великих аудиторій тут, тому їхній потенціал зростання в цьому контексті обмежений.
        </p>
        <aside class="story-aside">
          <p>
            Ukrainian phonk виріс із глобальної хвилі фонку — мемфіських лупів і трап-енергії, що вибухнули на SoundCloud і у короткометражних відео — і набув локального акценту завдяки об'єднанню <strong>Ukrainian Phonk Community</strong>. Сьогодні він часто незалежний, з важким басом і невіддільно "нічно-інтернетний," з аудиторією як вдома, так і за кордоном.
          </p>
        </aside>
        </div>
      </div>
    </section>

    <section class="chart-section" aria-labelledby="sec-deals">
      <div class="prose-block" style="padding-bottom:1rem">
        <p class="section-label">
          <span class="en-only">Section 6 · Signings</span>
          <span class="ua-only">Розділ 6 · Контракти</span>
        </p>
        <h2 id="sec-deals">
          <span class="en-only">Strange deals</span>
          <span class="ua-only">Дивні угоди</span>
        </h2>
      </div>
      <div class="prose-block">
        <div class="en-only">
        <p>
          When you go to the view where <strong>"each artist is a little sun — six slices of their story"</strong> and set the listener range to <strong>0–100</strong> while sorting by <strong>achievements</strong>, you notice something interesting: in that low‑listener group we still see a bunch of artists with <strong>signed deals</strong> — even though they don't have many streams.
        </p>
        <p>
          Right now, the data doesn't show exactly <strong>how those deals happened</strong> — especially for artists with small audiences — but it was obvious enough that we decided to call this pattern <strong>"strange deals"</strong> and look into it.
        </p>
        <p>
          Most of these so‑called strange deals aren't hidden in niche corners of the music scene. <strong>They actually lie within mainstream genres</strong> like <strong>pop, rap, indie, or rock</strong>, where there are already plenty of artists and competition. That makes it even more curious why some low‑listener artists still end up signed. It suggests that <strong>getting a label connection isn't only about big listener numbers anymore</strong>, and there may be other factors in play behind the scenes.<sup class="ref"><a href="https://liroom.com.ua/news/zvuchyt-vypusk-6" id="ref1-back">[1]</a></sup>
        </p>
        </div>
        <div class="ua-only">
        <p>
          Якщо перейти до вигляду, де <strong>"кожен артист — маленьке сонце"</strong> і встановити діапазон слухачів <strong>0–100</strong> із сортуванням за <strong>досягненнями</strong>, помічаєш щось цікаве: у цій групі з малою аудиторією все одно є купа артистів із <strong>підписаними угодами</strong> — попри невелику кількість стримів.
        </p>
        <p>
          Наразі дані не показують точно <strong>як відбулися ці угоди</strong> — особливо для артистів з малою аудиторією — але це було настільки очевидно, що ми вирішили назвати цю закономірність <strong>"дивними угодами"</strong> і розібратися в ній.
        </p>
        <p>
          Більшість цих так званих дивних угод не приховані в нішевих куточках музичної сцени. <strong>Вони насправді знаходяться у мейнстримних жанрах</strong> — <strong>поп, реп, інді або рок</strong>, де вже є велика кількість артистів і висока конкуренція. Це робить ще більш цікавим, чому деякі артисти з малою аудиторією все одно опиняються підписаними. Це натякає, що <strong>отримати зв'язок із лейблом більше не тільки про великі показники слухачів</strong>, і за лаштунками можуть бути інші фактори.<sup class="ref"><a href="https://liroom.com.ua/news/zvuchyt-vypusk-6" id="ref1-back">[1]</a></sup>
        </p>
        </div>
      </div>
"""

    s9 = chart_blocks[5]
    s10 = chart_blocks[6]

    # Section 6 closes after the chart (prose is now before the chart in block8).
    block_deals_prose = """
    </section>

"""

    block_money = """
    <section class="chart-section" aria-labelledby="sec-money">
      <div class="prose-block" style="padding-bottom:1rem">
        <p class="section-label">
          <span class="en-only">Section 7 · Money</span>
          <span class="ua-only">Розділ 7 · Гроші</span>
        </p>
        <h2 id="sec-money">
          <span class="en-only">Where's the money, Lebowski?</span>
          <span class="ua-only">Де гроші, Лебовскі?</span>
        </h2>
      </div>
      <div class="prose-block">
        <div class="en-only">
        <p>
          Listener counts do not translate directly into bank deposits. In the last couple of years, trade press and artist statements have often linked the same frustration to two threads:
          <strong>per‑stream payouts that stay small</strong> for many acts, and worry that <strong>AI‑generated or bulk‑uploaded catalog</strong> could dilute attention (and, indirectly, how royalty pools are shared)—part of the backdrop to <strong>high‑profile pullbacks or threats to leave Spotify</strong> that surfaced around 2024–2026. None of that shows up line‑by‑line in NUAM; it is context for why "streams up" and "rent paid" are different questions.
        </p>
        <p>
          The views below apply one <strong>Ukraine premium‑stream shortcut</strong> (~$1.33 per 1,000 paid streams, from third‑party royalty tables such as Dynamoi)
          to <strong>each month in the NUAM export</strong>. That yields a rough <em>lower‑bound style</em> estimate — not an official Spotify statement, and not a split between free and premium plays.
        </p>
        <p>
          The <strong>histogram</strong> doesn't ask about theory or technical charts — it <strong>reveals how streaming money is actually distributed among artists</strong>. It shows the number of artists earning at each level of total estimated payout from streams, and one thing is clear at a glance: <strong>most artists aren't making enough to live on</strong>. Approximately <strong>93 % of artists receive less than $300</strong> in total payouts from streaming alone — meaning most have to work full‑time jobs alongside their music.
        </p>
        <p>
          Below that, we've treated each artist's payout trends like a <strong>stock performance chart</strong>, because for many musicians streaming income <em>is like an investment in their own career</em>. You can see how their estimated monthly earnings change over time. If you type, for example, "Кажанна," you'll see her journey: from a relatively underpaid artist to one of the rare few who crossed the $300 boundary with her hit <em>"Boy."</em> Her line rises just like a breakout stock — showing how a viral moment can change an artist's income dynamics.
        </p>
        </div>
        <div class="ua-only">
        <p>
          Кількість слухачів не перетворюється безпосередньо у банківські депозити. Останніми роками галузева преса і заяви артистів часто пов'язують одне і те ж розчарування з двома речами:
          <strong>мізерні виплати за стрим</strong> для багатьох виконавців, і занепокоєння, що <strong>каталог, згенерований ШІ або масово завантажений</strong>, може розбавити увагу (і, опосередковано, розподіл роялті-пулів) — частина контексту, на тлі якого з'являлися <strong>гучні відходи або погрози залишити Spotify</strong> у 2024–2026 роках. Нічого з цього не відображається в NUAM рядок за рядком; це контекст для розуміння того, чому "стрими вгору" і "оплачена оренда" — різні питання.
        </p>
        <p>
          Наведені нижче вигляди застосовують один <strong>спрощений показник для України</strong> (~$1,33 за 1&thinsp;000 платних (преміум) стримів, із сторонніх таблиць роялті, зокрема Dynamoi)
          до <strong>кожного місяця в експорті NUAM</strong>. Це дає грубу оцінку <em>у стилі нижньої межі</em> — не офіційну заяву Spotify і не розподіл між безкоштовними та преміум-відтвореннями.
        </p>
        <p>
          <strong>Гістограма</strong> не ставить питань про теорію чи технічні чарти — вона <strong>розкриває, як насправді розподіляються стримінгові гроші між артистами</strong>. Вона показує кількість артистів, що заробляють на кожному рівні загальних розрахункових виплат, і одна річ видна відразу: <strong>більшість артистів заробляє недостатньо, щоб прожити</strong>. Приблизно <strong>93% артистів отримують менше $300</strong> загальних виплат від стримінгу — тобто більшість вимушені поєднувати музику з роботою на повну ставку.
        </p>
        <p>
          Нижче ми відобразили динаміку виплат кожного артиста як <strong>графік фондового ринку</strong>, тому що для багатьох музикантів стримінговий дохід <em>є ніби інвестицією у власну кар'єру</em>. Ви можете побачити, як змінюються їхні розрахункові місячні заробітки з часом. Якщо ввести, наприклад, "Кажанна," ви побачите її шлях: від відносно недооціненого артиста до одного з рідкісних, хто перетнув межу $300 із хітом <em>"Boy."</em> Її лінія зростає, як ціна акцій на прориві — показуючи, як вірусний момент може змінити динаміку доходів артиста.
        </p>
        </div>
      </div>
      <p class="chart-dek">
        <span class="en-only">Log-scaled payout histogram with a sub-$300 band; interactive monthly payout lines with a peak-listener range (min/max) and hover for exact month estimates.</span>
        <span class="ua-only"></span>
      </p>
"""

    block_money_close = """
      <div class="prose-block" style="margin-top:1.5rem">
        <h3 id="sec-royalties">
          <span class="en-only">Spotify royalty rate estimates for Ukraine (Dec&nbsp;2025)</span>
          <span class="ua-only">Оцінки ставок роялті Spotify для України (груд.&nbsp;2025)</span>
        </h3>
        <p>
          <span class="en-only">According to <a href="https://dynamoi.com/data/royalties/spotify/ua">Dynamoi</a> data, Spotify pays roughly:</span>
          <span class="ua-only">За даними <a href="https://dynamoi.com/data/royalties/spotify/ua">Dynamoi</a>, Spotify платить приблизно:</span>
        </p>
        <ul>
          <li>
            <span class="en-only"><strong>~$1.33 per 1,000 paid (premium) streams</strong> in Ukraine</span>
            <span class="ua-only"><strong>~$1,33 за 1&thinsp;000 платних (преміум) стримів</strong> в Україні</span>
          </li>
          <li>
            <span class="en-only"><strong>~$0.35 per 1,000 free / ad‑supported streams</strong> in Ukraine</span>
            <span class="ua-only"><strong>~$0,35 за 1&thinsp;000 безкоштовних / з рекламою стримів</strong> в Україні</span>
          </li>
        </ul>
        <p class="note-callout" style="padding:0;margin-top:0.5rem">
          <span class="en-only">These numbers come from a royalty dataset, not an official Spotify payout table — treat them as a market estimate. Lower local subscription prices and ad revenue often mean smaller per‑stream rates than in larger markets.</span>
          <span class="ua-only">Ці числа взяті з датасету роялті, а не з офіційної таблиці виплат Spotify — сприймайте їх як ринкову оцінку. Нижчі місцеві ціни підписок і рекламні доходи зазвичай означають менші ставки за стрим, ніж на більших ринках.</span>
        </p>
      </div>
    </section>

"""

    article_end = r"""    <section class="chart-section" aria-labelledby="sec-afterword">
      <div class="prose-block">
        <h2 id="sec-afterword" style="font-size:1.65rem;margin-bottom:1.25rem;">
          <span class="en-only">Afterword</span>
          <span class="ua-only">Післямова</span>
        </h2>
        <div class="en-only">
        <p>
          There's a lot of work behind this article, and it's not possible to capture every insight in one piece. For example, I haven't even touched on the question of how much value labels get from signing a large pool of artists — that's a whole topic on its own.
        </p>
        <p>
          I've added interactive controls to almost all the charts so that readers can play with the data, explore it for themselves, and draw their own conclusions.
        </p>
        <p>
          There's nothing here but data — just numbers and patterns from the scene.
        </p>
        <p>
          Huge thanks to <strong>Oleksii Efimenko</strong> and everyone at <strong>NUAM (New UA Music)</strong> for collecting and organizing this year's data — without their work, this whole analysis wouldn't be possible.
        </p>
        </div>
        <div class="ua-only">
        <p>
          За цією статтею стоїть багато роботи, і неможливо вмістити кожен інсайт в одній публікації. Наприклад, я навіть не торкнулася питання, яку цінність лейбли отримують від підписання великого пулу артистів — це ціла окрема тема.
        </p>
        <p>
          Я додала інтерактивні елементи управління майже до всіх графіків, щоб читачі могли гратися з даними, досліджувати їх самостійно та робити власні висновки.
        </p>
        <p>
          Тут немає нічого, крім даних — лише числа й закономірності зі сцени.
        </p>
        <p>
          Величезна подяка <strong>Олексію Єфіменку</strong> і всій команді <strong>NUAM (New UA Music)</strong> за збір та організацію даних цього року — без їхньої роботи весь цей аналіз був би неможливий.
        </p>
        </div>
      </div>
    </section>

    <footer class="sources-footer">
      <h2>
        <span class="en-only">Sources &amp; references</span>
        <span class="ua-only">Джерела та посилання</span>
      </h2>
      <ul>
        <li><a href="https://www.nuam.club/stat">NUAM — statistics and catalog</a>
          <span class="en-only">(data source for all graphics)</span>
          <span class="ua-only">(джерело даних для всіх графіків)</span></li>
        <li><a href="https://pudding.cool/2022/07/tiktok-story/">The Pudding — emerging artists on TikTok</a>
          <span class="en-only">(visual essay reference for milestones)</span>
          <span class="ua-only">(візуальне есе, що надихнуло на майлстоуни)</span></li>
        <li><a href="https://dynamoi.com/data/royalties/spotify/ua">Dynamoi — Spotify Ukraine royalty estimates</a></li>
        <li><a href="https://www.spotify.com/">Spotify</a> · <a href="https://www.apple.com/apple-music/">Apple Music</a></li>
        <li id="ref1">[1] <a href="https://liroom.com.ua/news/zvuchyt-vypusk-6">liroom.com.ua — Звучить, випуск 6</a>
          <span class="en-only">(on label signings and the Ukrainian music scene)</span>
          <span class="ua-only">(про підписання лейблів та українську музичну сцену)</span></li>
      </ul>
      <p style="margin-top:1rem;font-size:0.78rem;opacity:0.45;">
        <span class="en-only">&copy; 2026 Kateryna Siomina &mdash; original work, please credit when sharing.</span>
        <span class="ua-only">&copy; 2026 Kateryna Siomina &mdash; оригінальний твір, будь ласка, вказуйте авторство при поширенні.</span>
      </p>
    </footer>
  </article>
"""

    tail2 = """
<script>
(function () {
  var isUA = document.body.classList.contains('ua');
  var btnEN = document.getElementById('btn-lang-en');
  var btnUA = document.getElementById('btn-lang-ua');
  if (btnEN) btnEN.classList.toggle('active', !isUA);
  if (btnUA) btnUA.classList.toggle('active', isUA);
  window.__lang = isUA ? 'ua' : 'en';
  window.setLang = function (lang) {
    document.body.classList.toggle('ua', lang === 'ua');
    if (btnEN) btnEN.classList.toggle('active', lang !== 'ua');
    if (btnUA) btnUA.classList.toggle('active', lang === 'ua');
    localStorage.setItem('nuam-lang', lang);
    window.__lang = lang;
    document.dispatchEvent(new CustomEvent('langchange', { detail: lang }));
  };
})();
</script>
<script>
(function () {
  var CREDIT = [
    "",
    "\u2015\u2015\u2015",
    "Source: \u201cThe unlikely odds of making it big in Ukraine\u201d",
    "by Kateryna Siomina (Data Scientist & Artists Manager)",
    "https://t.me/sidel_meril  \u00b7  https://www.instagram.com/sidel_meril/",
    "\u00a9 2026 \u2014 original work, please credit when sharing.",
    "\u2015\u2015\u2015"
  ].join("\\n");

  document.addEventListener("copy", function (e) {
    var selection = window.getSelection();
    if (!selection || selection.isCollapsed) return;
    var text = selection.toString();
    if (text.length < 20) return; /* ignore single-word copies */
    e.preventDefault();
    e.clipboardData.setData("text/plain", text + CREDIT);
    e.clipboardData.setData("text/html",
      "<p>" + text.replace(/\\n/g, "<br>") + "</p>" +
      "<p style=\\"color:#888;font-size:0.85em\\">" +
        "Source: <em>The unlikely odds of making it big in Ukraine</em> " +
        "by <a href=\\"https://t.me/sidel_meril\\">Kateryna Siomina</a>. " +
        "&copy; 2026 &mdash; please credit when sharing." +
      "</p>"
    );
  });
})();
</script>
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
