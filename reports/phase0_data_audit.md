# Phase 0 data audit

Status: **in progress**. Sections are added as each check finishes.

## Inputs and run IDs

| Item | Value |
|---|---|
| OpenAlex snapshot | 2026-10-14 public release (`manifest.json` and `RELEASE_NOTES.txt` checked 2026-11-05) |
| arXiv metadata | Kaggle `Cornell-University/arxiv`, dataset version 21506946, snapshot file dated 2026-11-01, sha256 `dcaa0325…5795` |
| Derived tables | `works_core_r20261106a`, `authorship_long_r20261106b` (supersedes `…a`), `paper_family_r20261106b` (Glue database `openalex_2026_10`) |
| SQL | `sql/ctas_works_core.sql`, `sql/ctas_authorship_long.sql`, `sql/ctas_paper_family.sql` |
| AWS cost to date | $2.26 (`reports/cost_log.csv`) |

## 1. Snapshot reconciliation

- The works table has 464,765,485 rows, exactly the `manifest.json` count. 326,989,410 are non-xpac.
- The Parquet schema is identical across `updated_date` partitions from 2016 to 2026.
- Non-xpac works dated 2026 number 33.2M, against about 10–11M a year for 2010–2024. The excess is **datasets** (19.0M; NIFS alone has 13.7M) and DiSSCo specimen records (about 4M). Articles dated 2026 total 6.5M through October, which is normal. None of this affects the eligible sample (journal and conference research articles).
- 3.17M non-xpac works have no publication year.

## 2. arXiv metadata

- 3,233,620 records; 93 IDs appear twice (not yet resolved).
- Every record has a v1 date. The latest v1 is 2026-10-29.
- **452,913 papers have v1 in 2023–2024 (UTC).** By primary archive: cs 185,218 (41%), math 76,085, cond-mat 33,383, astro-ph 31,612, physics 29,623, eess 20,750, quant-ph 18,597, stat 10,985, hep-ph 10,299, other 46k.
- The share of papers listing the DOI of their published version falls by v1 year: 47.7% (2018) → 38.4% (2022) → 23.7% (2024) → 8.0% (2026).
- 3.5% of new-style IDs carry a YYMM that differs from the v1 month (month-boundary submissions). Windows use the v1 date, not the ID.
- The official OAI-PMH endpoint timed out or returned 503 for every historical datestamp on 2026-11-06 (see `docs/DECISIONS.md`). A random-sample check of v1 dates against OAI-PMH is pending.

## 3. arXiv → OpenAlex crosswalk (`paper_family`)

Matching uses (1) arXiv IDs found in OpenAlex work locations or `10.48550` DOIs, then (2) DOIs listed on the arXiv record. No title-based fallback has been run yet.

### Match rates by v1 year

| v1 year | arXiv papers | ≥1 OpenAlex work | Has an arXiv-hosted record | Has a non-arXiv (published) work | ≥2 works |
|---|---|---|---|---|---|
| 2017 | 123,781 | 99.8% | 36.1% | 70.6% | 11.9% |
| 2018 | 140,377 | 99.8% | 36.3% | 70.2% | 11.9% |
| 2019 | 155,917 | 99.8% | 37.5% | 69.3% | 12.3% |
| 2020 | 178,275 | 99.9% | 37.5% | 69.1% | 12.2% |
| 2021 | 181,599 | 99.9% | 39.8% | 66.8% | 12.3% |
| 2022 | 185,987 | 99.9% | 34.4% | 66.8% | 3.5% |
| 2023 | 209,223 | 99.9% | 37.9% | 62.2% | 2.6% |
| 2024 | 243,690 | 99.9% | 40.9% | 57.9% | 2.3% |
| 2025 | 284,162 | 100.0% | 57.8% | 40.7% | 10.1% |
| 2026 | 310,647 | 91.5% | 80.5% | 12.3% | 11.0% |

- Match rates for v1 in 2023–2024 are 99.8–100% in every primary archive.
- DOI matching almost never finds a work that arXiv-ID matching missed. The published versions it finds are usually already merged into the same OpenAlex work.
- **"Has a non-arXiv (published) work" is a lower bound on publication.** It falls for recent v1 years partly through publication lag. How many published versions exist but are not linked is not yet measured; see open items.

