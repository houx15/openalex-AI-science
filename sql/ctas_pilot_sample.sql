-- Phase 1 pilot sample lists (SPEC §10 Phase 1; decisions of 2026-11-08 in docs/DECISIONS.md).
-- One row per (sample, arxiv_id, author_id). No outcomes, no scores.
--   calibration : arXiv v1 2019-01-01..2022-10-31, same paper eligibility as exposure (<= 50 authors,
--                 an English family work, research-like title, no referee-report link), 5,000 per
--                 arXiv primary-category group by hash (seed 20261108). author_id is NULL.
--   pilot_main  : 3,300 main-sample authors (eligibility v1) ranked by hash (seed 20261107), with
--                 their k = 3 exposure papers (seed 20261105). Exposure papers whose family has a
--                 formal publication dated before 2022 are dropped first (gate decision), so authors
--                 left with none leave the main sample.
--   placebo     : 30,000 pseudo-timeline authors (pseudo_author_papers_r20261106a) ranked by hash
--                 (seed 20261107), k = 3 papers from 2017-18 (seed 20261105), dropping papers whose
--                 family has a formal publication dated before 2016 (the same rule shifted -6 years).
CREATE TABLE pilot_sample_${RUN_ID}
WITH (format = 'PARQUET', write_compression = 'ZSTD') AS
WITH prepub AS (
  SELECT DISTINCT arxiv_id, year(v1_date) AS v1_year
  FROM paper_family_r20261106b
  WHERE work_id IS NOT NULL AND NOT is_xpac AND NOT coalesce(is_arxiv_primary, false)
    AND type IN ('article', 'conference-paper', 'book-chapter', 'review', 'letter', 'book')
    AND coalesce(link_flag, '') <> 'exclude_peer_review'
    AND ((year(v1_date) IN (2023, 2024) AND publication_date < DATE '2022-01-01')
      OR (year(v1_date) IN (2017, 2018) AND publication_date < DATE '2016-01-01'))
),
-- pilot_main
main_slots AS (
  SELECT f.author_id, t.arxiv_id
  FROM author_funnel_r20261106b f CROSS JOIN UNNEST(f.elig_arxiv_ids) AS t(arxiv_id)
  WHERE f.n_base >= 4 AND f.n_ai_2018_22 * 1.0 / f.n_2018_22 < 0.5 AND f.n_arxiv_elig >= 1
    AND t.arxiv_id NOT IN (SELECT arxiv_id FROM prepub WHERE v1_year IN (2023, 2024))
),
main_rank AS (
  SELECT author_id, row_number() OVER (ORDER BY from_big_endian_64(xxhash64(to_utf8(author_id || '20261107')))) AS author_rank
  FROM (SELECT DISTINCT author_id FROM main_slots)
),
pilot_main AS (
  SELECT 'pilot_main' AS sample, s.arxiv_id, s.author_id
  FROM (SELECT ms.*, row_number() OVER (PARTITION BY ms.author_id
          ORDER BY from_big_endian_64(xxhash64(to_utf8(ms.author_id || ms.arxiv_id || '20261105')))) AS rn
        FROM main_slots ms JOIN main_rank r ON r.author_id = ms.author_id WHERE r.author_rank <= 3300) s
  WHERE s.rn <= 3
),
-- placebo
pseudo_slots AS (
  SELECT author_id, arxiv_id FROM pseudo_author_papers_r20261106a
  WHERE arxiv_id NOT IN (SELECT arxiv_id FROM prepub WHERE v1_year IN (2017, 2018))
),
pseudo_rank AS (
  SELECT author_id, row_number() OVER (ORDER BY from_big_endian_64(xxhash64(to_utf8(author_id || '20261107')))) AS author_rank
  FROM (SELECT DISTINCT author_id FROM pseudo_slots)
),
placebo AS (
  SELECT 'placebo' AS sample, s.arxiv_id, s.author_id
  FROM (SELECT ps.*, row_number() OVER (PARTITION BY ps.author_id
          ORDER BY from_big_endian_64(xxhash64(to_utf8(ps.author_id || ps.arxiv_id || '20261105')))) AS rn
        FROM pseudo_slots ps JOIN pseudo_rank r ON r.author_id = ps.author_id WHERE r.author_rank <= 30000) s
  WHERE s.rn <= 3
),
-- calibration
cal_fam AS (
  SELECT p.arxiv_id, arbitrary(p.primary_category) AS primary_category,
         coalesce(max(p.authors_count), 0) <= 50 AS small_team,
         bool_or(w.language = 'en') AS any_en,
         NOT regexp_like(lower(arbitrary(a.title)),
           '(^|[^a-z])(survey|review|tutorial|overview|position paper|perspective|primer|lecture notes|erratum|corrigendum|comment on|reply to|response to)([^a-z]|$)') AS research_title
  FROM paper_family_r20261106b p
  JOIN arxiv_versions_kaggle_v21506946 a ON a.arxiv_id = p.arxiv_id
  LEFT JOIN works_core_r20261106a w ON w.id = p.work_id
  WHERE p.v1_date >= TIMESTAMP '2019-01-01 00:00:00' AND p.v1_date < TIMESTAMP '2022-11-01 00:00:00'
    AND coalesce(p.link_flag, '') <> 'exclude_peer_review'
  GROUP BY 1
),
cal_pool AS (
  SELECT arxiv_id,
         CASE WHEN primary_category LIKE 'cs.%' THEN 'cs'
              WHEN primary_category LIKE 'math.%' OR primary_category = 'math-ph' THEN 'math'
              WHEN primary_category LIKE 'cond-mat%' THEN 'cond-mat'
              WHEN primary_category LIKE 'astro-ph%' THEN 'astro-ph'
              WHEN primary_category LIKE 'hep-%' OR primary_category LIKE 'nucl-%' OR primary_category = 'gr-qc' THEN 'hep-nucl-grqc'
              WHEN primary_category LIKE 'eess.%' THEN 'eess'
              WHEN primary_category = 'quant-ph' THEN 'quant-ph'
              WHEN primary_category LIKE 'stat.%' THEN 'stat'
              WHEN primary_category LIKE 'physics.%' OR primary_category LIKE 'nlin.%' THEN 'physics-nlin'
              WHEN primary_category LIKE 'q-bio.%' OR primary_category LIKE 'q-fin.%' OR primary_category LIKE 'econ.%' THEN 'qbio-qfin-econ'
              ELSE 'other' END AS cal_group
  FROM cal_fam WHERE small_team AND coalesce(any_en, false) AND research_title
),
calibration AS (
  SELECT 'calibration' AS sample, arxiv_id, CAST(NULL AS varchar) AS author_id, cal_group
  FROM (SELECT c.*, row_number() OVER (PARTITION BY cal_group
          ORDER BY from_big_endian_64(xxhash64(to_utf8(arxiv_id || '20261108')))) AS rn
        FROM cal_pool c WHERE cal_group <> 'other')
  WHERE rn <= 5000
),
all_rows AS (
  SELECT sample, arxiv_id, author_id, CAST(NULL AS varchar) AS cal_group FROM pilot_main
  UNION ALL SELECT sample, arxiv_id, author_id, CAST(NULL AS varchar) FROM placebo
  UNION ALL SELECT sample, arxiv_id, author_id, cal_group FROM calibration
)
SELECT r.sample, r.arxiv_id, r.author_id, r.cal_group, a.v1_date, a.n_versions, a.primary_category,
       a.versions[1].source_type AS v1_source_type, a.versions[1].size AS v1_size, a.license
FROM all_rows r JOIN arxiv_versions_kaggle_v21506946 a ON a.arxiv_id = r.arxiv_id
