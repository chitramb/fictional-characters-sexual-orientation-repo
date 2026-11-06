"""Run supplementary structured-source ingestion independently of WDQS."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .lezwatch import fetch_sexuality_export


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=["lezwatch", "all"], default="all")
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
    (output / "ingestion_summary.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8"
    )
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
