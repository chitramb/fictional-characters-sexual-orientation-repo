"""Broader LGBTQ+ fictional-character extraction from Wikidata.

Sexual orientation (P91) and gender identity (P21) are queried in separate
branches and never conflated. Records are candidates until statement references
and character/work links are reviewed.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from .wikidata import query_wikidata, binding, normalize_binding

GENDER_FILTER = "trans|non.?binary|agender|genderfluid|genderqueer|intersex"
ORIENTATION_FILTER = "heterosexual|straight|gay|lesbian|bisexual|pansexual|asexual|aromantic|queer|demisexual|graysexual|greysexual|polysexual|omnisexual|abrosexual|homosexual"

WORK_CLASSES = [
    ("Q11424", "Film"), ("Q5398426", "TV"), ("Q526877", "TV"),
    ("Q581714", "TV"), ("Q571", "Book"), ("Q7725634", "Book"),
    ("Q47461344", "Book"), ("Q1004", "Comics"), ("Q838795", "Comics"),
    ("Q725377", "Comics"), ("Q7889", "Video game"),
]

def build_query(start_year: int, end_year: int) -> str:
    classes = " ".join(f'(wd:{qid} "{medium}")' for qid, medium in WORK_CLASSES)
    return f"""
SELECT DISTINCT ?character ?characterLabel ?work ?workLabel ?country ?countryLabel
       ?medium ?orientation ?orientationLabel ?gender ?genderLabel ?date
WHERE {{
  VALUES (?workClass ?medium) {{ {classes} }}
  ?work wdt:P31/wdt:P279* ?workClass;
        wdt:P577 ?date;
        wdt:P495 ?country.
  ?country wdt:P30 wd:Q46.
  FILTER(?date >= "{start_year}-01-01T00:00:00Z"^^xsd:dateTime &&
         ?date < "{end_year}-01-01T00:00:00Z"^^xsd:dateTime)
  ?character wdt:P31/wdt:P279* wd:Q95074.
  {{
    ?character wdt:P91 ?orientation.
  }} UNION {{
    ?character wdt:P21 ?gender.
  }}
  {{ ?character wdt:P1441 ?work. }} UNION {{ ?work wdt:P674 ?character. }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
  FILTER(
    (BOUND(?orientation) && REGEX(STR(?orientationLabel), "{ORIENTATION_FILTER}", "i")) ||
    (BOUND(?gender) && REGEX(STR(?genderLabel), "{GENDER_FILTER}", "i"))
  )
}}
"""

def _record(row: dict) -> dict | None:
    date = binding(row, "date")
    if len(date) < 4 or not date[:4].isdigit():
        return None
    orientation = binding(row, "orientationLabel")
    gender = binding(row, "genderLabel")
    if orientation:
        label = orientation
        reason = f"Wikidata records sexual orientation as {orientation} (P91)."
    elif gender:
        label = "Not stated"
        reason = f"Wikidata records gender identity as {gender} (P21); sexual orientation is not stated."
    else:
        return None
    qid = normalize_binding(row, "character")
    return {
        "character": binding(row, "characterLabel"),
        "work": binding(row, "workLabel"),
        "medium": binding(row, "medium"),
        "year": int(date[:4]),
        "country": binding(row, "countryLabel"),
        "orientation": label,
        "reason": reason,
        "source": f"https://www.wikidata.org/wiki/{qid}",
    }

def scrape_wikidata_characters(output_dir: str | Path, start_year: int = 1900, end_year: int = 2027) -> list[dict]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    records: dict[tuple[str, str, str, int], dict] = {}
    checkpoint = out / "wikidata_character_candidates.jsonl"
    for start in range(start_year, end_year, 20):
        stop = min(start + 20, end_year)
        query = build_query(start, stop)
        try:
            rows = query_wikidata(query, timeout=120, attempts=3)
            for row in rows:
                record = _record(row)
                if not record or not record["character"]:
                    continue
                key = (record["character"].casefold(), record["work"].casefold(),
                       record["medium"], record["year"])
                records.setdefault(key, record)
            print(f"Wikidata {start}-{stop-1}: {len(rows):,} rows; {len(records):,} unique character-work candidates", flush=True)
        except Exception as exc:
            print(f"Wikidata partition {start}-{stop-1} failed: {exc}", flush=True)
        with checkpoint.open("w", encoding="utf-8") as handle:
            for record in records.values():
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        time.sleep(3)
    return list(records.values())
