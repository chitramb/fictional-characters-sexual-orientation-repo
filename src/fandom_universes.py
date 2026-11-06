"""Broad, universe-first discovery from general Fandom wikis.

This deliberately starts from ordinary universe character categories rather than
LGBTQ-specific lists. Orientation is recorded only when a character page itself
contains an explicit orientation/sexuality field. Missing values stay unknown.
"""
from __future__ import annotations
import json
import re
import time
from pathlib import Path
from urllib.parse import quote
import requests

UNIVERSES = [
    ("Harry Potter", "https://harrypotter.fandom.com/api.php", "Book/film", "Harry Potter"),
    ("Marvel", "https://marvel.fandom.com/api.php", "Comics/film/TV", "Marvel"),
    ("DC", "https://dc.fandom.com/api.php", "Comics/film/TV", "DC"),
    ("Star Wars", "https://starwars.fandom.com/api.php", "Film/TV/books", "Star Wars"),
    ("Doctor Who", "https://tardis.fandom.com/api.php", "TV", "Doctor Who"),
    ("Middle-earth", "https://lotr.fandom.com/api.php", "Book/film/TV", "The Lord of the Rings"),
    ("Star Trek", "https://memory-alpha.fandom.com/api.php", "TV/film", "Star Trek"),
    ("Buffy", "https://buffy.fandom.com/api.php", "TV", "Buffy the Vampire Slayer"),
    ("Supernatural", "https://supernatural.fandom.com/api.php", "TV", "Supernatural"),
    ("Sherlock", "https://sherlockbbc.fandom.com/api.php", "TV", "Sherlock"),
    ("Game of Thrones", "https://gameofthrones.fandom.com/api.php", "TV/book", "A Song of Ice and Fire / Game of Thrones"),
    ("The Walking Dead", "https://walkingdead.fandom.com/api.php", "Comics/TV", "The Walking Dead"),
    ("Avatar", "https://avatar.fandom.com/api.php", "Animation", "Avatar: The Last Airbender"),
    ("Pokémon", "https://pokemon.fandom.com/api.php", "Animation/game", "Pokémon"),
    ("Dragon Ball", "https://dragonball.fandom.com/api.php", "Animation/manga", "Dragon Ball"),
    ("One Piece", "https://onepiece.fandom.com/api.php", "Animation/manga", "One Piece"),
    ("Naruto", "https://naruto.fandom.com/api.php", "Animation/manga", "Naruto"),
    ("Zelda", "https://zelda.fandom.com/api.php", "Video game", "The Legend of Zelda"),
    ("Final Fantasy", "https://finalfantasy.fandom.com/api.php", "Video game", "Final Fantasy"),
    ("League of Legends", "https://leagueoflegends.fandom.com/api.php", "Video game", "League of Legends"),
    ("Overwatch", "https://overwatch.fandom.com/api.php", "Video game", "Overwatch"),
    ("Danganronpa", "https://danganronpa.fandom.com/api.php", "Video game", "Danganronpa"),
    ("The Witcher", "https://witcher.fandom.com/api.php", "Book/game/TV", "The Witcher"),
    ("Discworld", "https://discworld.fandom.com/api.php", "Book", "Discworld"),
    ("Asterix", "https://asterix.fandom.com/api.php", "Comics/film", "Asterix"),
    ("Tintin", "https://tintin.fandom.com/api.php", "Comics/film/TV", "The Adventures of Tintin"),
    ("The Simpsons", "https://simpsons.fandom.com/api.php", "Animation", "The Simpsons"),
    ("Futurama", "https://futurama.fandom.com/api.php", "Animation", "Futurama"),
    ("Disney", "https://disney.fandom.com/api.php", "Animation/film", "Disney"),
    ("Pixar", "https://pixar.fandom.com/api.php", "Animation/film", "Pixar"),
    ("Adventure Time", "https://adventuretime.fandom.com/api.php", "Animation", "Adventure Time"),
    ("Steven Universe", "https://steven-universe.fandom.com/api.php", "Animation", "Steven Universe"),
    ("My Little Pony", "https://mlp.fandom.com/api.php", "Animation", "My Little Pony"),
    ("RWBY", "https://rwby.fandom.com/api.php", "Animation", "RWBY"),
    ("Hazbin Hotel", "https://hazbinhotel.fandom.com/api.php", "Animation", "Hazbin Hotel"),
    ("Gundam", "https://gundam.fandom.com/api.php", "Animation", "Mobile Suit Gundam"),
]
HEADERS = {"User-Agent": "EuropeanFictionalCharacterResearch/0.7 (universe-first open research)"}
ORIENTATION_VALUES = (
    "homosexual", "heterosexual", "straight", "bisexual", "pansexual", "asexual",
    "demisexual", "graysexual", "greysexual", "queer", "lesbian", "gay",
    "aromantic", "polysexual", "omnisexual", "abrosexual",
)
FIELD_RE = re.compile(
    r"(?:sexuality|sexual orientation)\s*[:=]\s*([^|}\n<]{2,80})",
    re.I,
)
LABEL_RE = re.compile(
    r"\b(" + "|".join(map(re.escape, ORIENTATION_VALUES)) + r")\b", re.I
)

