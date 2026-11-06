# Decisions log

PI decisions made during execution. Newest first.

| Date | Decision | Context |
|---|---|---|
| 2026-11-06 | Full-text acquisition: hybrid. Phase 1 pilot per paper from arxiv.org; full scoring takes single-version papers from bulk S3 tars on EC2 and fetches v1 of revised papers (~42%) per paper | PI. Bulk tars hold the latest version (tar check, `reports/phase0_funnel.md`) |
| 2026-11-06 | AWS access set up for full-text extraction: agent can read `s3://arxiv` (requester pays) and launch tagged EC2 instances in us-east-1 (5 CPU types, ≤500 GB disks) running as role `oaai-extract-ec2`. Agent policy is now the managed policy `oaai-phase0-agent`. Agent still asks before downloading any tar or launching any instance | PI asked for one complete policy (2026-11-06). Recommended plan: per-paper arxiv.org download for the Phase 1 pilot, bulk S3 → EC2 extraction for full scoring after the Phase 1 gate (`reports/phase0_funnel.md`) |
| 2026-11-06 | `authorship_long` keeps xpac works (flagged `is_xpac`): exposure linkage uses them, formal outputs and career age exclude them | Author-bridge audit: 2.6% of unpublished 2023–24 arXiv papers exist in OpenAlex only as xpac records; dropping xpac biased exposure sets toward published papers |
| 2026-11-06 | v1 dates and all window boundaries use UTC (arXiv records version dates in GMT) | Interpretation of SPEC §6 'by arXiv v1 date'; 3 of 452,916 2023–24 papers change window under US Eastern time |
| 2026-11-06 | arXiv metadata source for `arxiv_versions`: Kaggle snapshot `Cornell-University/arxiv` (dataset version 21506946, sha256 recorded alongside the file), with a later random-sample check against OAI-PMH `arXivRaw` once that endpoint works | oaipmh.arxiv.org timed out / returned 503 on all historical datestamps on 2026-11-06. Kaggle snapshot is arXiv's own bulk export of the same metadata with full version history; downloaded without credentials |
| 2026-11-06 | CTAS outputs live at the workgroup-enforced path `athena-results/tables/<query_id>/`, not `derived/<table>/run=<id>/`; the 30-day expiry on `athena-results/` was removed so they persist | The enforced workgroup config (which the agent cannot change) rejects `external_location`. Each run is still immutable: table name carries the run ID and the cost log carries the query ID |
| 2026-11-06 | Interpretation for PI review: `authorship_long` and career age use non-xpac works only; `works_core` keeps xpac rows with the flag | SPEC §7 excludes xpac from eligible papers; SPEC does not say whether xpac counts for first-publication year |
| 2026-11-05 | Spending authority: agent may spend up to $100 on AWS; still stops and asks at $80 per SPEC §4 | PI |
| 2026-11-05 | Repo is `openalex-AI-science`; spec stays at `docs/SPEC.md` (SPEC §12 layout otherwise followed) | Repo renamed |
| 2026-11-05 | Reports in English | PI preference |
| 2026-11-05 | Phase 0 runs on AWS; Adroit used only on request (limited scratch space) | PI |
| 2026-11-05 | AWS account 596131721388, IAM user `phase0-agent`, is dedicated to this project | PI |
