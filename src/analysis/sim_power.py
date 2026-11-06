"""Phase 0 power simulation (SPEC §10 task 8): minimum detectable effects for W vs N and WI vs W.

Uses only 2018H1-2022H2 eligible-work counts of main-sample authors (sql/sim_power_panel.sql,
sql/sim_power_authors.sql); no later outcome data and no scores. Within that window a pseudo design
mirrors the main model: pre = 2018H1-2020H2, gap = 2021H1 (stands in for the excluded exposure
window), post = 2021H2-2022H2 (three half-years, like 2025H1-2026H1).

Author types are drawn at random (true effect zero) from paper-level flags, so prevalence depends
on n_i = min(eligible exposure papers, 3) as it will in the study: each selected paper is
writing-flagged with probability p_w and idea-flagged with probability p_i (higher on
writing-flagged papers), and an author has a signal when the flagged share is >= 0.5 (SPEC §8).
The model is SPEC §9's PPML:

    n_it ~ W x post + WI x post + I x post | author + field x career bin x half + exposure bin x half

(exposure bin = 1, 2, 3, 4-5, 6+ eligible exposure papers; it absorbs n_i x period). Standard
errors are clustered by author. MDE at 80% power, two-sided 5%: exp(2.8 * SE) - 1. A check run
injects a known effect and records the rejection rate.

Usage:
    python -m src.analysis.sim_power PANEL_CSV AUTHORS_CSV OUT_CSV
"""

import sys
import time

import numpy as np
import pandas as pd
import pyfixest as pf

SEED = 20261106
HALVES = list(range(2018 * 2, 2022 * 2 + 2))  # 2018H1 .. 2022H2
PRE_END, GAP, POST_START = 2020 * 2 + 1, 2021 * 2, 2021 * 2 + 1
SCENARIOS = [  # (label, p_w, p_i given writing flag, p_i given no writing flag)
    ("low", 0.05, 0.20, 0.01),
    ("mid", 0.15, 0.25, 0.02),
    ("high", 0.30, 0.30, 0.03),
]
SAMPLE_SIZES = [290_000, 100_000, 30_000, 10_000]


def build_panel(panel_csv, authors_csv):
    a = pd.read_csv(authors_csv, dtype={"author_id": str, "modal_field": str})
    a["n_i"] = a.n_arxiv_elig.clip(upper=3)
    a["exp_bin"] = pd.cut(a.n_arxiv_elig, [0, 1, 2, 3, 5, np.inf], labels=False)
    a["field"] = a.modal_field.fillna("none")
    c = pd.read_csv(panel_csv, dtype={"author_id": str})
    grid = a[["author_id", "first_year"]].merge(pd.DataFrame({"half": HALVES}), how="cross")
    grid = grid[grid.half >= np.maximum(grid.first_year * 2, HALVES[0])]  # zero-fill from first half-year
    p = grid.merge(c[["author_id", "half", "n"]], on=["author_id", "half"], how="left").fillna({"n": 0})
    p = p.merge(a[["author_id", "field", "n_i", "exp_bin"]], on="author_id")
    age = p.half // 2 - p.first_year
    p["career"] = pd.cut(age, [-np.inf, 5, 10, 20, np.inf], labels=["0-5", "6-10", "11-20", "21+"]).astype(str)
    p = p[p.half != GAP].copy()
    p["post"] = (p.half >= POST_START).astype(int)
    p["fch"] = p.field + "|" + p.career + "|" + p.half.astype(str)
    p["eh"] = p.exp_bin.astype(str) + "|" + p.half.astype(str)
    return a, p


def draw_types(a, p_w, p_i_w, p_i_nw, rng):
    n = a.n_i.to_numpy()
    w_flags = rng.binomial(n, p_w)
    i_flags = rng.binomial(w_flags, p_i_w) + rng.binomial(n - w_flags, p_i_nw)
    w = w_flags / n >= 0.5
    i = i_flags / n >= 0.5
    return pd.DataFrame({"author_id": a.author_id, "W": (w & ~i).astype(int),
                         "WI": (w & i).astype(int), "I": (~w & i).astype(int)})