def _get(session, api, params, attempts=4):
    for attempt in range(attempts):
        try:
            response = session.get(api, params=params, timeout=(15, 75))
            if response.status_code in (429, 500, 502, 503, 504):
                time.sleep(min(60, 6 * (2 ** attempt)))
                continue
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError):
            if attempt + 1 == attempts:
                raise
            time.sleep(min(60, 6 * (2 ** attempt)))
    return {}

def _character_categories(session, api):
    params = {"action":"query","list":"allcategories","aclimit":"max","format":"json"}
    found = []
    while True:
        payload = _get(session, api, params)
        for item in payload.get("query", {}).get("allcategories", []):
            title = item.get("*", "")
            low = title.casefold()
            identity_category = re.search(
                r"\b(lgbtq?|gay|lesbian|bisexual|pansexual|asexual|aromantic|queer|transgender|non.?binary|intersex)\b",
                low,
            )
            if "character" in low and not identity_category:
                found.append(title)
        cont = payload.get("continue")
        if not cont:
            break
        params.update(cont)
    # Prioritize the broad category itself and then subcategories with likely character pages.
    return sorted(set(found), key=lambda x: (0 if x.casefold() in
                   ("characters", "fictional characters", "main characters") else 1, x.casefold()))[:35]

def _category_pages(session, api, category, max_depth=2):
    queue = [(category, 0)]
    visited = set()
    while queue:
        current, depth = queue.pop(0)
        if current.casefold() in visited:
            continue
        visited.add(current.casefold())
        params = {
            "action": "query", "list": "categorymembers",
            "cmtitle": "Category:" + current,
            "cmtype": "page|subcat", "cmlimit": "max", "format": "json",
        }
        while True:
            payload = _get(session, api, params)
            for item in payload.get("query", {}).get("categorymembers", []):
                title = item.get("title", "")
                if not title:
                    continue
                if item.get("ns") == 14 or title.startswith("Category:"):
                    if depth < max_depth:
                        queue.append((title.removeprefix("Category:"), depth + 1))
                elif not title.startswith(("File:", "Template:", "User:")):
                    yield title
            cont = payload.get("continue")
            if not cont:
                break
            params.update(cont)
        time.sleep(0.1)

def _extract_pages(session, api, titles):
    for offset in range(0, len(titles), 20):
        batch = titles[offset:offset+20]
        params = {
            "action": "query", "prop": "revisions", "rvprop": "content",
            "rvslots": "main", "titles": "|".join(batch), "format": "json",
        }
        payload = _get(session, api, params)
        pages = payload.get("query", {}).get("pages", {})
        for page in pages.values():
            revisions = page.get("revisions", [])
            if not revisions:
                continue
            revision = revisions[0]
            main = revision.get("slots", {}).get("main", {})
            page["wikitext"] = main.get("*") or main.get("content") or revision.get("*") or ""
            yield page
        time.sleep(0.15)

def _orientation(extract):
    # Only accept an explicit infobox-like field, never an isolated identity word
    # somewhere in plot text, cast details, or an actor's biography.
    for line in extract.splitlines():
        match = FIELD_RE.search(line)
        if not match:
            continue
        value = match.group(1).strip(" .;,*")
        labels = [x.casefold() for x in LABEL_RE.findall(value)]
        if labels and not re.search(r"\\b(?:not|never|non)\\s+(?:gay|lesbian|bisexual|pansexual|asexual|queer|homosexual)\\b", value, re.I):
            label = "; ".join(dict.fromkeys(labels))
            return label, f"Character page explicitly gives sexuality/orientation as {label}."
    return "Not stated", "Character discovered from a general-universe character category; page has no explicit orientation field."

def scrape_fandom_universes(output_dir: str | Path) -> list[dict]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update(HEADERS)
    records = {}
    for universe, api, medium, work in UNIVERSES:
        try:
            categories = _character_categories(session, api)
        except Exception as exc:
            print(f"Fandom {universe}: category scan failed: {exc}", flush=True)
            continue
        titles = set()
        for category in categories:
            try:
                titles.update(_category_pages(session, api, category))
            except Exception as exc:
                print(f"Fandom {universe}: category {category} skipped: {exc}", flush=True)
            time.sleep(0.1)
        title_list = sorted(titles)
        print(f"Fandom {universe}: {len(title_list):,} character-page candidates from {len(categories)} general categories", flush=True)
        try:
            for page in _extract_pages(session, api, title_list):
                title = page.get("title", "")
                if not title:
                    continue
                orientation, reason = _orientation(page.get("extract", ""))
                url = api.split("/api.php")[0] + "/wiki/" + quote(title.replace(" ", "_"))
                records[(universe, title.casefold())] = {
                    "character": title,
                    "work": work,
                    "medium": medium,
                    "year": None,
                    "country": "",
                    "orientation": orientation,
                    "reason": reason,
                    "source": url,
                }
        except Exception as exc:
            print(f"Fandom {universe}: page extraction incomplete: {exc}", flush=True)
        print(f"Fandom {universe}: {sum(1 for k in records if k[0] == universe):,} extracted", flush=True)
    result = list(records.values())
    with (out / "fandom_universe_candidates.jsonl").open("w", encoding="utf-8") as handle:
        for row in result:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return result
