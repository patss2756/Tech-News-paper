#!/usr/bin/env python3
"""Builds a static newspaper page from trusted RSS feeds."""
import html
import os
import re
import time
import datetime as dt
import feedparser

# ---- Your sections and trusted sources --------------------------------------
# Each source is (display name, RSS URL). Google News search feeds act as
# a broad backstop and always return links to the original publisher.
SECTIONS = {
    "Semiconductors": [
        ("SemiEngineering", "https://semiengineering.com/feed/"),
        ("EE Times", "https://www.eetimes.com/feed/"),
        ("IEEE Spectrum", "https://spectrum.ieee.org/feeds/feed.rss"),
        ("Google News", "https://news.google.com/rss/search?q=semiconductor+chip+fab&hl=en-US&gl=US&ceid=US:en"),
    ],
    "Automotive": [
        ("Electrek", "https://electrek.co/feed/"),
        ("Automotive World", "https://www.automotiveworld.com/feed/"),
        ("Google News", "https://news.google.com/rss/search?q=automotive+EV+industry&hl=en-US&gl=US&ceid=US:en"),
    ],
    "Defence": [
        ("Breaking Defense", "https://breakingdefense.com/feed/"),
        ("Defense News", "https://www.defensenews.com/arc/outboundfeeds/rss/"),
        ("Google News", "https://news.google.com/rss/search?q=defense+military+technology&hl=en-US&gl=US&ceid=US:en"),
    ],
    "Data Centers": [
        ("Data Center Dynamics", "https://www.datacenterdynamics.com/en/rss/"),
        ("Google News", "https://news.google.com/rss/search?q=data+center+AI+infrastructure&hl=en-US&gl=US&ceid=US:en"),
    ],
    "Renewable Energy": [
        ("pv magazine", "https://www.pv-magazine.com/feed/"),
        ("Renewable Energy World", "https://www.renewableenergyworld.com/feed/"),
        ("Utility Dive", "https://www.utilitydive.com/feeds/news/"),
    ],
    "Power Management": [
        ("Power Electronics News", "https://www.powerelectronicsnews.com/feed/"),
        ("Google News", "https://news.google.com/rss/search?q=power+electronics+power+management+chip&hl=en-US&gl=US&ceid=US:en"),
    ],
    "Robotics": [
        ("The Robot Report", "https://www.therobotreport.com/feed/"),
        ("IEEE Spectrum", "https://spectrum.ieee.org/feeds/feed.rss"),
        ("Google News", "https://news.google.com/rss/search?q=robotics+humanoid+robot&hl=en-US&gl=US&ceid=US:en"),
    ],
    "Hardware & Tech": [
        ("Ars Technica", "https://feeds.arstechnica.com/arstechnica/index"),
        ("The Verge", "https://www.theverge.com/rss/index.xml"),
    ],
}

MAX_ITEMS_PER_SECTION = 10
MAX_AGE_DAYS = 3
OUT_FILE = os.path.join("docs", "index.html")


def clean(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text or "")
    return html.unescape(re.sub(r"\s+", " ", text)).strip()


def fetch_section(feeds):
    cutoff = time.time() - MAX_AGE_DAYS * 86400
    items, seen_links, seen_titles = [], set(), set()
    for source, url in feeds:
        parsed = feedparser.parse(url)
        for e in parsed.entries:
            link = e.get("link")
            title = clean(e.get("title", ""))
            if not link or not title:
                continue
            ts = time.mktime(e.published_parsed) if e.get("published_parsed") else 0
            if ts and ts < cutoff:
                continue
            key = title.lower()
            if link in seen_links or key in seen_titles:
                continue
            seen_links.add(link)
            seen_titles.add(key)
            items.append({
                "title": title,
                "link": link,
                "source": source,
                "ts": ts,
                "summary": clean(e.get("summary", ""))[:280],
            })
    items.sort(key=lambda x: x["ts"], reverse=True)
    return items[:MAX_ITEMS_PER_SECTION]


