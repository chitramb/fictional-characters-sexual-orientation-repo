"""Discovery adapters for community-maintained LGBTQ+ character archives.

These feeds are candidate sources, not independent verification. The source
category and page URL are retained; work origin and exact identity need review.
"""
from __future__ import annotations
import json
import re
import time
from pathlib import Path
from urllib.parse import quote
import requests

HEADERS = {"User-Agent": "EuropeanFictionalCharacterResearch/0.6 (research contact via repository)"}
WIKIS = {
    "Fictional Characters Wiki": "https://characters.fandom.com/api.php",
    "LGBTQIA+ Characters Wikia": "https://lgbtqia-characters.fandom.com/api.php",
}
PREFIXES = ("LGBT", "Gay", "Lesbian", "Bisexual", "Asexual", "Pansexual",
            "Queer", "Transgender", "Non-binary", "Intersex", "Agender")

def _get(session, url, params, attempts=4):
    for attempt in range(attempts):
        try:
            response = session.get(url, params=params, timeout=(15, 60))
            if response.status_code in (429, 500, 502, 503, 504):
                time.sleep(min(45, 5 * (2 ** attempt)))
                continue
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError):
            if attempt + 1 == attempts:
                raise
            time.sleep(min(45, 5 * (2 ** attempt)))
    return {}

def _orientation_from_category(category):
    c = category.casefold()
    for token, label in (("asexual", "Asexual"), ("aromantic", "Aromantic"),
                         ("pansexual", "Pansexual"), ("bisexual", "Bisexual"),
                         ("lesbian", "Lesbian"), ("gay", "Gay"), ("queer", "Queer")):
        if token in c:
            return label, ""
    gender = next((x for x in ("transgender", "trans woman", "trans man",
                                "non-binary", "nonbinary", "agender", "intersex")
                   if x in c), "")
    if gender:
        return "Not stated", f"Category indicates gender identity: {gender}; sexual orientation is not stated."
    return "Not stated", "Listed in a community-maintained LGBTQ+ fictional-character category; precise identity needs review."

def _category_names(session, api):
    names = set()
    for prefix in PREFIXES:
        params = {"action":"query","list":"allcategories","acprefix":prefix,
                  "aclimit":"max","format":"json"}
        while True:
            payload = _get(session, api, params)
            for item in payload.get("query", {}).get("allcategories", []):
                title = item.get("*", "")
                low = title.casefold()
                if "character" in low or "lgbt" in low or "lgbtq" in low:
                    names.add(title)
            cont = payload.get("continue")
            if not cont:
                break
            params.update(cont)
        time.sleep(0.25)
    # Avoid broad unrelated category explosions; prioritize direct identity/character lists.
    return sorted(names, key=lambda x: (0 if "lgbt" in x.casefold() else 1, x.casefold()))[:100]

def _members(session, api, category):
    params = {"action":"query","list":"categorymembers","cmtitle":"Category:"+category,
              "cmtype":"page","cmlimit":"max","format":"json"}
    while True:
        payload = _get(session, api, params)
        for item in payload.get("query", {}).get("categorymembers", []):
            yield item.get("title", "")
        cont = payload.get("continue")
        if not cont:
            break
        params.update(cont)

def scrape_community_wikis(output_dir: str | Path) -> list[dict]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update(HEADERS)
    records = {}
    for wiki_name, api in WIKIS.items():
        try:
            categories = _category_names(session, api)
        except Exception as exc:
            print(f"{wiki_name} category discovery unavailable: {exc}", flush=True)
            continue
        print(f"{wiki_name}: scanning {len(categories)} LGBTQ character categories", flush=True)
        for category in categories:
            try:
                for title in _members(session, api, category):
                    if not title or title.startswith(("Category:", "File:", "Template:", "User:")):
                        continue
                    key = (wiki_name, title.casefold())
                    orientation, reason = _orientation_from_category(category)
                    record = records.setdefault(key, {
                        "character": title,
                        "work": "",
                        "medium": "Unclassified",
                        "year": None,
                        "country": "",
                        "orientation": orientation,
                        "reason": reason,
                        "source": api.split("/api.php")[0] + "/wiki/" + quote(title.replace(" ", "_")),
                    })
                    if record["orientation"] == "Not stated" and orientation != "Not stated":
                        record["orientation"] = orientation
                        record["reason"] = f"Listed in {category}; sexual orientation label: {orientation}."
            except Exception as exc:
                print(f"{wiki_name} category '{category}' skipped: {exc}", flush=True)
            time.sleep(0.2)
        print(f"{wiki_name}: {sum(1 for k in records if k[0] == wiki_name):,} page candidates", flush=True)
    result = list(records.values())
    with (out / "community_wiki_candidates.jsonl").open("w", encoding="utf-8") as handle:
        for row in result:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return result
