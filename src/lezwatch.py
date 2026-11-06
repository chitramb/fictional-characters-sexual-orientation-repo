"""LezWatch.TV bulk-export adapter.

LezWatch is a television-focused supplementary source. It is not used as the
sole identity authority for the full research corpus. Raw source fields are
preserved so the resulting records can be audited.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

BASE = "https://lezwatchtv.com/wp-json/lwtv/v1"
USER_AGENT = "EuropeanFictionalCharacterResearch/0.3 (research; contact via GitHub)"
# These are API taxonomy slugs, not claims that categories are interchangeable.
SEXUALITY_TERMS = (
    "homosexual", "gay", "lesbian", "bisexual", "pansexual",
    "queer", "asexual", "demisexual", "questioning", "unlabeled",
)


def _get_json(url: str, session: requests.Session, attempts: int = 5) -> Any:
    for attempt in range(attempts):
        response = session.get(url, timeout=(15, 90))
        if response.status_code == 429 or response.status_code >= 500:
            if attempt + 1 == attempts:
                response.raise_for_status()
            wait = min(120, 10 * (2 ** attempt))
            print(f"LezWatch HTTP {response.status_code}; waiting {wait}s", flush=True)
            time.sleep(wait)
            continue
        response.raise_for_status()
        return response.json()
    raise RuntimeError(f"Unable to fetch {url}")


def fetch_sexuality_export(output_dir: str | Path) -> list[dict[str, Any]]:
    """Fetch sexuality-specific character exports, retaining raw source payload.

    The API documentation describes these full exports. Some taxonomy slugs
    may not exist in the live API; those are logged and skipped rather than
    silently treated as zero characters.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})
    all_rows: list[dict[str, Any]] = []
    retrieved = datetime.now(timezone.utc).isoformat()

    for term in SEXUALITY_TERMS:
        url = f"{BASE}/export/full/characters/sexuality/{term}/"
        try:
            payload = _get_json(url, session)
        except (requests.RequestException, ValueError) as exc:
            print(f"LezWatch term '{term}' unavailable: {exc}", flush=True)
            continue

        # Full exports are documented as a key-to-record object. Be defensive
        # about API changes and retain unexpected structures for inspection.
        if isinstance(payload, dict):
            items = payload.items()
        elif isinstance(payload, list):
            items = ((str(i), row) for i, row in enumerate(payload))
        else:
            print(f"Unexpected LezWatch payload for '{term}': {type(payload).__name__}", flush=True)
            continue

        count = 0
        for source_key, row in items:
            if not isinstance(row, dict):
                continue
            all_rows.append({
                "source": "LezWatch.TV",
                "source_url": url,
                "source_id": str(row.get("id") or source_key),
                "source_slug": str(row.get("id") or source_key),
                "name": row.get("name"),
                "identity_taxonomy_query": term,
                "identity_labels": row.get("sexuality", []),
                "gender_labels": row.get("gender", []),
                "shows": row.get("shows", []),
                "source_record_url": row.get("url"),
                "retrieved_at": retrieved,
                "raw_record_json": json.dumps(row, ensure_ascii=False, sort_keys=True),
                "verification_status": "candidate",
            })
            count += 1
        print(f"LezWatch '{term}': {count:,} source rows", flush=True)
        time.sleep(6)  # comfortably below the published API rate limit

    # De-duplicate records returned by overlapping taxonomy exports, while
    # preserving all observed identity labels and query terms.
    merged: dict[str, dict[str, Any]] = {}
    for row in all_rows:
        key = row["source_id"]
        if key not in merged:
            merged[key] = row
            continue
        old = merged[key]
        old["identity_taxonomy_query"] = sorted(set(
            ([old["identity_taxonomy_query"]] if isinstance(old["identity_taxonomy_query"], str)
             else old["identity_taxonomy_query"]) + [row["identity_taxonomy_query"]]
        ))
        old["identity_labels"] = sorted(set(old.get("identity_labels", []) + row.get("identity_labels", [])))
        old["gender_labels"] = sorted(set(old.get("gender_labels", []) + row.get("gender_labels", [])))

    records = list(merged.values())
    path = out / "lezwatch_characters.jsonl"
    with path.open("w", encoding="utf-8") as handle:
        for row in records:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"LezWatch unique source characters: {len(records):,}", flush=True)
    return records
