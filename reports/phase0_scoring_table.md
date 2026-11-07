# Phase 0 scoring and cost table

SPEC §10 task 11. **Draft: GPU throughput is blank until the Phase 1 pilot measures it.** Every other column is filled. No scores or outcomes are used; the 2025–26 counts below are arXiv postings of main-sample authors, not split by any signal (SPEC §1 firewall).

Code and inputs:
- Paper counts: `sql/scoring_counts_funnel.sql`, `sql/scoring_counts_extra.sql`, and a placebo subsample query (query IDs in `reports/cost_log.csv`; together $0.37).
- Table: `src/analysis/scoring_table.py`. Re-run it with the pilot's measured seconds per paper to fill the GPU columns: `python -m src.analysis.scoring_table PROSELENS_S IDEALENS_EXTRACT_S IDEALENS_SCORE_S`.
- Rules: eligibility v1, k = 3 papers per author by fixed-seed hash (seed 20261105), a paper shared by several authors scored once. Random author subsamples use seed 20261107.

## 1. Papers to score by analysis

Columns:
- **Papers**: unique papers the analysis needs.
- **Incremental**: papers not already counted on a line above it. Bytes, fetch time and GPU-hours use this column.
- **v1 source**: incremental papers × 4.0 MB, the mean v1 source package.
- **Per-paper fetch, all**: every incremental paper fetched from `arxiv.org/e-print/<id>v1` at 1 request per 3 s.
- **Per-paper fetch, hybrid**: only revised papers are fetched per paper (42% of 2023–24 papers, 44% in other years); single-version papers come from bulk tars (§2).
- **GPU-hours** = incremental papers × (ProseLens + IdeaLens extraction + IdeaLens scoring seconds per paper) / 3600. **Adroit wall-clock** assumes 2 A100s per user [VERIFY].

| Section | Item | Papers | Incremental | v1 source (GB) | Per-paper fetch, all (days) | Per-paper fetch, hybrid (days) | GPU-hours | Adroit wall-clock (days) | Note |
|---|---|---|---|---|---|---|---|---|---|
| Phase 1 pilot | Calibration, 5,000 x ~10 arXiv groups (2019-01..2022-10) | 50,000 | 50,000 | 200 | 1.7 | 0.8 |  |  | Reused as the full calibration set |
| Phase 1 pilot | Main-sample pilot, 2,000 random authors x k = 3 | 3,709 | 3,709 | 15 | 0.1 | 0.1 |  |  | Subset of main k = 3 |
| Phase 1 pilot | Score placebo, 30k pseudo-timeline authors x k = 3 | 47,168 | 47,168 | 189 | 1.6 | 0.7 |  |  | 50k authors: 71,047; all 154,993: 150,049 |
| Phase 1 pilot | Extraction stability, 1,000 papers x 2 repeat extractions | 2,000 | 2,000 |  |  |  |  |  | IdeaLens only; text already fetched |
| Phase 1 pilot | LaTeX vs PDF input, 1,000 papers | 1,000 | 1,000 |  |  |  |  |  | PDF fetch per paper; both models |
| Phase 1 pilot | AI-polishing, 500 pre-2023 papers | 500 | 500 |  |  |  |  |  | Plus text generation with a local LLM |
| Phase 1 pilot | AI-idea sensitivity and newer generators, ~1,100 generated papers | 1,100 | 1,100 |  |  |  |  |  | Plus text generation |
| Phase 1 pilot | Local vs Gemini outlines, 500 papers | 500 | 0 |  |  |  |  |  | External; needs PI approval; API cost not estimated |
| Main | Main sample, all 293,950 authors x k = 3 | 273,645 | 269,936 | 1,080 | 9.4 | 3.9 |  |  | Pilot papers counted above |
| Main |   or random 100k authors x k = 3 | 137,450 |  | 550 | 4.8 | 2.0 |  |  | Replaces the line above |
| Main |   or random 30k authors x k = 3 | 50,699 |  | 203 | 1.8 | 0.7 |  |  | Replaces the line above |
| Extra | Monthly first detection / rolling exposure (all eligible 2023-24 papers) | 352,575 | 78,930 | 316 | 2.7 | 1.2 |  |  | Both use the same extra papers |
| Extra | AI researchers, 33,506 authors x k = 3 | 56,573 | 27,613 | 110 | 1.0 | 0.4 |  |  | Rest are co-authored with main authors |
| Extra | New entrants (first paper 2023-24), 114,029 authors x k = 3 | 114,222 | 45,598 | 182 | 1.6 | 0.7 |  |  | Includes AI-field entrants and split author IDs |
| Extra | H1 follow-up 2025H1-2026H1, cap 1 per author per half-year | 126,603 | 126,603 | 506 | 4.4 | 1.9 |  |  | Upper bound: 142,056 authors before removing those already flagged |

