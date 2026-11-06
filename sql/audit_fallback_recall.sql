-- Phase 0 audit: recall of the title + author fallback rules, on KNOWN published versions. For
-- 2023-2024 arXiv papers linked by arXiv ID or DOI to a published work that is a separate record from
-- OpenAlex's arXiv record, would the fallback have found that work? Same normalization, similarity
-- and shared-author-ID definitions as sql/fallback_candidates_author_block.sql (the best-candidate
-- condition is not applied, so jaccard-rule recall is an upper bound). No outcomes, no scores.
WITH pairs AS (
  SELECT DISTINCT p.arxiv_id, p.work_id, q.work_id AS arxiv_work_id, year(p.v1_date) AS v1_year,
         split_part(p.primary_category, '.', 1) IN ('cs', 'math', 'stat', 'eess') AS cs_math
  FROM paper_family_r20261106b p
  JOIN paper_family_r20261106b q ON q.arxiv_id = p.arxiv_id AND q.is_arxiv_primary
  WHERE year(p.v1_date) IN (2023, 2024) AND p.link_flag IS NULL AND NOT p.is_xpac
    AND NOT coalesce(p.is_arxiv_primary, true) AND p.authors_count <= 50
),
shared AS (
  SELECT pr.arxiv_id, pr.work_id, count(DISTINCT a.author_id) AS shared_authors
  FROM pairs pr
  JOIN authorship_long_r20261106b a ON a.work_id = pr.arxiv_work_id
  JOIN authorship_long_r20261106b b ON b.work_id = pr.work_id AND b.author_id = a.author_id
  WHERE a.author_id IS NOT NULL
    AND a.publication_year_bin IN ('2022', '2023', '2024', '2025', '2026')
    AND b.publication_year_bin IN ('2022', '2023', '2024', '2025', '2026')
  GROUP BY 1, 2
),
titles AS (
  SELECT pr.*, coalesce(s.shared_authors, 0) AS shared_authors,
         regexp_split(trim(regexp_replace(regexp_replace(lower(normalize(ax.title, NFKD)), '[^a-z0-9 ]', ' '), ' +', ' ')), ' ') AS ta,
         regexp_split(trim(regexp_replace(regexp_replace(lower(normalize(w.title, NFKD)), '[^a-z0-9 ]', ' '), ' +', ' ')), ' ') AS tb
  FROM pairs pr
  JOIN (SELECT arxiv_id, arbitrary(title) AS title FROM arxiv_versions_kaggle_v21506946 GROUP BY 1) ax ON ax.arxiv_id = pr.arxiv_id
  JOIN works_core_r20261106a w ON w.id = pr.work_id
  LEFT JOIN shared s ON s.arxiv_id = pr.arxiv_id AND s.work_id = pr.work_id
),
scored AS (
  SELECT v1_year, cs_math, shared_authors,
         array_join(ta, '') = array_join(tb, '') AS exact_title,
         cardinality(array_intersect(array_distinct(ta), array_distinct(tb))) * 1.0
           / cardinality(array_union(array_distinct(ta), array_distinct(tb))) AS jaccard,
         1 - levenshtein_distance(array_join(ta, ''), array_join(tb, '')) * 1.0
           / greatest(length(array_join(ta, '')), length(array_join(tb, '')), 1) AS lev_sim
  FROM titles
)
SELECT v1_year, cs_math, count(*) AS n_pairs,
       count_if(shared_authors >= 1) AS n_shared_author,
       count_if(exact_title) AS n_exact,
       count_if(shared_authors >= 1 AND exact_title) AS n_exact_id,
       count_if(shared_authors >= 1 AND (exact_title OR lev_sim >= 0.9)) AS n_exact_or_lev,
       count_if(shared_authors >= 1 AND (exact_title OR lev_sim >= 0.9 OR jaccard >= 0.8)) AS n_any_rule
FROM scored GROUP BY 1, 2 ORDER BY 1, 2
