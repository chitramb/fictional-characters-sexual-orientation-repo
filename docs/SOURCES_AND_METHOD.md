# Multi-source collection strategy

## Research target

Build a deduplicated repository of at least 15,000 fictional-character entities, with source-level evidence and work links. This is a collection target, not a promise that 15,000 records will pass the final evidence and Europe/medium filters. Report the number of raw candidates, resolved entities, verified identities, and analysis-eligible records separately.

## Source tiers

### Tier 1 — structured character/identity records
- **Wikidata**: open structured entity graph. The new broad extractor queries 27 non-heterosexual P91 values and a separate set of transgender, non-binary and intersex P21 values, then joins characters to dated European-origin film, TV, book, comic and video-game works. Sexual orientation and gender identity remain separate; source statements and work links still need review. The original homosexuality-only query remains a strict baseline.
- **LezWatch.TV**: public, no-key API with bulk character exports and sexuality-specific exports. Strong supplementary source for television characters, particularly queer women, trans and non-binary characters. Its public site reports roughly 7,450 character records and 2,290 shows; it is not a global all-media census. The complete export is ingested as candidate discovery; profile-level labels are retained separately from gender identity and orientation. Observe its published rate limit (100 requests/IP/10 minutes).
- **Queer Comics Database**: series-level discovery index spanning print, web, independent and major-publisher comics. It catalogs titles, not a complete character-level identity list; use its series pages to discover individual characters and seek profile/issue-level evidence.
- **AroAce Database**: specialist searchable compilation of aromantic and asexual fictional characters in prose fiction. Useful for named-character discovery and orientation cross-checking; verify each entry against cited sources.
- **Queer SFF Database**: searchable bibliography of queer science-fiction and fantasy books with identity and relationship filters. Treat as work-level discovery and resolve individual character names from the books and independent references.
- **Queerlit (Sweden)**: research bibliography and linked-data project indexing LGBTQI topics in Swedish fiction across historical periods. Valuable for non-English and historical European literature; it is primarily work/subject metadata, not a direct character roster.

### Tier 2 — curated candidate lists with references
- **Wikipedia list pages**: lists of fictional gay, lesbian, bisexual, transgender and other LGBTQ+ characters; lists by medium and period; modern written fiction; animated series; TV and made-for-TV films. Use these to discover candidates and cited references, not as an unqualified identity authority. Each row must be linked to a cited source or explicitly marked as needing review.
- **LGBT Fans Deserve Better (LGBTFansDB)**: historical/archived television-character identifiers are represented in Wikidata by P6780. Treat this as an identifier/crosswalk, not a current independently verified identity claim.
- **Specialist scholarship and published reference works**: use for historical characters and periods where modern structured databases are sparse. Capture bibliographic citation and page/section, not just a search-result snippet.

### Tier 3 — work metadata and entity resolution
- **TMDB**: candidate work metadata and IDs for film/TV, where API access and terms permit. It does not independently establish a character's sexuality; join only through character/credit records and retain the identity evidence separately.
- **IMDb non-commercial datasets**: useful for local exploratory matching of titles/credits, but IMDb's terms restrict use to personal/non-commercial purposes and prohibit republishing/repurposing the data as another database. Do not ingest IMDb bulk files into this public repository or redistribute derived IMDb records without a suitable licence.
- **Open Library / library catalogues**: book/work identity, editions, publication metadata and identifiers. These do not generally supply LGBTQ character identities; use to validate work metadata after character discovery.
- **Open comic/fiction knowledge bases**: may provide character and first-appearance crosswalks. Evaluate each dataset's licence and evidence model before ingestion; broad entity dumps are candidate enrichment, not proof of sexuality.

## Inclusion and evidence model

A record is not analysis-ready merely because a name appears on a list. Preserve:
- canonical character ID (Wikidata QID when available; otherwise source-qualified ID);
- canonical name and aliases;
- identity category exactly as stated by source (gay, lesbian, bisexual, queer, pansexual, asexual, trans identity, etc.); do not collapse sexual orientation and gender identity;
- evidence URL, source name, source record ID, quotation/snippet or bibliographic locator, retrieval date, and confidence/review status;
- work ID, title, medium, original country/countries, first publication/release year, and date precision;
- entity-resolution decisions and duplicate/variant relationships.

Use distinct statuses: `candidate`, `source-supported`, `independently-verified`, `disputed`, `excluded`. A curated list can seed a candidate but should not automatically promote it to verified.

## Europe and historical dating

Define European origin explicitly: original country of production/publication, with co-productions retained as multiple countries. Do not equate language, setting, author nationality, publisher location, or current rights-holder with work origin. Keep uncertain and multi-country cases visible.

Store the earliest substantiated first publication/release date for the work, plus all alternative dates and their source/meaning. Do not let reprints, international release dates, streaming dates, or later editions create duplicate annual character appearances. For serial works, preserve series premiere and episode/season appearances separately.

## Bias and reporting

A larger sample does not automatically become representative. The source ecosystem is uneven by geography, language, era, gender, medium, popularity, and the degree to which a character's identity is explicit. Report source coverage, evidence tiers, missingness, and sensitivity analyses. Never describe the resulting count as the actual number of LGBTQ+ characters in European culture.

## Initial source references

- Lezwatch API docs: https://docs.lezwatchtv.com/api/
- LezWatch export endpoint docs: https://docs.lezwatchtv.com/api/global/export/
- Queer Comics Database: https://queercomicsdatabase.com/
- AroAce Database discovery portal: https://www.tulsalibrary.org/lgbt-recs
- Queer SFF book database: https://queersff.theillustratedpage.net/
- Queerlit project overview: https://ecp.ep.liu.se/index.php/hic/article/download/889/797/909
- LezWatch character statistics docs: https://docs.lezwatchtv.com/api/statistics/characters/
- Wikidata WikiProject LGBT models: https://www.wikidata.org/wiki/Wikidata:WikiProject_LGBT/Models
- Wikipedia LGBTQ fiction lists: https://en.wikipedia.org/wiki/Lists_of_LGBTQ_figures_in_fiction_and_myth
- Modern written fiction list: https://en.wikipedia.org/wiki/List_of_LGBTQ_characters_in_modern_written_fiction
- IMDb non-commercial data terms/docs: https://data.imdb.com/documentation
- TMDB daily ID exports: https://developer.themoviedb.org/docs/daily-id-exports
