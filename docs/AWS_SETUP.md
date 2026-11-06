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

### 4. EC2 text extraction: role + agent permissions (added 2026-11-06)

For full-text extraction next to the arXiv bucket (`reports/phase0_funnel.md`, option A), the agent launches short-lived EC2 instances in us-east-1, and each instance runs as role `oaai-extract-ec2`. Launching costs money, and the agent still asks before each extraction run (SPEC §4).

Files:
- `config/aws/extract-ec2-role-trust.json`: only EC2 in this account can use the role.
- `config/aws/extract-ec2-role-policy.json`: the instance may read `s3://arxiv` and the project bucket, and write only `fulltext/` and `logs/extract/` in the project bucket.
- `config/aws/phase0-agent-policy.json`: adds EC2 for the agent. Its limits:
  - us-east-1 only;
  - instance types c7i.2xlarge, c7i.4xlarge, c7i.8xlarge, m7i.4xlarge or c6i.4xlarge;
  - instances and volumes must be tagged `Project=oaai`, volumes ≤500 GB;
  - the agent can stop or terminate only tagged instances;
  - it can pass only `oaai-extract-ec2` to EC2;
  - all other IAM actions stay denied, including any change to that role.

The agent policy is now about 4,600 characters, which may exceed the size limit for an inline user policy. So it becomes a customer-managed policy (6,144-character limit) attached to the user. Run as admin, from the repo root:

```bash
# role for the instances
aws iam create-role --role-name oaai-extract-ec2 \
  --assume-role-policy-document file://config/aws/extract-ec2-role-trust.json
aws iam put-role-policy --role-name oaai-extract-ec2 --policy-name oaai-extract \
  --policy-document file://config/aws/extract-ec2-role-policy.json
aws iam create-instance-profile --instance-profile-name oaai-extract-ec2
aws iam add-role-to-instance-profile --instance-profile-name oaai-extract-ec2 --role-name oaai-extract-ec2

# agent policy: managed policy replaces the inline one
aws iam create-policy --policy-name oaai-phase0-agent \
  --policy-document file://config/aws/phase0-agent-policy.json
aws iam attach-user-policy --user-name phase0-agent \
  --policy-arn arn:aws:iam::596131721388:policy/oaai-phase0-agent
aws iam delete-user-policy --user-name phase0-agent --policy-name oaai-phase0
```

Later edits to the agent policy:
```bash
aws iam create-policy-version --policy-arn arn:aws:iam::596131721388:policy/oaai-phase0-agent \
  --policy-document file://config/aws/phase0-agent-policy.json --set-as-default
```
A managed policy keeps at most 5 versions; delete old ones with `aws iam delete-policy-version` when needed.

Notes:
- The instances use the default VPC and no SSH key. The job runs from the launch script, and logs go to `logs/extract/`. The agent checks the default VPC exists with `ec2:DescribeVpcs`.
- On-demand only. Spot would need a service-linked role that the agent cannot create.
- Each instance shuts itself down (shutdown behavior = terminate) when the job ends, with a hard time limit in the launch script.
- Data transfer from S3 to Adroit: price it before moving anything.
