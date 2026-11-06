-- Phase 0: size of the author x publication panel for the main sample (m = 1), for storage and
-- compute planning. Totals only over 2018-2026: no per-period, per-author or per-signal breakdown,
-- so no outcome information is produced. Eligible work definition as in sql/ctas_author_funnel.sql.
WITH main AS (
  SELECT author_id, first_year
  FROM author_funnel_r20261106a
  WHERE n_base >= 4 AND n_ai_2018_22 * 1.0 / n_2018_22 < 0.5 AND n_arxiv_elig >= 1
),
elig AS (
  SELECT id AS work_id, authors_count
  FROM works_core_r20261106a
  WHERE publication_year BETWEEN 2018 AND 2026 AND NOT is_xpac AND publication_date IS NOT NULL
    AND type IN ('article', 'conference-paper') AND pl_source_type IN ('journal', 'conference', 'book series')
    AND NOT coalesce(is_paratext, false) AND NOT coalesce(is_retracted, false)
),
aw AS (
  SELECT DISTINCT al.author_id, al.work_id
  FROM authorship_long_r20261106b al
  JOIN main m ON m.author_id = al.author_id
  WHERE al.publication_year_bin IN ('2018', '2019', '2020', '2021', '2022', '2023', '2024', '2025', '2026')
)
SELECT (SELECT count(*) FROM main) AS main_authors,
       (SELECT sum(CASE WHEN first_year <= 2018 THEN 17 ELSE (2026 - first_year) * 2 + 1 END) FROM main) AS author_halfyear_rows,
       count(*) AS author_work_rows,
       count(DISTINCT aw.work_id) AS distinct_works,
       approx_percentile(e.authors_count, 0.5) AS median_authors_per_work
FROM aw JOIN elig e ON e.work_id = aw.work_id
