# Data dictionary

## Existing Wikidata outputs

### character_work_records.csv
| Field | Meaning |
|---|---|
| character_qid | Wikidata item identifier for the fictional character |
| character_label | English Wikidata label |
| work_qid | Wikidata item identifier for the book/film/series |
| work_label | English Wikidata label |
| publication_date | Wikidata P577 date value |
| year | Four-digit year parsed from P577 |
| country_qid | Wikidata country of origin (P495) |
| country_label | English country label |
| channel | movies, tv_web_series, or books |

### yearly_counts.csv
| Field | Meaning |
|---|---|
| year | Calendar year, inclusive 1900–2026 by default |
| channel | One of the three media categories |
| character_count | Distinct character QIDs linked to eligible works in that year/channel |

## Supplementary source output

### data/raw/supplementary/lezwatch_characters.jsonl
One raw-source-preserving JSON object per deduplicated LezWatch character:
- `source`, `source_url`, `source_id`, `source_slug`: provenance and stable source key;
- `name`: source display name;
- `identity_taxonomy_query`, `identity_labels`, `gender_labels`: original taxonomy values, kept separate;
- `shows`: associated TV shows as returned by the source;
- `source_record_url`, `retrieved_at`, `raw_record_json`: audit trail;
- `verification_status`: starts at `candidate`, never auto-promoted to verified.

This output is not yet merged into the European-origin annual analysis. Entity matching, work-origin validation, and evidence review must happen before inclusion.

## Planned canonical entity schema

The consolidated dataset will use one canonical row per character entity and separate linked tables for identities, works, appearances, sources/evidence, aliases, and entity-resolution decisions. This avoids flattening multiple identities, works, or conflicting statements into one lossy record.

Required provenance for every identity claim: source, source record/URL, exact source label or statement, retrieval date, evidence tier, review status, and notes. Keep sexuality, romantic orientation, and gender identity as separate dimensions.

## Inclusion rule (legacy baseline)

The original WDQS baseline requires P91=Q6636 (homosexuality) and fictional-character class Q95074 or subclass, with a P1441 or P674 work link. This remains a reproducible narrow baseline; it is not the expanded corpus definition.
