# European fictional characters and sexual orientation

A reproducible research pipeline for counting fictional characters explicitly documented as homosexual in European-origin books, films, and television/web series, by year (1900–2026).

## What this project measures

This project measures **Wikidata documentation**, not the true prevalence of homosexual characters in European culture. A character is included only when Wikidata has an explicit sexual-orientation statement and a traceable connection to an eligible work.

Default definition:
- Character class: fictional character (Q95074), including subclasses.
- Sexual orientation: homosexuality (Q6636), via P91.
- Character/work link: P1441 (present in work) or P674 (characters).
- Work date: P577 (publication/release date).
- European origin: work country of origin P495 whose continent P30 is Europe (Q46).
- Channels: film; TV series/web series/animated series; book/novel/literary work.
- Counting unit: distinct character QID × first/recorded work year × channel.

Bisexuality, queer identity without an explicit homosexuality statement, and orientation inferred from plot, actor, author, or relationship are not silently included. A later extension may provide broader LGBTQ+ categories separately.

## Pipeline

The extraction uses Wikidata Query Service (WDQS) in **year-bounded batches**, persists each successful batch, retries transient failures, and resumes from completed partitions. It does not download a large global TSV first: that file contains character labels/IDs only and cannot by itself classify sexuality, works, media, country, or dates.

## Run locally

Python 3.11+:

```bash
python -m pip install -r requirements.txt
python -m src.run_pipeline --start-year 1900 --end-year 2026
```

Output files:
- `data/raw/wikidata_batches/*.jsonl`: raw query rows by channel/year partition.
- `data/processed/character_work_records.csv`: enriched character-work records.
- `data/processed/yearly_counts.csv`: complete year × channel panel, including zeroes.
- `reports/homosexual_characters_europe_1900_2026.png`: three-panel graph.
- `reports/summary.json`: run metadata and counts.

Resume after interruption by rerunning the same command. To force re-fetches, add `--refresh`.

## GitHub Actions

The workflow can be run manually from Actions or on a monthly schedule. Data files and figures are uploaded as workflow artifacts; raw query results are not committed by default. This avoids large/noisy commits and keeps the repository code-focused.

## Interpretation and known limitations

Wikidata coverage is sparse and socially/historically uneven. A zero means **no matching documented records returned by this query**, not that no homosexual characters existed. Older works and marginalised identities are likely underrepresented. Publication dates, country-of-origin statements, work classes and character links may be absent or inconsistent. Co-productions can have multiple countries. Series are assigned their recorded series-level publication/release year; episode-level or season-level counts are not attempted.

Results should be reported as “Wikidata-recorded characters” rather than total representation. The query logic and software versions are kept with the outputs to support replication.

## Multi-source expansion (in progress)

The original Wikidata extraction is retained as a strict, reproducible baseline. A separate supplementary ingestion path now collects:
- LezWatch.TV sexuality-specific character exports (TV-focused structured source);
- curated Wikipedia LGBTQ+ fiction list rows (candidate discovery only; rows require evidence review).

Run supplementary ingestion locally:

```bash
python -m src.ingest_sources --source all
```

Outputs are written to `data/raw/supplementary/`. They are source-preserving candidate data and are **not automatically merged into the Europe-only annual graph**. Entity matching, work-origin validation, source citation checks, and review must happen first.

See [SOURCES_AND_METHOD.md](docs/SOURCES_AND_METHOD.md) for source coverage, licensing constraints, and the evidence model. In particular, IMDb's non-commercial bulk data is not ingested into or redistributed by this public repository. The project will report candidate counts separately from verified, analysis-eligible unique characters. The 15,000-character target is a minimum research objective, not a claim that the current sources already meet it.
