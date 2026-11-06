# Phase 0 sample funnel and data volume

OpenAlex snapshot 2026-10-14; arXiv metadata Kaggle v21506946. Run ID r20261106a. No outcome by score, flag or type has been computed (SPEC §1 firewall). All rules marked [PROPOSED] are for the Phase 0 gate.

Code: `sql/ctas_author_funnel.sql` (author table `author_funnel_r20261106a`), `sql/funnel_counts.sql`, `sql/panel_volume.sql`, `sql/funnel_pseudo_timeline.sql`, `src/data/sample_arxiv_sizes.py`.

## Rules used

- **Eligible work** [PROPOSED; v0]: not xpac; publication date present; type `article` or `conference-paper`; primary source a journal, conference or **book series** (admits LNCS-style proceedings, 225k conference papers in 2018–21); not paratext or retracted. Excluded pending the conference/book-chapter audit: conference papers with a repository or missing primary source (0.8M in 2018–21), and book chapters.
- **AI researcher** [PROPOSED]: ≥50% of eligible 2018–2022 works have primary-topic subfield *Artificial Intelligence* (1702) or *Computer Vision and Pattern Recognition* (1707).
- **Eligible arXiv paper** [PROPOSED; VERIFY]: v1 in 2023–2024 (UTC); all family works have ≤50 authors; at least one family work has OpenAlex language `en`; title does not match a review/survey/tutorial/position/erratum/comment pattern. The author link runs through any family work (arXiv record or published version, including xpac).
- **Main sample**: ≥4 eligible works in 2018–2021, not an AI researcher, ≥`m` eligible arXiv papers.

## Funnel (authors)

| Step | All | Physical Sci. | Health Sci. | Social Sci. | Life Sci. |
|---|---|---|---|---|---|
| ≥1 eligible work 2018–21 | 18,355,433 | 6,107,363 | 5,402,314 | 4,285,091 | 2,532,989 |
| ≥4 eligible works 2018–21 | 5,009,495 | 1,874,621 | 1,642,311 | 758,225 | 730,234 |
| … and not AI researcher | 4,927,856 | 1,793,472 | 1,642,117 | 758,011 | 730,152 |
| … with an eligible work in 2023–24 | 3,841,834 | 1,418,667 | 1,297,999 | 541,023 | 582,282 |
| … with any arXiv v1 in 2023–24 | 319,756 | 261,085 | 28,080 | 14,211 | 16,348 |
| **… m = 1 eligible arXiv v1** | **290,330** | **234,631** | **26,525** | **13,647** | **15,496** |
| … m = 2 | 157,563 | 136,885 | 9,087 | 6,062 | 5,514 |
| … m = 3 | 105,575 | 94,390 | 4,609 | 3,644 | 2,923 |

Domain is the author's modal 2018–2022 domain; 31 m=1 authors have none.

Other cuts, for m = 1:
- **AI researchers excluded:** 31,799. Alternatives: 0.25 cut → 4,840,612 not-AI at ≥4 works; 0.75 cut → 4,974,103.
- **ORCID:** 276,248 (95.1%) have it.
- **Posted to arXiv in 2018–2022:** 201,355 (69.4%).
- **Lower baseline threshold (comparison only):** authors with 2–3 baseline works would add 62,309.

### m = 1 by field (modal 2018–2022 field)

| Field | m = 1 | m = 3 | Field | m = 1 | m = 3 |
|---|---|---|---|---|---|
| Physics and Astronomy | 71,497 | 38,770 | Environmental Science | 5,894 | 900 |
| Engineering | 69,858 | 20,046 | Social Sciences | 4,527 | 1,052 |
| Computer Science (non-AI) | 40,828 | 18,012 | Earth and Planetary Sci. | 3,891 | 692 |
| Medicine | 25,669 | 4,501 | Neuroscience | 3,534 | 850 |
| Mathematics | 19,076 | 9,632 | Chemistry | 2,792 | 472 |
| Materials Science | 18,907 | 5,569 | Agricultural and Biological Sci. | 2,487 | 326 |
| Biochem., Genetics, Mol. Biol. | 9,115 | 1,717 | Economics, Econometrics, Finance | 2,466 | 880 |

Thirteen further fields have fewer than 2,400 authors each. The full table is in query `119d4f04`.

### m = 1 by career age in 2023 (years since first non-xpac publication)

| 0–5 | 6–10 | 11–20 | 21+ |
|---|---|---|---|
| 20,194 | 46,959 | 98,405 | 124,772 |

Reading:
- The sample is large but concentrated: 81% of authors are in Physical Sciences (physics, engineering, CS, mathematics, materials).
- Health, social and life sciences contribute about 56k authors in total, few of them with 3 papers.
- Early-career authors are underrepresented by construction: the ≥4-works baseline rule removes them.

## Data volume

### Author × publication panel (metadata only)

| Object | Rows |
|---|---|
| Main-sample authors (m = 1) | 290,330 |
| Author × half-year panel (2018H1–2026H1, zero-filled from first publication half-year) | 4,904,796 |
| Author × eligible-work rows, 2018–2026 | 15,593,029 |
| Distinct eligible works, 2018–2026 | 7,801,953 (median 7 authors) |

