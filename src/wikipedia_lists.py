"""Lean candidate discovery from curated Wikipedia LGBTQ+ fiction lists."""
from __future__ import annotations
import json
import re
import time
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
HEADERS = {"User-Agent": "EuropeanFictionalCharacterResearch/0.4 (research)"}


def scrape(output_dir: str | Path) -> list[dict]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    records, seen = [], set()
    for page in PAGES:
        try:
            response = session.get(API, params={
                "action": "parse", "page": page, "prop": "text",
                "format": "json", "formatversion": 2,
            }, headers=HEADERS, timeout=(15, 90))
            response.raise_for_status()
            payload = response.json()
            html = payload["parse"]["text"]
        except Exception as exc:
            print(f"Wikipedia list unavailable ({page}): {exc}", flush=True)
            continue
        soup = BeautifulSoup(html, "html.parser")
        list_url = "https://en.wikipedia.org/wiki/" + quote(page)
        for table in soup.select("table.wikitable"):
            for tr in table.select("tr"):
                cells = tr.find_all(["th", "td"], recursive=False)
                if not cells or all(c.name == "th" for c in cells):
                    continue
                link = cells[0].find("a", href=re.compile(r"^/wiki/"))
                if not link:
                    continue
                name = link.get_text(" ", strip=True)
                href = link.get("href", "")
                if not name or ":" in href:
                    continue
                row_text = " | ".join(c.get_text(" ", strip=True) for c in cells)
                key = (name.casefold(), page)
                if key in seen:
                    continue
                seen.add(key)
                orientation = page.replace("_", " ").replace("List of fictional ", "").replace("List of ", "")
                records.append({
                    "character": name,
                    "work": row_text,
                    "medium": "Unclassified",
                    "orientation": orientation,
                    "reason": f"Included in Wikipedia's curated list: {page.replace('_', ' ')}.",
                    "source": list_url,
                    "character_reference": "https://en.wikipedia.org" + href,
                })
        print(f"Wikipedia {page}: {len(records):,} candidate rows total", flush=True)
        time.sleep(1.2)
    with (out / "wikipedia_list_candidates.jsonl").open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return records