### Family composition

- Most multi-work families are an arXiv record plus a separate published article, the intended case, counted once per family.
- Fewer unmerged pairs after 2021 (3.4k in 2023 vs 8.4k in 2019) reflect OpenAlex merging preprint and published versions into one work more often, not a matching failure.
- OpenAlex has duplicate arXiv records: 3.7k pairs for v1 in 2019, and 5.1k plus 16.5k xpac duplicates for 2025. Family-level counting absorbs them.
- About 1,500 OpenAlex works link to 2+ arXiv papers (v1 2017+). Not yet resolved.

### Work types among linked works (v1 2023–2024, non-xpac)

| type | arXiv primary? | has published journal/conference location | links |
|---|---|---|---|
| article | no | yes | 186,626 |
| preprint | yes | no | 171,751 |
| conference-paper | no | yes | 59,012 |
| conference-paper | no | no | 11,722 |
| conference-paper | unknown source | — | 9,137 |
| preprint | no | no | 7,526 |
| article | no | no | 3,423 |

Formal-output rules must handle conference papers with no published location (11.7k) or no primary source (9.1k), and preprint-typed works that do have a published location (290). This feeds the conference-classification and preprint-handling checks.

### Precision audit

- Fixed-seed random sample of 400 links (v1 2023–2024, non-xpac), half from single-work and half from multi-work families. After the publication-year join, 394 remained (the 6 dropped were early-published works; see below). Saved in `reports/phase0/crosswalk_audit_sample.csv`.
- Titles compared automatically. All 30 pairs with similarity < 0.8 were checked by hand.

| Finding | n | Correct? |
|---|---|---|
| Title similarity ≥ 0.8 | 364 | yes |
| Journal version retitled (author-listed DOI, same paper) | ~17 | yes |
| Truncated OpenAlex title | 2 | yes |
| SciPost referee report ("Report on 2406.12695v2"), type `peer-review` | 8 | **no** |
| Wrong DOI on the arXiv record | 1 | **no** |
| DOI of the whole proceedings volume | 1 | **no** |
| OpenAlex merged the arXiv ID into a different paper by the same group | 1 | **no** |

**Precision: 383/394 = 97.2% (unweighted).** It is 99.2% once `peer-review` links are excluded, and about 99.7% when weighted to the true mix (all errors are in multi-work families, about 3% of 2023–24 papers). This passes the proposed 0.95 target. Several "retitled" judgments are close calls; counting them as errors still leaves precision ≥ 97%.

### Flags added (`link_flag`)

| Flag | Links (all years) | Meaning and handling |
|---|---|---|
| `exclude_peer_review` | 3,323 | A referee report carries the arXiv ID. Drop from families. |
| `published_before_v1` | 19,330 | Work published 2+ years before the arXiv v1. The link is correct (an old paper posted late), but see the PI decision below. |

## 4. Selection on publication status (raised by PI, 2026-11-06)

Question: does the arXiv→OpenAlex pipeline favour papers that were published, or published quickly?

The ~99.9% match rate does not involve selection, because almost every arXiv paper links to OpenAlex's own arXiv record. Selection can still enter through: (a) eligibility rules based on OpenAlex `type`, since unpublished papers are all typed `preprint`; (b) author identification; (c) unlinked published versions staying in outcomes; (d) the proposed pre-2022 exposure exclusion, which conditions on earlier publication.

Test of (b), on arXiv papers with v1 in 2023–2024, comparing published vs never-published families:

| | Unpublished | Published |
|---|---|---|
| Papers | 185,188 | 267,456 |
| Authorships with an OpenAlex author ID | 90.4% | 88.7% |
| Authorships with ORCID | 74.0% | 85.0% |
| Papers with no authorship rows | **4.69%** | 0.0% |
| Mean distinct authors | 4.0 | 10.2 |

Share of (paper, author) pairs whose author has ≥4 article/conference works in 2018–2021:

