# Data dictionary

## character_work_records.csv

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

The same character may have more than one row because they can appear in multiple works, countries, or publication-date statements. This table is a relationship table, not a unique-character table.

## yearly_counts.csv

| Field | Meaning |
|---|---|
| year | Calendar year, inclusive 1900–2026 by default |
| channel | One of the three media categories |
| character_count | Number of distinct character QIDs linked to eligible works in that year and channel |

A character is counted once within a given year/channel even if multiple linked works appear in the results.

## Inclusion rule

The current query requires the character's P91 statement to point to Q6636 (homosexuality), and its P31 class to be fictional character Q95074 or a subclass. This narrow explicit-claim rule deliberately avoids classifying characters from plot text, fan interpretation, performer identity, or relationship inference.

## Caveats requiring attention

- P91 is not a complete or uniformly applied classification of fictional characters.
- Multiple sources and works can have inconsistent or changing claims.
- P577 can represent publication, release, broadcast, or another publication event. This pipeline uses the earliest four digits of each returned date and does not yet resolve competing date qualifiers.
- P495 may list multiple production countries. Any European P495 country qualifies the work.
- The type hierarchy may have gaps; the three media channel definitions are operational approximations, not a complete theory of media.
- TV series are assigned a year based on a series-level publication date. A single character appearing in multiple seasons is not counted once per season.
- The project currently measures explicitly documented homosexuality only. It is not a general LGBTQ+ census.
