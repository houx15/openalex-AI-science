# Decisions log

PI decisions made during execution. Newest first.

| Date | Decision | Context |
|---|---|---|
| 2026-11-06 | CTAS outputs live at the workgroup-enforced path `athena-results/tables/<query_id>/`, not `derived/<table>/run=<id>/`; the 30-day expiry on `athena-results/` was removed so they persist | The enforced workgroup config (which the agent cannot change) rejects `external_location`. Each run is still immutable: table name carries the run ID and the cost log carries the query ID |
| 2026-11-06 | Interpretation for PI review: `authorship_long` and career age use non-xpac works only; `works_core` keeps xpac rows with the flag | SPEC §7 excludes xpac from eligible papers; SPEC does not say whether xpac counts for first-publication year |
| 2026-11-05 | Spending authority: agent may spend up to $100 on AWS; still stops and asks at $80 per SPEC §4 | PI |
| 2026-11-05 | Repo is `openalex-AI-science`; spec stays at `docs/SPEC.md` (SPEC §12 layout otherwise followed) | Repo renamed |
| 2026-11-05 | Reports in English | PI preference |
| 2026-11-05 | Phase 0 runs on AWS; Adroit used only on request (limited scratch space) | PI |
| 2026-11-05 | AWS account 596131721388, IAM user `phase0-agent`, is dedicated to this project | PI |