def fmt_date(ts):
    if not ts:
        return ""
    return dt.datetime.fromtimestamp(ts).strftime("%b %d, %H:%M")


def render_item(i):
    summary = html.escape(i["summary"]) + ("…" if len(i["summary"]) >= 280 else "")
    return f"""
    <article>
      <h3><a href="{html.escape(i['link'])}" target="_blank" rel="noopener">{html.escape(i['title'])}</a></h3>
      <p class="meta">{html.escape(i['source'])} · {fmt_date(i['ts'])}</p>
      <p class="summary">{summary}</p>
      <a class="source" href="{html.escape(i['link'])}" target="_blank" rel="noopener">Read full article at {html.escape(i['source'])} →</a>
    </article>"""


CSS = """
:root { --bg:#faf8f3; --ink:#1a1a1a; --muted:#6b6b6b; --rule:#d8d3c7; --accent:#8b1e1e; }
@media (prefers-color-scheme: dark) {
  :root { --bg:#141414; --ink:#ececec; --muted:#9a9a9a; --rule:#333; --accent:#e06c6c; }
}
* { box-sizing: border-box; }
body { margin:0; background:var(--bg); color:var(--ink);
       font-family: Georgia, "Times New Roman", serif; line-height:1.5;
       padding: env(safe-area-inset-top) 16px env(safe-area-inset-bottom); }
header { text-align:center; border-bottom:3px double var(--ink); padding:16px 0 10px; }
header h1 { margin:0; font-size:2.2rem; letter-spacing:1px; }
header .date { color:var(--muted); font-family: -apple-system, system-ui, sans-serif; font-size:.85rem; }
nav { display:flex; flex-wrap:wrap; gap:8px 14px; justify-content:center; padding:10px 0;
      border-bottom:1px solid var(--rule); font-family: -apple-system, system-ui, sans-serif; font-size:.85rem; }
nav a { color:var(--accent); text-decoration:none; }
main { max-width:1100px; margin:0 auto; display:grid; gap:24px;
       grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); padding-top:16px; }
section { border-top:2px solid var(--ink); padding-top:8px; }
section > h2 { font-size:1.25rem; text-transform:uppercase; letter-spacing:1px; margin:0 0 6px; color:var(--accent); }
article { border-bottom:1px solid var(--rule); padding:10px 0; }
article h3 { font-size:1.05rem; margin:0 0 4px; line-height:1.3; }
article h3 a { color:var(--ink); text-decoration:none; }
.meta { font-family: -apple-system, system-ui, sans-serif; font-size:.75rem; color:var(--muted); margin:0 0 4px; }
.summary { font-size:.92rem; margin:0 0 6px; }
.source { font-family: -apple-system, system-ui, sans-serif; font-size:.8rem; color:var(--accent); text-decoration:none; }
footer { text-align:center; color:var(--muted); font-size:.75rem; padding:24px 0;
         font-family: -apple-system, system-ui, sans-serif; }
"""


def build():
    now = dt.datetime.now().strftime("%A, %B %d, %Y · %H:%M")
    nav_links, sections_html = [], []
    for name, feeds in SECTIONS.items():
        anchor = re.sub(r"\W+", "-", name.lower()).strip("-")
        items = fetch_section(feeds)
        nav_links.append(f'<a href="#{anchor}">{html.escape(name)}</a>')
        body = "".join(render_item(i) for i in items) or "<p class='meta'>No recent stories found.</p>"
        sections_html.append(f'<section id="{anchor}"><h2>{html.escape(name)}</h2>{body}</section>')

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="My Paper">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<title>My Paper</title>
<style>{CSS}</style>
</head>
<body>
<header>
  <h1>THE DAILY HARDWARE</h1>
  <div class="date">Updated {now}</div>
</header>
<nav>{''.join(nav_links)}</nav>
<main>{''.join(sections_html)}</main>
<footer>Headlines and excerpts come from the publishers listed. Click through to read the full story at its source.</footer>
</body>
</html>"""

    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"Wrote {OUT_FILE}")


if __name__ == "__main__":
    build()