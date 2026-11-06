"""Phase 0: randomization check of the power simulation's standard errors.

Under random type assignment the true effect is zero, so across many draws the spread of the W vs
N and WI vs W estimates is the real sampling variability, and the share of draws with |t| > 1.96 is
the real false-positive rate of author-clustered SEs. If the spread exceeds the reported SE, MDEs
must be based on the empirical spread. Also reruns with hyper-prolific authors (mean > 30 eligible
works per half-year in 2018-2022) dropped, to see whether they drive the gap.

Usage:
    python -m src.analysis.sim_power_ri PANEL_CSV AUTHORS_CSV OUT_CSV [DRAWS]
"""

import sys

import numpy as np
import pandas as pd

from src.analysis.sim_power import SCENARIOS, SEED, build_panel, draw_types, fit


def main(panel_csv, authors_csv, out_csv, draws=40):
    rng = np.random.default_rng(SEED + 1)
    a, p = build_panel(panel_csv, authors_csv)
    mean_out = p.groupby("author_id").n.mean()
    prolific = set(mean_out[mean_out > 30].index)
    print(f"hyper-prolific authors (mean > 30 per half-year): {len(prolific):,}", flush=True)
    rows = []
    for label, keep in [("all", a), ("drop_prolific", a[~a.author_id.isin(prolific)])]:
        pk = p[p.author_id.isin(keep.author_id)]
        for r in range(int(draws)):
            res = fit(pk, draw_types(keep, *SCENARIOS[1][1:], rng))
            rows.append({"sample": label, "authors": len(keep), "draw": r, **res})
            print(rows[-1], flush=True)
            pd.DataFrame(rows).to_csv(out_csv, index=False)
    d = pd.DataFrame(rows)
    s = d.groupby("sample").agg(
        draws=("b_w", "size"), mean_b_w=("b_w", "mean"), sd_b_w=("b_w", "std"), mean_se_w=("se_w", "mean"),
        sd_b_wi_w=("b_wi_minus_w", "std"), mean_se_wi_w=("se_wi_minus_w", "mean"))
    s["reject5_w"] = d.assign(r=abs(d.b_w / d.se_w) > 1.96).groupby("sample").r.mean()
    s["reject5_wi_w"] = d.assign(r=abs(d.b_wi_minus_w / d.se_wi_minus_w) > 1.96).groupby("sample").r.mean()
    s["MDE_W_vs_N_%_empirical"] = (np.exp(2.8 * s.sd_b_w) - 1) * 100
    s["MDE_WI_vs_W_%_empirical"] = (np.exp(2.8 * s.sd_b_wi_w) - 1) * 100
    print(s.round(4).to_string())
    s.to_csv(out_csv.replace(".csv", "_summary.csv"))


if __name__ == "__main__":
    main(*sys.argv[1:5])
