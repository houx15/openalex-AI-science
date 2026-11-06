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

## Later (not needed yet)

- arXiv requester-pays bucket (`s3://arxiv`): needs separate PI approval for the spending (SPEC §4), then a policy addition.
- Data transfer from S3 to Adroit: price it before moving anything.
