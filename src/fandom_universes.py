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
    ("Percy Jackson", "https://riordan.fandom.com/api.php", "Book/film/TV", "Percy Jackson"),
    ("The Hunger Games", "https://thehungergames.fandom.com/api.php", "Book/film", "The Hunger Games"),
    ("Twilight", "https://twilightsaga.fandom.com/api.php", "Book/film", "The Twilight Saga"),
    ("The Chronicles of Narnia", "https://narnia.fandom.com/api.php", "Book/film", "The Chronicles of Narnia"),
    ("His Dark Materials", "https://hisdarkmaterials.fandom.com/api.php", "Book/TV", "His Dark Materials"),
    ("Moomin", "https://moomin.fandom.com/api.php", "Book/animation", "Moomin"),
    ("Sailor Moon", "https://sailormoon.fandom.com/api.php", "Manga/animation", "Sailor Moon"),
    ("JoJo's Bizarre Adventure", "https://jojo.fandom.com/api.php", "Manga/animation", "JoJo's Bizarre Adventure"),
    ("Death Note", "https://deathnote.fandom.com/api.php", "Manga/animation", "Death Note"),
    ("Attack on Titan", "https://attackontitan.fandom.com/api.php", "Manga/animation", "Attack on Titan"),
    ("My Hero Academia", "https://myheroacademia.fandom.com/api.php", "Manga/animation", "My Hero Academia"),
    ("Fairy Tail", "https://fairytail.fandom.com/api.php", "Manga/animation", "Fairy Tail"),
    ("Demon Slayer", "https://kimetsu-no-yaiba.fandom.com/api.php", "Manga/animation", "Demon Slayer"),
    ("Genshin Impact", "https://genshin-impact.fandom.com/api.php", "Video game", "Genshin Impact"),
    ("Honkai: Star Rail", "https://honkai-star-rail.fandom.com/api.php", "Video game", "Honkai: Star Rail"),
    ("The Elder Scrolls", "https://elderscrolls.fandom.com/api.php", "Video game", "The Elder Scrolls"),
    ("Fallout", "https://fallout.fandom.com/api.php", "Video game", "Fallout"),
    ("Elden Ring", "https://eldenring.fandom.com/api.php", "Video game", "Elden Ring"),
    ("Minecraft", "https://minecraft.fandom.com/api.php", "Video game", "Minecraft"),
    ("Sonic the Hedgehog", "https://sonic.fandom.com/api.php", "Video game/animation", "Sonic the Hedgehog"),
    ("Mario", "https://mario.fandom.com/api.php", "Video game", "Super Mario"),
    ("SpongeBob SquarePants", "https://spongebob.fandom.com/api.php", "Animation", "SpongeBob SquarePants"),
    ("Gravity Falls", "https://gravityfalls.fandom.com/api.php", "Animation", "Gravity Falls"),
    ("Regular Show", "https://regularshow.fandom.com/api.php", "Animation", "Regular Show"),
    ("The Owl House", "https://theowlhouse.fandom.com/api.php", "Animation", "The Owl House"),
    ("Amphibia", "https://amphibia.fandom.com/api.php", "Animation", "Amphibia"),
    ("Rick and Morty", "https://rickandmorty.fandom.com/api.php", "Animation", "Rick and Morty"),
    ("Merlin", "https://merlin.fandom.com/api.php", "TV", "Merlin"),
    ("Downton Abbey", "https://downtonabbey.fandom.com/api.php", "TV", "Downton Abbey"),
    ("James Bond", "https://jamesbond.fandom.com/api.php", "Film/book", "James Bond"),
    ("Dune", "https://dune.fandom.com/api.php", "Book/film/TV", "Dune"),
    ("Warhammer 40,000", "https://warhammer40k.fandom.com/api.php", "Tabletop/game/fiction", "Warhammer 40,000"),
]
HEADERS = {"User-Agent": "EuropeanFictionalCharacterResearch/0.7 (universe-first open research)"}
ORIENTATION_VALUES = (
    "homosexual", "heterosexual", "straight", "bisexual", "pansexual", "asexual",
    "demisexual", "graysexual", "greysexual", "queer", "lesbian", "gay",
    "aromantic", "polysexual", "omnisexual", "abrosexual",
)
FIELD_RE = re.compile(
    r"(?im)^\s*\|\s*(?:sexuality|sexual\s+orientation)\s*=\s*(.*?)(?=\n\s*\||\n\s*\}\}|$)",
)
LABEL_RE = re.compile(
    r"\b(" + "|".join(map(re.escape, ORIENTATION_VALUES)) + r")\b", re.I
)

