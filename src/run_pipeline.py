"""Resumable year-bucket extraction, aggregation, and plotting."""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import pandas as pd

from .wikidata import CHANNEL_CLASSES, fetch_partition

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "wikidata_batches"
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"

def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-year", type=int, default=1900)
    parser.add_argument("--end-year", type=int, default=2026)
    parser.add_argument("--bucket-years", type=int, default=1,
                        help="Years per WDQS request. Small buckets are more resumable.")
    parser.add_argument("--refresh", action="store_true",
                        help="Re-fetch partitions even when cached JSONL exists.")
    parser.add_argument("--pause", type=float, default=2.0,
                        help="Seconds between WDQS requests.")
    return parser.parse_args()

def partition_path(channel: str, lo: int, hi_exclusive: int) -> Path:
    return RAW / f"{channel}_{lo}_{hi_exclusive - 1}.jsonl"

def run_extract(args) -> pd.DataFrame:
    RAW.mkdir(parents=True, exist_ok=True)
    all_records = []
    for channel in CHANNEL_CLASSES:
        for lo in range(args.start_year, args.end_year + 1, args.bucket_years):
            hi = min(lo + args.bucket_years, args.end_year + 1)
            cache = partition_path(channel, lo, hi)
            if cache.exists() and not args.refresh:
                print(f"Using cached partition: {cache.name}", flush=True)
                part = pd.read_json(cache, lines=True)
                all_records.extend(part.to_dict("records"))
                continue
            print(f"Fetching {channel}: {lo}–{hi - 1}", flush=True)
            records = fetch_partition(lo, hi, channel)
            # Atomic write: an interrupted process cannot leave a partial cache.
            tmp = cache.with_suffix(".jsonl.tmp")
            pd.DataFrame(records).to_json(tmp, orient="records", lines=True, force_ascii=False)
            tmp.replace(cache)
            all_records.extend(records)
            print(f"  received {len(records):,} character-work rows", flush=True)
            time.sleep(args.pause)
    return pd.DataFrame(all_records)

def save_outputs(detail: pd.DataFrame, start: int, end: int):
    PROCESSED.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    detail_path = PROCESSED / "character_work_records.csv"
    detail.to_csv(detail_path, index=False, encoding="utf-8-sig")

    if detail.empty:
        raise RuntimeError(
            "No matches were returned. Check WDQS availability and query coverage; "
            "do not interpret an empty extraction as evidence of zero representation."
        )

    # A character may feature in multiple works in a year. Count it once per
    # channel/year, but preserve every character-work association in detail.
    unique = detail[["character_qid", "year", "channel"]].drop_duplicates()
    counts = (unique.groupby(["year", "channel"])["character_qid"]
              .nunique().rename("character_count").reset_index())
    channels = ["movies", "tv_web_series", "books"]
    panel = pd.MultiIndex.from_product(
        [range(start, end + 1), channels], names=["year", "channel"]
    ).to_frame(index=False)
    panel = panel.merge(counts, how="left", on=["year", "channel"])
    panel["character_count"] = panel["character_count"].fillna(0).astype(int)
    panel.to_csv(PROCESSED / "yearly_counts.csv", index=False, encoding="utf-8-sig")

    summary = {
        "start_year": start,
        "end_year": end,
        "character_work_rows": int(len(detail)),
        "unique_characters": int(detail["character_qid"].nunique()),
        "unique_character_year_channel": int(len(unique)),
        "counts_by_channel": {
            ch: int(detail.loc[detail["channel"] == ch, "character_qid"].nunique())
            for ch in channels
        },
        "method": "Wikidata explicit homosexuality (P91=Q6636), fictional character class, linked dated European-origin works",
        "warning": "Counts measure Wikidata documentation, not actual prevalence.",
    }
    (REPORTS / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    titles = {
        "movies": "Movies",
        "tv_web_series": "TV / web series",
        "books": "Books",
    }
    fig, axes = plt.subplots(3, 1, figsize=(15, 11), sharex=True)
    for ax, channel in zip(axes, channels):
        subset = panel[panel["channel"] == channel]
        ax.plot(subset["year"], subset["character_count"], linewidth=1.7)
        ax.fill_between(subset["year"], subset["character_count"], alpha=.16)
        ax.set_title(titles[channel], loc="left", fontsize=12, fontweight="bold")
        ax.set_ylabel("Distinct characters")
        ax.grid(True, alpha=.25)
        ax.set_xlim(start, end)
        ax.set_ylim(bottom=0)
    axes[-1].set_xlabel("Year of publication / release recorded in Wikidata")
    fig.suptitle(
        "Wikidata-recorded homosexual fictional characters in European-origin works",
        fontsize=15, fontweight="bold"
    )
    fig.text(
        .01, .01,
        "Explicit P91 = homosexuality (Q6636); character linked to dated work with European country of origin. "
        "Counts represent documented records, not historical prevalence. Missing metadata causes undercounting.",
        fontsize=8, wrap=True
    )
    fig.tight_layout(rect=[0, .04, 1, .96])
    fig.savefig(REPORTS / "homosexual_characters_europe_1900_2026.png",
                dpi=220, bbox_inches="tight")
    plt.close(fig)
    return summary

def main():
    args = parse_args()
    if args.start_year < 1900 or args.end_year > 2026 or args.start_year > args.end_year:
        raise SystemExit("Years must be within 1900–2026 and start <= end.")
    if args.bucket_years < 1:
        raise SystemExit("--bucket-years must be >= 1.")
    detail = run_extract(args)
    # Drop exact duplicate rows returned through multiple link paths or country records.
    if not detail.empty:
        detail = detail.drop_duplicates()
    summary = save_outputs(detail, args.start_year, args.end_year)
    print(json.dumps(summary, indent=2))
    print("Plots and processed CSVs saved.")

if __name__ == "__main__":
    main()
