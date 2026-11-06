"""LezWatch.TV bulk character ingestion using documented sexuality slugs.

The API's taxonomy slugs are not the same as everyday labels (for example,
"homosexual", "gay", and "lesbian" are not all valid endpoint slugs).
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

import requests

BASE = "https://lezwatchtv.com/wp-json/lwtv/v1"
# These are the documented taxonomy slugs exposed by /stats/characters/sexuality/.
TERMS = ("asexual", "bisexual", "fluid", "homosexual", "pansexual", "queer", "unlabeled")
HEADERS = {"User-Agent": "EuropeanFictionalCharacterResearch/0.5 (open research)"}
IDENTITY = {
    "asexual": "asexual",
    "bisexual": "bisexual",
    "fluid": "fluid / sexually fluid",
    "homosexual": "homosexual",
    "pansexual": "pansexual",
    "queer": "queer",
    "unlabeled": "unlabeled",
}
PATTERNS = [
    (re.compile(r"\basexual\b", re.I), "asexual"),
    (re.compile(r"\bbisexual\b", re.I), "bisexual"),
    (re.compile(r"\bpansexual\b", re.I), "pansexual"),
    (re.compile(r"\bhomosexual\b|\bgay\b|\blesbian\b", re.I), "homosexual"),
    (re.compile(r"\bsexually fluid\b|\bfluid sexuality\b", re.I), "fluid / sexually fluid"),
    (re.compile(r"\bqueer\b", re.I), "queer"),
]


def get_json(url: str, session: requests.Session, attempts: int = 5) -> Any:
    last_error = None
    for attempt in range(attempts):
        try:
            response = session.get(url, timeout=(15, 90))
            if response.status_code == 404:
                return None
            if response.status_code == 429 or response.status_code >= 500:
                if attempt + 1 == attempts:
                    response.raise_for_status()
                delay = min(120, 10 * (2 ** attempt))
                print(f"LezWatch HTTP {response.status_code}; retry in {delay}s", flush=True)
                time.sleep(delay)
                continue
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            if attempt + 1 == attempts:
                raise
            time.sleep(min(120, 10 * (2 ** attempt)))
    raise RuntimeError(f"Unable to fetch {url}: {last_error}")


def _items(payload: Any):
    if isinstance(payload, dict):
        return payload.items()
    if isinstance(payload, list):
        return ((str(i), row) for i, row in enumerate(payload))
    return ()


def _orientation(labels: Any, description: str = "") -> str:
    text = " ".join(map(str, labels)) if isinstance(labels, list) else str(labels or "")
    if not text:
        text = description
    found = []
    for pattern, label in PATTERNS:
        if pattern.search(text) and label not in found:
            found.append(label)
    return "; ".join(found) if found else ""


def fetch_sexuality_export(output_dir: str | Path) -> list[dict]:
    """Collect character records across the API's documented sexuality categories."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update(HEADERS)
    merged: dict[str, dict] = {}

    for term in TERMS:
        url = f"{BASE}/export/full/characters/sexuality/{term}/"
        try:
            payload = get_json(url, session)
        except (requests.RequestException, ValueError) as exc:
            print(f"LezWatch '{term}' unavailable: {exc}", flush=True)
            continue
        count = 0
        for source_key, item in _items(payload):
            if not isinstance(item, dict):
                continue
            source_id = str(item.get("id") or source_key)
            labels = item.get("sexuality") or [IDENTITY[term]]
            orientation = _orientation(labels)
            if not orientation:
                orientation = IDENTITY[term]
            shows = item.get("shows") or []
            work_names = [s.get("name", "") for s in shows if isinstance(s, dict) and s.get("name")]
            source_url = item.get("url") or f"https://lezwatchtv.com/character/{source_key}/"
            record = merged.setdefault(source_id, {
                "character": item.get("name", ""),
                "work": "; ".join(dict.fromkeys(work_names)),
                "medium": "TV",
                "orientation": orientation,
                "reason": f"LezWatch character record explicitly lists: {orientation}.",
                "source": source_url,
            })
            if orientation not in record["orientation"]:
                record["orientation"] += "; " + orientation
                record["reason"] = f"LezWatch character record lists: {record['orientation']}."
            if work_names and not record["work"]:
                record["work"] = "; ".join(dict.fromkeys(work_names))
            count += 1
        print(f"LezWatch {term}: {count:,} rows; {len(merged):,} unique characters so far", flush=True)
        time.sleep(6)

    # Always ingest the complete curated character export as a discovery source.
    # The site covers queer female, trans and non-binary TV characters; a row's
    # presence is a candidate signal, not proof of a specific sexual orientation.
    url = f"{BASE}/export/list/characters/"
    try:
        payload = get_json(url, session)
        for source_key, item in _items(payload):
            if not isinstance(item, dict):
                continue
            source_id = str(item.get("id") or source_key)
            description = str(item.get("description") or "")
            orientation = _orientation(item.get("sexuality") or "", description)
            shows = item.get("shows") or []
            work_names = [s.get("name", "") for s in shows if isinstance(s, dict) and s.get("name")]
            gender_terms = re.findall(
                r"\\b(trans(?:gender)?(?: man| woman)?|non[- ]binary|agender|genderfluid|genderqueer|two[- ]spirit|intersex)\\b",
                description, flags=re.I
            )
            if orientation:
                reason = f"LezWatch profile explicitly describes sexual orientation: {orientation}."
            elif gender_terms:
                reason = "LezWatch profile describes gender identity as " + ", ".join(dict.fromkeys(gender_terms)) + "; sexual orientation is not stated."
                orientation = "Not stated"
            else:
                reason = "Included in LezWatch's specialist queer-character database; precise identity requires profile-level review."
                orientation = "Not stated"
            source_url = item.get("url") or f"https://lezwatchtv.com/character/{source_id}/"
            record = merged.setdefault(source_id, {
                "character": item.get("name", ""),
                "work": "; ".join(dict.fromkeys(work_names)),
                "medium": "TV",
                "orientation": orientation,
                "reason": reason,
                "source": source_url,
            })
            if work_names and not record.get("work"):
                record["work"] = "; ".join(dict.fromkeys(work_names))
            if record.get("orientation") == "Not stated" and orientation != "Not stated":
                record["orientation"] = orientation
                record["reason"] = reason
    except (requests.RequestException, ValueError) as exc:
        print(f"LezWatch complete-list export unavailable: {exc}", flush=True)

    records = [r for r in merged.values() if r.get("character")]
    with (out / "lezwatch_characters.jsonl").open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"LezWatch unique candidates: {len(records):,}", flush=True)
    return records
