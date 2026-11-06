"""WDQS client with retries, timeout handling, and bounded query templates."""
from __future__ import annotations

import json
import random
import time
from pathlib import Path
from typing import Any

import requests

ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = "EuropeanFictionalCharacterResearch/0.1 (open reproducible research)"
SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": USER_AGENT,
    "Accept": "application/sparql-results+json",
})

# Classes are queried via subclass closure. Keep film and series classes
# separate so a TV movie is not automatically counted as an episodic series.
CHANNEL_CLASSES = {
    "movies": ["Q11424"],  # film
    "tv_web_series": ["Q5398426", "Q526877", "Q581714"],  # television series, web series, animated series
    "books": ["Q571", "Q7725634", "Q47461344"],  # book, literary work, novel
}

def build_query(start_year: int, end_year_exclusive: int, channel: str) -> str:
    if channel not in CHANNEL_CLASSES:
        raise ValueError(f"Unknown channel: {channel}")
    if not (1800 <= start_year < end_year_exclusive <= 2030):
        raise ValueError("Invalid year range")
    values = " ".join(f"wd:{qid}" for qid in CHANNEL_CLASSES[channel])
    return f"""
SELECT DISTINCT
  ?character ?characterLabel
  ?work ?workLabel
  ?date ?country ?countryLabel
WHERE {{
  ?character wdt:P91 wd:Q6636;
             wdt:P31/wdt:P279* wd:Q95074.
  {{
    ?character wdt:P1441 ?work.
  }} UNION {{
    ?work wdt:P674 ?character.
  }}
  ?work wdt:P577 ?date;
        wdt:P495 ?country;
        wdt:P31/wdt:P279* ?workClass.
  VALUES ?workClass {{ {values} }}
  ?country wdt:P30 wd:Q46.
  FILTER(?date >= "{start_year}-01-01T00:00:00Z"^^xsd:dateTime &&
         ?date < "{end_year_exclusive}-01-01T00:00:00Z"^^xsd:dateTime)
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}}
"""

def query_wikidata(query: str, *, timeout: int = 180, attempts: int = 6) -> list[dict[str, Any]]:
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            response = SESSION.get(
                ENDPOINT,
                params={"query": query, "format": "json"},
                timeout=(20, timeout),
            )
            if response.status_code in {429, 500, 502, 503, 504}:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else min(90, 5 * (2 ** attempt)) + random.random()
                print(f"WDQS HTTP {response.status_code}; sleeping {delay:.1f}s")
                time.sleep(delay)
                continue
            response.raise_for_status()
            payload = response.json()
            return payload.get("results", {}).get("bindings", [])
        except (requests.RequestException, ValueError, json.JSONDecodeError) as exc:
            last_error = exc
            delay = min(90, 5 * (2 ** attempt)) + random.random()
            print(f"WDQS attempt {attempt + 1}/{attempts} failed: {exc}; sleeping {delay:.1f}s")
            time.sleep(delay)
    raise RuntimeError(f"WDQS query failed after {attempts} attempts: {last_error}")

def binding(row: dict[str, Any], key: str) -> str:
    return row.get(key, {}).get("value", "")

def normalize_binding(row: dict[str, Any], key: str) -> str:
    value = binding(row, key)
    return value.rsplit("/", 1)[-1] if value else ""

def rows_to_records(rows: list[dict[str, Any]], channel: str) -> list[dict[str, Any]]:
    records = []
    for row in rows:
        date = binding(row, "date")
        if len(date) < 4 or not date[:4].isdigit():
            continue
        records.append({
            "character_qid": normalize_binding(row, "character"),
            "character_label": binding(row, "characterLabel"),
            "work_qid": normalize_binding(row, "work"),
            "work_label": binding(row, "workLabel"),
            "publication_date": date,
            "year": int(date[:4]),
            "country_qid": normalize_binding(row, "country"),
            "country_label": binding(row, "countryLabel"),
            "channel": channel,
        })
    return records

def fetch_partition(start_year: int, end_year_exclusive: int, channel: str) -> list[dict[str, Any]]:
    return rows_to_records(
        query_wikidata(build_query(start_year, end_year_exclusive, channel)),
        channel,
    )
