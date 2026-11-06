"""Phase 0: power check by injection. Adds a known W effect (post-period counts of W authors
scaled by exp(effect) via Poisson thinning-up) on the full main sample, mid scenario, and records
how often the W vs N coefficient is significant at 5%. Expected about 80% at the MDE.

Usage:
    python -m src.analysis.sim_power_check PANEL_CSV AUTHORS_CSV OUT_CSV EFFECT_PCT [RUNS]
"""

import sys

import numpy as np
import pandas as pd

from src.analysis.sim_power import SCENARIOS, SEED, build_panel, draw_types, fit


def main(panel_csv, authors_csv, out_csv, effect_pct, runs=30):
    rng = np.random.default_rng(SEED + 2)
    a, p = build_panel(panel_csv, authors_csv)
    effect = np.log1p(float(effect_pct) / 100)
    rows = []
    for r in range(int(runs)):
        res = fit(p, draw_types(a, *SCENARIOS[1][1:], rng), effect_w=effect, rng=rng)
        rows.append({"effect_pct": float(effect_pct), "run": r, **res, "reject": abs(res["b_w"] / res["se_w"]) > 1.96})
        print(rows[-1], flush=True)
    d = pd.DataFrame(rows)
    d.to_csv(out_csv, index=False)
    print(f"effect {effect_pct}%: mean estimate {np.expm1(d.b_w.mean()):.3%}, rejection rate {d.reject.mean():.2f} over {len(d)} runs")


if __name__ == "__main__":
    main(*sys.argv[1:6])
