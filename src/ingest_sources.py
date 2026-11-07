"""Run neutral, universe-first character discovery sources."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

from .wikidata_characters import scrape_wikidata_characters
from .fandom_universes import scrape_fandom_universes
from .merge_candidates import merge as merge_candidates

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=["wikidata", "fandom", "all"], default="all")
    parser.add_argument("--output-dir", default="data/raw/supplementary")
    args = parser.parse_args()
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    results = {}
    if args.source in {"wikidata", "all"}:
        records = scrape_wikidata_characters(output)
        results["Wikidata character records"] = {
            "candidate_rows": len(records),
            "file": str(output / "wikidata_character_candidates.jsonl"),
            "note": "Broad European-origin fiction discovery; sexual orientation P91 and sex/gender P21 remain separate; P21 is not treated as gender identity.",
        }
    if args.source in {"fandom", "all"}:
        records = scrape_fandom_universes(output)
        results["General Fandom universes"] = {
            "candidate_rows": len(records),
            "distinct_character_names": len({r["character"].casefold() for r in records}),
            "file": str(output / "fandom_universe_candidates.jsonl"),
            "note": "Universe-first discovery from general character categories; orientation only recorded from explicit page fields.",
        }
    results["Cross-source merge"] = merge_candidates(output)
    (output / "ingestion_summary.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