Notes on the lines:
- **Pilot main sample:** 2,000 random authors give 3,709 papers, not SPEC's "up to 6,000". Most authors have one or two eligible papers. Use 3,300 authors to reach about 6,000 papers.
- **Score placebo:** sized at 30k pseudo-timeline authors [PROPOSED]. The placebo compares the top decile of author mean score with the rest within domain and `n_i`, so 30k authors give about 3,000 top-decile authors. Its power has not been simulated; run the §9-style simulation on the pseudo sample if the PI wants a firmer size.
- **Synthetic tests** [PROPOSED sizes]: these papers need text generation as well as scoring. Generation needs a local open-weights model on GPU (throughput blank) unless the PI approves an external LLM. The Gemini comparison costs API fees, not GPU time, and needs approval.
- **100k subsample:** about half the main scoring, not a third. Subsampled authors share fewer papers, so unique papers fall more slowly than authors. The power simulation's MDE for this size is about 2.7% (W vs N) and 5.5% (WI vs W), mid prevalence (`reports/phase0_simulation.md`).
- **Monthly first detection / rolling exposure:** the same 78,930 extra papers serve both. They are main-sample authors' eligible 2023–24 papers beyond the k = 3 draw. The simulation found monthly first detection biased (+3%) even under random detection.
- **AI researchers:** half their k = 3 papers are already scored because they are co-authored with main-sample authors.
- **New entrants:** first non-xpac OpenAlex paper in 2023–24 and an eligible 2023–24 arXiv paper. Two caveats: no AI-researcher split exists for entrants yet, and OpenAlex author-ID splits create false "new" authors. A per-author cap of 1 paper, or a random 30k-entrant sample, would cut this line.
- **H1 follow-up:** 2025H1–2026H1 papers of main-sample authors, capped at one per author per half-year. This is an upper bound. The H1 sample drops authors already idea-flagged in 2023–24, which is unknown until scoring. It also needs the 2025–26 bulk window (§2), the only line that does.
- Not counted: OpenAlex full-text fallback (only if the Phase 0 gate rejects arXiv coverage), and abstract-only writing scores (cheap; abstracts are already in metadata).

## 2. arXiv text access: bulk S3 vs per paper

Bulk tars are sorted by month and hold each paper's latest version, so a window's tars must be read in full whatever the number of papers needed. Bulk source tars by window (manifests read 2026-11-06):

| Window | Needed for | Source tars | Items |
|---|---|---|---|
| Exposure 2023-01–2024-12 | Main, monthly/rolling, AI researchers, new entrants, pilot main sample | 1,943 GB | 452,524 |
| Calibration 2019-01–2022-10 | Calibration | 1,884 GB | 669,359 |
| Placebo 2017-01–2018-12 | Score placebo | 374 GB | 264,139 |
| Follow-up 2025-01–2026-06 | H1 follow-up | 1,828 GB | 453,948 |

Cost per bulk window on EC2 in `us-east-1` (list prices [VERIFY at approval]):
- S3 → EC2 transfer is free in region. Requester-pays GET requests cost cents (one request per ~0.5 GB tar).
- Compute: a `c7i.4xlarge` ($0.71/h) streaming and untarring at about 250 MB/s needs about 2 h per TB, so roughly $1.5–3 per TB including slack.
- Temporary EBS (200 GB gp3, a few days): about $1–2. Tars are streamed, not stored.
- Extracted text stays in S3 until copied to Adroit: about 50–100 KB per paper, so ≤30 GB for every line combined. Egress to Adroit at $0.09/GB is ≤$3.
- **Per window: about $3–8. All four windows: about $15–30.** This is within the remaining AWS budget (spent so far: $3.64 of $100).

Comparison for the main options:

| Scenario | Papers fetched | All per paper (C) | Hybrid: bulk windows + revised per paper | Hybrid AWS cost |
|---|---|---|---|---|
| Pilot only (calibration + placebo 30k + pilot main + synthetic) | 100,877 | 3.5 days, $0 | 1.5 days per paper + calibration and placebo windows | ~$5–12 (or use C, $0) |
| Pilot + main (100k authors) | 234,618 | 8.1 days, $0 | 3.5 days + 3 windows | ~$10–20 |
| Pilot + main (all authors) | 370,813 | 12.9 days, $0 | 5.5 days + 3 windows | ~$10–20 |
| Everything above (all extras, all authors) | 649,557 | 22.6 days, $0 | 9.6 days + 4 windows | ~$15–30 |

Recommendation, unchanged from `reports/phase0_funnel.md`: per paper (C) for the Phase 1 pilot, because it is v1-exact and avoids any spend before the measures are validated; the hybrid for full scoring. arXiv asks bulk users to use S3, so a 13–23-day per-paper run is the option to avoid.

## 3. GPU compute (blank until the pilot)

| Model step | Seconds per paper on one A100 | Source |
|---|---|---|
| ProseLens (writing) | — | Phase 1 pilot |
| IdeaLens outline extraction, local model | — | Phase 1 pilot |
| IdeaLens scoring | — | Phase 1 pilot |
| Synthetic-text generation, local LLM | — | Phase 1 pilot |

Scale for reading the table once speeds are known: each 1 s per paper costs 27.8 GPU-hours per 100k papers, which is 0.6 days of wall-clock on 2 A100s. Adroit has no cash cost to the project [VERIFY allocation], so the binding limit is queue time: `gpu-long` allows 2 days per job [VERIFY], so jobs must be split and resumable. AWS GPU instances are not in the plan or the IAM allowlist and would count toward the $100 cap.

## 4. Decisions for the PI

1. **Main scoring size:** all 293,950 authors (273,645 papers) or a random 100k (137,450 papers).
2. **Which extra lines to keep:** monthly first detection / rolling exposure (+78,930), AI researchers (+27,613), new entrants (+45,598, or capped), H1 follow-up (≤126,603, plus the 2025–26 bulk window).
3. **Placebo size:** 30k authors (47,168 papers) proposed; 50k (71,047) or all (150,049) possible.
4. **Pilot main-sample size:** 2,000 authors (3,709 papers) or 3,300 authors (~6,000 papers, SPEC's target).
5. **Synthetic-test generation:** local open-weights model, or external LLM (needs approval).
6. **Access route:** per-paper for the pilot; hybrid bulk + per-paper for full scoring. EC2 launches and tar downloads still need your approval each time.
