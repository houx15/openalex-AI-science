# SPEC: How AI Moves from Writing into Ideas, and What Changes in Scientific Output

**Audience:** coding agent executing this project on behalf of the principal investigator (PI), Yuxin Hou.
**Spec date:** 2026-11-05
**Design document:** https://claude.ai/artifact/C1a4Wn2zAndNNrw5gk27zR (human-readable design, in Chinese). If this spec and the design document conflict, stop and ask the PI.

Status labels used below:

- **[DECIDED]** The PI has made this decision. Do not change it without approval.
- **[PROPOSED]** Default to use unless evidence suggests otherwise. Report the evidence and ask before changing it.
- **[VERIFY]** A fact or implementation detail that has not been checked. Check it before relying on it.

Naming note: **V1** (capital) is the within-author value analysis. **v1** (lowercase) is the first version of an arXiv paper.

---

## 1. How to work

1. Read this whole spec before running anything.
2. Execute one phase at a time. **Stop at every gate** (Section 11) and wait for PI approval.
3. **Outcome firewall.** Until the PI clears the "Before Phase 3" gate, do not compute or view any count or citation dated 2022 or later (including V1 outcomes) by score, flag or type, and no earlier outcome by score except the Phase 1 placebo. Aggregate 2025–2026 counts for completeness checks may not be joined to any score table.
4. Do not change a sample, threshold or model because of its results. Log any deviation in `docs/DEVIATIONS.md`.
5. Report what was done, what was found, what failed and what remains unverified. Do not describe an association as a causal effect.
6. Stop and ask when: a budget limit is near, a gate fails, a license is unclear, a required field is missing, or text would need to leave Princeton-controlled systems.

---

## 2. Research question and argument

**Core question:** As text signals resembling AI expand from writing to ideas, do later paper counts and citations differ?

Most prior work asks whether authors whose writing shows LLM signals publish more. This project focuses on the next step on the gradient: writing only versus writing plus ideas. The contribution should come from the idea dimension and from separating quantity from citation-based value. The writing-only result is a benchmark against Kusumegi et al. (Science, 2025), not the headline.

### Analyses

| Label | Question | Role |
|---|---|---|
| **H2a** | Do writing-only (W) authors change output relative to authors with neither signal (N)? | Benchmark |
| **H2b** | Do authors with writing and idea signals change output relative to writing-only authors? | **Core result** |
| **V1** | Within an author, do papers with idea signals receive different citations? | Value analysis; conditional association |
| **H1** | Conditional on pre-2023 characteristics, do early writing-signal authors (first flagged paper in 2023) show idea signals sooner? Code timing is reported in Phase 4. | Conditional association; not causal |
| **AI** | Do the same comparisons hold among pre-2023 AI researchers? | Separate analysis |
| **NE** | How do new entrants differ by cohort and signal type? | Descriptive |
| **CX** | How does code use fit the gradient after 2025? | Extension; preliminary output evidence only |

Do not assume that paper counts and citations move in the same direction. A rise in quantity with no rise in citations may be substantive, but mean citations per paper can fall mechanically when marginal papers are added. Citation outcomes are not direct measures of value.

### Allowed conclusions

Allowed: "Under the parallel-trends assumption, these groups show different changes relative to baseline." Also state that groups are defined after the baseline by signals in their own output, and that parallel trends is especially doubtful for WI vs W, because idea-signal authors may self-select into different projects and trajectories.

Scope: signals come from arXiv first versions, and the sample is limited to authors who posted on arXiv in 2023–2024. Results apply to those authors and to what they posted. Do not describe them as all of science, or as a measure of an author's unposted or final published text.

Not allowed without new evidence: "AI caused," "AI-generated ideas caused," or "the effect of starting to use AI." A detector score shows that text resembles AI writing or AI ideas. It does not prove who used AI, or how.

---

## 3. Decisions already made

| Topic | Decision | Status |
|---|---|---|
| Data roles | arXiv first-version (v1) full text measures signals. OpenAlex public snapshot, October 2026 release, provides author IDs, the baseline rule, paper counts, publication timing and citations | [DECIDED; final after the Phase 0 gate] |
| Disciplines | Multi-disciplinary within arXiv's coverage; not limited to computer science. Stop at the Phase 0 gate if the eligible non-AI sample is concentrated in one or two fields | [DECIDED] |
| Publications | Journal and conference papers; no books | [DECIDED] |
| Authors | All authors in main analysis; first/last authors in robustness checks | [DECIDED] |
| Baseline sample | At least 4 eligible papers in 2018–2021 | [DECIDED; PI wants the strictness checked in the funnel] |
| Exposure | Fixed 2023–2024 window by arXiv v1 date; no individual adoption date | [DECIDED] |
| Outcome overlap | Papers with arXiv v1 in the exposure window are excluded from main outcomes, whatever their score; including them is a robustness check | [DECIDED] |
| Main dimensions | Writing and ideas; three dimensions are not required | [DECIDED] |
| Code | Extension from 2025 onward | [DECIDED] |
| Text | Main analysis uses arXiv v1 full text only. Do not mix text sources in the main measure. Other sources may be used only for validation or the approved fallback | [DECIDED] |
| Signal definition | Thresholds calibrated on pre-2023 papers; test multiple thresholds | [DECIDED] |
| AI researchers | Exclude from main analysis at author level; analyze separately | [DECIDED] |
| Main outcomes | Formal paper count and citations from OpenAlex | [DECIDED] |
| Leading indicator | arXiv v1 submissions per author-half-year; secondary outcome, not a measure of formal output | [DECIDED] |
| Value proxy | Citation-based outcomes only for now | [DECIDED] |
| AWS spend | At most **$100** for Athena and subset storage | [DECIDED] |
| Outline extraction | Default to local GPU; test against Gemini on a small sample | [PROPOSED; external use needs approval] |

