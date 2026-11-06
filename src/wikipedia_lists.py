"""Discover LGBTQ+ fictional characters from curated, medium-specific lists.

These are candidate records. The table's identity/notes and linked character page
are retained as leads; final verification must cite an underlying reliable source.
"""
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
    # Individual-character lists by orientation
    "List_of_fictional_gay_characters",
    "List_of_fictional_lesbian_characters",
    "List_of_fictional_bisexual_characters",
    "List_of_fictional_pansexual_characters",
    "List_of_fictional_asexual_characters",
    "List_of_fictional_aromantic_characters",
    "List_of_LGBTQ_characters_in_modern_written_fiction",
    "List_of_gay_characters_in_television",
    "List_of_lesbian_characters_in_television",
    "List_of_bisexual_characters_in_television",
    "List_of_gay_characters_in_animation",
    "List_of_lesbian_characters_in_animation",
    "List_of_bisexual_characters_in_animation",
    "List_of_graphic_art_works_with_LGBTQ_characters",
    "List_of_video_games_with_LGBTQ_characters",
    "List_of_webcomics_with_LGBT_characters",
]
HEADERS = {"User-Agent": "EuropeanFictionalCharacterResearch/0.5 (research)"}
YEAR_RE = re.compile(r"(?<!\\d)(18\\d{2}|19\\d{2}|20\\d{2})(?!\\d)")


def _norm(value: str) -> str:
    return re.sub(r"\\s+", " ", value or "").strip().casefold()


def _medium(page: str) -> str:
    p = page.casefold()
    if "animation" in p:
        return "Animation"
    if "television" in p:
        return "TV"
    if "video_game" in p:
        return "Video game"
    if any(x in p for x in ("graphic_art", "webcomic")):
        return "Comics"
    if "written_fiction" in p:
        return "Book"
    return "Unclassified"


def _orientation(page: str, identity_cell: str = "") -> str:
    if identity_cell and identity_cell.strip() not in {"—", "-", "N/A"}:
        return identity_cell.strip()
    p = page.casefold()
    for token, label in (
        ("asexual", "Asexual"), ("aromantic", "Aromantic"),
        ("pansexual", "Pansexual"), ("bisexual", "Bisexual"),
        ("lesbian", "Lesbian"), ("gay", "Gay"),
    ):
        if token in p:
            return label
    return "LGBTQ+ (specific orientation not stated in list title)"


def scrape(output_dir: str | Path) -> list[dict]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    records: list[dict] = []
    seen: set[tuple[str, str]] = set()

    for page in PAGES:
        try:
            response = session.get(
                API,
                params={"action": "parse", "page": page, "prop": "text",
                        "format": "json", "formatversion": 2},
                headers=HEADERS, timeout=(15, 90),
            )
            response.raise_for_status()
            html = response.json()["parse"]["text"]
        except Exception as exc:
            print(f"Wikipedia list unavailable ({page}): {exc}", flush=True)
            continue

        soup = BeautifulSoup(html, "html.parser")
        list_url = "https://en.wikipedia.org/wiki/" + quote(page)
        page_count = 0
        for table in soup.select("table.wikitable"):
            header_row = table.find("tr")
            headers = [_norm(c.get_text(" ", strip=True))
                       for c in header_row.find_all(["th", "td"], recursive=False)] if header_row else []

            def col_index(words: tuple[str, ...]) -> int | None:
                for i, h in enumerate(headers):
                    if any(w in h for w in words):
                        return i
                return None

            char_idx = col_index(("character", "characters", "name"))
            work_idx = col_index(("title", "work", "show", "series", "novel", "game", "comic"))
            identity_idx = col_index(("identity", "sexuality", "orientation", "gender"))
            year_idx = col_index(("year", "date", "debut", "duration", "years"))
            country_idx = col_index(("country", "origin", "nation"))
            notes_idx = col_index(("notes", "description", "details"))

            for tr in table.select("tr"):
                cells = tr.find_all(["th", "td"], recursive=False)
                if not cells or all(c.name == "th" for c in cells):
                    continue
                # If this is a work-level table without a character column, do
                # not mistake titles or dates for character names.
                if char_idx is None:
                    if headers and not any(x in " ".join(headers) for x in ("character", "characters")):
                        continue
                    char_idx = 0
                if char_idx >= len(cells):
                    continue
                char_cell = cells[char_idx]
                links = char_cell.find_all("a", href=re.compile(r"^/wiki/"))
                for link in links:
                    name = link.get_text(" ", strip=True)
                    href = link.get("href", "")
                    if not name or ":" in href:
                        continue
                    key = (name.casefold(), page)
                    if key in seen:
                        continue
                    seen.add(key)

                    def cell_text(index: int | None) -> str:
                        return cells[index].get_text(" ", strip=True) if index is not None and index < len(cells) else ""

                    identity = _orientation(page, cell_text(identity_idx))
                    work = cell_text(work_idx)
                    if not work and len(cells) > 1:
                        work = " | ".join(c.get_text(" ", strip=True) for i, c in enumerate(cells) if i != char_idx)
                    year_text = cell_text(year_idx)
                    years = YEAR_RE.findall(year_text or " ".join(c.get_text(" ", strip=True) for c in cells))
                    country = cell_text(country_idx)
                    notes = cell_text(notes_idx)
                    reason = f"Listed as {identity} in the curated Wikipedia character list."
                    if notes:
                        reason += " " + notes[:350]
                    records.append({
                        "character": name,
                        "work": work,
                        "medium": _medium(page),
                        "year": int(years[0]) if years else None,
                        "country": country,
                        "orientation": identity,
                        "reason": reason,
                        "source": list_url,
                        "character_reference": "https://en.wikipedia.org" + href,
                    })
                    page_count += 1
        print(f"Wikipedia {page}: {page_count:,} new candidates; {len(records):,} total", flush=True)
        time.sleep(1.2)

    with (out / "wikipedia_list_candidates.jsonl").open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return records