| Field group | Authorship has ORCID? | Unpublished | Published | Gap |
|---|---|---|---|---|
| cs/math/stat/eess | all | 60.3% | 64.2% | −3.9 |
| cs/math/stat/eess | yes | 72.0% | 71.2% | +0.8 |
| cs/math/stat/eess | no | 16.8% | 17.5% | −0.7 |
| other | all | 71.1% | 79.2% | −8.1 |
| other | yes | 78.1% | 83.4% | −5.3 |
| other | no | 24.4% | 38.9% | −14.5 |

Reading:
- In cs/math/stat/eess, the gap disappears within ORCID strata. It comes from unpublished papers having more non-ORCID authorships (21% vs 13% of pairs), and non-ORCID authorships rarely sit on established profiles (about 17% vs 72%). That fits author-profile fragmentation when no ORCID is present, though genuinely new authors are also more common without ORCID. The two can't be separated yet.
- In other fields a gap remains even with ORCID. Large physics collaborations, which are mostly published and mostly established authors, likely contribute. Repeat with the ≤50-author scoring rule before drawing conclusions.
- ~~4.7% of unpublished 2023–24 papers have no authors in OpenAlex.~~ **Corrected (§5):** this was an artifact of the first `authorship_long`, which dropped xpac works. 4,784 unpublished papers (2.6%, against 0 published) exist in OpenAlex only as xpac records. `authorship_long` is now rebuilt with xpac rows flagged.

Implications to carry into the design (for the Phase 0 gate):
1. Exposure eligibility (research paper vs review/position/note) must use arXiv-side information applied the same way to all papers, not OpenAlex `type`.
2. An author's exposure papers come from OpenAlex attribution, which is less complete for unpublished papers, especially without ORCID. Signal types could then be computed from a published-skewed set of papers. Planned checks: ORCID-only robustness (already in SPEC §9), a published-vs-unpublished split of signal prevalence at the Phase 1 pilot, and an estimate of how many unpublished papers by sampled authors are missing from their profiles (name + coauthor matching on a sample).
3. The proposed pre-2022 exposure exclusion conditions on publication. Treat it as a robustness check, not the main rule, unless the PI prefers otherwise.

## 5. Author bridge: are unpublished arXiv papers attributed to the right author profile?

Sample: 400 authors drawn with a fixed seed (`sql/audit_author_bridge_sample.sql`). Each has ≥4 article/conference works in 2018–2021 and ≥1 2023–24 arXiv paper attributed in OpenAlex. 100 per stratum of profile ORCID (yes/no) × majority arXiv archive in cs/math/stat/eess (yes/no).

**Attempt 1 (rejected): name matching against arXiv author lists.** A paper counted as the author's when it listed the author's name and a 2018–2022 coauthor's name. This produced up to 960 papers per author (large collaborations, common names), so attribution rates were dominated by false matches. Not used.

**Attempt 2: OpenAlex coauthor IDs** (`sql/audit_author_bridge_fragments.sql`, `src/data/audit_author_bridge.py`). Candidate papers are 2023–24 arXiv papers containing one of the author's 2018–2022 coauthor *IDs* (works with ≤50 authors) and an authorship whose name is compatible with the author's (last name equal; first names equal, or one is an initial of the other). A candidate counts as attributed when that authorship carries the sampled author's ID.

| | Unpublished | Published |
|---|---|---|
| Candidate (author, paper) pairs | 374 | 1,403 |
| Attributed, pair-weighted | 84.5% | 81.0% |
| Attributed, author-weighted (152 / 184 authors) | 88.8% | 85.7% |
| Within-author, 84 authors with both kinds | 83.2% | 81.0% |

By stratum (author-weighted), attribution ranges from 76% to 98%, with no consistent published/unpublished direction.

