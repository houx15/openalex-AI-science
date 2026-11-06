"""Phase 0 false-positive simulation (SPEC §10 task 9) on the -6-year pseudo-timeline.

Sample: >= 4 eligible works 2012-2015, not AI, >= 1 eligible arXiv v1 in 2017-2018
(sql/sim_pseudo_authors.sql). Pre = 2012H1-2016H2 (reference 2016H2), pseudo exposure window =
2017-2018 (excluded from the fixed-window model), pseudo outcome = 2019H1-2020H1 (and without
2020H1). No real scores exist here: AI has NO effect by construction. Paper flags are generated
from author propensity scenarios, so every nonzero type coefficient is spurious.

Scenarios for the per-paper writing-flag probability (base 0.15; idea flag 0.25 on writing-flagged
papers, 0.02 otherwise), logit shift gamma = 0.5 per SD of:
  S0 random              nothing (detection still rises with the number of papers posted)
  S1 output_trend        pre-period growth, log(2015-16 output + 1) - log(2012-13 output + 1)
  S2 young               minus career age in 2017
  S3 arxiv_intensity     log number of eligible 2017-18 arXiv papers
  S4 low_baseline        minus log 2012-2015 output (mean-reversion channel)

Exposure rules:
  R1 fixed_window   types from up to k = 3 fixed-seed selected papers, share >= 0.5 (main design);
                    PPML on pre + post with type x post | author + field x career x half
                    [+ exposure bin x half]
  R2 monthly_first  staggered: treated from the half-year of the first flagged paper (all eligible
                    exposure papers), all half-years 2012H1-2020H1
  R3 rolling        share of flagged papers among papers posted before half-year t, lagged one
                    half-year, all half-years 2012H1-2020H1

Output: mean coefficient, mean clustered SE, and the share of runs rejecting at 5%, per cell.

Usage:
    python -m src.analysis.sim_false_positive PAPERS_CSV COUNTS_CSV OUT_CSV [AUTHORS] [REPS]
"""

import sys
import time

import numpy as np
import pandas as pd
import pyfixest as pf

from src.analysis.fe_groups import add_fch

SEED = 20261106
SELECT_SEED = "20261105"
HALVES = list(range(2012 * 2, 2020 * 2 + 1))  # 2012H1 .. 2020H1
PRE_END, EXP_START, EXP_END, POST_START = 2016 * 2 + 1, 2017 * 2, 2018 * 2 + 1, 2019 * 2
BASE_P, P_I_W, P_I_NW, GAMMA = 0.15, 0.25, 0.02, 0.5
FIT_KW = {"fixef_maxiter": 200_000}  # default 10,000 did not converge on 50k authors
SCENARIOS = ["S0_random", "S1_output_trend", "S2_young", "S3_arxiv_intensity", "S4_low_baseline"]


