-- Phase 0 audit: (1) arXiv IDs that appear twice in the Kaggle snapshot table; (2) OpenAlex works
-- (non-xpac, not arXiv-primary) linked to 2+ arXiv papers with v1 2017+, and whether any of those
-- papers are in the pilot sample lists. Metadata only; no outcomes, no scores.
WITH pilot AS (
  SELECT arxiv_id, array_join(array_agg(DISTINCT sample), '|') AS samples
  FROM pilot_sample_r20261108a GROUP BY 1
),
dup_rows AS (
  SELECT 'dup_id' AS kind, a.arxiv_id AS key, a.title, CAST(a.v1_date AS varchar) AS v1, a.n_versions,
         a.primary_category, CAST(NULL AS bigint) AS n_arxiv, CAST(NULL AS varchar) AS arxiv_ids,
         CAST(NULL AS varchar) AS work_type, CAST(NULL AS varchar) AS link_flags, p.samples AS in_pilot
  FROM arxiv_versions_kaggle_v21506946 a
  LEFT JOIN pilot p ON p.arxiv_id = a.arxiv_id
  WHERE a.arxiv_id IN (SELECT arxiv_id FROM arxiv_versions_kaggle_v21506946 GROUP BY 1 HAVING count(*) > 1)
),
links AS (
  SELECT DISTINCT f.work_id, f.arxiv_id, f.type, coalesce(f.link_flag, 'none') AS link_flag, year(f.v1_date) AS v1_year, p.samples
  FROM paper_family_r20261106b f LEFT JOIN pilot p ON p.arxiv_id = f.arxiv_id
  WHERE f.work_id IS NOT NULL AND NOT coalesce(f.is_xpac, false) AND NOT coalesce(f.is_arxiv_primary, false)
    AND year(f.v1_date) >= 2017
),
multi AS (
  SELECT work_id, count(DISTINCT arxiv_id) AS n_arxiv, array_join(array_agg(DISTINCT arxiv_id), '|') AS arxiv_ids,
         arbitrary(type) AS work_type, array_join(array_agg(DISTINCT link_flag), '|') AS link_flags,
         min(v1_year) AS min_v1_year, array_join(array_agg(DISTINCT samples) FILTER (WHERE samples IS NOT NULL), '|') AS in_pilot
  FROM links GROUP BY 1 HAVING count(DISTINCT arxiv_id) > 1
)
SELECT * FROM dup_rows
UNION ALL
SELECT 'multi_work', m.work_id, w.title, CAST(m.min_v1_year AS varchar), CAST(NULL AS integer), CAST(NULL AS varchar),
       m.n_arxiv, m.arxiv_ids, m.work_type, m.link_flags, nullif(m.in_pilot, '')
FROM multi m LEFT JOIN works_core_r20261106a w ON w.id = m.work_id
