# Data dictionary

The expanded discovery corpus intentionally keeps only a few useful fields:

| Field | Meaning |
|---|---|
| character | Character name |
| work | Film, series, book, or associated show |
| medium | Movie, TV, book, or unclassified |
| year | First publication/release year when established; blank if not yet checked |
| country | Work's country of origin; blank if not yet checked |
| orientation | Source's own orientation label; do not merge unlike categories |
| reason | One short sentence explaining why the orientation was assigned |
| source | Direct URL to the supporting source |

The LezWatch and Wikipedia candidate exports use these compact fields. A source that only suggests a candidate should be marked as such during review; a list-page URL is useful discovery provenance but is not always sufficient as final evidence. The character reference link in the Wikipedia file is a convenience for checking the entry, not a substitute for an identity citation.

## Existing Wikidata baseline

The legacy `character_work_records.csv` and `yearly_counts.csv` remain available. The former contains QIDs, work links, publication dates and country identifiers; the latter contains yearly counts by channel. This baseline is kept separate from the broader multi-source discovery corpus.

## Counting and deduplication

Count unique character entities, not source rows or character/work appearances. Merge obvious aliases and repeated source entries. Do not merge distinct adaptations or separate characters solely because they share a name. If a reliable canonical ID is unavailable, use a source-qualified ID internally; the public-facing table can remain concise.
