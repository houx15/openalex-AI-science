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

**Rerun with fallback-augmented families and the ≤50-author rule (2026-11-09).** Query `sql/audit_selection_publication.sql` (qid 2458e076, 4.2 GB); counts in `data/derived/audit/selection_publication_rerun.csv`. Unit: distinct (paper, author) pairs. "Before" uses ID/DOI links only and reproduces the table above exactly; "after" also counts title + author fallback links (§7) as published.

| Teams | Field group | ORCID? | Gap before | Gap after |
|---|---|---|---|---|
| all | cs/math/stat/eess | all | −3.9 | −5.2 |
| all | cs/math/stat/eess | yes | +0.8 | +0.3 |
| all | cs/math/stat/eess | no | −0.7 | −1.9 |
| all | other | all | −8.1 | −10.3 |
| all | other | yes | −5.3 | −6.6 |
| all | other | no | −14.5 | −15.5 |
| ≤50 authors | cs/math/stat/eess | yes | +0.9 | +0.3 |
| ≤50 authors | cs/math/stat/eess | no | −0.7 | −1.9 |
| ≤50 authors | other | all | −2.8 | −5.8 |
| ≤50 authors | other | yes | +0.8 | −0.9 |
| ≤50 authors | other | no | −6.6 | −7.2 |

(Gap = established share, unpublished minus published, in percentage points.)

- As expected, moving falsely "unpublished" papers to published widens the gaps by 1–3 points. No direction changes.
- **With the ≤50-author scoring rule, the gap within ORCID strata is under 1 point in both field groups.** The −5 to −7 points seen in other fields came from large collaborations, which are excluded from scoring.
- The remaining gap is among non-ORCID authorships (−2 points in cs/math, −7 elsewhere), and unpublished papers have more of them (20.5% vs 10.4% of pairs). This supports making ORCID-only results a central robustness check (SPEC §9), as already planned.

Implications to carry into the design (for the Phase 0 gate):
1. Exposure eligibility (research paper vs review/position/note) must use arXiv-side information applied the same way to all papers, not OpenAlex `type`.
2. An author's exposure papers come from OpenAlex attribution, which is less complete for unpublished papers, especially without ORCID. Signal types could then be computed from a published-skewed set of papers. Planned checks: ORCID-only robustness (already in SPEC §9), a published-vs-unpublished split of signal prevalence at the Phase 1 pilot, and an estimate of how many unpublished papers by sampled authors are missing from their profiles (name + coauthor matching on a sample).
3. The proposed pre-2022 exposure exclusion conditions on publication. Treat it as a robustness check, not the main rule, unless the PI prefers otherwise. **Gate decision (2026-11-08):** excluded in the main analysis, because the earlier publication date is pre-treatment; inclusion is the robustness check (`docs/DECISIONS.md`).

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

### 7b. Pseudo-timeline extension (arXiv v1 2017–2018), added 2026-11-09

The same queries and accept rules, shifted by −6 years (v1 2017–18, candidate works published 2016–2020): `sql/fallback_candidates_author_block_2017_18.sql`, `sql/fallback_candidates_exact_title_2017_18.sql`, `sql/fallback_linked_works_2016plus.sql`. Output: Athena table `paper_family_fallback_2017_18_r20261109a` (sha256 of `links.parquet` 218c923b…). Placebo families = `paper_family_r20261106b` ∪ these links.

| Method | Links | arXiv papers |
|---|---|---|
| `title_exact_id` | 21,079 | 19,815 |
| `title_exact_name` | 423 | 408 |
| `title_fuzzy_id` | 9,683 | 9,423 |
| Total (deduplicated) | 31,185 | 29,428 |

- 17,505 of the 80,554 "unpublished" 2017–18 families (21.7%) gain a published version, close to the 23.1% for 2023–24, so the placebo and the main analysis get the same treatment.
- Precision, from a review of fixed-seed samples (seed 20261109): Levenshtein ≥ 0.9 about 22/25 correct (misses: a same-group paper on a different molecule, two follow-up papers with near-identical titles); the Jaccard rule about 25/30 (misses are companion papers or highlights versions). With exact titles counted as correct, weighted precision is about 96%, above the 0.95 target. It is slightly lower than for 2023–24, as older authors have had longer to write companion papers.
- Effect on the pilot placebo list: none. The pre-2016 published exclusion only concerns works dated before 2016, which this fallback never adds (its candidates are dated 2016 or later), as for the main sample's pre-2022 rule. The links matter for placebo *outcomes*: they keep published versions of 2017–18 exposure papers out of the pseudo outcome window.

