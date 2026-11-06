# Phase 0 simulations: power and false positives

SPEC §10 tasks 8–9. No real AI scores exist yet. Every author type below is simulated, so nothing here uses or reveals an outcome by signal (SPEC §1 firewall).
- The power simulation uses only 2018–2022 output.
- The false-positive simulation uses the −6-year pseudo-timeline (2012–2020 output).

Code:
- `src/analysis/sim_power.py`, `sim_power_ri.py`, `sim_power_check.py`, `sim_false_positive.py`, `fe_groups.py`.
- Inputs: `sql/sim_power_panel.sql`, `sim_power_authors.sql`, `sim_pseudo_authors.sql`, `sim_pseudo_counts.sql`.
- Seeds: 20261106 (simulation draws) and 20261105 (k = 3 paper selection).

Inputs:
- Eligibility rule v0 (`reports/phase0_funnel.md`). Under v1 the sample is 1.2% larger, which does not change these conclusions.
- Main sample (m = 1): 290,330 authors, 2.58M author × half-year rows, mean 2.9 eligible works per half-year.
- Pseudo-timeline sample: 154,993 authors, 489,594 author × 2017–18 arXiv-paper rows, 2.62M author × half-year rows.

Model: SPEC §9 PPML.
- Author fixed effects; period fixed effects; exposure-volume bin (1, 2, 3, 4–5, 6+ eligible exposure papers) × half-year, which absorbs `n_i` × period; clustered by author.
- **Deviation:** the period fixed effects are additive, field × half-year + career bin × half-year. The three-way field × career × half-year version did not converge in pyfixest 0.60.0 (`docs/DEVIATIONS.md`) and must be re-tested with another PPML implementation before the pre-analysis plan.

Simulated types:
- Each selected paper is writing-flagged with probability p_w, and idea-flagged with probability 0.20–0.30 if writing-flagged, 0.01–0.03 otherwise.
- An author has a signal when the flagged share of their k ≤ 3 papers is ≥ 0.5 (SPEC §8).

## 1. Power (task 8)

Pseudo design inside 2018–2022: pre = 2018H1–2020H2, 2021H1 left out (stands in for the excluded exposure window), post = 2021H2–2022H2 (three half-years, like 2025H1–2026H1).

Minimum detectable effect, 80% power, two-sided 5%, as a percent change in output. Mean over 3 draws per cell (`data/derived/sim/power_results_fits.csv`):

| Authors | Prevalence scenario (paper flag rate p_w) | W authors | WI authors | MDE W vs N | MDE WI vs W |
|---|---|---|---|---|---|
| 290,000 | low (0.05) | 10,093 | 2,438 | 2.8% | 6.4% |
| 290,000 | mid (0.15) | 31,157 | 9,474 | **1.6%** | **3.2%** |
| 290,000 | high (0.30) | 65,289 | 24,022 | 1.2% | 2.0% |
| 100,000 | low | 3,409 | 834 | 4.8% | 10.0% |
| 100,000 | mid | 10,873 | 3,292 | 2.7% | 5.5% |
| 100,000 | high | 22,354 | 8,257 | 2.0% | 3.5% |
| 30,000 | low | 1,040 | 246 | 9.0% | 21.7% |
| 30,000 | mid | 3,187 | 969 | 4.9% | 10.4% |
| 30,000 | high | 6,759 | 2,484 | 3.8% | 6.6% |
| 10,000 | low | 326 | 89 | 16.1% | 35.6% |
| 10,000 | mid | 1,107 | 342 | 9.1% | 17.1% |
| 10,000 | high | 2,217 | 826 | 6.8% | 11.7% |

**Checks.**
- *Randomization check* (`sim_power_ri.py`): 40 null draws on the full sample, mid scenario. The spread of the W vs N estimate across draws (SD 0.0061) matches the mean clustered SE (0.0058). The false-positive rate is 7.5%, or 3/40, consistent with 5%. For WI vs W: SD 0.0120 against SE 0.0114, false-positive rate 5%. Dropping the 1,511 hyper-prolific authors (mean > 30 eligible works per half-year) changes little.
- *Injected effect* (`sim_power_check.py`): with a true +1.7% W effect, 30 runs detect it 80% of the time, and the mean estimate is +1.9%. So the MDEs above are calibrated.

**Reading.** On sampling noise alone, the full sample detects effects of about 1–3% for W vs N and 2–6% for WI vs W. MDE scales roughly with 1/√authors. A random **100k-author subsample** still detects about 3% (W vs N) and 5–6% (WI vs W) at mid prevalence, and needs about 35% of the scoring, roughly 95k papers instead of 272k. Below 30k authors, WI vs W becomes weak at low prevalence. These MDEs are **far smaller than the confounding biases in §2**, so sample size is not the binding constraint. Identification is.

## 2. False positives on the −6-year pseudo-timeline (task 9)