def load(papers_csv, counts_csv, n_authors):
    pp = pd.read_csv(papers_csv, dtype={"author_id": str, "arxiv_id": str, "modal_field": str})
    pp["v1_half"] = pd.to_datetime(pp.v1_date).pipe(lambda d: d.dt.year * 2 + (d.dt.month > 6))
    authors = pp.groupby("author_id").agg(first_year=("first_year", "first"),
                                          field=("modal_field", "first"), n_exp=("arxiv_id", "nunique")).reset_index()
    authors["field"] = authors.field.fillna("none")
    if n_authors and n_authors < len(authors):
        authors = authors.sample(int(n_authors), random_state=SEED)
    pp = pp[pp.author_id.isin(authors.author_id)].copy()
    # fixed-seed k = 3 selection (same hash idea as sql/funnel_counts.sql; any fixed seed works here)
    pp["h"] = pd.util.hash_pandas_object(pp.author_id + pp.arxiv_id + SELECT_SEED, index=False)
    pp["rank"] = pp.groupby("author_id").h.rank(method="first")
    pp["selected"] = pp["rank"] <= 3

    c = pd.read_csv(counts_csv, dtype={"author_id": str})
    grid = authors[["author_id", "first_year"]].merge(pd.DataFrame({"half": HALVES}), how="cross")
    grid = grid[grid.half >= np.maximum(grid.first_year * 2, HALVES[0])]
    p = grid.merge(c, on=["author_id", "half"], how="left").fillna({"n_all": 0, "n_excl": 0})
    p = p.merge(authors[["author_id", "field", "n_exp"]], on="author_id")
    age = p.half // 2 - p.first_year
    p["career"] = pd.cut(age, [-np.inf, 5, 10, 20, np.inf], labels=["0-5", "6-10", "11-20", "21+"]).astype(str)
    p["exp_bin"] = pd.cut(p.n_exp, [0, 1, 2, 3, 5, np.inf], labels=False).astype(str)
    p["fch"] = p.field + "|" + p.career + "|" + p.half.astype(str)
    p["eh"] = p.exp_bin + "|" + p.half.astype(str)

    # author covariates for propensity scenarios (pre-period only)
    pre = p[p.half <= PRE_END]
    out_early = pre[pre.half < 2014 * 2].groupby("author_id").n_all.sum()
    out_late = pre[pre.half >= 2015 * 2].groupby("author_id").n_all.sum()
    out_base = pre[pre.half < 2016 * 2].groupby("author_id").n_all.sum()
    a = authors.set_index("author_id")
    z = pd.DataFrame(index=a.index)
    z["S1_output_trend"] = np.log1p(out_late.reindex(a.index, fill_value=0)) - np.log1p(out_early.reindex(a.index, fill_value=0))
    z["S2_young"] = -(2017 - a.first_year)
    z["S3_arxiv_intensity"] = np.log(a.n_exp)
    z["S4_low_baseline"] = -np.log1p(out_base.reindex(a.index, fill_value=0))
    z = (z - z.mean()) / z.std()
    z["S0_random"] = 0.0
    return authors, pp, p, z


def draw_flags(pp, z, scenario, rng):
    logit = np.log(BASE_P / (1 - BASE_P)) + GAMMA * pp.author_id.map(z[scenario]).to_numpy()
    pw = 1 / (1 + np.exp(-logit))
    w = rng.random(len(pp)) < pw
    i = rng.random(len(pp)) < np.where(w, P_I_W, P_I_NW)
    return pp.assign(w=w, i=i)


def types_fixed_window(f):
    s = f[f.selected].groupby("author_id").agg(w=("w", "mean"), i=("i", "mean"), n_i=("w", "size"))
    W, I = s.w >= 0.5, s.i >= 0.5
    return pd.DataFrame({"W": (W & ~I).astype(int), "WI": (W & I).astype(int), "I": (~W & I).astype(int),
                         "n_i": s.n_i}).reset_index()


def coef(m, name):
    b = m.coef()[name]
    se = m.se()[name]
    return b, se


def fit_r1(p, t, exclusion=True, volume=True, post_end=2020 * 2, by_ni=False):
    d = add_fch(p[(p.half <= PRE_END) | ((p.half >= POST_START) & (p.half <= post_end))].merge(t, on="author_id"))
    d["post"] = (d.half >= POST_START).astype(int)
    d["y"] = np.where((d.post == 1) & exclusion, d.n_excl, d.n_all)
    fe = "author_id + fch" + (" + eh" if volume else "")
    if by_ni:
        terms = []
        for k in (1, 2, 3):
            for ty in ("W", "WI", "I"):
                d[f"{ty}_post_n{k}"] = d[ty] * d.post * (d.n_i == k)
                terms.append(f"{ty}_post_n{k}")
        m = pf.fepois(f"y ~ {' + '.join(terms)} | {fe}", data=d, vcov={"CRV1": "author_id"}, **FIT_KW)
        return {f"b_W_n{k}": coef(m, f"W_post_n{k}")[0] for k in (1, 2, 3)} | \
               {f"se_W_n{k}": coef(m, f"W_post_n{k}")[1] for k in (1, 2, 3)}
    for ty in ("W", "WI", "I"):
        d[f"{ty}_post"] = d[ty] * d.post
    m = pf.fepois(f"y ~ W_post + WI_post + I_post | {fe}", data=d, vcov={"CRV1": "author_id"}, **FIT_KW)
    names = list(m.coef().index)
    v = m._vcov
    iw, iwi = names.index("W_post"), names.index("WI_post")
    b_w, se_w = coef(m, "W_post")
    return {"b_W": b_w, "se_W": se_w, "b_WI_minus_W": m.coef()["WI_post"] - b_w,
            "se_WI_minus_W": np.sqrt(v[iw, iw] + v[iwi, iwi] - 2 * v[iw, iwi])}


