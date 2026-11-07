"""Neutral, work-linked fictional-character discovery from Wikidata.

Discovery does not depend on sexual orientation or gender. P91 and P21 are
optional enrichment fields and remain separate. Records are candidates, not
verified identity claims or automatically Europe-eligible observations.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from .wikidata import query_wikidata, binding, normalize_binding

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
       ?medium ?orientationLabel ?genderLabel ?date
WHERE {{
  VALUES (?workClass ?medium) {{ {classes} }}
  ?work wdt:P31/wdt:P279* ?workClass;
        wdt:P577 ?date.
  OPTIONAL {{ ?work wdt:P495 ?country. }}
  FILTER(?date >= "{start_year}-01-01T00:00:00Z"^^xsd:dateTime &&
         ?date < "{end_year}-01-01T00:00:00Z"^^xsd:dateTime)
  ?character wdt:P31/wdt:P279* wd:Q95074.
  {{ ?character wdt:P1441 ?work. }} UNION {{ ?work wdt:P674 ?character. }}
  OPTIONAL {{ ?character wdt:P91 ?orientation. }}
  OPTIONAL {{ ?character wdt:P21 ?gender. }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}}
"""

def _record(row: dict) -> dict | None:
    date = binding(row, "date")
    if len(date) < 4 or not date[:4].isdigit():
        return None
    qid = normalize_binding(row, "character")
    if not qid:
        return None
    orientation = binding(row, "orientationLabel") or "Not stated"
    gender = binding(row, "genderLabel") or "Not stated"
    evidence = []
    if orientation != "Not stated":
        evidence.append(f"Wikidata P91 label: {orientation}.")
    if gender != "Not stated":
        evidence.append(f"Wikidata P21 (sex or gender) label: {gender}.")
    return {
        "character": binding(row, "characterLabel"),
        "work": binding(row, "workLabel"),
        "medium": binding(row, "medium"),
        "year": int(date[:4]),
        "country": binding(row, "countryLabel"),
        "orientation": orientation,
        "gender_identity": gender,
        "reason": " ".join(evidence) if evidence else "Neutral character/work link; no P91 or P21 value returned.",
        "source": f"https://www.wikidata.org/wiki/{qid}",
        "source_id": qid,
        "source_name": "Wikidata",
        "evidence_status": "candidate",
    }

def scrape_wikidata_characters(
    output_dir: str | Path, start_year: int = 1900, end_year: int = 2027,
    bucket_years: int = 5,
) -> list[dict]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    records: dict[tuple[str, str, str, int], dict] = {}
    checkpoint = out / "wikidata_character_candidates.jsonl"
    for start in range(start_year, end_year, bucket_years):
        stop = min(start + bucket_years, end_year)
        try:
            rows = query_wikidata(build_query(start, stop), timeout=180, attempts=5)
            for row in rows:
                record = _record(row)
                if not record or not record["character"]:
                    continue
                key = (record["source_id"], record["work"].casefold(),
                       record["medium"], record["year"])
                records.setdefault(key, record)
            print(
                f"Wikidata {start}-{stop-1}: {len(rows):,} rows; "
                f"{len(records):,} unique character-work candidates",
                flush=True,
            )
        except Exception as exc:
            print(f"Wikidata partition {start}-{stop-1} failed: {exc}", flush=True)
        # Persist every completed/partially completed set so interruptions are recoverable.
        tmp = checkpoint.with_suffix(".jsonl.tmp")
        with tmp.open("w", encoding="utf-8") as handle:
            for record in records.values():
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        tmp.replace(checkpoint)
        time.sleep(2)
    return list(records.values())
