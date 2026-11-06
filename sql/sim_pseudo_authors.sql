-- Phase 0 false-positive simulation input (SPEC §10 task 9): the -6-year pseudo-timeline sample.
-- Authors with >= 4 eligible works 2012-2015, AI share of eligible 2012-2016 works < 0.5, and >= 1
-- eligible arXiv v1 in 2017-2018 (rules as sql/funnel_pseudo_timeline.sql). One row per
-- (author, eligible 2017-18 arXiv paper) with its v1 date, plus author attributes. No scores.
CREATE TABLE pseudo_author_papers_${RUN_ID}
WITH (format = 'PARQUET', write_compression = 'ZSTD') AS
WITH elig AS (
  SELECT id AS work_id, publication_year, field_id,
         subfield_id IN ('https://openalex.org/subfields/1702', 'https://openalex.org/subfields/1707') AS is_ai
  FROM works_core_r20261106a
  WHERE publication_year BETWEEN 2012 AND 2016 AND NOT is_xpac AND publication_date IS NOT NULL
    AND type IN ('article', 'conference-paper') AND pl_source_type IN ('journal', 'conference', 'book series')
    AND NOT coalesce(is_paratext, false) AND NOT coalesce(is_retracted, false)
),
au_work AS (
  SELECT DISTINCT al.author_id, e.work_id, e.publication_year, e.field_id, e.is_ai
  FROM elig e JOIN authorship_long_r20261106b al ON al.work_id = e.work_id
  WHERE al.author_id IS NOT NULL AND al.publication_year_bin IN ('2012', '2013', '2014', '2015', '2016')
),
au AS (
  SELECT author_id, count_if(publication_year <= 2015) AS n_base,
         count_if(is_ai) * 1.0 / count(*) AS ai_share
  FROM au_work GROUP BY 1
),
au_field AS (
  SELECT author_id, max_by(field_id, n) AS modal_field
  FROM (SELECT author_id, field_id, count(*) AS n FROM au_work GROUP BY 1, 2) GROUP BY 1
),
first_year AS (
  SELECT author_id, min(publication_year) AS first_year
  FROM authorship_long_r20261106b
  WHERE author_id IS NOT NULL AND NOT is_xpac AND publication_year IS NOT NULL
  GROUP BY 1
),
fam AS (
  SELECT p.arxiv_id, arbitrary(p.v1_date) AS v1_date,
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
  JOIN authorship_long_r20261106b al ON al.work_id = p.work_id
  WHERE year(p.v1_date) IN (2017, 2018) AND coalesce(p.link_flag, '') <> 'exclude_peer_review' AND al.author_id IS NOT NULL
)
SELECT ax.author_id, ax.arxiv_id, f.v1_date, au.n_base, af.modal_field, fy.first_year
FROM ax
JOIN fam f ON f.arxiv_id = ax.arxiv_id AND f.eligible
JOIN au ON au.author_id = ax.author_id AND au.n_base >= 4 AND au.ai_share < 0.5
LEFT JOIN au_field af ON af.author_id = ax.author_id
LEFT JOIN first_year fy ON fy.author_id = ax.author_id