def fit(p, types, effect_w=0.0, rng=None):
    d = p.merge(types, on="author_id")
    if effect_w:
        lift = (d.W == 1) & (d.post == 1)
        d.loc[lift, "n"] = d.loc[lift, "n"] + rng.poisson((np.exp(effect_w) - 1) * d.loc[lift, "n"])
    for t in ("W", "WI", "I"):
        d[f"{t}_post"] = d[t] * d.post
    m = pf.fepois("n ~ W_post + WI_post + I_post | author_id + fch + eh", data=d,
                  vcov={"CRV1": "author_id"})
    b, v = m.coef(), m._vcov
    names = list(b.index)
    iw, iwi = names.index("W_post"), names.index("WI_post")
    se_w = np.sqrt(v[iw, iw])
    se_diff = np.sqrt(v[iw, iw] + v[iwi, iwi] - 2 * v[iw, iwi])
    return {"b_w": b["W_post"], "se_w": se_w, "b_wi_minus_w": b["WI_post"] - b["W_post"],
            "se_wi_minus_w": se_diff, "n_W": int(types.W.sum()), "n_WI": int(types.WI.sum()),
            "n_N": int(((types.W + types.WI + types.I) == 0).sum()), "nobs": int(m._N)}


def main(panel_csv, authors_csv, out_csv, reps=3):
    rng = np.random.default_rng(SEED)
    a, p = build_panel(panel_csv, authors_csv)
    print(f"panel: {a.author_id.nunique():,} authors, {len(p):,} rows; mean count {p.n.mean():.2f}", flush=True)
    rows = []
    for size in SAMPLE_SIZES:
        sub = a if size >= len(a) else a.sample(size, random_state=SEED)
        ps = p[p.author_id.isin(sub.author_id)]
        for label, p_w, p_i_w, p_i_nw in SCENARIOS:
            for r in range(int(reps)):
                t0 = time.time()
                res = fit(ps, draw_types(sub, p_w, p_i_w, p_i_nw, rng))
                rows.append({"authors": len(sub), "scenario": label, "rep": r, **res,
                             "seconds": round(time.time() - t0, 1)})
                print(rows[-1], flush=True)
    out = pd.DataFrame(rows)
    # injected-effect check on the full sample, mid scenario: power at the computed MDE for W vs N
    full_mid = out[(out.authors == len(a)) & (out.scenario == "mid")]
    mde_log = 2.8 * full_mid.se_w.mean()
    hits = []
    for r in range(int(reps) * 3):
        res = fit(p, draw_types(a, *SCENARIOS[1][1:]), effect_w=mde_log, rng=rng)
        hits.append(abs(res["b_w"] / res["se_w"]) > 1.96)
    print(f"injected W effect {np.exp(mde_log) - 1:.3%}: rejection rate {np.mean(hits):.2f} over {len(hits)} runs")
    out["check_injected_effect"] = np.exp(mde_log) - 1
    out["check_rejection_rate"] = np.mean(hits)
    out.to_csv(out_csv, index=False)
    s = out.groupby(["authors", "scenario"]).agg(
        n_W=("n_W", "mean"), n_WI=("n_WI", "mean"), se_w=("se_w", "mean"), sd_b_w=("b_w", "std"),
        se_wi_w=("se_wi_minus_w", "mean"), sd_b_wi_w=("b_wi_minus_w", "std"))
    s["MDE_W_vs_N_%"] = (np.exp(2.8 * s.se_w) - 1) * 100
    s["MDE_WI_vs_W_%"] = (np.exp(2.8 * s.se_wi_w) - 1) * 100
    print(s.round(4).to_string())


if __name__ == "__main__":
    main(*sys.argv[1:4])
