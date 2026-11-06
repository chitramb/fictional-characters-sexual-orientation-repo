"""Conservatively merge supplementary discovery candidates."""
from __future__ import annotations
import json
import re
from pathlib import Path

FILES = (
    "wikidata_lgbtq_candidates.jsonl",
    "fandom_universe_candidates.jsonl",
)

def norm(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip()).casefold()

def merge(output_dir: str | Path) -> dict:
    root = Path(output_dir)
    merged = {}
    source_rows = {}
    for filename in FILES:
        path = root / filename
        if not path.exists():
            continue
        source = filename.removesuffix(".jsonl")
        count = 0
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                name = str(row.get("character") or "").strip()
                if not name:
                    continue
                work = str(row.get("work") or "").strip()
                medium = str(row.get("medium") or "").strip()
                # Work-qualified keys avoid collapsing unrelated characters
                # with common names; blank-work records use source-independent
                # name + medium and remain candidates for manual resolution.
                key = (norm(name), norm(work) if work else "", norm(medium) if not work else "")
                if key not in merged:
                    merged[key] = {
                        "character": name,
                        "work": work,
                        "medium": medium,
                        "year": row.get("year"),
                        "country": row.get("country", ""),
                        "orientation": row.get("orientation", "Not stated"),
                        "reason": row.get("reason", ""),
                        "source": row.get("source", ""),
                    }
                else:
                    current = merged[key]
                    if not current.get("year") and row.get("year"):
                        current["year"] = row["year"]
                    if not current.get("country") and row.get("country"):
                        current["country"] = row["country"]
                    if current.get("orientation") in ("", "Not stated") and row.get("orientation") not in ("", "Not stated"):
                        current["orientation"] = row["orientation"]
                        current["reason"] = row.get("reason", current["reason"])
                count += 1
        source_rows[source] = count
    output = root / "all_character_candidates.jsonl"
    with output.open("w", encoding="utf-8") as handle:
        for row in merged.values():
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    orientations = {}
    media = {}
    for row in merged.values():
        label = row.get("orientation") or "Not stated"
        orientations[label] = orientations.get(label, 0) + 1
        medium = row.get("medium") or "Unclassified"
        media[medium] = media.get(medium, 0) + 1
    summary = {
        "source_rows": source_rows,
        "merged_candidate_records": len(merged),
        "distinct_character_names": len({norm(row["character"]) for row in merged.values()}),
        "records_with_explicit_orientation": sum(1 for row in merged.values() if row.get("orientation") not in ("", "Not stated")),
        "orientation_counts": orientations,
        "medium_counts": media,
        "output": str(output),
        "note": "General-universe candidate dictionary; records still require entity resolution, source review, and Europe eligibility checks.",
    }
    (root / "merge_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    project_root = Path(__file__).resolve().parents[1]
    processed = project_root / "data" / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    dictionary_path = processed / "character_dictionary.jsonl"
    summary_path = processed / "collection_summary.json"
    dictionary_path.write_text(output.read_text(encoding="utf-8"), encoding="utf-8")
    summary["persistent_dictionary"] = str(dictionary_path)
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary
