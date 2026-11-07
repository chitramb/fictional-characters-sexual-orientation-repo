"""Generate a transparent quality audit for the broad character candidate dictionary."""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path


def normalize(value: str) -> str:
    return re.sub(r"\\s+", " ", (value or "").strip()).casefold()


def audit(dictionary_path: str | Path, output_path: str | Path) -> dict:
    name_records = defaultdict(list)
    counters = Counter()
    source_counts = Counter()
    scope_counts = Counter()
    orientation_counts = Counter()
    sex_or_gender_counts = Counter()
    gender_identity_counts = Counter()
    provenance_counts = Counter()

    with Path(dictionary_path).open(encoding="utf-8") as handle:
        for line in handle:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                counters["invalid_json_lines"] += 1
                continue
            name = str(row.get("character") or "").strip()
            if not name:
                counters["records_without_character_name"] += 1
                continue
            counters["candidate_records"] += 1
            name_records[normalize(name)].append(row)
            orientation_counts[row.get("orientation") or "Not stated"] += 1
            sex_or_gender_counts[row.get("sex_or_gender") or "Not stated"] += 1
            gender_identity_counts[row.get("gender_identity") or "Not stated"] += 1
            scope_counts[row.get("work_scope") or "unspecified"] += 1
            sources = row.get("sources") or []
            provenance_counts[str(len(sources))] += 1
            if not row.get("source") and not sources:
                counters["records_without_source_url"] += 1
            if not row.get("source_id") and not sources:
                counters["records_without_source_id"] += 1
            if row.get("year") in (None, ""):
                counters["records_without_work_year"] += 1
            if not row.get("country"):
                counters["records_without_work_country"] += 1
            if (row.get("orientation") or "Not stated") == "Not stated":
                counters["orientation_not_stated"] += 1
            else:
                counters["records_with_explicit_orientation"] += 1
            if (row.get("sex_or_gender") or "Not stated") != "Not stated":
                counters["records_with_sex_or_gender_value"] += 1
            if (row.get("gender_identity") or "Not stated") != "Not stated":
                counters["records_with_explicit_gender_identity"] += 1
            for source in sources:
                source_counts[source.get("source_name") or "Unknown"] += 1

    duplicate_groups = [rows for rows in name_records.values() if len(rows) > 1]
    multi_universe_groups = 0
    cross_source_groups = 0
    for rows in duplicate_groups:
        if len({row.get("work") for row in rows}) > 1:
            multi_universe_groups += 1
        labels = set()
        for row in rows:
            for source in row.get("sources") or []:
                labels.add(source.get("source_name") or "Unknown")
        if len(labels) > 1:
            cross_source_groups += 1

    report = {
        "candidate_records": counters["candidate_records"],
        "distinct_normalized_character_names": len(name_records),
        "duplicate_name_groups_not_automatically_merged": len(duplicate_groups),
        "same_name_across_multiple_work_or_universe_labels": multi_universe_groups,
        "same_name_with_multiple_source_labels": cross_source_groups,
        "records_with_explicit_orientation": counters["records_with_explicit_orientation"],
        "orientation_not_stated": counters["orientation_not_stated"],
        "records_with_sex_or_gender_value": counters["records_with_sex_or_gender_value"],
        "records_with_explicit_gender_identity": counters["records_with_explicit_gender_identity"],
        "records_without_source_url": counters["records_without_source_url"],
        "records_without_source_id": counters["records_without_source_id"],
        "records_without_work_year": counters["records_without_work_year"],
        "records_without_work_country": counters["records_without_work_country"],
        "invalid_json_lines": counters["invalid_json_lines"],
        "records_without_character_name": counters["records_without_character_name"],
        "work_scope_counts": dict(scope_counts),
        "orientation_counts": dict(orientation_counts),
        "sex_or_gender_counts": dict(sex_or_gender_counts),
        "gender_identity_counts": dict(gender_identity_counts),
        "source_record_counts": dict(source_counts),
        "source_provenance_count_distribution": dict(provenance_counts),
        "interpretation": (
            "Discovery-corpus quality diagnostics, not entity-resolution results. "
            "Same-name groups are flagged, never automatically collapsed. "
            "Missing orientation is not evidence of heterosexuality; P21 sex/gender "
            "is not treated as gender identity. Universe-level records are not "
            "specific-work or Europe-eligible observations."
        ),
    }
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    source = root / "data" / "processed" / "character_dictionary.jsonl"
    output = root / "data" / "processed" / "quality_audit.json"
    print(json.dumps(audit(source, output), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
