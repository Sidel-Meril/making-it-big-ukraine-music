#!/usr/bin/env python3
"""Apply bilingual (EN/UA) support to the merge script and chart HTML files."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ─── 1. MERGE SCRIPT ──────────────────────────────────────────────────────────

MERGE = ROOT / "scripts" / "merge_ukraine_music_story.py"
src = MERGE.read_text(encoding="utf-8")
# Normalize typographic quotes to ASCII for reliable string matching
# (all curly quotes in the file are inside prose blocks that we're replacing)
src = (src.replace('\u201c', '"').replace('\u201d', '"')
          .replace('\u2019', "'").replace('\u2018', "'")
          .replace('\u202f', ' '))

# ── 1a. Add lang-toggle CSS to story_css ──────────────────────────────────────
OLD_CSS_END = '''    .note-callout {
      max-width: var(--max-prose);
      margin: 1.25rem auto 0;
      padding: 0 1.5rem;
      font-size: 0.9rem;
      color: var(--ink-muted);
      font-style: italic;
    }
"""'''

NEW_CSS_END = '''    .note-callout {
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
"""'''

assert OLD_CSS_END in src, "CSS end marker not found"
src = src.replace(OLD_CSS_END, NEW_CSS_END, 1)

# ── 1b. Add body init script + toggle button in middle / hero ─────────────────
OLD_BODY = '''"""
  </style>
'''

NEW_BODY = '''"""
  </style>
  <script>(function(){if(localStorage.getItem('nuam-lang')==='ua')document.body.classList.add('ua');})()</script>
'''

assert OLD_BODY in src, "middle style-end not found"
src = src.replace(OLD_BODY, NEW_BODY, 1)

# Inject toggle button after ambient div
OLD_AMBIENT = '''  <div class="ambient" aria-hidden="true"></div>
  <article class="story">'''
NEW_AMBIENT = '''  <div class="ambient" aria-hidden="true"></div>
  <div class="lang-toggle" aria-label="Language / Мова">
    <button id="btn-lang-en" onclick="setLang(\'en\')">EN</button>
    <button id="btn-lang-ua" onclick="setLang(\'ua\')">UA</button>
  </div>
  <article class="story">'''
assert OLD_AMBIENT in src, "ambient div not found"
src = src.replace(OLD_AMBIENT, NEW_AMBIENT, 1)

# Bilingual kicker
OLD_KICKER = '      <p class="kicker">Ukrainian music market \xb7 NUAM</p>'
NEW_KICKER = '''      <p class="kicker">
        <span class="en-only">Ukrainian music market \xb7 NUAM</span>
        <span class="ua-only">\u041c\u0443\u0437\u0438\u0447\u043d\u0438\u0439 \u0440\u0438\u043d\u043e\u043a \u0423\u043a\u0440\u0430\u0457\u043d\u0438 \xb7 NUAM</span>
      </p>'''
assert OLD_KICKER in src, "kicker not found"
src = src.replace(OLD_KICKER, NEW_KICKER, 1)

# Bilingual h1
OLD_H1 = '      <h1>The unlikely odds of making it big in Ukraine</h1>'
NEW_H1 = '''      <h1>
        <span class="en-only">The unlikely odds of making it big in Ukraine</span>
        <span class="ua-only">\u041d\u0435\u0439\u043c\u043e\u0432\u0456\u0440\u043d\u0456 \u0448\u0430\u043d\u0441\u0438 \u0441\u0442\u0430\u0442\u0438 \u0432\u0456\u0434\u043e\u043c\u0438\u043c \u0432 \u0423\u043a\u0440\u0430\u0457\u043d\u0456</span>
      </h1>'''
assert OLD_H1 in src, "h1 not found"
src = src.replace(OLD_H1, NEW_H1, 1)

# Bilingual lede — anchor on distinctive substring
OLD_LEDE = "      <p class=\"lede\">\n        How much Jerry Heil earns"
NEW_LEDE = '''      <p class="lede">
        <span class="en-only">How much Jerry Heil earns'''
assert OLD_LEDE in src, "lede start not found"
LEDE_END_SEARCH = "drawn from NUAM's public catalogue.\n      </p>"
LEDE_END_REPLACE = (
    "drawn from NUAM\u2019s public catalogue.</span>\n"
    "        <span class=\"ua-only\">"
    "\u0421\u043a\u0456\u043b\u044c\u043a\u0438 \u0437\u0430\u0440\u043e\u0431\u043b\u044f\u0454 Jerry Heil, "
    "\u0447\u0438 \u0441\u043f\u0440\u0430\u0432\u0434\u0456 \u0404\u0432\u0440\u043e\u0431\u0430\u0447\u0435\u043d\u043d\u044f "
    "\u043f\u0440\u043e\u0441\u0443\u0432\u0430\u0454 \u043a\u0430\u0440\u2019\u0454\u0440\u0443, "
    "\u0456 \u0432 \u044f\u043a\u0438\u0445 \u0436\u0430\u043d\u0440\u0430\u0445 \u0432\u0430\u0440\u0442\u043e "
    "\u0442\u0432\u043e\u0440\u0438\u0442\u0438 \u043c\u0443\u0437\u0438\u043a\u0443, "
    "\u044f\u043a\u0449\u043e \u0445\u043e\u0447\u0435\u0448 \u0437\u0440\u043e\u0431\u0438\u0442\u0438 "
    "\u0437 \u043d\u0435\u0457 \u0431\u0456\u0437\u043d\u0435\u0441 \u2014 "
    "\u043d\u0430 \u043e\u0441\u043d\u043e\u0432\u0456 \u043f\u0443\u0431\u043b\u0456\u0447\u043d\u043e\u0433\u043e "
    "\u043a\u0430\u0442\u0430\u043b\u043e\u0433\u0443 NUAM.</span>\n      </p>"
)
assert LEDE_END_SEARCH in src, f"lede end not found"
src = src.replace(OLD_LEDE, NEW_LEDE, 1)
src = src.replace(LEDE_END_SEARCH, LEDE_END_REPLACE, 1)

# ── 1c. Byline: add UA "Data Scientist & менеджер артистів" ──────────────────
OLD_BYLINE = '''        By <strong>Kateryna Siomina</strong>
        <span class="sep">&middot;</span>
        Data Scientist &amp; Artists Manager'''

NEW_BYLINE = '''        By <strong>Kateryna Siomina</strong>
        <span class="sep">&middot;</span>
        <span class="en-only">Data Scientist &amp; Artists Manager</span>
        <span class="ua-only">Data Scientist і менеджер артистів</span>'''

assert OLD_BYLINE in src, "byline not found"
src = src.replace(OLD_BYLINE, NEW_BYLINE, 1)

# ── 1d. Section 1 label + h2 + chart-dek ─────────────────────────────────────
OLD_S1 = '''      <div class="prose-block" style="padding-bottom:1rem">
        <p class="section-label">Section 1 · Time series</p>
        <h2 id="sec-listeners">Total listeners over time (2024–2026)</h2>
      </div>
      <p class="chart-dek">
        Summed monthly listeners across artists in NUAM. The vertical scale is trimmed to the visible range (not zero); month-to-month change is labeled on the chart.
      </p>'''

NEW_S1 = '''      <div class="prose-block" style="padding-bottom:1rem">
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
        <span class="ua-only">Сума місячних слухачів усіх артистів у NUAM. Вертикальна шкала обрізана до видимого діапазону; помісячна зміна позначена на графіку.</span>
      </p>'''

assert OLD_S1 in src, "section 1 header not found"
src = src.replace(OLD_S1, NEW_S1, 1)

# ── 1e. listeners_followup prose ─────────────────────────────────────────────
OLD_LF = '''    listeners_followup = """
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
    </section>'''

NEW_LF = '''    listeners_followup = """
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
    </section>'''

assert OLD_LF in src, "listeners_followup not found"
src = src.replace(OLD_LF, NEW_LF, 1)

# ── 1f. History spoiler ───────────────────────────────────────────────────────
OLD_HIST = '''    <div class="prose-block" style="padding-top:0.5rem">
      <details class="history-spoiler">
        <summary>How we got here</summary>
        <div class="history-body">
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
      </details>
    </div>'''

NEW_HIST = '''    <div class="prose-block" style="padding-top:0.5rem">
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
    </div>'''

assert OLD_HIST in src, "history spoiler not found"
src = src.replace(OLD_HIST, NEW_HIST, 1)

# ── 1g. Section 2 ─────────────────────────────────────────────────────────────
OLD_S2 = '''    <section class="chart-section" aria-labelledby="sec-distribution">
      <div class="prose-block" style="padding-bottom:1rem">
        <p class="section-label">Section 2 · Distribution</p>
        <h2 id="sec-distribution">How many listeners do Ukrainian artists have?</h2>
      </div>
      <div class="prose-block">
        <p>
          The distribution is sharply skewed. A large share of artists in the NUAM catalogue attract only a handful of streams; the curve drops off steeply, and only a small slice ever breaks through to significant listener counts. The histogram below makes that shape visible — drag the slider to see where any top‑percentile cutoff lands in actual listener count terms.
        </p>
      </div>
      <p class="chart-dek">
        Move the slider to watch how the highlighted frame changes — it shows how many artists are included once you set the listener threshold.
      </p>'''

NEW_S2 = '''    <section class="chart-section" aria-labelledby="sec-distribution">
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
      </p>'''

assert OLD_S2 in src, "section 2 header not found"
src = src.replace(OLD_S2, NEW_S2, 1)

# ── 1h. dist_close / Section 3 ────────────────────────────────────────────────
OLD_DC = '''    dist_close = """
    </section>

    <section class="chart-section" aria-labelledby="sec-labels">
      <div class="prose-block" style="padding-bottom:1rem">
        <p class="section-label">Section 3 · Labels</p>
        <h2 id="sec-labels">Top‑rated Ukrainian labels</h2>
      </div>
      <p class="chart-dek">
        Each glyph is a label: the center scales with how many artists sit on that imprint; green marks labels with several high-listener acts. Legend and sort sit with the graphic.
      </p>
"""'''

NEW_DC = '''    dist_close = """
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
      <p class="chart-dek">
        <span class="en-only">Each glyph is a label: the center scales with how many artists sit on that imprint; green marks labels with several high-listener acts. Legend and sort sit with the graphic.</span>
        <span class="ua-only">Кожен гліф — це лейбл: центр масштабується залежно від кількості підписаних артистів; зеленим позначено лейбли з кількома виконавцями з великою аудиторією.</span>
      </p>
"""'''

assert OLD_DC in src, "dist_close / section 3 not found"
src = src.replace(OLD_DC, NEW_DC, 1)

# ── 1i. block4 — labels prose ─────────────────────────────────────────────────
OLD_B4_START = '''    block4 = """
      <div class="prose-block">
        <p>
          For many artists, record labels can be an important step in building a professional career in music.'''

NEW_B4_START = '''    block4 = """
      <div class="prose-block">
        <div class="en-only">
        <p>
          For many artists, record labels can be an important step in building a professional career in music.'''

assert OLD_B4_START in src, "block4 start not found"
src = src.replace(OLD_B4_START, NEW_B4_START, 1)

# Find block4 end and add UA version
OLD_B4_END = '''          <li style="color:#9aa0a6;list-style:none;padding-top:0.25rem">— and 13 more labels visible on the chart above</li>
        </ul>
        <p>
          <strong>pomitni</strong> has only been active since <strong>2022</strong> but is already growing quickly, with artists like Nadya Dorofeyeva and Кажанна. Getting a deal with one of these <strong>26 top‑rated labels</strong> is both an opportunity and a signal that an artist is on a credible path.
        </p>
      </div>
    </section>'''

NEW_B4_END = '''          <li style="color:#9aa0a6;list-style:none;padding-top:0.25rem">— and 13 more labels visible on the chart above</li>
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
    </section>'''

assert OLD_B4_END in src, "block4 end not found"
src = src.replace(OLD_B4_END, NEW_B4_END, 1)

# ── 1j. Section 4 — Milestones header ────────────────────────────────────────
OLD_S4 = '''    <section class="chart-section" aria-labelledby="sec-milestones">
      <div class="prose-block" style="padding-bottom:1rem">
        <p class="section-label">Section 4 · Careers</p>
        <h2 id="sec-milestones">How mature is Ukraine's music market?</h2>
      </div>
      <div class="prose-block">
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
"""'''

NEW_S4 = '''    <section class="chart-section" aria-labelledby="sec-milestones">
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
"""'''

assert OLD_S4 in src, "section 4 milestones not found"
src = src.replace(OLD_S4, NEW_S4, 1)

# ── 1k. block6 — milestones distribution prose ───────────────────────────────
OLD_B6 = '''    block6 = """
      <div class="prose-block">
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
    </section>'''

NEW_B6 = '''    block6 = """
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
    </section>'''

assert OLD_B6 in src, "block6 milestones dist not found"
src = src.replace(OLD_B6, NEW_B6, 1)

# ── 1l. Section 5 — Genres ────────────────────────────────────────────────────
OLD_S5_HDR = '''    <section class="chart-section" aria-labelledby="sec-genres">
      <div class="prose-block" style="padding-bottom:1rem">
        <p class="section-label">Section 5 · Genres</p>
        <h2 id="sec-genres">Genres</h2>
      </div>
"""'''

NEW_S5_HDR = '''    <section class="chart-section" aria-labelledby="sec-genres">
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
"""'''

assert OLD_S5_HDR in src, "section 5 genres header not found"
src = src.replace(OLD_S5_HDR, NEW_S5_HDR, 1)

# ── 1m. block8 — genres prose ─────────────────────────────────────────────────
OLD_B8 = '''    block8 = """
      <div class="prose-block">
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
    </section>'''

NEW_B8 = '''    block8 = """
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
    </section>'''

assert OLD_B8 in src, "block8 genres prose not found"
src = src.replace(OLD_B8, NEW_B8, 1)

# ── 1n. Section 6 — Strange deals ────────────────────────────────────────────
OLD_S6_HDR = '''    <section class="chart-section" aria-labelledby="sec-deals">
      <div class="prose-block" style="padding-bottom:1rem">
        <p class="section-label">Section 6 · Signings</p>
        <h2 id="sec-deals">Strange deals</h2>
      </div>
      <div class="prose-block">
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
"""'''

NEW_S6_HDR = '''    <section class="chart-section" aria-labelledby="sec-deals">
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
"""'''

assert OLD_S6_HDR in src, "section 6 strange deals not found"
src = src.replace(OLD_S6_HDR, NEW_S6_HDR, 1)

# ── 1o. block_money — Section 7 ──────────────────────────────────────────────
OLD_BM = '''    block_money = """
    <section class="chart-section" aria-labelledby="sec-money">
      <div class="prose-block" style="padding-bottom:1rem">
        <p class="section-label">Section 7 · Money</p>
        <h2 id="sec-money">Where's the money, Lebowski?</h2>
      </div>
      <div class="prose-block">
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
      <p class="chart-dek">
        Log-scaled payout histogram with a sub-$300 band; interactive monthly payout lines with a peak-listener range (min/max) and hover for exact month estimates.
      </p>
"""'''

NEW_BM = '''    block_money = """
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
        <span class="ua-only">Гістограма виплат із логарифмічною шкалою та смугою нижче $300; інтерактивні лінії місячних виплат із діапазоном піку слухачів і підказками при наведенні.</span>
      </p>
"""'''

assert OLD_BM in src, "block_money not found"
src = src.replace(OLD_BM, NEW_BM, 1)

# ── 1p. block_money_close — royalty note ─────────────────────────────────────
OLD_BMC = '''      <div class="prose-block" style="margin-top:1.5rem">
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
    </section>'''

NEW_BMC = '''      <div class="prose-block" style="margin-top:1.5rem">
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
    </section>'''

assert OLD_BMC in src, "block_money_close royalty not found"
src = src.replace(OLD_BMC, NEW_BMC, 1)

# ── 1q. article_end — afterword + sources ─────────────────────────────────────
OLD_AE = r'''    article_end = r"""    <section class="chart-section" aria-labelledby="sec-afterword">
      <div class="prose-block">
        <h2 id="sec-afterword" style="font-size:1.65rem;margin-bottom:1.25rem;">Afterword</h2>
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
    </section>'''

NEW_AE = r'''    article_end = r"""    <section class="chart-section" aria-labelledby="sec-afterword">
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
    </section>'''

assert OLD_AE in src, "article_end afterword not found"
src = src.replace(OLD_AE, NEW_AE, 1)

# ── 1r. Sources footer ────────────────────────────────────────────────────────
OLD_FOOTER = '''    <footer class="sources-footer">
      <h2>Sources &amp; references</h2>
      <ul>
        <li><a href="https://www.nuam.club/stat">NUAM — statistics and catalog</a> (data source for all graphics)</li>
        <li><a href="https://pudding.cool/2022/07/tiktok-story/">The Pudding — emerging artists on TikTok</a> (visual essay reference for milestones)</li>
        <li><a href="https://dynamoi.com/data/royalties/spotify/ua">Dynamoi — Spotify Ukraine royalty estimates</a></li>
        <li><a href="https://www.spotify.com/">Spotify</a> · <a href="https://www.apple.com/apple-music/">Apple Music</a></li>
        <li id="ref1">[1] <a href="https://liroom.com.ua/news/zvuchyt-vypusk-6">liroom.com.ua — Звучить, випуск 6</a> (on label signings and the Ukrainian music scene)</li>
      </ul>
      <p style="margin-top:1rem;font-size:0.78rem;opacity:0.45;">&copy; 2026 Kateryna Siomina &mdash; original work, please credit when sharing.</p>
    </footer>'''

NEW_FOOTER = '''    <footer class="sources-footer">
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
    </footer>'''

assert OLD_FOOTER in src, "sources footer not found"
src = src.replace(OLD_FOOTER, NEW_FOOTER, 1)

# ── 1s. tail2 — add setLang JS before copy protection ────────────────────────
OLD_TAIL = '''    tail2 = """
<script>
(function () {
  var CREDIT = ['''

NEW_TAIL = '''    tail2 = """
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
  var CREDIT = ['''

assert OLD_TAIL in src, "tail2 not found"
src = src.replace(OLD_TAIL, NEW_TAIL, 1)

MERGE.write_text(src, encoding="utf-8")
print("✓ merge script patched")

# ─── 2. CHART HTML FILES ──────────────────────────────────────────────────────

def patch_chart(path: Path, replacements: list[tuple[str, str]]) -> None:
    html = path.read_text(encoding="utf-8")
    for old, new in replacements:
        if old not in html:
            print(f"  WARNING: pattern not found in {path.name}: {old[:60]!r}")
            continue
        html = html.replace(old, new, 1)
    path.write_text(html, encoding="utf-8")
    print(f"✓ {path.parent.name}/index.html patched")


CH = ROOT / "data" / "charts"

# ── uk_listeners_growth ───────────────────────────────────────────────────────
patch_chart(CH / "uk_listeners_growth" / "index.html", [
    (
        '<h1 id="title-main">Ukrainian artists on Spotify — how the audience grew</h1>',
        '<h1 id="title-main">'
        '<span class="en-only">Ukrainian artists on Spotify — how the audience grew</span>'
        '<span class="ua-only">Українські артисти на Spotify — як зростала аудиторія</span>'
        '</h1>',
    ),
])

# ── listeners_dist ── already patched on previous run, skip ───────────────────

# ── label_rosters ─────────────────────────────────────────────────────────────
patch_chart(CH / "label_rosters" / "index.html", [
    (
        '<option value="roster-desc">Most artists on label first</option>',
        '<option value="roster-desc"><span class="en-only">Most artists on label first</span><span class="ua-only">Найбільше артистів першими</span></option>',
    ),
    (
        '<option value="roster-asc">Fewest artists first</option>',
        '<option value="roster-asc"><span class="en-only">Fewest artists first</span><span class="ua-only">Найменше артистів першими</span></option>',
    ),
    (
        '<option value="hits-desc">Most "big listener" ticks first</option>',
        '<option value="hits-desc"><span class="en-only">Most "big listener" ticks first</span><span class="ua-only">Більше "великих" артистів першими</span></option>',
    ),
    (
        '<option value="hits-asc">Fewest ticks first</option>',
        '<option value="hits-asc"><span class="en-only">Fewest ticks first</span><span class="ua-only">Менше тіків першими</span></option>',
    ),
    (
        '<option value="name-asc">Label name (A\u2013Z)</option>',
        '<option value="name-asc"><span class="en-only">Label name (A\u2013Z)</span><span class="ua-only">Назва лейблу (А\u2013Я)</span></option>',
    ),
])

# ── milestones ────────────────────────────────────────────────────────────────
patch_chart(CH / "milestones" / "index.html", [
    (
        '<option value="achievements-desc">Most milestones</option>',
        '<option value="achievements-desc"><span class="en-only">Most milestones</span><span class="ua-only">Найбільше досягнень</span></option>',
    ),
    (
        '<option value="achievements-asc">Fewest milestones</option>',
        '<option value="achievements-asc"><span class="en-only">Fewest milestones</span><span class="ua-only">Найменше досягнень</span></option>',
    ),
    (
        '<option value="listeners-desc" selected>Highest estimated earnings</option>',
        '<option value="listeners-desc" selected><span class="en-only">Highest estimated earnings</span><span class="ua-only">Найбільші розрахункові виплати</span></option>',
    ),
    (
        '<option value="name-asc">Name (A\u2013Z)</option>',
        '<option value="name-asc"><span class="en-only">Name (A\u2013Z)</span><span class="ua-only">Назва (А\u2013Я)</span></option>',
    ),
])

# ── genres_popularity ─────────────────────────────────────────────────────────
patch_chart(CH / "genres_popularity" / "index.html", [
    (
        '<h1>Genres as bubbles — drag the band to filter by listeners per artist</h1>',
        '<h1>'
        '<span class="en-only">Genres as bubbles — drag the band to filter by listeners per artist</span>'
        '<span class="ua-only">Жанри як бульбашки — перетягніть смугу, щоб фільтрувати за слухачами</span>'
        '</h1>',
    ),
])

# ── signed_deals ──────────────────────────────────────────────────────────────
patch_chart(CH / "signed_deals" / "index.html", [
    (
        '<h1>Many artists get signed before they build a real audience</h1>',
        '<h1>'
        '<span class="en-only">Many artists get signed before they build a real audience</span>'
        '<span class="ua-only">Багато артистів підписуються до того, як набрати реальну аудиторію</span>'
        '</h1>',
    ),
])

# ── money_about ───────────────────────────────────────────────────────────────
patch_chart(CH / "money_about" / "index.html", [
    (
        'Monthly estimates — slide the peak band, hover a line',
        '<span class="en-only">Monthly estimates — slide the peak band, hover a line</span>'
        '<span class="ua-only">Місячні оцінки — пересуньте діапазон, наведіть на лінію</span>',
    ),
    (
        'placeholder="Jump to artist\u2026"',
        'placeholder="Jump to artist\u2026"',
    ),
])

print("\nAll done! Now run: python scripts/merge_ukraine_music_story.py")