def _get(session, api, params, attempts=4):
    for attempt in range(attempts):
        try:
            response = session.get(api, params=params, timeout=(12, 35))
            if response.status_code in (401, 403, 404):
                return {}
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
            title = item.get("category") or item.get("*") or item.get("title", "")
            low = title.casefold()
            identity_category = re.search(
                r"\b(lgbtq?|gay|lesbian|bisexual|pansexual|asexual|aromantic|queer|transgender|non.?binary|intersex)\b",
                low,
            )
            if "character" in low and not identity_category:
                found.append((title, int(item.get("size", 0) or 0)))
        cont = payload.get("continue")
        if not cont:
            break
        params.update(cont)
    # Prioritize broad categories, then the largest ordinary character categories.
    # An alphabetical cap discarded most useful categories in large wikis.
    unique = {name: size for name, size in found}
    ordered = sorted(unique.items(), key=lambda item: (
        0 if item[0].casefold() in ("characters", "fictional characters", "main characters") else 1,
        -item[1], item[0].casefold()))
    return [name for name, _ in ordered[:300]]

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
            "action": "query", "prop": "revisions", "rvprop": "ids|timestamp|content",
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
            page["source_revision_id"] = revision.get("revid")
            page["source_revision_timestamp"] = revision.get("timestamp")
            yield page
        time.sleep(0.15)

def _orientation(extract):
    # Only accept an explicit infobox-like field, never an isolated identity word
    # somewhere in plot text, cast details, or an actor's biography.
    for match in FIELD_RE.finditer(extract):
        value = match.group(1).strip(" .;,*")
        value = re.sub(r"\[\[([^]|]+)(?:\|([^]]+))?\]\]", lambda m: m.group(2) or m.group(1), value)
        value = re.sub(r"\{\{[^{}]*\}\}", " ", value)
        value = re.sub(r"<[^>]+>", " ", value)
        labels = [x.casefold() for x in LABEL_RE.findall(value)]
        if labels and not re.search(r"\b(?:not|never|non)\s+(?:gay|lesbian|bisexual|pansexual|asexual|queer|homosexual)\b", value, re.I):
            label = "; ".join(dict.fromkeys(labels))
            return label, f"Character page explicitly gives sexuality/orientation as {label}; field value: {value[:160]}."
    return "Not stated", "Character discovered from a general-universe character category; page has no explicit orientation field."

def scrape_fandom_universes(output_dir: str | Path) -> list[dict]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    checkpoint = out / "fandom_universe_candidates.jsonl"
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
                orientation, reason = _orientation(page.get("wikitext", ""))
                url = api.split("/api.php")[0] + "/wiki/" + quote(title.replace(" ", "_"))
                records[(universe, title.casefold())] = {
                    "character": title,
                    "source_name": f"Fandom:{universe}",
                    "source_id": f"fandom:{universe.casefold()}:{page.get(\"pageid\", title.casefold())}",
                    "source_revision_id": revision.get("revid"),
                    "source_retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "work": work,
                    "medium": medium,
                    "year": None,
                    "country": "",
                    "orientation": orientation,
                    "reason": reason,
                    "source": url,
                    "evidence_status": "candidate",
                }
        except Exception as exc:
            print(f"Fandom {universe}: page extraction incomplete: {exc}", flush=True)
        print(f"Fandom {universe}: {sum(1 for k in records if k[0] == universe):,} extracted", flush=True)
        with checkpoint.open("w", encoding="utf-8") as handle:
            for row in records.values():
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return list(records.values())
