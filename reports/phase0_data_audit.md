# Phase 0 data audit

Status: **in progress**. Sections are added as each check finishes.

## Inputs and run IDs

| Item | Value |
|---|---|
| OpenAlex snapshot | 2026-10-14 public release (`manifest.json` and `RELEASE_NOTES.txt` checked 2026-11-05) |
| arXiv metadata | Kaggle `Cornell-University/arxiv`, dataset version 21506946, snapshot file dated 2026-11-01, sha256 `dcaa0325…5795` |
| Derived tables | `works_core_r20261106a`, `authorship_long_r20261106a`, `paper_family_r20261106b` (Glue database `openalex_2026_10`) |
| SQL | `sql/ctas_works_core.sql`, `sql/ctas_authorship_long.sql`, `sql/ctas_paper_family.sql` |
| AWS cost to date | $1.53 (`reports/cost_log.csv`) |

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
- 4.7% of unpublished 2023–24 papers have no authors in OpenAlex and can never enter an author's exposure set.

Implications to carry into the design (for the Phase 0 gate):
1. Exposure eligibility (research paper vs review/position/note) must use arXiv-side information applied the same way to all papers, not OpenAlex `type`.
2. An author's exposure papers come from OpenAlex attribution, which is less complete for unpublished papers, especially without ORCID. Signal types could then be computed from a published-skewed set of papers. Planned checks: ORCID-only robustness (already in SPEC §9), a published-vs-unpublished split of signal prevalence at the Phase 1 pilot, and an estimate of how many unpublished papers by sampled authors are missing from their profiles (name + coauthor matching on a sample).
3. The proposed pre-2022 exposure exclusion conditions on publication. Treat it as a robustness check, not the main rule, unless the PI prefers otherwise.

## Open items

1. **PI decision (exposure eligibility).** About 0.9% of 2023–24 arXiv papers are versions of papers published years earlier, e.g. a 2017 IEEE article first posted to arXiv in 2024. SPEC §6 defines exposure by v1 date alone, so these would be scored as 2023–24 text. **Proposed:** exclude papers whose family has a formal publication dated before 2022 from exposure scoring. Not applied.
2. **Unlinked published versions.** Run a conservative title + author + date match for 2023–24 arXiv papers that have no published work, to estimate how many published versions are missed. This matters for the rule excluding exposure-window papers from outcomes.
3. Resolve the 93 duplicate arXiv IDs and the ~1,500 works linked to several arXiv papers.
4. Sample check of v1 dates against OAI-PMH once the endpoint works.
5. Remaining audit sections: conference and book-chapter classification, preprint handling, 2026H1 completeness, author-ID quality, indexing delay, `has_content` coverage.
