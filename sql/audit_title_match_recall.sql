-- Phase 0 audit: recall of exact-title matching, measured on KNOWN published versions. For 2023-2024
-- arXiv papers already linked (by arXiv ID or DOI) to a published work that is a separate record
-- from OpenAlex's arXiv record, how often does that published work carry the same normalized title
-- as the arXiv record? Normalization as in sql/audit_title_match_unlinked.sql. No outcomes, no scores.
WITH ax AS (
  SELECT arxiv_id, arbitrary(regexp_replace(lower(normalize(title, NFKD)), '[^a-z0-9]', '')) AS tkey
  FROM arxiv_versions_kaggle_v21506946
  WHERE year(v1_date) IN (2023, 2024)
  GROUP BY 1
),
pub AS (
  SELECT p.arxiv_id, p.work_id, year(p.v1_date) AS v1_year,
         split_part(p.primary_category, '.', 1) IN ('cs', 'math', 'stat', 'eess') AS cs_math,
         bool_or(q.is_arxiv_primary) OVER (PARTITION BY p.arxiv_id) AS family_has_arxiv_record
  FROM paper_family_r20261106b p
  JOIN paper_family_r20261106b q ON q.arxiv_id = p.arxiv_id
  WHERE year(p.v1_date) IN (2023, 2024) AND p.link_flag IS NULL AND NOT p.is_xpac
    AND NOT coalesce(p.is_arxiv_primary, true)
),
pairs AS (
  SELECT DISTINCT arxiv_id, work_id, v1_year, cs_math FROM pub WHERE family_has_arxiv_record
)
SELECT pairs.v1_year, pairs.cs_math, count(*) AS n_pairs,
       count_if(length(ax.tkey) >= 25) AS n_long_title,
       count_if(length(ax.tkey) >= 25 AND ax.tkey = regexp_replace(lower(normalize(w.title, NFKD)), '[^a-z0-9]', '')) AS n_exact
FROM pairs
JOIN ax ON ax.arxiv_id = pairs.arxiv_id
JOIN works_core_r20261106a w ON w.id = pairs.work_id
GROUP BY 1, 2
ORDER BY 1, 2