def fit_r2(p, f):
    first = f[f.w].groupby("author_id").v1_half.min().rename("detect_half")
    d = add_fch(p.merge(first, on="author_id", how="left"))
    d["D"] = (d.half >= d.detect_half).fillna(False).astype(int)
    m = pf.fepois("n_all ~ D | author_id + fch + eh", data=d, vcov={"CRV1": "author_id"}, **FIT_KW)
    b, se = coef(m, "D")
    return {"b_W": b, "se_W": se}


def fit_r3(p, f):
    g = f.groupby(["author_id", "v1_half"]).agg(nw=("w", "sum"), n=("w", "size")).reset_index()
    rows = []
    for h in HALVES:
        s = g[g.v1_half <= h - 1].groupby("author_id").agg(nw=("nw", "sum"), n=("n", "sum"))  # lagged one half-year
        rows.append(pd.DataFrame({"author_id": s.index, "half": h, "X": (s.nw / s.n).to_numpy()}))
    x = pd.concat(rows)
    d = add_fch(p.merge(x, on=["author_id", "half"], how="left").fillna({"X": 0.0}))
    m = pf.fepois("n_all ~ X | author_id + fch + eh", data=d, vcov={"CRV1": "author_id"}, **FIT_KW)
    b, se = coef(m, "X")
    return {"b_W": b, "se_W": se}


def main(papers_csv, counts_csv, out_csv, n_authors=50_000, reps=6):
    rng = np.random.default_rng(SEED)
    authors, pp, p, z = load(papers_csv, counts_csv, int(n_authors))
    print(f"{len(authors):,} authors, {len(pp):,} author-paper rows, {len(p):,} panel rows", flush=True)
    cells = []
    for s in SCENARIOS:
        cells += [("R1_fixed_window", s, "main"), ("R1_fixed_window", s, "by_n_i"),
                  ("R2_monthly_first", s, "main"), ("R3_rolling", s, "main")]
    for s in ("S0_random", "S1_output_trend", "S4_low_baseline"):
        cells += [("R1_fixed_window", s, "no_exclusion"), ("R1_fixed_window", s, "no_volume_fe"),
                  ("R1_fixed_window", s, "post_without_2020H1")]
    rows = []
    for rule, s, spec in cells:
        for r in range(int(reps)):
            t0 = time.time()
            f = draw_flags(pp, z, s, rng)
            if rule == "R1_fixed_window":
                t = types_fixed_window(f)
                kw = {"main": {}, "by_n_i": {"by_ni": True}, "no_exclusion": {"exclusion": False},
                      "no_volume_fe": {"volume": False}, "post_without_2020H1": {"post_end": 2019 * 2 + 1}}[spec]
                res = fit_r1(p, t, **kw)
                res["share_W"], res["share_WI"] = t.W.mean(), t.WI.mean()
            elif rule == "R2_monthly_first":
                res = fit_r2(p, f)
            else:
                res = fit_r3(p, f)
            rows.append({"rule": rule, "scenario": s, "spec": spec, "rep": r, **res,
                         "seconds": round(time.time() - t0, 1)})
            print(rows[-1], flush=True)
        pd.DataFrame(rows).to_csv(out_csv, index=False)
    out = pd.DataFrame(rows)
    summary = []
    for (rule, s, spec), g in out.groupby(["rule", "scenario", "spec"], sort=False):
        rec = {"rule": rule, "scenario": s, "spec": spec, "runs": len(g)}
        for b in [c for c in g.columns if c.startswith("b_")]:
            se = b.replace("b_", "se_")
            if g[b].notna().any():
                rec[f"mean_{b}"] = g[b].mean()
                rec[f"mean_{se}"] = g[se].mean()
                rec[f"reject5_{b}"] = (abs(g[b] / g[se]) > 1.96).mean()
        summary.append(rec)
    s = pd.DataFrame(summary)
    s.to_csv(out_csv.replace(".csv", "_summary.csv"), index=False)
    print(s.round(4).to_string())


if __name__ == "__main__":
    main(*sys.argv[1:6])