Pre = 2012H1–2016H2, pseudo exposure = arXiv v1 in 2017–18 (left out of the fixed-window model), post = 2019H1–2020H1. The pseudo-outcome excludes families with v1 in 2017–18. AI has **no** effect by construction.

Detection scenarios: writing-flag probability 0.15, shifted by 0.5 logit per SD of an author trait.
- **S0:** nothing, random detection.
- **S1:** pre-period output growth.
- **S2:** youth.
- **S3:** arXiv intensity.
- **S4:** low 2012–15 baseline output, the mean-reversion channel.

10 runs per cell (`data/derived/sim/fp_results_summary.csv`). Each cell shows the mean spurious W effect (log points), with the share of runs significant at 5% in brackets:

| Rule | S0 random | S1 output trend | S2 young | S3 arXiv intensity | S4 low baseline |
|---|---|---|---|---|---|
| R1 fixed window, k = 3 (main) | −0.002 (0/10) | **+0.077 (10/10)** | +0.007 (0/10) | +0.007 (1/10) | **+0.103 (10/10)** |
| R2 monthly first detection | **+0.029 (10/10)** | +0.092 (10/10) | +0.039 (10/10) | +0.034 (10/10) | +0.105 (10/10) |
| R3 rolling lagged exposure | 0.000 (0/10) | +0.087 (10/10) | +0.006 (1/10) | +0.008 (1/10) | +0.094 (10/10) |

- WI vs W stays near zero in every scenario, between −0.003 and +0.002, rejected in at most 2/10 runs. All scenarios shift writing and idea propensity together.
- **By `n_i` (R1):**

  | | `n_i` = 1 | `n_i` = 2 | `n_i` = 3 |
  |---|---|---|---|
  | S0 random | −0.004 | −0.001 | −0.006 |
  | S1 output trend | +0.069 | +0.068 | +0.110 |
  | S4 low baseline | +0.094 | +0.099 | +0.128 |

  The n_i = 3 stratum is slightly more exposed to confounding.
- **Exposure-window exclusion:** turning it off barely moves S0 (+0.000). Under S1/S4 the bias is +0.091 and +0.094 with or without it. As a guard against mechanical overlap it costs nothing.
- **Exposure-volume control is needed:** without the exposure-bin × period fixed effects, S0 shows a spurious **−0.015 (4/10 significant)**. The share rule ties W to `n_i`: W is easiest to reach with 2 papers and hardest with 3.
- **Dropping 2020H1 from the outcome window:** no material change (S0 +0.004).

**Pre-period controls** (R1, 10 runs each; `data/derived/sim/fp_controls_summary.csv`). Bins are built only from pre-period output: baseline-output quintile (2012–15) and pre-growth tercile (2015–16 vs 2012–13), each interacted with half-year:

| Scenario | Main R1 | + baseline quintile × half | + baseline quintile and pre-growth tercile × half |
|---|---|---|---|
| S0 random | −0.002 (0/10) | −0.002 (0/10) | −0.003 (0/10) |
| S1 output trend | +0.077 (10/10) | +0.075 (10/10) | **+0.026 (9/10)** |
| S4 low baseline | +0.103 (10/10) | **+0.017 (6/10)** | +0.018 (7/10) |

- The baseline-output control removes about 85% of the mean-reversion bias.
- The pre-growth control removes about two-thirds of the trend bias.
- Neither costs precision (SE 0.0084–0.0088 against 0.0090) or creates bias under random detection.
- A residual of about 0.02–0.03 remains under strong confounding (0.5 logit per SD). That is roughly the size of the full-sample MDE, so it would still read as significant.
- WI vs W stays near zero throughout.

## What this means for the design

1. **Keep the fixed-window share rule (R1) as the main design**, as SPEC proposes. It is unbiased under random detection and under youth- or arXiv-linked detection, as long as exposure volume × period is controlled.
2. **Drop monthly first detection** as anything but a labelled comparison. It shows a spurious +3% even when detection is pure chance, because detection months coincide with posting, and posting with output. This confirms SPEC §3.
3. **The real threat is detection that tracks output trajectories.** If authors who get flagged were already rising, or are coming off a low baseline (mean reversion), all three rules show spurious effects of +8–10%, about 5× the MDE. Author and period fixed effects do not remove this.
   - **Proposed for the main model** [PROPOSED]: add baseline-output quintile × period and pre-growth tercile × period fixed effects. They cut the spurious effect to about 2–3%, at no precision cost.
   - Rely on event-study pre-trends (SPEC §9) for the remainder.
   - The Phase 1 score placebo measures the real version of this risk: whether real 2017–18 scores predict 2019–20 growth.
   - The **WI vs W contrast is robust** in every scenario tried, because confounders that shift writing and idea detection together cancel. It is the better-identified of the two primary contrasts.
4. **Sample size:** a scoring budget of about 100k randomly chosen authors keeps MDEs at about 3% (W vs N) and 5–6% (WI vs W), well under the confounding magnitudes. Scoring all 290k buys precision the design cannot use unless confounding is ruled out first.
