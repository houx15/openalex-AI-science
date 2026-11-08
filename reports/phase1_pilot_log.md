# Phase 1 pilot: run log

Decisions behind the pilot are in `docs/DECISIONS.md` (2026-11-08).

## Sample lists (run r20261108a)

`sql/ctas_pilot_sample.sql` → Athena table `pilot_sample_r20261108a`. No outcomes, no scores.

| Sample | Rule | Authors | Papers |
|---|---|---|---|
| calibration | arXiv v1 2019-01..2022-10, exposure paper eligibility, 5,000 per group by hash (seed 20261108): astro-ph, cond-mat, cs, eess, hep-nucl-grqc, math (+math-ph), physics-nlin, qbio-qfin-econ, quant-ph, stat | — | 50,000 |
| pilot_main | 3,300 main-sample authors by hash (seed 20261107), k = 3 (seed 20261105), after dropping exposure papers with a formal publication before 2022 | 3,300 | 6,133 |
| placebo | 30,000 pseudo-timeline authors by hash (seed 20261107), k = 3 from 2017–18, dropping papers with a formal publication before 2016 | 30,000 | 47,115 |
| Total unique | | | 103,248 |

The placebo list uses the ID/DOI families only. The title fallback has not yet been extended to 2017–18 v1 (Phase 0 leftover); when it is, the pre-2016 exclusion may drop a few more placebo papers.

Files (gitignored, also on Adroit at `/scratch/network/yh6580/ai_division_of_labor/data/pilot/`):

| File | sha256 |
|---|---|
| `data/derived/pilot/pilot_sample_r20261108a.csv` (114,219 rows: sample, arxiv_id, author_id, cal_group, v1_date, n_versions, primary_category, license) | `b8aaf793fd4678fa6739e4a7a535abb54a54547f8fb40261d4094766cb18f51d` |
| `data/derived/pilot/fetch_order_r20261108a.txt` (unique IDs: pilot_main, then calibration, then placebo) | `57a4a3309af94141c67f29bc84e48a1c8f112e6b7717464b32136095e2206553` |

## Text acquisition

- Started 2026-11-08 09:00 (local time) in tmux session `arxivfetch` on login node **adroit5**: `src/text/fetch_arxiv_v1.py`, one request per 3 s to `arxiv.org/e-print/<id>v1`. Expected run time about 3.6 days.
- Output: `/scratch/network/yh6580/ai_division_of_labor/text/arxiv_v1_pilot/`, with `manifest.jsonl` (one record per attempt) and `fetch.log`. Only LaTeX text members (`.tex/.ltx/.bbl`) are kept, or PDF-extracted text for PDF-only submissions. Expected size is 2–3 GB (11–39 KB per paper in the first records).
- Environment: `/scratch/network/yh6580/ai_division_of_labor/envs/fetch` (Python 3.12.7 from anaconda3/2024.10, requests 2.32.3, PyMuPDF 1.24.10). Adroit scratch had ~64 GB free at the start.
- To check: `ssh adroit5.princeton.edu` (the `adroit` alias may land on another login node), then `tmux attach -t arxivfetch`, or `tail` the log; the manifest is on shared scratch and readable from any node. Rerunning the same command resumes from the manifest.