Rejected as the main design: monthly first-detection timing, because detected months are mechanically linked to high-output months (see Renault et al.). It remains a comparison analysis.

---

## 4. Environment and constraints

### Princeton Adroit

- Code lives in `~`; project data lives under `/scratch/network/yh6580/`.
- Slurm manages jobs. **Compute nodes are offline.** Cache models and data from an internet-connected node before submitting compute jobs.
- GPU: A100 with 80 GB memory. Check current queue limits with cluster tools. Published guidance lists `gpu-long` at 2 days and up to 2 GPUs per user [VERIFY].
- Scratch is shared storage of about 24 TB. Run `checkquota` before downloads. Do not treat scratch as long-term backup.
- Existing OpenAlex data on the server cover only 2023-04 to 2025-03. **Do not mix it with the new release.** Author IDs and fields can differ across releases.

### Budget

| Item | Limit | Rule |
|---|---|---|
| AWS Athena and S3 subset | $100 total | Set budget alerts at $50 and $80, plus an Athena per-query scan limit, because alerts lag and are not a hard stop. Log estimated and actual cost per query. Check transfer cost from S3 to Adroit [VERIFY]. Stop at $80 and ask |
| OpenAlex PDF or TEI download | Not needed for the main design. Not yet approved beyond free allowance | Use only for a PI-approved version comparison or the fallback. The free allowance covers about 100 files per day |
| External LLM calls | Not yet approved | Use only after PI approval |
| arXiv full text | Not yet approved | Separate from the $100 limit. Phase 0 estimates S3 data transfer, any `us-east-1` EC2 filtering, storage and per-paper access. Get PI approval before any paid download |

### Data and license rules

- OpenAlex metadata are CC0. Follow arXiv's API and bulk-data terms, including rate limits.
- Do not redistribute full text. Most arXiv papers cannot be redistributed under the default arXiv license. Keep full text out of git.
- `idealens` code is CC BY-NC-SA 4.0. Check each model's own license, including ProseLens, on its model card [VERIFY].
- Do not send full text to external providers until the PI confirms data-use requirements.
- Use a file permission and secret-management approach that keeps API keys out of git and logs.

### Reproducibility

- Pin package versions. Start with `idealens==0.1.7` unless PI approves an upgrade. Note that its vLLM extra pins `vllm==0.21.*`, `transformers>=5.15`, and `xgrammar==0.2.1`; check Adroit compatibility [VERIFY].
- Use fixed random seeds and save them with each output.
- Save the OpenAlex `manifest.json`, release date, query text, row counts and code commit for every derived dataset.
- Use immutable output directories named with a run ID.

---

## 5. Data sources

| Source | Use | Notes |
|---|---|---|
| OpenAlex snapshot, Parquet | Authors, baseline rule, works, formal publication dates, citations, arXiv links in work records | `s3://openalex/data/parquet/`; anonymous S3 access; partitioned by `updated_date`, so publication year cannot be filtered by partition |
| arXiv metadata | arXiv IDs, v1 dates, primary categories, DOI and journal references | Use a source with full version history, such as OAI-PMH `arXivRaw` [VERIFY] |
| arXiv S3 or per-paper access | v1 LaTeX source and PDF | Main signal text. S3 is requester pays. Confirm that S3 tars contain v1, not only later versions [VERIFY]. If they do not, price rate-limited retrieval of `arxiv.org/pdf/<id>v1` and the source equivalent |
| OpenAlex content API | Published-version text | Validation or fallback only; $0.01 per file; `$1/day` free allowance covers about 100 files |
| rs-graph-v1 | Paper-repository and author-developer links | Code extension; Dataverse access may need a request |
| Papers with Code archive | Paper-repository links | Code extension; static after July 2025 |
| GitHub or World of Code | Repository history | Code extension |
| AI disclosure statements (ICLR/EMNLP) | External validation | https://ai-disclosure.github.io/ |
| ORCID in OpenAlex, DBLP | Author-record checks | DBLP is for computer-science checks |

Use `RELEASE_NOTES.txt` and the manifest to confirm that the selected snapshot is the October 2026 public release [VERIFY].

---

## 6. Time windows

Use half-year periods.

| Period | Dates | Use |
|---|---|---|
| Pre-history | Before 2018 | Career age. 2012–2017 also supports the pseudo-timeline in Phase 0 and Phase 1 only |
| Baseline for sample | 2018-01 to 2021-12 | At least 4 eligible works |
| Baseline for DiD | 2018H1 to 2022H2 | Pre-trends; omit 2022H2 as the reference period |
| Exposure | 2023-01-01 to 2024-12-31 by arXiv v1 date | Define signal types only; exclude 2023–2024 periods from main DiD estimation |
| Main count outcome | 2025H1 to 2026H1 by formal publication date, excluding papers with exposure-window v1 | Paper-count DiD |
| Leading indicator | 2018H1 to 2022H2 and 2025H1 to 2026H1 by arXiv v1 date | Secondary submission DiD |
| Citation cohorts | Pre: 2018–2021 publications; reference 2021; 2022 excluded. Post: 2025 publications, excluding papers with exposure-window v1 | 2026 publications lack a usable citation window |
| Code extension | 2025 onward | Preliminary output only |