Reading:
- **No evidence that unpublished arXiv papers are attributed to established author profiles less often than published ones**, provided the paper has OpenAlex authorships. If anything, the difference runs slightly the other way.
- The "misses" are dominated by name ambiguity, not split profiles: common names on papers with several compatible names (e.g. "Jie Zhang" on a paper with seven other J. Zhangs; "Xu Wang" vs "X. Wang"). Attribution rates here are therefore lower bounds. A few look like real splits (same full name, different ID, same coauthor network).
- Not covered: papers whose coauthors are also mis-attributed, and single-author papers.
- With §4, the ORCID gap between published and unpublished papers looks more like **who the authors are** (fewer established, ORCID-holding researchers on unpublished papers) than OpenAlex failing to recognize established authors. That is a real sample-composition difference, but it is not an attribution error.

**Real asymmetry found and fixed:** 4,784 unpublished 2023–24 arXiv papers (2.6%; 0 published) exist in OpenAlex only as xpac records. The first `authorship_long` dropped xpac works, so these papers could never count toward an author. `authorship_long_r20261106b` keeps xpac rows with an `is_xpac` flag. Formal-output and career-age rules still exclude xpac; exposure linkage now includes it.

## 6. Unlinked published versions (exact-title match)

Question: how many 2023–24 arXiv papers that look unpublished (no published work in their `paper_family`) actually have a published version in OpenAlex that arXiv-ID and DOI matching missed?

Method (`sql/audit_title_match_unlinked.sql`, `src/data/audit_title_match.py`):
- Candidates are OpenAlex works published 2022–2026 (not arXiv-hosted; not dataset or peer-review) with the **same normalized title**: lowercase, accents folded, only `[a-z0-9]` kept, ≥25 characters. Works already in the family are excluded.
- A pair is **author-confirmed** when at least one arXiv author name is compatible with an OpenAlex author name.
- A confirmed pair counts as a **publication** when the work is a formal-output type (article, conference paper, book chapter, review, letter, book), is not xpac or paratext, and has a published journal/conference location or a journal/conference/book-series primary source.

| v1 year | Field group | Looks unpublished | With an exact-title, author-confirmed publication | Share |
|---|---|---|---|---|
| 2023 | cs/math/stat/eess | 60,368 | 7,582 | 12.6% |
| 2023 | other | 20,039 | 4,130 | 20.6% |
| 2024 | cs/math/stat/eess | 81,270 | 8,424 | 10.4% |
| 2024 | other | 23,777 | 4,756 | 20.0% |
| **Total** | | **185,454** | **24,892** | **13.4%** |

- **Precision.** In a random sample of 40 confirmed papers, all 40 were the same paper with the same authors in a real journal or conference (95% CI lower bound ≈ 91%). Median time from v1 to publication was 149 days, and 5% were published more than 167 days before v1.
- **Rejected pairs are mostly true matches.** Of the 641 pairs that failed the author check, most are true matches with name-order differences ("Lee Zheng Han" vs "Zheng Han Lee") or collaboration authors. A further 342 have no OpenAlex authors. The confirmed count is therefore conservative.
- **Bug fixed during this audit.** The shared name parser did not decode LaTeX accents in arXiv author strings (`Kov\'a\v{c}`). This wrongly rejected about 300 true matches. The fix is in `delatex` and has a test. It does not affect §5, whose final method compares OpenAlex names with OpenAlex names.
- **Recall of exact titles is only about 49%** (`sql/audit_title_match_recall.sql`). Among 2023–24 arXiv papers already linked to a separate published record, only 3,877 of 7,881 (49%) share the arXiv title exactly; titles often change at publication. A rough recall adjustment puts the true unlinked share at **13–27% of "unpublished" papers**. That is an extrapolation, because the linked pairs may differ from the unlinked ones.
- **Why linking fails.** Almost none of the matched works carry an arXiv ID (55) or are linked to another arXiv paper (65). The published record simply never mentions the preprint, and the arXiv record does not list the journal DOI.

Implications:
1. **Outcome contamination.** SPEC excludes an author's exposure-window papers from the outcome counts. With ID and DOI links alone, at least 25k published versions of 2023–24 arXiv papers would count as *new* formal outputs. That inflates outcomes for exactly the authors who posted during exposure, and could correlate with signals. **The production crosswalk needs a title + author fallback** (exact title, then fuzzy title with author and date checks), plus a measured residual.
2. **§4 published/unpublished comparisons.** At least 13% of the "unpublished" group is in fact published. The §4 gaps are therefore attenuated and should be re-run after the fallback. Directions are unlikely to change.
3. **Published share (lower bound) rises** from 61.6% to 67.2% for v1 2023, and from 56.9% to 62.3% for v1 2024.