### 7c. Duplicate arXiv IDs and works linked to several arXiv papers (2026-11-09)

Query `sql/audit_duplicates.sql` (qid e7edd689, 11.0 GB).

- **Duplicate arXiv IDs:** the "93 IDs appearing twice" are 93 extra rows on 81 IDs (71 twice, 8 three times, 2 four times). All are old-style IDs with v1 in 1998–2007, with identical titles and v1 dates; some copies differ only in the version count. None is in any analysis window or pilot list. Rule: keep one row per ID, the one with the most versions. No effect on any sample.
- **Works linked to 2+ arXiv papers** (non-xpac, not arXiv-primary, v1 2017+): 1,386 works, 1,337 of them with two papers. 77% are articles, 16% conference papers; 46 are books, i.e. proceedings volumes or edited books legitimately holding several papers. Spot checks show three cases: companion papers merged into one journal article (e.g. two 2018 MiniBooNE papers), an article that later absorbed an older preprint, and series/proceedings volumes.
- **In the pilot lists:** 169 works touch pilot papers (82 calibration, 79 placebo, 5 pilot_main, 3 both placebo and calibration). Calibration does not use publication status, and 5 pilot_main papers are negligible, so the pilot lists stay as they are.
- **Rule [PROPOSED, applied when the analysis families are built in Phase 2]:** a work linked to several arXiv papers counts as the published version of each of them for the outcome exclusion (conservative: it never becomes a "new" output for those authors), but it counts toward "published" status only for the arXiv paper with the closest title (the Levenshtein and Jaccard measures of §7); books and proceedings volumes never set "published" status.

## 8. Citation window, 2026H1 completeness and date heaping (SPEC §10 task 10)

Aggregate counts of works by publication month and year. No signal data. Queries `4933b033` and `97a9e0ca`.

**Last complete month: September 2026.**
- Eligible works per month in Jan–Sep 2026 match 2025 levels: 450k–1.05M per month, against 410k–1.21M.
- October 2026 is partial (176k) because the snapshot is dated 2026-10-14.
- The window rule "citations through September 30 of y+1" therefore works for the 2025 post cohort, and for pre cohorts with their own y+1.

**2026H1 completeness** (provisional): 3.84M eligible works, against 3.74M in 2025H1 (+2.5%). For comparison, 2025H1 grew 7.7% over 2024H1. Slightly slower growth is consistent with a small indexing lag, at most about 5%. This is a pass at the aggregate level. The field-level rule at equal indexing age needs an earlier snapshot, which we do not have, so field ratios are to be added.

**Reference coverage of citing works drops after 2023.** Share of eligible works with any parsed reference:

| Year | All | Physical Sci. | Health Sci. | Life Sci. | Social Sci. | Mean refs |
|---|---|---|---|---|---|---|
| 2018 | 60.5% | 73.8% | 63.9% | 70.1% | 39.9% | 19.3 |
| 2020 | 65.5% | 78.3% | 70.4% | 76.2% | 45.0% | 22.4 |
| 2022 | 73.7% | 84.9% | 76.9% | 82.9% | 56.0% | 26.2 |
| 2023 | 72.7% | 85.5% | 74.6% | 82.1% | 54.9% | 25.5 |
| 2024 | 63.8% | 79.0% | 67.0% | 74.1% | 41.5% | 24.3 |
| 2025 | 55.8% | 72.3% | 60.8% | 66.6% | 31.1% | 22.3 |
| 2026 | 52.4% | 67.3% | 56.7% | 62.9% | 29.0% | 19.6 |

- Citations to the post cohort (2025 papers) come from citing works dated 2025–26, of which 52–56% have references. Citations to pre cohorts come from citing works dated 2018–2022, of which 60–74% have references.
- **Raw citation counts are therefore not comparable pre vs post.** SPEC's primary citation outcome normalizes within field × publication half-year × document class. That removes a coverage drop that is uniform within a cell; it does not remove one that differs across authors within a cell, for example by publisher.
- **Proposed checks at the gate:**
  1. a robustness version counting only citing works from sources whose reference coverage is stable across 2018–2026;
  2. reporting coverage by field and publisher;
  3. if coverage differences across signal types appear after the Phase 3 gate, treating the citation DiD as descriptive (SPEC §8 already allows this).

**January-1 date heaping.** Share of eligible works dated exactly January 1:

| 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|
| 20.0% | 18.9% | 18.5% | 15.6% | 13.2% | 12.4% | 11.9% | 11.1% | 11.0% |

