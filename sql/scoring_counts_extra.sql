-- Phase 0 scoring table (SPEC §10 task 11): sizes of the new-entrant and H1 follow-up samples.
-- Eligible arXiv paper: same rules as sql/ctas_author_funnel.sql (<= 50 authors, any English family
-- work, research-like title), extended to v1 dates 2023-01-01 to 2026-06-30 (last complete half-year).
-- New entrants: first non-xpac OpenAlex publication in 2023-2024 and >= 1 eligible 2023-24 arXiv v1;
--   k = 3 per author by the same hash rule; "new" papers are those not already in the main k = 3 set.
-- H1 follow-up: main-sample authors (eligibility v1) with eligible arXiv v1 in 2025H1-2026H1, capped
--   at one paper per author per half-year by hash. Counts only; no outcomes by score, no scores.
WITH fam_lang AS (
  SELECT p.arxiv_id, bool_or(w.language = 'en') AS any_en
  FROM paper_family_r20261106b p JOIN works_core_r20261106a w ON w.id = p.work_id
  WHERE p.v1_date >= DATE '2023-01-01' AND p.v1_date < DATE '2026-07-01'
  GROUP BY 1
),
arx_fam AS (
  SELECT p.arxiv_id, min(p.v1_date) AS v1_date,
         coalesce(max(p.authors_count), 0) <= 50 AS small_team,
         NOT regexp_like(lower(arbitrary(a.title)),
           '(^|[^a-z])(survey|review|tutorial|overview|position paper|perspective|primer|lecture notes|erratum|corrigendum|comment on|reply to|response to)([^a-z]|$)') AS research_title
  FROM paper_family_r20261106b p JOIN arxiv_versions_kaggle_v21506946 a ON a.arxiv_id = p.arxiv_id
  WHERE p.v1_date >= DATE '2023-01-01' AND p.v1_date < DATE '2026-07-01'
    AND coalesce(p.link_flag, '') <> 'exclude_peer_review'
  GROUP BY 1
),
elig_arx AS (
  SELECT f.arxiv_id, f.v1_date
  FROM arx_fam f JOIN fam_lang l ON l.arxiv_id = f.arxiv_id
  WHERE f.small_team AND l.any_en AND f.research_title
),
arx_auth AS (
  SELECT DISTINCT al.author_id, e.arxiv_id, e.v1_date
  FROM elig_arx e JOIN paper_family_r20261106b p ON p.arxiv_id = e.arxiv_id
  JOIN authorship_long_r20261106b al ON al.work_id = p.work_id
  WHERE al.author_id IS NOT NULL AND coalesce(p.link_flag, '') <> 'exclude_peer_review'
),
first_year AS (
  SELECT author_id, min(publication_year) AS first_year
  FROM authorship_long_r20261106b
  WHERE author_id IS NOT NULL AND NOT is_xpac AND publication_year IS NOT NULL
  GROUP BY 1
),
main_auth AS (
  SELECT author_id, elig_arxiv_ids FROM author_funnel_r20261106b
  WHERE n_base >= 4 AND n_ai_2018_22 * 1.0 / n_2018_22 < 0.5 AND n_arxiv_elig >= 1
),
main_k3 AS (
  SELECT DISTINCT arxiv_id FROM (
    SELECT t.arxiv_id, row_number() OVER (PARTITION BY m.author_id
             ORDER BY from_big_endian_64(xxhash64(to_utf8(m.author_id || t.arxiv_id || '20261105')))) AS rn
    FROM main_auth m CROSS JOIN UNNEST(m.elig_arxiv_ids) AS t(arxiv_id)) WHERE rn <= 3
),
entr AS (
  SELECT x.author_id, x.arxiv_id,
         row_number() OVER (PARTITION BY x.author_id
                            ORDER BY from_big_endian_64(xxhash64(to_utf8(x.author_id || x.arxiv_id || '20261105')))) AS rn
  FROM arx_auth x JOIN first_year fy ON fy.author_id = x.author_id
  WHERE fy.first_year IN (2023, 2024) AND year(x.v1_date) IN (2023, 2024)
),
h1 AS (
  SELECT x.author_id, x.arxiv_id,
         row_number() OVER (PARTITION BY x.author_id, year(x.v1_date), month(x.v1_date) <= 6
                            ORDER BY from_big_endian_64(xxhash64(to_utf8(x.author_id || x.arxiv_id || '20261105')))) AS rn
  FROM arx_auth x JOIN main_auth m ON m.author_id = x.author_id
  WHERE x.v1_date >= DATE '2025-01-01'
)
SELECT 'entrant_authors' AS item, count(DISTINCT author_id) AS n FROM entr
UNION ALL SELECT 'entrant_k3_papers', count(DISTINCT arxiv_id) FROM entr WHERE rn <= 3
UNION ALL SELECT 'entrant_k3_papers_not_in_main', count(DISTINCT e.arxiv_id)
  FROM entr e LEFT JOIN main_k3 m ON m.arxiv_id = e.arxiv_id WHERE e.rn <= 3 AND m.arxiv_id IS NULL
UNION ALL SELECT 'h1_authors_with_2025_26_paper', count(DISTINCT author_id) FROM h1
UNION ALL SELECT 'h1_papers_cap1_per_half', count(DISTINCT arxiv_id) FROM h1 WHERE rn = 1
UNION ALL SELECT 'h1_papers_uncapped', count(DISTINCT arxiv_id) FROM h1
