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

ORIENTATIONS = [
    "Q6636", "Q43200", "Q724351", "Q271534", "Q23912283", "Q8354594",
    "Q339014", "Q51415", "Q592", "Q25447263", "Q25326668", "Q19810527",
    "Q106589379", "Q2094204", "Q97180617", "Q20011275", "Q43850015",
    "Q43850027", "Q89364372", "Q115068942", "Q255155", "Q116820152",
    "Q3626860", "Q116286410", "Q116295197", "Q116280707", "Q108472356",
]
GENDER_IDENTITIES = [
    "Q189125", "Q1052281", "Q2449503", "Q48270", "Q1097630",
    "Q1399232", "Q3277905", "Q746411", "Q350374", "Q660882",
]
WORK_CLASSES = [
    ("Q11424", "Film"), ("Q5398426", "TV"), ("Q526877", "TV"),
    ("Q581714", "TV"), ("Q571", "Book"), ("Q7725634", "Book"),
    ("Q47461344", "Book"), ("Q1004", "Comics"), ("Q838795", "Comics"),
    ("Q725377", "Comics"), ("Q7889", "Video game"),
]

def build_query(start_year: int, end_year: int) -> str:
    classes = " ".join(f"(wd:{qid} \"{medium}\")" for qid, medium in WORK_CLASSES)
    orientations = " ".join(f"wd:{qid}" for qid in ORIENTATIONS)
    genders = " ".join(f"wd:{qid}" for qid in GENDER_IDENTITIES)
    return f"""
SELECT ?character ?characterLabel ?work ?workLabel ?country ?countryLabel
       ?medium ?orientation ?orientationLabel ?gender ?genderLabel
       (MIN(?date) AS ?date)
WHERE {{
  VALUES (?workClass ?medium) {{ {classes} }}
  ?work wdt:P31/wdt:P279* ?workClass;
        wdt:P577 ?date;
        wdt:P495 ?country.
  ?country wdt:P30 wd:Q46.
  FILTER(?date >= \"{start_year}-01-01T00:00:00Z\"^^xsd:dateTime &&
         ?date < \"{end_year}-01-01T00:00:00Z\"^^xsd:dateTime)
  ?character wdt:P31/wdt:P279* wd:Q95074.
  {{
    ?character wdt:P91 ?orientation.
    VALUES ?orientation {{ {orientations} }}
  }} UNION {{
    ?character wdt:P21 ?gender.
    VALUES ?gender {{ {genders} }}
  }}
  {{ ?character wdt:P1441 ?work. }} UNION {{ ?work wdt:P674 ?character. }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language \"en\". }}
}}
GROUP BY ?character ?characterLabel ?work ?workLabel ?country ?countryLabel
         ?medium ?orientation ?orientationLabel ?gender ?genderLabel
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

def scrape(output_dir: str | Path, start_year: int = 1900, end_year: int = 2027) -> list[dict]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    records: dict[tuple[str, str, str, int], dict] = {}
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
            print(f"Wikidata LGBTQ {start}-{stop-1}: {len(rows):,} rows; {len(records):,} unique character-work candidates", flush=True)
        except Exception as exc:
            print(f"Wikidata LGBTQ partition {start}-{stop-1} failed: {exc}", flush=True)
        time.sleep(3)
    result = list(records.values())
    with (out / "wikidata_lgbtq_candidates.jsonl").open("w", encoding="utf-8") as f:
        for record in result:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return result
