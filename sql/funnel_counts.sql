-- Phase 0 funnel counts from author_funnel_r20261106a (sql/ctas_author_funnel.sql), by modal 2018-2022
-- domain and overall. Main sample: >= 4 eligible works 2018-2021, AI share of 2018-2022 eligible works
-- < 0.5, >= m eligible arXiv v1 papers in 2023-2024. Papers to score: up to k = 3 per author by a
-- fixed-seed hash (seed 20261105), unique papers counted once. No outcomes, no scores.
WITH a AS (
  SELECT f.*, coalesce(d.display_name, '(none)') AS domain,
         n_ai_2018_22 * 1.0 / n_2018_22 AS ai_share
  FROM author_funnel_r20261106a f LEFT JOIN domains d ON d.id = f.modal_domain
),
main AS (SELECT * FROM a WHERE n_base >= 4 AND ai_share < 0.5 AND n_arxiv_elig >= 1),
sel AS (
  SELECT domain, arxiv_id
  FROM (SELECT m.domain, t.arxiv_id,
               row_number() OVER (PARTITION BY m.author_id
                                  ORDER BY from_big_endian_64(xxhash64(to_utf8(m.author_id || t.arxiv_id || '20261105')))) AS rn
        FROM main m CROSS JOIN UNNEST(m.elig_arxiv_ids) AS t(arxiv_id))
  WHERE rn <= 3
),
counts AS (
  SELECT domain,
         count(*) AS all_authors,
         count_if(n_base >= 2) AS base_ge2,
         count_if(n_base >= 3) AS base_ge3,
         count_if(n_base >= 4) AS base_ge4,
         count_if(n_base >= 4 AND ai_share < 0.5) AS not_ai,
         count_if(n_base >= 4 AND ai_share < 0.25) AS not_ai_25,
         count_if(n_base >= 4 AND ai_share < 0.75) AS not_ai_75,
         count_if(n_base >= 4 AND ai_share < 0.5 AND n_elig_2023_24 >= 1) AS elig_work_23_24,
         count_if(n_base >= 4 AND ai_share < 0.5 AND n_arxiv_any >= 1) AS any_arxiv_23_24,
         count_if(n_base >= 4 AND ai_share < 0.5 AND n_arxiv_elig >= 1) AS m1,
         count_if(n_base >= 4 AND ai_share < 0.5 AND n_arxiv_elig >= 2) AS m2,
         count_if(n_base >= 4 AND ai_share < 0.5 AND n_arxiv_elig >= 3) AS m3,
         count_if(n_base >= 4 AND ai_share < 0.5 AND n_arxiv_elig >= 1 AND has_orcid) AS m1_orcid,
         count_if(n_base >= 4 AND ai_share < 0.5 AND n_arxiv_elig >= 1 AND posted_arxiv_2018_22) AS m1_pre_arxiv,
         count_if(n_base >= 4 AND ai_share >= 0.5 AND n_arxiv_elig >= 1) AS ai_researchers_m1,
         count_if(n_base IN (2, 3) AND ai_share < 0.5 AND n_arxiv_elig >= 1) AS m1_base_2_3,
         sum(CASE WHEN n_base >= 4 AND ai_share < 0.5 AND n_arxiv_elig >= 1 THEN least(n_arxiv_elig, 3) END) AS author_paper_slots_k3
  FROM a GROUP BY ROLLUP (domain)
),
papers AS (
  SELECT domain, count(DISTINCT arxiv_id) AS unique_papers_k3 FROM sel GROUP BY ROLLUP (domain)
),
all_papers AS (
  SELECT m.domain, count(DISTINCT t.arxiv_id) AS unique_papers_all
  FROM main m CROSS JOIN UNNEST(m.elig_arxiv_ids) AS t(arxiv_id) GROUP BY ROLLUP (m.domain)
)
SELECT coalesce(c.domain, 'ALL') AS domain, c.*, p.unique_papers_k3, ap.unique_papers_all
FROM counts c
LEFT JOIN papers p ON p.domain IS NOT DISTINCT FROM c.domain
LEFT JOIN all_papers ap ON ap.domain IS NOT DISTINCT FROM c.domain
ORDER BY c.all_authors DESC
