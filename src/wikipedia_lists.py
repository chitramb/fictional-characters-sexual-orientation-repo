"""Candidate discovery from curated Wikipedia LGBTQ+ fiction list pages.

Rows are discovery leads only. The scraper does not infer an identity from a
name or page title and does not promote records to verified status.
"""
from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

API = "https://en.wikipedia.org/w/api.php"
PAGES = [
    "List_of_fictional_gay_characters",
    "List_of_fictional_lesbian_characters",
    "List_of_fictional_bisexual_characters",
    "List_of_LGBTQ_characters_in_modern_written_fiction",
    "List_of_gay_characters_in_television",
    "List_of_lesbian_characters_in_television",
    "List_of_bisexual_characters_in_television",
    "List_of_animated_series_with_LGBTQ_characters",
    "List_of_made-for-television_films_with_LGBTQ_characters",
    "Lists_of_LGBTQ_figures_in_fiction_and_myth",
]
HEADERS = {"User-Agent": "EuropeanFictionalCharacterResearch/0.3 (research)"}


def fetch_page(session: requests.Session, title: str) -> str:
    response = session.get(API, params={
        "action": "parse", "page": title, "prop": "text", "format": "json",
        "formatversion": 2,
    }, headers=HEADERS, timeout=(15, 90))
    response.raise_for_status()
    payload = response.json()
    if "error" in payload:
        raise ValueError(payload["error"])
    return payload["parse"]["text"]


def scrape(output_dir: str | Path) -> list[dict]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    retrieved = datetime.now(timezone.utc).isoformat()
    candidates = []
    for title in PAGES:
        try:
            html = fetch_page(session, title)
        except Exception as exc:
            print(f"Wikipedia list unavailable ({title}): {exc}", flush=True)
            continue
        soup = BeautifulSoup(html, "html.parser")
        for table_index, table in enumerate(soup.select("table.wikitable")):
            for row_index, tr in enumerate(table.select("tr")):
                cells = tr.find_all(["th", "td"], recursive=False)
                if not cells or all(c.name == "th" for c in cells):
                    continue
                first = cells[0]
                link = first.find("a", href=re.compile(r"^/wiki/"))
                if not link:
                    continue
                name = link.get_text(" ", strip=True)
                href = link.get("href", "")
                if not name or ":" in href:
                    continue
                candidates.append({
                    "source": "Wikipedia curated list",
                    "source_page": title.replace("_", " "),
                    "source_url": "https://en.wikipedia.org/wiki/" + quote(title),
                    "source_row": row_index,
                    "table_index": table_index,
                    "candidate_name": name,
                    "candidate_article_url": "https://en.wikipedia.org" + href,
                    "row_text": " | ".join(c.get_text(" ", strip=True) for c in cells),
                    "retrieved_at": retrieved,
                    "verification_status": "candidate",
                })
        time.sleep(1.2)  # be polite to Wikimedia API
        print(f"Wikipedia {title}: {len(candidates):,} cumulative table candidates", flush=True)

    # Exact duplicate page/character rows are removed; different list-page
    # memberships remain as separate provenance records.
    seen = set()
    unique = []
    for row in candidates:
        key = (row["source_page"], row["candidate_article_url"], row["row_text"])
        if key not in seen:
            seen.add(key)
            unique.append(row)
    path = out / "wikipedia_list_candidates.jsonl"
    with path.open("w", encoding="utf-8") as handle:
        for row in unique:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"Wikipedia list candidate rows: {len(unique):,}", flush=True)
    return unique
