"""Lean LezWatch.TV character candidate export."""
from __future__ import annotations
import json
import time
from pathlib import Path
from typing import Any
import requests

BASE = "https://lezwatchtv.com/wp-json/lwtv/v1"
TERMS = ("homosexual", "gay", "lesbian", "bisexual", "pansexual",
         "queer", "asexual", "demisexual", "questioning", "unlabeled")
HEADERS = {"User-Agent": "EuropeanFictionalCharacterResearch/0.4 (research)"}


def get_json(url: str, session: requests.Session, attempts: int = 5) -> Any:
    for attempt in range(attempts):
        response = session.get(url, timeout=(15, 90))
        if response.status_code == 429 or response.status_code >= 500:
            if attempt + 1 == attempts:
                response.raise_for_status()
            delay = min(120, 10 * (2 ** attempt))
            print(f"LezWatch HTTP {response.status_code}; retry in {delay}s", flush=True)
            time.sleep(delay)
            continue
        response.raise_for_status()
        return response.json()
    raise RuntimeError(f"Unable to fetch {url}")


def fetch_sexuality_export(output_dir: str | Path) -> list[dict]:
    """Return only useful fields: name, work, medium, orientation, reason, source."""
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
        items = payload.items() if isinstance(payload, dict) else (
            (str(i), row) for i, row in enumerate(payload)
        ) if isinstance(payload, list) else []
        for source_id, item in items:
            if not isinstance(item, dict):
                continue
            key = str(item.get("id") or source_id)
            labels = item.get("sexuality") or [term]
            label_text = ", ".join(map(str, labels)) if isinstance(labels, list) else str(labels)
            record = merged.setdefault(key, {
                "character": item.get("name", ""),
                "work": item.get("shows", []),
                "medium": "TV",
                "orientation": label_text,
                "reason": f"LezWatch classifies this character under: {label_text}.",
                "source": item.get("url") or url,
            })
            if label_text not in record["orientation"]:
                record["orientation"] += "; " + label_text
                record["reason"] = f"LezWatch sexuality categories: {record['orientation']}."
        print(f"LezWatch {term}: {len(merged):,} unique characters so far", flush=True)
        time.sleep(6)

    records = list(merged.values())
    with (out / "lezwatch_characters.jsonl").open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"LezWatch unique candidates: {len(records):,}", flush=True)
    return records
