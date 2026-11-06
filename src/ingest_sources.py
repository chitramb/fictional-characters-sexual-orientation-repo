"""Run supplementary source ingestion independently of WDQS."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .lezwatch import fetch_sexuality_export
from .wikipedia_lists import scrape as scrape_wikipedia


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=["lezwatch", "wikipedia", "all"], default="all")
    parser.add_argument("--output-dir", default="data/raw/supplementary")
    args = parser.parse_args()
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)

    results = {}
    if args.source in {"lezwatch", "all"}:
        records = fetch_sexuality_export(output)
        results["LezWatch.TV"] = {
            "unique_source_characters": len(records),
            "file": str(output / "lezwatch_characters.jsonl"),
            "note": "TV-focused candidate source; Europe/work eligibility and identity evidence require reconciliation.",
        }
    if args.source in {"wikipedia", "all"}:
        records = scrape_wikipedia(output)
        results["Wikipedia lists"] = {
            "candidate_rows": len(records),
            "file": str(output / "wikipedia_list_candidates.jsonl"),
            "note": "Curated list rows are discovery leads, not automatically verified identity claims.",
        }
    (output / "ingestion_summary.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8"
    )
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