Exposure eligibility uses arXiv v1 date alone. A paper with v1 in 2023–2024 can be an exposure paper even if it is published in 2025 or later or never formally published. Do not condition exposure on later publication.

arXiv policy changes fall inside the outcome window: stricter computer-science review and position-paper rules (announced 2025-10-31), stricter endorsement (2026-01-21) and a full-English requirement (effective 2026-02-11 per the source reviewed; arXiv's blog excerpt showed an inconsistent date, so [VERIFY]). They mainly threaten the leading indicator. Run it with review or position-like papers removed, and with a window ending before 2025-10-31.

Check whether 2026H1 is complete enough before using it [VERIFY]. Phase 0 proposes a numeric rule, such as a field-level ratio against prior-year counts at the same indexing age. If it fails, propose a shorter window at the Phase 0 gate. Do not use 2026H2. Also check January-1 date heaping and its effect on half-year assignment.

---

## 7. Sample

### Eligible papers [VERIFY field names and values]

Include works that meet all of these:

- `is_xpac` is false.
- Publication date is present and within the relevant window.
- Primary source is a journal or conference.
- Work type is a research article, including conference papers. Exclude reviews from the primary sample unless the Phase 0 report shows this creates a problem.
- Not paratext, editorial, letter, erratum or retraction notice.
- Not retracted.

Important checks:

- Determine how conference papers appear in the current OpenAlex schema. Kusumegi et al. found that a meaningful share of Springer "book chapters" were conference papers. Sample and report any misclassification.
- Ensure preprints are not counted as formal output. Check how preprint and published versions are merged.
- Build a paper-family crosswalk linking each arXiv ID to its OpenAlex record or records, using arXiv IDs and DOIs first, then a conservative title, author and date match. Audit a random sample and report precision [PROPOSED target: at least 0.95]. A family counts once and its citations are summed with duplicate citing works removed.
- Check extremely large-author papers. Default rule: exclude works with more than 50 authors from exposure scoring only. They still count toward output and the baseline rule. Report the effect on sample size [PROPOSED].
- Audit author-ID splits and merges, which directly affect counts.

### Main analytic authors

An author enters the main sample if all of these hold:

1. At least 4 eligible works in 2018–2021.
2. At least 1 eligible arXiv paper with v1 in 2023–2024 and usable v1 text, matched to the author's OpenAlex record.
3. Not classified as a pre-2023 AI researcher.
4. Valid OpenAlex author ID.

Rule 1 uses OpenAlex formal publications and does not require any arXiv paper before 2023. An eligible arXiv paper is English, has 50 or fewer authors for scoring, and is a research paper rather than a review, position paper, or note [VERIFY how to identify these using arXiv metadata, OpenAlex type and a validated title rule].

Never condition on publishing in 2025–2026. Author-periods with no paper have zero output. Do not require publication in every period. Zero-fill from the author's first publication half-year onward; a fully balanced panel is robustness only, because zeros before a first paper are structural.

The sample conditions on posting to arXiv in the exposure window, a post-2022 event that signal use could affect. The ≥4 rule in 2018–2021 and the exposure rule can also create mean reversion around 2022H2. Report these limits and run robustness with fixed effects by 2023–2024 output bin × period.

Report funnel counts for minimum eligible arXiv v1 paper thresholds `m` = 1, 2 and 3. The main threshold remains `m` = 1 unless the PI changes it.

### Defining AI researchers [PROPOSED]

Use only works published before 2023:

- Build a transparent list of AI-related OpenAlex topics or subfields.
- Classify an author as an AI researcher if at least 50% of eligible 2018–2022 works fall in that list.
- Report 25% and 75% alternatives.
- Do not use post-2022 papers to classify authors. Keep all papers from non-AI authors who later move into AI, then test removal of their post-2022 AI papers as robustness and report topic shifts as a descriptive correlate.

### Author covariates

- **Field (fixed):** modal OpenAlex field in 2018–2022 eligible works. Use domain when a field is too small. Also store the author's modal arXiv primary category for exposure papers.
- **arXiv coverage:** share of the author's 2023–2024 paper families with an eligible v1, and whether the author posted to arXiv before 2023.
- **Career age (time-varying):** years since first OpenAlex publication. Default bins are 0–5, 6–10, 11–20 and 21+ [PROPOSED].
- **Baseline output and citations:** 2018–2021.
- **Team size:** mean baseline authors per paper.
- **Country or language group:** institution-based proxy where available. Report missingness. Do not infer race, ethnicity or gender from names without PI approval.

### Author-record quality

- Flag authors with ORCID.
- Flag initials-only display names where available.
- Compare main descriptive statistics for ORCID authors and all authors.
- In computer science, compare a sample with DBLP.

---

## 8. Measurement

### Text

- Main text: cleaned full text of the arXiv v1 of each selected paper.
- Remove references and other boilerplate. Decide the handling of long documents using `idealens` documentation and a pilot. Save the exact rule [VERIFY].
- Use English papers for the main analysis unless validation supports including others. Specify the language-detection method.
- Use one fixed parsing pipeline: v1 LaTeX source when usable, otherwise v1 PDF [PROPOSED]. Record the arXiv ID, version, input type and parser for each paper. Report parsing and text-acquisition failures by field and year. Never replace v1 with a later version in the main measure.
- Set `format` to `Academic Writing` for scholarly papers, so the method does not misclassify them. Confirm this is supported [VERIFY].

### Writing signal

Use `ProseLens` on the full text. Compare with `Pangram` only if the PI approves external use. Compute a transparent vocabulary-based measure as a low-cost cross-check [PROPOSED].

### Idea signal

Use the `idealens` pipeline:

1. Assign or confirm format.
2. Extract an outline.
3. Score with an outline model.

Known limits from the authors of IdeaLens: no large academic ground truth, stochastic extraction, weaker results on some newer generators, and a tendency to score unspecific or unverifiable ideas as more AI-like. Treat the signal as "resembles AI-generated ideas," not proven provenance.

Run the default local extractor first. Published thresholds were fitted on Gemini 3.7 Flash outlines, so **local extraction requires new calibration**.

### Calibration

- Use arXiv papers with v1 dated 2019-01 to 2022-10, scored on v1 with the same parser. Do not use these for author exposure or the placebo.
- Default groups: major arXiv primary-category groups, merging small groups at the Phase 0 gate because OpenAlex domains may be sparse in this sample [PROPOSED]. Field-level cuts need explicit additional budget.
- Use at least 2,500 fit papers and at least 2,500 held-out papers per group, or 5,000 papers per group. A 1% cut then has at least 25 expected fit cases. Even so, the 95% interval on a 1% rate at n = 2,500 is roughly 0.6%–1.4%.
- A group is reportable when it has at least 2,500 held-out papers.
- Fit cuts separately for ProseLens and IdeaLens at nominal false-positive rates of 1% and 5%. Report 0.5% only where fit n is at least 5,000.
- Main cut: 1% [PROPOSED].

### Author types

Select up to `k = 3` eligible arXiv v1 papers per author from 2023–2024 using a fixed random seed. Let `n_i` be the number selected (1, 2 or 3). Score each unique paper once, except in the extraction-stability test. Save the extraction seed.

- `writing_share_i` = share of selected papers flagged by ProseLens.
- `idea_share_i` = share of selected papers flagged by IdeaLens.
- Main rule: an author has a signal when the relevant share is at least 0.5 [PROPOSED]. This rule is mechanically tied to `n_i`, so all type models include `n_i` × period fixed effects and all reports show type prevalence by `n_i`. Alternatives: at least one paper, at least 2/3 (exact fraction), and all selected papers.

| Type | Writing signal | Idea signal |
|---|---|---|
| N | No | No |
| W | Yes | No |
| WI | Yes | Yes |
| I | No | Yes; exploratory only |

Main contrasts: W vs N, and WI vs W.

Robustness:

- Threshold grid.
- Continuous scores with appropriate transformations.
- Binned dose-response plots.
- Drop gray-zone authors, defined as any selected paper within a pre-specified score band around the cut.
- `n_i` = 3 authors only.
- Authors above a pre-specified arXiv coverage share.
- Authors who posted to arXiv before 2023.

### Timing and publication lag

Exposure uses arXiv v1 date. Formal outcomes use publication date. For the leading indicator, use v1 date. For a timing robustness check on formal papers, use the earliest available date: arXiv v1, then received or submitted date, then publication date. Report the date source. Report the v1-to-publication lag by field and year, and treat recent formal publication as right-censored.

Run conference papers as a separate robustness sample because their deadlines give a clearer timing signal.

### Outcomes

Compute formal counts over **all** eligible publications in OpenAlex, including papers never posted to arXiv.

**Avoiding mechanical overlap.** In the main outcome window and the post citation cohort, exclude every paper family with arXiv v1 in 2023–2024. Apply this by date to all of them, not only scored papers. This removes papers that could mechanically link exposure to later output. It also removes more output from heavy arXiv users, so main models include an exposure-volume control, the Phase 0 simulation tests the rule, and a robustness check adds these papers back.

**Quantity:**

- Whole count of formal publications per author-half-year; primary.
- Fractional count (1 / number of authors).
- First-or-last-author count.
- arXiv v1 submissions per author-half-year; secondary leading indicator. Compare it with the formal count, because a rise in submissions alone may reflect a change in posting rather than output.

**Citations:**

- Build citations from dated citing works: `referenced_works` joined to the citing work's publication date. Check scan cost first [VERIFY]. `counts_by_year` is a cross-check only, because annual counts cannot be cut at a month. Sum across each paper family and remove duplicate citing works. Report how the preprint-to-formal citation split changes over time.
- Window: for every cohort, count citations through September 30 of year y+1, or the last complete month set at Phase 0 given the October 2026 snapshot.
- Normalize within field × publication half-year × document class.
- Primary citation outcome: sum of normalized citations per author-year, zeros retained, PPML.
- Secondary: count of top-10% papers within the same normalization cell, zeros retained.
- Mean per paper and top-10% share exist only for authors with papers. Label them conditional and descriptive.
- Indexing backfill differs between old and recent cohorts. Report this limit. If citing dates are unusable, treat the citation DiD as descriptive and ask the PI.
- Do not use all-time citations or `fwci` as the main comparison across periods.

---

## 9. Empirical design

### Main count model

Estimate on 2018H1–2022H2 and 2025H1–2026H1, excluding 2023–2024:

```text
E[Y_it] = exp(alpha_i + lambda_{field(i), careerbin(i,t), t} + sum_k beta_k * Type_ik * Post_t)
```

- `Y_it`: papers for author `i` in half-year `t`.
- `Post_t`: 2025H1 onward.
- Estimator: Poisson pseudo-maximum likelihood with high-dimensional fixed effects.
- Reference type is N. WI vs W = β_WI − β_W, tested by the delta method. Type I stays in the sample with its own coefficient and is not interpreted. Include `n_i` × period fixed effects and fixed effects for bins of the number of eligible exposure-window arXiv papers × period [PROPOSED].
- Report relative changes as percent changes in the exponentiated ratio.
- Primary contrasts: W vs N and WI vs W.

Also estimate the event-study version, relative to 2022H2. Fit any version with 2023–2024 separately, so those periods cannot alter the main model, and label those coefficients descriptive.

Use a joint test on pre-period coefficients and sensitivity analysis for departures from parallel trends. Passing a pre-trend test does not prove parallel trends.

### Standard errors [PROPOSED]

Primary: cluster by author. Coauthors share papers, and clustering by field is weak with few fields and field × time effects absorbed. Assess a co-authorship dependence approach, such as collaboration-community clusters. Name the PPML package, run a scale test, and finalize this in the pre-analysis plan.

### Citation models

**Author panel:** estimate the same structure at the author-year level on the 2018–2021 and 2025 cohorts, with 2021 as reference, using the primary and secondary citation outcomes in Section 8.

**V1, within-author paper model:** use scored 2023–2024 arXiv papers. Set cohort by v1 date, and start the citation window from v1. `Citations_pa` is normalized citations under the Section 8 window length:

```text
Citations_pa = alpha_a + gamma_{field,year} + delta_1 Idea_p + delta_2 Writing_p + delta_3 TeamSize_p + error
```

Use authors with at least two scored papers. Cluster by author and paper. Interpret as a conditional association, since authors may use AI on different kinds of projects.

### H1

Use a discrete-time hazard model with half-year or yearly bins. Outcome in Phase 3: first visible idea signal. Code timing belongs to Phase 4. Condition on pre-2023 characteristics using propensity score stratification or matching. State that signal timing is not a measure of first use. Model opportunities by scored papers or repositories. Score H1 follow-up papers only for the H1 sample, with a per-author cap.

### Selection and arXiv checks

For inclusion into scored samples, report by baseline characteristics and field:

- Whether an author published in 2023–2024.
- Whether an author posted an eligible arXiv paper in 2023–2024.
- Whether an author posted to arXiv before 2023.

Then:

- Compare authors with and without eligible arXiv papers at baseline, including 2018–2022 output and citation trends.
- Compare arXiv coverage share across signal types, only after the "Before Phase 3" gate.
- Fit inverse-probability weights using only baseline variables.
- Provide a bounding or sensitivity analysis.
- Report match rates by field and year, and compare matched and unmatched arXiv papers.
- Compare abstract-only writing results across a broader sample if abstracts are sufficiently available.

An optional external-validity check uses a random sample of OpenAlex full text in non-arXiv fields. It needs PI approval and stays outside the main measure.

### Required robustness checks

Author roles:

- Signals assigned only from papers where the author is first or last.
- Output limited to first-or-last-author papers.
- Fractional counting.
- Small-team fields.
- Lead writers where contribution statements exist.

Design and sample:

- Monthly first-detection timing on the same sample.
- Rolling lagged writing exposure or annual cohorts.
- Conference-only sample.
- Matched sample.
- Baseline threshold alternatives.
- Any analysis here that needs extra scoring proceeds only if the Phase 0 scoring table lists it and the PI approves it.
- Exclusion of post-2022 AI papers among non-AI authors.
- Outcomes that add back papers with exposure-window v1.
- Restriction to authors who posted to arXiv before 2023, and to authors above the coverage cut.
- Leading indicator without review or position-like papers, and with a window ending before 2025-10-31.
- ORCID-only authors.

### Heterogeneity [PROPOSED]

Predefine these dimensions only: OpenAlex domain, baseline career age, baseline output and institution-based English-language group. Report missingness. Other subgroup analyses are exploratory.

### Multiple comparisons

Define two primary outcomes (paper count and summed normalized citations) and two primary contrasts. Pre-specify the adjustment method for them. Secondary and exploratory analyses must be labeled as such.

---

## 10. Phases

### Phase 0: Data subset and sample funnel

**Goal:** determine who can enter the study, and whether arXiv text plus OpenAlex outcomes is viable across fields, without looking at outcomes by AI signal.

Tasks:

1. **AWS setup.** Use region `us-east-1`. Set budget alerts and an Athena workgroup scan limit. Before each large query, estimate scanned bytes.
2. **Schema check.** Inspect Parquet structure from a small sample, especially `authorships`, `primary_location`, `counts_by_year`, `locations`, `ids`, `has_content`, `open_access`, `type`, `topics`, `is_xpac`.
3. **Create subsets.** Prefer Athena. If Athena cannot access the public bucket, try DuckDB remote reading on an online node. Do not download the full snapshot.
4. Create:
   - `works_core`: eligible-field columns, 2012 onward. 2012–2017 is for the pseudo-timeline only. Omit abstracts at first.
   - `authorship_long`: work, author, author position, institutions, country.
   - `arxiv_versions`: arXiv ID, version dates, primary and cross-list categories, DOI and journal reference.
   - `paper_family`: arXiv-to-OpenAlex crosswalk, match method and match quality.
   - `author_first_year`: first publication year per author across all years.
   - `sources`, `topics`: lookups needed for classification.
5. **Quality checks.** Reconcile rows with manifests, by year and domain. Check conference classification, preprint handling, 2026 completeness, abstract coverage, arXiv indexing delay in OpenAlex, availability of v1 source and PDF, and `has_content` coverage for fallback sizing.
6. **Funnel.** Report counts of authors and papers, by domain, field and career age:
   - All authors with eligible works.
   - At least 4 eligible works in 2018–2021.
   - Not AI researcher.
   - Eligible work in 2023–2024.
   - Eligible arXiv v1 in 2023–2024, for `m` = 1, 2 and 3.
   - Share of these authors' 2023–2024 paper families with an eligible v1.
   - Papers needed for scoring under k = 3.
   - Authors meeting the same rule through OpenAlex `has_content` works, plus overlap with the arXiv sample, for fallback comparison only.
   - Code-extension links and repository coverage, reported separately.
   - Results using lower baseline thresholds of 2 and 3, for comparison only.
7. **Check strictness and coverage.** Say whether "at least 4" is too strict for formal publications. Report arXiv-to-OpenAlex match rate, and median and interquartile v1-to-publication lag, by field and year. Say which fields have enough eligible non-AI authors.
8. **Power simulation.** Use 2018–2022 distributions of author output, no later outcome data, and the same sample conditions. Report minimum detectable differences for W vs N and WI vs W under plausible signal prevalence and author counts. Rerun at the Phase 1 gate with pilot prevalence.
9. **False-positive simulation.** Use the −6-year pseudo-timeline: sample ≥4 eligible works in 2012–2015; pre-period 2012H1–2016H2; pseudo-exposure by arXiv v1 in 2017–2018; pseudo-outcome 2019H1–2020H1, reported with and without 2020H1. No real scores are used. Assume AI has no effect, generate detection from paper counts, arXiv posting and author-level propensity, apply the same sample rules, `k`, `n_i` strata, fixed effects and PPML, and compare:
   - Fixed-window share rule.
   - Monthly first detection.
   - Rolling lagged exposure.

   Test each author-type rule by `n_i`, with and without the exposure-window exclusion and exposure-volume control. Report spurious differences for W vs N and WI vs W, and report mean-reversion bias separately.
10. **Citation-window audit, with no signal data.** Check dated citing works, complete months and scan cost. Set the citation window.
11. **Scoring and cost table.** List each analysis, papers to score, arXiv text cost, compute cost and GPU-hours, including monthly first detection, rolling exposure, AI researchers, new entrants, H1, placebo and a line-item Phase 1 pilot. Compare S3 and per-paper arXiv access. The PI chooses what to keep.

Outputs:

- `reports/phase0_data_audit.md`
- `reports/phase0_funnel.md`
- `reports/phase0_simulation.md`
- Cost log and manifest.

### Phase 1: Measurement validation

**Goal:** decide whether writing and idea signals can support the study.

Default pilot: 5,000 calibration papers per group (fit and held out; groups set at the Phase 0 gate) and about 2,000 sampled main-sample authors with all their selected papers (up to 6,000 papers), plus the placebo and synthetic-test samples sized at Phase 0. The outcome firewall applies, except for the placebo.

Tasks:

1. Acquire and parse arXiv v1 text. Compare LaTeX-based and PDF-based text on the same papers. If the PI approves, compare v1 with published text on a small sample.
2. Run IdeaLens on local GPU. Measure throughput and failures.
3. Compare local outlines with Gemini 3.7 Flash on about 500 papers, after PI approves external use. If not approved, skip this comparison; local calibration stands.
4. Fit calibration cuts by group.
5. Run validation tests:

| Test | Question | Proposed pass criterion |
|---|---|---|
| False positives | Is realized false-positive rate close to nominal on held-out pre-2023 papers? | At most twice nominal in reportable groups |
| Group differences | Does it vary greatly by field, English group, career age, or input type? | Differences are explained and can be handled by group cuts |
| Parser and version | Do verdicts change between LaTeX and PDF input, or between v1 and later text where approved? | Report agreement; proposed at least 90% for input type |
| Extraction stability | Do repeated extractions yield the same verdict? | At least 90% agreement on a random sample; report near-threshold performance |
| AI-polishing | Does AI polishing of pre-2023 papers increase idea score? | Writing signal rises; idea flag rate stays low, proposed at most 10% |
| AI-idea sensitivity | Does AI-generated scientific text from AI plans get flagged? | Report rate; propose at least 70% |
| Newer models | Does sensitivity fall on recent generators? | Report; explain implications |
| Time pattern | Using data through 2024-12 only, do signal rates rise after late 2022? | Yes, with a plausible field pattern. A pass means no contradiction found, not proof of provenance |
| Concreteness | Do idea scores merely reflect specificity? | Report correlation with a concreteness measure; high overlap triggers review |
| Disclosure check | Do disclosure categories relate to signals? | Directionally consistent, recognizing that disclosures mostly report writing |
| Score placebo | On the −6-year pseudo-timeline, with 2017–2018 scores and no outcome dated 2021 or later, do high-score authors (top decile of author mean score, within domain and `n_i`) have faster 2019–2020 growth? Run ProseLens and IdeaLens separately, plus continuous scores. Check arXiv v1 coverage and out-of-time scoring first | 95% CI entirely outside 0.90–1.10: stop. Otherwise outside 0.95–1.05: PI review. A pass means no contradiction found |
| Signal overlap | What is the 2×2 distribution of writing and ideas? Which appears first? | Report descriptively; enough WI and W authors are needed |

Thresholds in this table are proposed. Report the actual results; do not silently pass near misses.

Outputs:

- `reports/phase1_measurement_validation.md`
- Calibration files and sample lists.
- Local-versus-Gemini comparison, if approved.
- Recommendation: continue, continue with changes, or switch to the fallback.

### Phase 2: Pre-analysis plan and full scoring

**Goal:** lock the analysis before looking at outcomes by signal type.

Tasks:

1. Draft `docs/PRE_ANALYSIS_PLAN.md`, including:
   - Final sample and eligible-paper rules.
   - Final signal thresholds and types.
   - Primary outcomes and contrasts.
   - Clustering and multiple-testing plan.
   - Timing rule and citation window.
   - All required robustness and subgroup analyses.
   - What counts as support, no support, or inconclusive.
2. PI approves or edits the plan.
3. Then build exposure data:
   - Select papers using the locked seed.
   - Retrieve and parse arXiv v1 text.
   - Run extraction and scoring.
   - Produce author-level signal tables and QA.
4. Build the author-half-year panel, zero-filled from each author's first publication half-year, with score and outcome tables kept in separate paths. Do not join or summarize outcomes by signal type until the "Before Phase 3" gate is cleared.
5. Score only the additional samples the PI approved in the Phase 0 scoring table (H1 follow-up, AI researchers, new entrants), with per-author caps.
6. Report realized type counts and full-text failures, then stop at the gate.

Outputs:

- `data/final/author_signals.parquet`
- `data/final/author_period_panel.parquet`
- `data/final/paper_scores.parquet`
- `reports/phase2_data_build.md`

### Phase 3: Main analysis

Run only what the approved plan specifies, then clearly separate exploratory work.

1. **H2a/H2b:** paper count DiD and event studies.
2. **Citations:** author panel and V1.
3. **H1:** sequence and hazard models.
4. **Robustness and heterogeneity.**
5. **Selection and arXiv checks.**
6. **AI researchers:** repeat core comparisons separately.
7. **New entrants:** compare 2023–2024 entrants with 2019–2020 entrants at equal career age. Types apply only to 2023–2024 entrants; the 2019–2020 cohort is a pre-LLM reference. No pre-trends and no causal claims.

Figure rules:

- Figure 1 presents the whole framework and how the analyses relate.
- Axes need clear labels. Add short notes that explain direction and scale.
- Label pre-period, exposure and outcome periods.
- Report uncertainty.

Outputs:

- `reports/phase3_results.md`
- Tables and figures
- A results narrative based on evidence, without choosing results to fit a framework.

### Phase 4: Code extension

Run after Phase 3 unless the PI changes the order. This phase does not change H2 primary results.

Tasks:

1. Build paper-repository links from rs-graph-v1, Papers with Code, and links extracted from full text or LaTeX.
2. Distinguish a paper's own repository from cited repositories. Manually check a random sample; target precision is at least 0.90.
3. Match authors to GitHub accounts using the Brown et al. model `evamxb/dev-author-em-clf`. Target precision is at least 0.90 in a checked sample. Be careful with short names and organization accounts.
4. Prefer `git clone --filter=blob:none` for history collection, then use the GitHub API where needed. Respect rate limits. Do not treat deleted repositories as non-use.
5. Detect signals following Khosravani & Mockus: bot accounts, commit signatures, author-name suffixes and files such as `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.claude/`, `.cursor/`, `.cursorrules`, `.github/copilot-instructions.md`.
6. Treat lack of repository or trace as **missing**, not non-use.
7. Treat 2024 evidence as weak and descriptive.
8. Report adoption sequence, code-signal hazards and preliminary 2026 output associations. Plan formal output analysis only when 2027 data are available.

Outputs:

- `reports/phase4_code_extension.md`
- Link and signal tables with quality checks.

---

## 11. Gates

| Gate | Requires | Stop if |
|---|---|---|
| **After Phase 0** | Funnel, arXiv match rates and field coverage, v1-to-publication lag, 2026 completeness, citation window, scoring table, cost, power | Minimum detectable difference for WI vs W exceeds a level the PI sets after seeing the power table; eligible non-AI authors are concentrated in one or two fields; or crosswalk, conference or published-version handling is unreliable |
| **After Phase 1** | Validation results, calibration, rerun power, recommendation | IdeaLens fails any of: false positives, extraction stability, AI-polishing, placebo. AI-idea sensitivity failure goes to PI review |
| **Before full scoring** | PI-approved, time-stamped and hashed `docs/PRE_ANALYSIS_PLAN.md`, with numeric definitions of support, no support and inconclusive, and a registration decision | Plan not approved |
| **Before Phase 3** | Phase 2 data build: realized type counts, full-text failures, QA, and no outcome-by-type output | Type counts or attrition make the planned contrasts infeasible |
| **After Phase 3** | Results and robustness | Pre-trends or selection checks undermine interpretation; ask how to report |
| **After Phase 4** | Link precision, signal tables, preliminary results | Link precision below target |

### Fallback if arXiv coverage fails

If the Phase 0 gate rejects arXiv coverage, stop and ask. The default fallback uses one main text source: OpenAlex full text. Define eligible authors by `has_content`, draw a stratified random sample of authors by field and career age, score all eligible exposure papers for those authors, and use sampling weights. Budget changes the number of authors, not the paper-selection rule. Record text version and run a same-version robustness check. Do not fill gaps with a mixture of sources.

### Fallback if idea measurement fails

Do not force the idea analysis into the main results. Stop and ask whether to proceed. The fallback contrast is any writing signal vs no writing signal; WI vs W and `delta_1` are dropped, and idea-signal validity is reported as a separate finding. Tell the PI this is mainly a replication of Kusumegi et al. and materially weakens the original contribution.

---

## 12. Repository layout

```text
ai-division-of-labor/
├── README.md
├── SPEC.md
├── docs/
│   ├── PRE_ANALYSIS_PLAN.md
│   ├── DEVIATIONS.md
│   └── DATA_DICTIONARY.md
├── config/
│   ├── project.yml
│   └── thresholds/
├── src/
│   ├── data/
│   ├── measure/
│   ├── analysis/
│   ├── code_extension/
│   └── utils/
├── sql/
├── slurm/
├── tests/
├── reports/
└── figures/
```

Keep data, full text, model weights, secrets and credentials out of git. Use symlinks or configured paths to `/scratch/network/yh6580/ai_division_of_labor/`.

Required tests:

- Eligible-paper rules on hand-written fixtures.
- Zero-filled balanced panels.
- Exposure and outcome window separation, including exclusion of papers with exposure-window v1.
- arXiv-to-OpenAlex crosswalk and paper-family deduplication, including summed citations with no duplicate citing works.
- Fixed random selection.
- Threshold assignment.
- Citation-window calculation.
- Simulated data where the known effect is zero.
- Firewall: score and outcome tables live in separate paths. The only join code before Phase 3 is the placebo module. A test fails on any other join or on placebo data past its cutoff.

---

## 13. Required items in every report

1. Input data version and run ID.
2. Exact sample counts at each filter.
3. Cost and compute used.
4. Main findings in plain language.
5. Tests failed and limitations.
6. Unverified assumptions.
7. Recommendation and PI decision needed.

---

## 14. Decisions still open

Resolve these in the indicated phase:

| Item | Resolve in |
|---|---|
| Whether at least 4 baseline papers is too strict | Phase 0 |
| Whether arXiv coverage is broad enough, or the OpenAlex full-text fallback is needed | Phase 0 gate |
| arXiv text source, access route and budget | Phase 0 scoring table |
| AI-researcher rule | Phase 0 |
| Whether 2026H1 is usable | Phase 0 |
| External LLM use and license check | Before Phase 1 |
| Local extractor | Phase 1 |
| Calibration group level | Phase 1 |
| Paper-level false-positive rate, author-level share and threshold grid | Phase 1 and pre-analysis plan |
| Clustering and multiple-testing rules | Pre-analysis plan |
| Citation window details | Phase 0 and pre-analysis plan |
| Which extra-scoring analyses to keep | Phase 0 scoring table |
| Minimum detectable difference that stops the project | Phase 0 gate |
| Public registration of the plan | Pre-analysis plan |
| Whether code extension becomes formal after 2027 data | Later PI decision |

---

## 15. Key references

- Kusumegi et al., *Scientific production in the era of large language models*, Science (2025). https://gwern.net/doc/science/2025-kusumegi.pdf
- Renault et al., comment on first-detection timing. https://arxiv.org/pdf/2605.17979
- Filimonovic et al., *Can GenAI Improve Academic Performance?* https://arxiv.org/html/2510.02408v1
- Hao et al., *AI expands scientists' impact but contracts science's focus*. https://arxiv.org/abs/2412.07727
- Rajendhran et al., *IdeaLens*. https://arxiv.org/pdf/2610.06778 ; package: https://pypi.org/project/idealens/
- Khosravani & Mockus, *Detecting AI Coding Agents in Open Source*. https://arxiv.org/pdf/2606.24429
- Brown et al., *Code Contribution and Credit in Science*. https://arxiv.org/pdf/2510.16242
- Mohapatra & Pruthi, AI disclosure statements. https://arxiv.org/pdf/2608.23271
- OpenAlex snapshot documentation. https://help.openalex.org/access/snapshot/
- OpenAlex fields. https://help.openalex.org/data/works/attributes/
- OpenAlex full text. https://help.openalex.org/access/fulltext/
- arXiv bulk data on S3. https://info.arxiv.org/help/bulk_data_s3.html
- arXiv moderation policy notices. https://blog.arxiv.org/category/moderation
- Adroit documentation. https://researchcomputing.princeton.edu/adroit
