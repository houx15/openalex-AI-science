-- Phase 0 power simulation input (SPEC §10 task 8): eligible-work counts per main-sample author
-- (m = 1) and half-year, 2018H1-2022H2 ONLY (no later outcome data). Nonzero cells only; zero-filled
-- locally. Half-year from publication_date; Jan-1 dates flagged for the date-heaping check.
WITH main AS (
  SELECT author_id
  FROM author_funnel_r20261106a
  WHERE n_base >= 4 AND n_ai_2018_22 * 1.0 / n_2018_22 < 0.5 AND n_arxiv_elig >= 1
),
elig AS (
  SELECT id AS work_id, publication_year, publication_date, authors_count
  FROM works_core_r20261106a
  WHERE publication_year BETWEEN 2018 AND 2022 AND NOT is_xpac AND publication_date IS NOT NULL
    AND type IN ('article', 'conference-paper') AND pl_source_type IN ('journal', 'conference', 'book series')
    AND NOT coalesce(is_paratext, false) AND NOT coalesce(is_retracted, false)
),
aw AS (
  SELECT DISTINCT al.author_id, al.work_id
  FROM authorship_long_r20261106b al JOIN main m ON m.author_id = al.author_id
  WHERE al.publication_year_bin IN ('2018', '2019', '2020', '2021', '2022')
)
SELECT aw.author_id,
       e.publication_year * 2 + CASE WHEN CAST(substr(CAST(e.publication_date AS varchar), 6, 2) AS integer) > 6 THEN 1 ELSE 0 END AS half,
       count(*) AS n,
       sum(1.0 / greatest(e.authors_count, 1)) AS n_frac,
       count_if(substr(CAST(e.publication_date AS varchar), 6, 5) = '01-01') AS n_jan1
FROM aw JOIN elig e ON e.work_id = aw.work_id
GROUP BY 1, 2
