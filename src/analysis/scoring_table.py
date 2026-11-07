"""Phase 0 scoring and cost table (SPEC §10 task 11).

Paper counts come from sql/scoring_counts_funnel.sql, sql/scoring_counts_extra.sql and the placebo
subsample query logged in reports/cost_log.csv (eligibility v1, k = 3, seed 20261105). GPU seconds
per paper are measured in the Phase 1 pilot; until then they are None and GPU-hours print blank.
Re-run with measured values to fill the table:

Usage:
    python -m src.analysis.scoring_table [PROSELENS_S IDEALENS_EXTRACT_S IDEALENS_SCORE_S]
"""

import sys

MB_PER_PAPER = 4.0           # mean v1 source package, reports/phase0_funnel.md (400-paper sample)
SECONDS_PER_REQUEST = 3.0    # arXiv per-paper access rate
REVISED_SHARE = 0.42         # selected 2023-24 papers with > 1 version (113,898 / 271,952 under v0)
REVISED_SHARE_OTHER = 0.44   # other v1 years, 43-44% (reports/phase0_funnel.md)
ADROIT_GPUS = 2              # per-user GPU limit on gpu-long [VERIFY]

# (section, item, papers to score, incremental over items above it, window, revised share, note).
# Fetch, bytes and GPU-hours use the incremental papers; None = alternative to the line above.
ITEMS = [
    ("Phase 1 pilot", "Calibration, 5,000 x ~10 arXiv groups (2019-01..2022-10)", 50_000, 50_000, "calibration", REVISED_SHARE_OTHER, "Reused as the full calibration set"),
    ("Phase 1 pilot", "Main-sample pilot, 2,000 random authors x k = 3", 3_709, 3_709, "exposure", REVISED_SHARE, "Subset of main k = 3"),
    ("Phase 1 pilot", "Score placebo, 30k pseudo-timeline authors x k = 3", 47_168, 47_168, "placebo", REVISED_SHARE_OTHER, "50k authors: 71,047; all 154,993: 150,049"),
    ("Phase 1 pilot", "Extraction stability, 1,000 papers x 2 repeat extractions", 2_000, 2_000, None, 0.0, "IdeaLens only; text already fetched"),
    ("Phase 1 pilot", "LaTeX vs PDF input, 1,000 papers", 1_000, 1_000, None, 0.0, "PDF fetch per paper; both models"),
    ("Phase 1 pilot", "AI-polishing, 500 pre-2023 papers", 500, 500, None, 0.0, "Plus text generation with a local LLM"),
    ("Phase 1 pilot", "AI-idea sensitivity and newer generators, ~1,100 generated papers", 1_100, 1_100, None, 0.0, "Plus text generation"),
    ("Phase 1 pilot", "Local vs Gemini outlines, 500 papers", 500, 0, None, 0.0, "External; needs PI approval; API cost not estimated"),
    ("Main", "Main sample, all 293,950 authors x k = 3", 273_645, 269_936, "exposure", REVISED_SHARE, "Pilot papers counted above"),
    ("Main", "  or random 100k authors x k = 3", 137_450, None, "exposure", REVISED_SHARE, "Replaces the line above"),
    ("Main", "  or random 30k authors x k = 3", 50_699, None, "exposure", REVISED_SHARE, "Replaces the line above"),
    ("Extra", "Monthly first detection / rolling exposure (all eligible 2023-24 papers)", 352_575, 78_930, "exposure", REVISED_SHARE, "Both use the same extra papers"),
    ("Extra", "AI researchers, 33,506 authors x k = 3", 56_573, 27_613, "exposure", REVISED_SHARE, "Rest are co-authored with main authors"),
    ("Extra", "New entrants (first paper 2023-24), 114,029 authors x k = 3", 114_222, 45_598, "exposure", REVISED_SHARE, "Includes AI-field entrants and split author IDs"),
    ("Extra", "H1 follow-up 2025H1-2026H1, cap 1 per author per half-year", 126_603, 126_603, "followup", REVISED_SHARE_OTHER, "Upper bound: 142,056 authors before removing those already flagged"),
]
# Bulk source tars per window (GB), arXiv manifests read 2026-11-06
BULK_GB = {"exposure": 1943, "calibration": 1884, "placebo": 374, "followup": 1828}


def fmt(x, nd=0):
    return "" if x is None else f"{x:,.{nd}f}"


def gpu_hours(papers, rates):
    if any(r is None for r in rates):
        return None
    return papers * sum(rates) / 3600


def main(proselens_s=None, idealens_extract_s=None, idealens_score_s=None):
    rates = [None if r is None else float(r) for r in (proselens_s, idealens_extract_s, idealens_score_s)]
    print("| Section | Item | Papers | Incremental | v1 source (GB) | Per-paper fetch, all (days) "
          "| Per-paper fetch, hybrid (days) | GPU-hours | Adroit wall-clock (days) | Note |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for sec, item, n, inc, window, rev, note in ITEMS:
        m = inc if inc is not None else n  # papers not already scored for an item above
        fetched = window is not None
        gb = m * MB_PER_PAPER / 1000 if fetched else None
        all_days = m * SECONDS_PER_REQUEST / 86400 if fetched else None
        hyb_days = m * rev * SECONDS_PER_REQUEST / 86400 if fetched else None
        g = gpu_hours(m, rates)
        wall = None if g is None else g / ADROIT_GPUS / 24
        print(f"| {sec} | {item} | {fmt(n)} | {fmt(inc)} | {fmt(gb)} | {fmt(all_days, 1)} | {fmt(hyb_days, 1)} "
              f"| {fmt(g)} | {fmt(wall, 1)} | {note} |")
    print()
    print("| Bulk window | Source tars (GB) |")
    print("|---|---|")
    for w, gb in BULK_GB.items():
        print(f"| {w} | {gb:,} |")


if __name__ == "__main__":
    main(*sys.argv[1:4])
