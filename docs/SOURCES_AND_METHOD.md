# Multi-source collection strategy

## Research target

Build a broad, universe-first dictionary of at least 15,000 fictional-character entities, with source-level evidence and work links. Character discovery is not filtered by LGBTQ status: orientation is recorded when explicit evidence exists and otherwise remains Not stated. This is a collection target, not a promise that 15,000 records will pass final evidence and Europe/medium filters. Report raw candidates, distinct names, work-qualified candidates, resolved entities, verified orientation statements, and Europe-eligible records separately.

## Source tiers

### Tier 1 — broad structured character/identity records
- **Wikidata**: neutral discovery begins with fictional-character entities linked to dated works across film, TV, books, comics and video games. Sexual orientation (P91) and sex/gender (P21) are optional enrichment fields; neither is a discovery filter. The two fields are retained separately. A P21 value is labelled as Wikidata sex/gender, not automatically interpreted as a trans identity. Country of origin is retained when available, but is not a filter at candidate-discovery stage.
- **General-universe Fandom wikis**: character categories and character-page infoboxes from broad fictional universes (for example Harry Potter, Marvel, DC, Star Wars, Doctor Who, Middle-earth, Star Trek, Pokémon, Zelda and others). Universe inclusion is independent of LGBTQ status. Character orientation is recorded only from an explicit sexuality/orientation field; absent fields remain “Not stated”.

### Tier 2 — work metadata and cross-checks
- **Wikipedia and specialist bibliographies** may be used for title metadata, dates, countries and corroboration after broad character discovery, but LGBTQ-only lists and queer-specialist databases are excluded from the main candidate collection to avoid source-selection bias.
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

Use distinct statuses: `candidate`, `source-supported`, `independently-verified`, `disputed`, `excluded`. A curated list can seed a candidate but should not automatically promote it to verified. The current merged dictionary retains a list of source records per candidate; automated source extraction does not independently verify claims.

## Europe and historical dating

Define European origin explicitly: original country of production/publication, with co-productions retained as multiple countries. Do not equate language, setting, author nationality, publisher location, or current rights-holder with work origin. Keep uncertain and multi-country cases visible.

Store the earliest substantiated first publication/release date for the work, plus all alternative dates and their source/meaning. Do not let reprints, international release dates, streaming dates, or later editions create duplicate annual character appearances. For serial works, preserve series premiere and episode/season appearances separately.

## Bias and reporting

A larger sample does not automatically become representative. The source ecosystem is uneven by geography, language, era, gender, medium, popularity, and the degree to which a character's identity is explicit. Report source coverage, evidence tiers, missingness, and sensitivity analyses. Never describe the resulting count as the actual number of LGBTQ+ characters in European culture.
