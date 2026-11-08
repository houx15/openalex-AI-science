# Deviations from SPEC

Any change to a sample, threshold, model or rule relative to `docs/SPEC.md`. Newest first.

| Date | SPEC section | Deviation | Reason | PI approval |
|---|---|---|---|---|
| 2026-11-06 | §9 main count model (Phase 0 simulations only) | Period fixed effects are additive, field × half-year + career bin × half-year (+ exposure bin × half-year), instead of field × career bin × half-year. Fields with <500 sampled authors use their domain | With pyfixest 0.60.0 the PPML demeaning did not converge with the three-way interaction on 30k–50k-author samples (10,000–20,000 iterations), while the additive version converged in ~1 s. Simulation results (MDE, false positives) are not expected to depend on this. The three-way version must be re-tested with another PPML implementation (e.g. R `fixest` or `ppmlhdfe`) before the pre-analysis plan | Approved 2026-11-08 (re-test still required) |