This is a small dataset: well under 1 GB as Parquet. It can be built in Athena for a few dollars and run locally or on Adroit. Citations (dated citing works) are the larger part; they are sized in the citation-window audit, which is not yet run.

### Full text to acquire and score (arXiv v1)

| Use | Papers | Note |
|---|---|---|
| Main sample, k = 3 | 271,952 | Unique papers; 553,468 author-paper slots, shared papers scored once |
| Main sample, all eligible papers | 351,640 | Only if monthly first detection or rolling exposure is kept (+79,688) |
| Calibration, 2019-01 to 2022-10 | ~50,000 | 5,000 × ~10 arXiv groups (cs, math, cond-mat, physics, astro-ph, hep/nucl/gr-qc, eess, quant-ph, stat, q-bio/q-fin/econ; math-ph and nlin to merge). Pool: 669,553 papers |
| Placebo, −6-year pseudo-timeline (2017–18 v1) | 150,049 at k = 3 (192,524 all) | 154,993 authors. A subsample is enough for the placebo; size at the gate |
| Phase 1 pilot | ~6,000 + calibration | 2,000 authors × ≤3 papers (a subset of the main sample) |

Totals:
- **Core:** main k = 3 + calibration ≈ **322k papers**.
- **Maximal:** with all eligible papers and the full placebo ≈ **595k papers**.

### Bytes

**Per paper:** fixed-seed sample of 400 k = 3 papers (`data/derived/funnel/v1_size_sample.csv`). v1 source-package size is read from the arXiv submission history (export.arxiv.org; OAI-PMH timed out). Mean 4.0 MB, median 1.55 MB, p90 10.2 MB, max 45 MB.

**Bulk:** arXiv requester-pays manifests, read 2026-11-06 under the manifest-only policy (`src/data/arxiv_bulk_volume.py`):

| Window | Source tars | PDF tars | Items |
|---|---|---|---|
| Exposure 2023-01–2024-12 | 1,943 GB (4.29 MB/item) | 1,607 GB | 452,524 |
| Calibration 2019-01–2022-10 | 1,884 GB | 1,605 GB | 669,359 |
| Placebo 2017-01–2018-12 | 374 GB | 397 GB | 264,139 |

The manifests list one item per paper; 452,524 is about our 452,913 v1 count. Whether the item is v1 or the version current when the tar was built is still [VERIFY]. This needs one tar opened, and it decides how often a later version would have to be replaced by v1 from per-paper access.

| Volume needed | Source (LaTeX) | PDF |
|---|---|---|
| Main k = 3 (272k papers) | ≈1.1 TB | ≈1.0 TB |
| Calibration (50k) | ≈0.14 TB | ≈0.12 TB |
| Extracted plain text, all core papers (assumes ~50–100 KB per paper) | ≈15–30 GB | |

### Access options (prices are standard us-east-1 list prices [VERIFY at approval])

| Option | What moves | Approx. cost | Time | Notes |
|---|---|---|---|---|
| **A. Bulk S3 → EC2 in us-east-1, extract there** | ~2 TB of 2023–24 source tars, plus ~0.4–1.9 TB for the placebo and calibration windows, read inside AWS | S3 → EC2 same-region transfer is free; requests are cents. EC2 plus temporary EBS ≈ $10–30. Moving the extracted text (~30 GB) to Adroit ≈ $3 | Hours | Cheapest. Only extracted text leaves AWS, and full text is not redistributed. Needs PI approval for the EC2 spend and access to `arxiv/src/*`. Counts toward the $100 cap |
| B. Bulk S3 → Adroit directly | ~2–4 TB out of AWS | Egress ≈ $0.09/GB → **$180–350** | Days | Exceeds the AWS cap; needs 2–4 TB of scratch |
| C. Per-paper from arxiv.org | ~1.1 TB for 272k papers | $0 | ~10 days at 1 request / 3 s for main k = 3 (≈11 days with calibration) | arXiv asks bulk users to use S3. Gives exact v1 (`/e-print/<id>v1`). Good for the Phase 1 pilot (6k papers ≈ 5 hours) and for v1 replacements |

**Recommendation:** use C for the Phase 1 pilot, which is small and v1-exact, and A for full scoring after the Phase 1 gate. Either way, Adroit stores only extracted text (≤30 GB), not tars.

## Is the panel needed?

Yes, for the main design. The outcome side and the author × publication panel come entirely from OpenAlex metadata and are cheap. Only the scoring side needs arXiv full text, and that is where the size and cost lie. With SPEC's k = 3 rule, scoring needs about 272k main-sample papers plus about 50k calibration papers. The main-sample part is about 60% of all 452,913 arXiv v1s from 2023–24, so bulk access may beat per-paper access. It can be cut further by scoring a random subset of authors if power allows (power simulation, task 8).

## Not yet done (Phase 0)

- Conference/book-chapter classification audit; this may change eligible counts.
- 2026H1 completeness and the citation-window audit, which sizes the citation data.
- Power and false-positive simulations, which decide whether all 290k authors are needed.
- Usable-v1-text rate (LaTeX vs PDF) and language detection; the counts above assume usable text.
- Open one bulk tar to check v1 vs later version (about 0.5 GB inside us-east-1; needs PI approval and a policy change).
- GPU-hours: ProseLens and IdeaLens throughput is measured in the Phase 1 pilot. Multiply the paper counts above by the measured per-paper time.