The share is highest in social sciences: 26.5% in 2018, 11.5% in 2025. These are year-only dates, and all of them land in H1. Field × period fixed effects absorb a common H1 bump within field. Two things remain:
- the bump shrinks over time, so pre-period H1 counts are inflated more than post-period ones;
- authors who publish in venues that give only a year get noisier half-year timing.

**Proposed:**
- an annual-period robustness version of the count DiD;
- an H2-only check;
- sending Jan-1-dated works to the conference/timing robustness check only through their earliest dated source, as SPEC §8 already allows.

**Scan cost of dated citation edges.** Building `referenced_works` → citing publication date needs about 37 GB per build (`referenced_works` 31.6 GB, plus id and date columns), about $0.19.

## 9. Conference and book-chapter classification (SPEC §7)

Works from 2018–2021, non-xpac. Queries `47a7516b`, `6a7ce715`, `da55c8e8`, `5f6013d9`.

**Conference papers with no primary source are real proceedings.**
- 375,445 `conference-paper` works have no primary source and Crossref raw type `proceedings-article`.
- The top DOI prefixes are IEEE 10.1109 (83.5k), SPIE 10.1117 (41.1k), ACM 10.1145 (29.8k), Atlantis Press 10.2991 (22.0k), ASME 10.1115 (18.3k) and ACL 10.18653 (6.8k).
- All have a published location.
- The v0 eligibility rule (`reports/phase0_funnel.md`) drops them because it requires a journal, conference or book-series primary source. That undercounts formal output in CS and engineering, the fields that dominate the sample.

**Book chapters that are conference papers.** 64,187 book chapters sit in book series with conference-like names (Lecture Notes …, Communications in Computer and Information Science, Advances in Intelligent Systems …, Proceedings …). This is the Springer pattern described by Kusumegi et al. A further 423k book-series chapters have other names, a mix of edited volumes and some proceedings. 3.0M book chapters are on ebook platforms, mostly edited volumes.

**Repository-only conference objects** (HAL, institutional repositories, Zenodo; about 0.4M) are mostly deposits of papers with a formal version elsewhere, or local proceedings. Exclude them, as in v0.

**Proposed eligibility rule v1** [PROPOSED, replaces v0]:
- `article` with a journal or conference primary source, as before;
- `conference-paper` with a journal, conference or book-series primary source, **or with no primary source, raw type `proceedings-article` and a DOI**;
- `book-chapter` in a book series whose name matches the conference pattern;
- otherwise unchanged (non-xpac, dated, not paratext or retracted).

**Effect on the funnel** (`author_funnel_r20261106b` under v1, against `r20261106a` under v0; query `c09a0bc5`):

| | v0 | v1 | Change |
|---|---|---|---|
| ≥4 eligible works 2018–21 | 5,009,495 | 5,079,341 | +1.4% |
| Main sample, m = 1 | 290,330 | 293,950 | +1.2% |
| m = 3 | 105,575 | 106,441 | +0.8% |
| AI researchers excluded (m = 1) | 31,799 | 33,506 | +5.4% |
| Author-paper slots, k = 3 | 553,468 | 559,552 | +1.1% |

Almost all of the change is in Physical Sciences (+3,475 m = 1 authors). v1 matters more for **outcome counts** of CS and engineering authors than for who enters the sample. The power and false-positive simulations use v0 inputs; the difference is too small to change their conclusions.

## Open items

1. **PI decision (exposure eligibility).** About 0.9% of 2023–24 arXiv papers are versions of papers published years earlier, e.g. a 2017 IEEE article first posted to arXiv in 2024. SPEC §6 defines exposure by v1 date alone, so these would be scored as 2023–24 text. **Decided at the gate (2026-11-08):** exclude papers whose family has a formal publication dated before 2022 from exposure scoring in the main analysis; include them as a robustness check.
2. **Unlinked published versions.** The fallback is built (§7) with precision ≈97% and recall ≈65%. Residual rule decided at the gate (two robustness checks, `docs/DECISIONS.md`). Fallback extended to pseudo-timeline v1 years 2017–18 (§7b, 2026-11-09). §4 comparisons re-run with fallback-augmented families (2026-11-09): no direction changes; within ORCID strata the gap is under 1 point for ≤50-author papers.
3. ~~Resolve the 93 duplicate arXiv IDs and the ~1,500 works linked to several arXiv papers.~~ Done (§7c): duplicate IDs are 1998–2007 only; rule proposed for the 1,386 multi-linked works.
4. Sample check of v1 dates against OAI-PMH once the endpoint works.
5. Remaining audit sections: conference and book-chapter classification, preprint handling, 2026H1 completeness, author-ID quality, indexing delay, `has_content` coverage.
