-- Phase 0 scoring table (SPEC §10 task 11): papers to score per analysis, from the eligibility-v1
-- author table author_funnel_r20261106b (sql/ctas_author_funnel.sql). k = 3 papers per author by the
-- fixed-seed hash (seed 20261105); a paper shared by several authors is scored once. The 100k / 30k
-- author subsamples rank authors by a separate hash (seed 20261107). No outcomes, no scores.
WITH a AS (
  SELECT f.*, n_ai_2018_22 * 1.0 / n_2018_22 AS ai_share,
         row_number() OVER (ORDER BY from_big_endian_64(xxhash64(to_utf8(f.author_id || '20261107')))) AS author_rank
  FROM author_funnel_r20261106b f
  WHERE n_base >= 4 AND n_arxiv_elig >= 1
),
slots AS (
  SELECT a.author_id, a.ai_share < 0.5 AS is_main, a.author_rank, t.arxiv_id,
         row_number() OVER (PARTITION BY a.author_id
                            ORDER BY from_big_endian_64(xxhash64(to_utf8(a.author_id || t.arxiv_id || '20261105')))) AS rn
  FROM a CROSS JOIN UNNEST(a.elig_arxiv_ids) AS t(arxiv_id)
),
main_rank AS (
  SELECT author_id, row_number() OVER (ORDER BY author_rank) AS main_rank
  FROM a WHERE ai_share < 0.5
),
s AS (SELECT s.*, m.main_rank FROM slots s LEFT JOIN main_rank m ON m.author_id = s.author_id),
main_k3 AS (SELECT DISTINCT arxiv_id FROM s WHERE is_main AND rn <= 3)
SELECT 'main_authors' AS item, count(DISTINCT author_id) AS n FROM s WHERE is_main
UNION ALL SELECT 'main_k3_papers', count(*) FROM main_k3
UNION ALL SELECT 'main_k3_slots', count(*) FROM s WHERE is_main AND rn <= 3
UNION ALL SELECT 'main_all_papers', count(DISTINCT arxiv_id) FROM s WHERE is_main
UNION ALL SELECT 'sub100k_k3_papers', count(DISTINCT arxiv_id) FROM s WHERE is_main AND rn <= 3 AND main_rank <= 100000
UNION ALL SELECT 'sub30k_k3_papers', count(DISTINCT arxiv_id) FROM s WHERE is_main AND rn <= 3 AND main_rank <= 30000
UNION ALL SELECT 'pilot2k_k3_papers', count(DISTINCT arxiv_id) FROM s WHERE is_main AND rn <= 3 AND main_rank <= 2000
UNION ALL SELECT 'ai_authors', count(DISTINCT author_id) FROM s WHERE NOT is_main
UNION ALL SELECT 'ai_k3_papers', count(DISTINCT arxiv_id) FROM s WHERE NOT is_main AND rn <= 3
UNION ALL SELECT 'ai_k3_papers_not_in_main', count(DISTINCT s.arxiv_id)
  FROM s LEFT JOIN main_k3 m ON m.arxiv_id = s.arxiv_id WHERE NOT s.is_main AND s.rn <= 3 AND m.arxiv_id IS NULL