## 7. Title + author fallback for `paper_family` (built)

Covers arXiv papers with v1 in 2023–2024 and candidate works published 2022–2026. Output is the Athena table `paper_family_fallback_r20261106a`; production families are `paper_family_r20261106b` ∪ fallback links.

Candidates:
- **Author-blocked** (`sql/fallback_candidates_author_block.sql`): article, conference-paper, book-chapter, review or letter works (non-xpac) that share at least one OpenAlex author ID with the paper's family, with similar titles. Families with more than 50 authors are skipped.
- **Exact title, any authors** (`sql/fallback_candidates_exact_title.sql`): author names are checked locally.

Accept rules [PROPOSED] (`src/data/paper_family_fallback.py`):

| Method | Rule | Links | arXiv papers |
|---|---|---|---|
| `title_exact_id` | exact normalized title + ≥1 shared author ID | 33,083 | 30,629 |
| `title_exact_name` | exact title (≥25 chars) + compatible author name + formal-output work | 781 | 767 |
| `title_fuzzy_id` | shared author ID, work not linked to another arXiv paper, published ≤365 days before v1, and Levenshtein similarity ≥ 0.9, or token Jaccard ≥ 0.8 as each side's best candidate | 17,731 | 17,415 |

**Precision** (manual review of fixed-seed samples):
- Exact title: all sampled pairs correct, including short titles.
- Levenshtein ≥ 0.9: 24/25 correct. The miss was a yearly shared-task system paper ("IWSLT 2024" vs "IWSLT 2025").
- Jaccard rule: about 26–27/30 correct. Misses are companion papers by the same authors.
- Weighted precision is about 97%, above the 0.95 target in SPEC §7.

**Recall** (`sql/audit_fallback_recall.sql`), measured on 7,478 known separate published versions:

| Rule | Recall |
|---|---|
| Exact title + shared ID | 48.7% |
| + Levenshtein ≥ 0.9 | 62.9% |
| + Jaccard ≥ 0.8 | 67.5% (upper bound; best-candidate condition not applied) |

Recall is lower in cs/math (about 60%) than in other fields (about 71%), because titles change more at publication.

Effect:
- 42,784 of the 185,454 "unpublished" 2023–24 families (23.1%) gain a published version.
- A further 6,171 links attach extra versions to families that were already published.
- **Residual:** dividing by recall puts the true number of unlinked published versions at about 63k. That leaves about 20k (≈11% of the originally "unpublished") still missed. In the outcome window these would be counted as new output. SPEC's robustness check that adds exposure papers back covers this direction. A further option is to drop all 2025–26 works sharing an author ID with the author's own exposure paper and having title Jaccard ≥ 0.5 [to decide at the Phase 0 gate].

## Open items

1. **PI decision (exposure eligibility).** About 0.9% of 2023–24 arXiv papers are versions of papers published years earlier, e.g. a 2017 IEEE article first posted to arXiv in 2024. SPEC §6 defines exposure by v1 date alone, so these would be scored as 2023–24 text. **Proposed:** exclude papers whose family has a formal publication dated before 2022 from exposure scoring. Not applied.
2. **Unlinked published versions.** The fallback is built (§7) with precision ≈97% and recall ≈65%. Still to do: decide the residual rule at the gate, extend the fallback to pseudo-timeline v1 years (2017–2018), and re-run the §4 comparisons with fallback-augmented families.
3. Resolve the 93 duplicate arXiv IDs and the ~1,500 works linked to several arXiv papers.
4. Sample check of v1 dates against OAI-PMH once the endpoint works.
5. Remaining audit sections: conference and book-chapter classification, preprint handling, 2026H1 completeness, author-ID quality, indexing delay, `has_content` coverage.
