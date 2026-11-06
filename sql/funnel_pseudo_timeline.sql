-- Phase 0: size of the -6-year pseudo-timeline sample (SPEC §10 task 9; Phase 1 score placebo).
-- Same rules as the main funnel shifted by 6 years: >= 4 eligible works 2012-2015, AI share of
-- eligible 2012-2016 works < 0.5, >= 1 eligible arXiv v1 in 2017-2018 (<= 50 authors, English
-- family work, research-like title). Counts only; no outcomes, no scores. Eligibility and AI list
-- as in sql/ctas_author_funnel.sql.
WITH elig AS (
  SELECT id AS work_id, publication_year,
         subfield_id IN ('https://openalex.org/subfields/1702', 'https://openalex.org/subfields/1707') AS is_ai
  FROM works_core_r20261106a
  WHERE publication_year BETWEEN 2012 AND 2016 AND NOT is_xpac AND publication_date IS NOT NULL
    AND type IN ('article', 'conference-paper') AND pl_source_type IN ('journal', 'conference', 'book series')
    AND NOT coalesce(is_paratext, false) AND NOT coalesce(is_retracted, false)
),
au AS (
  SELECT author_id, count_if(publication_year <= 2015) AS n_base,
         count_if(is_ai) * 1.0 / count(*) AS ai_share
  FROM (SELECT DISTINCT al.author_id, e.work_id, e.publication_year, e.is_ai
        FROM elig e JOIN authorship_long_r20261106b al ON al.work_id = e.work_id
        WHERE al.author_id IS NOT NULL AND al.publication_year_bin IN ('2012', '2013', '2014', '2015', '2016'))
  GROUP BY 1
),
fam AS (
  SELECT p.arxiv_id,
         coalesce(max(p.authors_count), 0) <= 50
           AND bool_or(w.language = 'en')
           AND NOT regexp_like(lower(arbitrary(a.title)),
             '(^|[^a-z])(survey|review|tutorial|overview|position paper|perspective|primer|lecture notes|erratum|corrigendum|comment on|reply to|response to)([^a-z]|$)') AS eligible
  FROM paper_family_r20261106b p
  JOIN arxiv_versions_kaggle_v21506946 a ON a.arxiv_id = p.arxiv_id
  LEFT JOIN works_core_r20261106a w ON w.id = p.work_id
  WHERE year(p.v1_date) IN (2017, 2018) AND coalesce(p.link_flag, '') <> 'exclude_peer_review'
  GROUP BY 1
),
ax AS (
  SELECT DISTINCT al.author_id, p.arxiv_id
  FROM paper_family_r20261106b p
  JOIN fam f ON f.arxiv_id = p.arxiv_id AND f.eligible
  JOIN authorship_long_r20261106b al ON al.work_id = p.work_id
  WHERE year(p.v1_date) IN (2017, 2018) AND coalesce(p.link_flag, '') <> 'exclude_peer_review' AND al.author_id IS NOT NULL
),
samp AS (
  SELECT ax.author_id, ax.arxiv_id,
         row_number() OVER (PARTITION BY ax.author_id
                            ORDER BY from_big_endian_64(xxhash64(to_utf8(ax.author_id || ax.arxiv_id || '20261105')))) AS rn
  FROM ax JOIN au ON au.author_id = ax.author_id
  WHERE au.n_base >= 4 AND au.ai_share < 0.5
)
SELECT count(DISTINCT author_id) AS authors_m1,
       count(DISTINCT arxiv_id) AS unique_papers_all,
       count(DISTINCT CASE WHEN rn <= 3 THEN arxiv_id END) AS unique_papers_k3
FROM samp
