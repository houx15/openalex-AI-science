-- Phase 0 funnel (SPEC §7, §10 task 6): one row per author with >= 1 eligible work in 2018-2021.
-- No outcomes (nothing after 2024 except arXiv-family membership), no scores.
-- Eligible work, v0 [PROPOSED; conference/book-chapter audit pending]: not xpac, publication date
--   present, type article or conference-paper, primary source journal, conference or book series
--   (book series admits LNCS-style proceedings), not paratext, not retracted.
-- AI researcher [PROPOSED]: >= 50% of eligible 2018-2022 works have primary-topic subfield
--   Artificial Intelligence (1702) or Computer Vision and Pattern Recognition (1707); counts kept so
--   25%/75% alternatives come from this table.
-- Eligible arXiv paper [PROPOSED; VERIFY]: v1 in 2023-2024 (UTC); family works have <= 50 authors;
--   at least one family work has OpenAlex language 'en'; title not review/survey/position-like
--   (regex below). Authors linked through any family work except referee reports.
-- Career age: first non-xpac OpenAlex publication year, all years (docs/DECISIONS.md).
CREATE TABLE author_funnel_${RUN_ID}
WITH (format = 'PARQUET', write_compression = 'ZSTD') AS
WITH elig AS (
  SELECT id AS work_id, publication_year, field_id, domain_id,
         subfield_id IN ('https://openalex.org/subfields/1702', 'https://openalex.org/subfields/1707') AS is_ai
  FROM works_core_r20261106a
  WHERE publication_year BETWEEN 2018 AND 2024 AND NOT is_xpac AND publication_date IS NOT NULL
    AND type IN ('article', 'conference-paper') AND pl_source_type IN ('journal', 'conference', 'book series')
    AND NOT coalesce(is_paratext, false) AND NOT coalesce(is_retracted, false)
),
au_work AS (
  SELECT DISTINCT al.author_id, e.work_id, e.publication_year, e.field_id, e.domain_id, e.is_ai
  FROM elig e JOIN authorship_long_r20261106b al ON al.work_id = e.work_id
  WHERE al.author_id IS NOT NULL
    AND al.publication_year_bin IN ('2018', '2019', '2020', '2021', '2022', '2023', '2024')
),
au_elig AS (
  SELECT author_id,
         count_if(publication_year BETWEEN 2018 AND 2021) AS n_base,
         count_if(publication_year BETWEEN 2018 AND 2022) AS n_2018_22,
         count_if(publication_year BETWEEN 2018 AND 2022 AND is_ai) AS n_ai_2018_22,
         count_if(publication_year IN (2023, 2024)) AS n_elig_2023_24
  FROM au_work GROUP BY 1
  HAVING count_if(publication_year BETWEEN 2018 AND 2021) >= 1
),
au_field AS (
  SELECT author_id, max_by(field_id, n) AS modal_field, max_by(domain_id, n) AS modal_domain
  FROM (SELECT author_id, field_id, arbitrary(domain_id) AS domain_id, count(*) AS n
        FROM au_work WHERE publication_year BETWEEN 2018 AND 2022 GROUP BY 1, 2)
  GROUP BY 1
),
first_year AS (
  SELECT author_id, min(publication_year) AS first_year
  FROM authorship_long_r20261106b
  WHERE author_id IS NOT NULL AND NOT is_xpac AND publication_year IS NOT NULL
  GROUP BY 1
),
fam_lang AS (
  SELECT p.arxiv_id, bool_or(w.language = 'en') AS any_en
  FROM paper_family_r20261106b p JOIN works_core_r20261106a w ON w.id = p.work_id
  WHERE year(p.v1_date) IN (2023, 2024)
  GROUP BY 1
),
arx_fam AS (
  SELECT p.arxiv_id, arbitrary(p.primary_category) AS primary_category,
         coalesce(max(p.authors_count), 0) <= 50 AS small_team,
         NOT regexp_like(lower(arbitrary(a.title)),
           '(^|[^a-z])(survey|review|tutorial|overview|position paper|perspective|primer|lecture notes|erratum|corrigendum|comment on|reply to|response to)([^a-z]|$)') AS research_title
  FROM paper_family_r20261106b p JOIN arxiv_versions_kaggle_v21506946 a ON a.arxiv_id = p.arxiv_id
  WHERE year(p.v1_date) IN (2023, 2024) AND coalesce(p.link_flag, '') <> 'exclude_peer_review'
  GROUP BY 1
),
arx_auth AS (
  SELECT DISTINCT al.author_id, p.arxiv_id
  FROM paper_family_r20261106b p JOIN authorship_long_r20261106b al ON al.work_id = p.work_id
  WHERE year(p.v1_date) IN (2023, 2024) AND coalesce(p.link_flag, '') <> 'exclude_peer_review'
    AND al.author_id IS NOT NULL
),
au_arx AS (
  SELECT x.author_id, count(*) AS n_arxiv_any,
         count_if(f.small_team AND coalesce(l.any_en, false) AND f.research_title) AS n_arxiv_elig,
         array_agg(x.arxiv_id) FILTER (WHERE f.small_team AND coalesce(l.any_en, false) AND f.research_title) AS elig_arxiv_ids
  FROM arx_auth x JOIN arx_fam f ON f.arxiv_id = x.arxiv_id LEFT JOIN fam_lang l ON l.arxiv_id = x.arxiv_id
  GROUP BY 1
),
pre_arx AS (
  SELECT DISTINCT al.author_id
  FROM paper_family_r20261106b p JOIN authorship_long_r20261106b al ON al.work_id = p.work_id
  WHERE year(p.v1_date) BETWEEN 2018 AND 2022 AND p.link_flag IS NULL AND al.author_id IS NOT NULL
)
SELECT e.author_id, au.orcid IS NOT NULL AS has_orcid, au.display_name,
       e.n_base, e.n_2018_22, e.n_ai_2018_22, e.n_elig_2023_24,
       f.modal_field, f.modal_domain, fy.first_year,
       coalesce(x.n_arxiv_any, 0) AS n_arxiv_any, coalesce(x.n_arxiv_elig, 0) AS n_arxiv_elig, x.elig_arxiv_ids,
       pa.author_id IS NOT NULL AS posted_arxiv_2018_22
FROM au_elig e
LEFT JOIN au_field f ON f.author_id = e.author_id
LEFT JOIN first_year fy ON fy.author_id = e.author_id
LEFT JOIN au_arx x ON x.author_id = e.author_id
LEFT JOIN pre_arx pa ON pa.author_id = e.author_id
LEFT JOIN authors au ON au.id = e.author_id
