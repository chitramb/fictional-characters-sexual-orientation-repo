"""Merge neutral character candidates while preserving source-level provenance."""
from __future__ import annotations
import json
import re
from pathlib import Path

FILES = ("wikidata_character_candidates.jsonl", "fandom_universe_candidates.jsonl")

def norm(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip()).casefold()

def _source_entry(row: dict, source_fallback: str) -> dict:
    return {
        "source_name": row.get("source_name") or source_fallback,
        "source": row.get("source", ""),
        "source_id": row.get("source_id", ""),
        "source_revision_id": row.get("source_revision_id"),
        "source_revision_timestamp": row.get("source_revision_timestamp"),
        "source_retrieved_at": row.get("source_retrieved_at"),
        "evidence_status": row.get("evidence_status", "candidate"),
        "orientation": row.get("orientation", "Not stated"),
        "sex_or_gender": row.get("sex_or_gender", "Not stated"),
        "gender_identity": row.get("gender_identity", "Not stated"),
        "reason": row.get("reason", ""),
    }

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
                year = row.get("year")
                # A source-qualified entity ID is preferred. Work-qualified names
                # are fallback candidates, not final entity resolution.
                source_id = str(row.get("source_id") or "").strip()
                key = (source_id, norm(work), norm(medium), year) if source_id else (
                    norm(name), norm(work) if work else "", norm(medium) if not work else ""
                )
                entry = _source_entry(row, source)
                if key not in merged:
                    merged[key] = {
                        "character": name, "work": work, "medium": medium,
                        "year": year, "country": row.get("country", ""),
                        "orientation": row.get("orientation", "Not stated"),
                        "sex_or_gender": row.get("sex_or_gender", "Not stated"),
                        "gender_identity": row.get("gender_identity", "Not stated"),
                        "reason": row.get("reason", ""),
                        "source": row.get("source", ""),
                        "source_id": source_id,
                        "evidence_status": row.get("evidence_status", "candidate"),
                        "sources": [entry],
                    }
                else:
                    current = merged[key]
                    if not current.get("year") and year:
                        current["year"] = year
                    if not current.get("country") and row.get("country"):
                        current["country"] = row["country"]
                    if current.get("orientation") in ("", "Not stated") and row.get("orientation") not in ("", "Not stated"):
                        current["orientation"] = row["orientation"]
                        current["reason"] = row.get("reason", current["reason"])
                    if current.get("sex_or_gender") in ("", "Not stated") and row.get("sex_or_gender") not in ("", "Not stated"):
                        current["sex_or_gender"] = row["sex_or_gender"]
                    if current.get("gender_identity") in ("", "Not stated") and row.get("gender_identity") not in ("", "Not stated"):
                        current["gender_identity"] = row["gender_identity"]
                    if entry not in current["sources"]:
                        current["sources"].append(entry)
                count += 1
        source_rows[source] = count

    output = root / "all_character_candidates.jsonl"
    with output.open("w", encoding="utf-8") as handle:
        for row in merged.values():
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    orientation_counts, sex_or_gender_counts, gender_identity_counts, medium_counts = {}, {}, {}, {}
    for row in merged.values():
        orientation = row.get("orientation") or "Not stated"
        sex_or_gender = row.get("sex_or_gender") or "Not stated"
        gender_identity = row.get("gender_identity") or "Not stated"
        medium = row.get("medium") or "Unclassified"
        orientation_counts[orientation] = orientation_counts.get(orientation, 0) + 1
        sex_or_gender_counts[sex_or_gender] = sex_or_gender_counts.get(sex_or_gender, 0) + 1
        gender_identity_counts[gender_identity] = gender_identity_counts.get(gender_identity, 0) + 1
        medium_counts[medium] = medium_counts.get(medium, 0) + 1

    summary = {
        "source_rows": source_rows,
        "merged_candidate_records": len(merged),
        "distinct_character_names": len({norm(row["character"]) for row in merged.values()}),
        "records_with_explicit_orientation": sum(1 for row in merged.values() if row.get("orientation") not in ("", "Not stated")),
        "records_with_sex_or_gender_value": sum(1 for row in merged.values() if row.get("sex_or_gender") not in ("", "Not stated")),
        "records_with_explicit_gender_identity": sum(1 for row in merged.values() if row.get("gender_identity") not in ("", "Not stated")),
        "orientation_counts": orientation_counts,
        "sex_or_gender_counts": sex_or_gender_counts,
        "gender_identity_counts": gender_identity_counts,
        "medium_counts": medium_counts,
        "output": str(output),
        "note": "Neutral discovery candidates. Source evidence is preserved per record; entity resolution, source review, and Europe eligibility remain separate steps.",
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

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="data/raw/supplementary")
    args = parser.parse_args()
    print(json.dumps(merge(args.output_dir), indent=2))
