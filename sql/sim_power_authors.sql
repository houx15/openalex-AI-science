-- Phase 0 power simulation input: attributes of main-sample authors (m = 1) from the funnel table.
-- Pre-2023 attributes and exposure-paper counts only; no outcomes, no scores.
SELECT f.author_id, f.modal_field, f.modal_domain, f.first_year, f.has_orcid, f.n_base, f.n_arxiv_elig,
       f.posted_arxiv_2018_22
FROM author_funnel_r20261106a f
WHERE f.n_base >= 4 AND f.n_ai_2018_22 * 1.0 / f.n_2018_22 < 0.5 AND f.n_arxiv_elig >= 1
