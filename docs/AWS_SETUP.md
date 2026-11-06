# AWS setup (Phase 0)

Account `596131721388`, region `us-east-1`. The agent works as IAM user `phase0-agent`.

## Steps for the PI (admin credentials, one time)

On 2026-11-05, `phase0-agent` could read the public OpenAlex bucket and nothing else: no Athena, no writes to its own S3 bucket, and no budget view. Two steps fix that.

### 1. Attach the agent policy

Policy file: `config/aws/phase0-agent-policy.json`. It allows:

- Reading `s3://openalex` (public snapshot).
- Creating and using a single work bucket, `oaai-phase0-596131721388`, for Athena results and derived subsets.
- Running Athena only in the `oaai-phase0` workgroup, plus Glue tables in `openalex_*` databases.
- Viewing budgets and Cost Explorer, read-only.
- **Denied explicitly:** changing or deleting the workgroup (which holds the per-query scan limit), editing budgets, deleting the bucket, changing bucket policy, and any IAM action. The agent cannot loosen its own limits.

Console: IAM → Users → `phase0-agent` → Add permissions → Create inline policy → JSON → paste the file → name it `oaai-phase0`.

Or with the CLI, as an admin:

```bash
aws iam put-user-policy --user-name phase0-agent --policy-name oaai-phase0 \
  --policy-document file://config/aws/phase0-agent-policy.json
```

### 2. Create the budget alerts ($50 and $80 of $100)

The PI creates these so the agent cannot edit them. Console: Billing → Budgets → Create budget → Cost budget, monthly, $100. Add email alerts on **actual** cost at 50% and 80%, and one on **forecasted** cost at 100%.

Budgets lag by hours and are not a hard stop. The real controls are the workgroup's per-query scan limit (set when the agent creates the workgroup, which it cannot change afterwards) and the agent's own rule to stop at $80 (SPEC §4).

### 3. arXiv requester-pays bucket (updated 2026-11-06)

Statement `ReadArxivRequesterPaysBucket` lets the agent read anything in `s3://arxiv`. The PI chose one complete policy over step-by-step additions. The cost risk is the requester-pays charge: each tar is about 0.5 GB, so about $0.05 when read from outside AWS. The agent still downloads tars only with PI approval for each batch (SPEC §4 rule on arXiv full text), and logs each read in `reports/cost_log.csv`. Re-run step 1 to apply.

## Later (not needed yet)

- EC2 in us-east-1 for bulk text extraction (Phase 2). An instance needs an IAM role to read S3. The agent cannot create roles or pass them (`iam:*` is denied), so the PI creates one role and the agent gets `iam:PassRole` on that role only, plus EC2 limited to tagged instances. This is drafted when scoring is approved.
- Data transfer from S3 to Adroit: price it before moving anything.
