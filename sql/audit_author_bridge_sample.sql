-- Phase 0 audit: author bridge (does OpenAlex attribute an author's unpublished arXiv papers to
-- their profile as reliably as published ones?). Draws a fixed-seed sample of main-sample-like
-- authors: >=4 article/conference works in 2018-2021 and >=1 2023-24 arXiv paper attributed in
-- OpenAlex. 100 per stratum: profile ORCID (yes/no) x majority arXiv archive in cs/math/stat/eess
-- (yes/no). Returns names and pre-2023 coauthor names (2018-2022 works with <=50 authors), so the
-- local matcher can find each author's 2023-24 arXiv papers independently of OpenAlex attribution.
-- No outcomes, no scores.
WITH base AS (
  SELECT author_id
  FROM authorship_long_r20261106a
  WHERE publication_year_bin IN ('2018', '2019', '2020', '2021')
    AND type IN ('article', 'conference-paper') AND author_id IS NOT NULL
  GROUP BY 1 HAVING count(*) >= 4
),
arx AS (
  SELECT DISTINCT a.author_id, p.arxiv_id,
         split_part(p.primary_category, '.', 1) IN ('cs', 'math', 'stat', 'eess') AS cs_math
  FROM paper_family_r20261106b p
  JOIN authorship_long_r20261106a a ON a.work_id = p.work_id
  WHERE year(p.v1_date) IN (2023, 2024) AND p.link_flag IS NULL AND NOT p.is_xpac
    AND a.publication_year_bin IN ('2022', '2023', '2024', '2025', '2026') AND a.author_id IS NOT NULL
),
frame AS (
  SELECT x.author_id, array_agg(DISTINCT x.arxiv_id) AS attributed_arxiv_ids,
         count_if(x.cs_math) * 2 >= count(*) AS cs_math_major
  FROM arx x JOIN base b ON b.author_id = x.author_id
  GROUP BY 1
),
strat AS (
  SELECT f.*, au.display_name, au.display_name_alternatives, au.orcid,
         row_number() OVER (PARTITION BY au.orcid IS NOT NULL, f.cs_math_major
                            ORDER BY from_big_endian_64(xxhash64(to_utf8(f.author_id || '20261105')))) AS rn
  FROM frame f JOIN authors au ON au.id = f.author_id
),
samp AS (SELECT * FROM strat WHERE rn <= 100),
small_works AS (
  SELECT id FROM works_core_r20261106a
  WHERE publication_year BETWEEN 2018 AND 2022 AND authors_count <= 50 AND NOT is_xpac
),
co AS (
  SELECT DISTINCT s.author_id, a2.author_id AS co_id
  FROM samp s
  JOIN authorship_long_r20261106a a1 ON a1.author_id = s.author_id
  JOIN small_works w ON w.id = a1.work_id
  JOIN authorship_long_r20261106a a2 ON a2.work_id = a1.work_id AND a2.author_id <> s.author_id
  WHERE a1.publication_year_bin IN ('2018', '2019', '2020', '2021', '2022')
    AND a2.publication_year_bin IN ('2018', '2019', '2020', '2021', '2022')
),
co_names AS (
  SELECT co.author_id, array_join(array_agg(DISTINCT au.display_name), '|') AS coauthor_names
  FROM co JOIN authors au ON au.id = co.co_id
  GROUP BY 1
)
SELECT s.author_id, s.display_name, array_join(s.display_name_alternatives, '|') AS name_alternatives,
       s.orcid IS NOT NULL AS has_orcid, s.cs_math_major,
       array_join(s.attributed_arxiv_ids, '|') AS attributed_arxiv_ids,
       c.coauthor_names
FROM samp s LEFT JOIN co_names c ON c.author_id = s.author_id
