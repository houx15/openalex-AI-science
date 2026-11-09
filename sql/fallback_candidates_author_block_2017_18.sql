-- PSEUDO-TIMELINE COPY (2026-11-09): same query with years shifted -6 (arXiv v1 2017-2018,
-- works published 2016-2020) for the placebo sample. Generated from sql/fallback_candidates_author_block.sql.
-- Phase 0: paper_family title + author fallback, candidate generation (blocking on shared author IDs).
-- For every arXiv paper with v1 in 2023-2024, take the OpenAlex author IDs on its existing family
-- works (families whose works have <= 50 authors), and pair the paper with every other formal-type
-- work published 2022-2026 by any of those authors that is not already in the family. Keep pairs
-- whose titles are similar (token Jaccard >= 0.5 or normalized Levenshtein similarity >= 0.7).
-- Thresholds for accepting a link are set locally after a precision audit
-- (src/data/paper_family_fallback.py). Exact titles without shared author IDs come from
-- sql/fallback_candidates_exact_title.sql. No outcomes, no scores.
WITH fam AS (
  SELECT arxiv_id, arbitrary(v1_date) AS v1_date, arbitrary(primary_category) AS primary_category,
         array_agg(work_id) AS family_works, max(authors_count) AS max_authors,
         bool_or(NOT coalesce(is_arxiv_primary, true) AND NOT coalesce(is_xpac, false) AND link_flag IS NULL) AS published
  FROM paper_family_r20261106b
  WHERE year(v1_date) IN (2017, 2018) AND work_id IS NOT NULL AND coalesce(link_flag, '') <> 'exclude_peer_review'
  GROUP BY 1
),
ax AS (
  SELECT f.arxiv_id, f.v1_date, f.primary_category, f.family_works, f.published,
         arbitrary(a.title) AS arxiv_title
  FROM fam f JOIN arxiv_versions_kaggle_v21506946 a ON a.arxiv_id = f.arxiv_id
  WHERE f.max_authors <= 50
  GROUP BY 1, 2, 3, 4, 5
),
fam_authors AS (
  SELECT DISTINCT ax.arxiv_id, al.author_id
  FROM ax CROSS JOIN UNNEST(ax.family_works) AS t(work_id)
  JOIN authorship_long_r20261106b al ON al.work_id = t.work_id
  WHERE al.author_id IS NOT NULL
    AND al.publication_year_bin IN ('2016', '2017', '2018', '2019', '2020')
),
w AS (
  SELECT id AS work_id, title, type, publication_date, publication_year, is_xpac, is_paratext,
         pl_source_type, pl_source_name, doi, authors_count,
         any_match(locs, l -> l.is_published AND l.source_type IN ('journal', 'conference')) AS has_published_location
  FROM works_core_r20261106a
  WHERE publication_year BETWEEN 2016 AND 2020 AND title IS NOT NULL AND NOT is_xpac
    AND type IN ('article', 'conference-paper', 'book-chapter', 'review', 'letter')
    AND coalesce(pl_source_id, '') <> 'https://openalex.org/S4306400194'
),
cand AS (
  SELECT fa.arxiv_id, al.work_id, count(DISTINCT fa.author_id) AS shared_authors
  FROM fam_authors fa
  JOIN authorship_long_r20261106b al ON al.author_id = fa.author_id
  WHERE al.publication_year_bin IN ('2016', '2017', '2018', '2019', '2020') AND NOT al.is_xpac
    AND al.type IN ('article', 'conference-paper', 'book-chapter', 'review', 'letter')
  GROUP BY 1, 2
),
pairs AS (
  SELECT ax.arxiv_id, ax.v1_date, ax.primary_category, ax.published AS family_published, ax.arxiv_title,
         c.shared_authors, w.*,
         regexp_split(trim(regexp_replace(regexp_replace(lower(normalize(ax.arxiv_title, NFKD)), '[^a-z0-9 ]', ' '), ' +', ' ')), ' ') AS ta,
         regexp_split(trim(regexp_replace(regexp_replace(lower(normalize(w.title, NFKD)), '[^a-z0-9 ]', ' '), ' +', ' ')), ' ') AS tb
  FROM cand c
  JOIN ax ON ax.arxiv_id = c.arxiv_id
  JOIN w ON w.work_id = c.work_id
  WHERE NOT contains(ax.family_works, c.work_id)
),
scored AS (
  SELECT p.*,
         cardinality(array_intersect(array_distinct(ta), array_distinct(tb))) * 1.0
           / cardinality(array_union(array_distinct(ta), array_distinct(tb))) AS jaccard,
         array_join(ta, '') AS ka, array_join(tb, '') AS kb
  FROM pairs p
)
SELECT arxiv_id, v1_date, primary_category, family_published, arxiv_title, shared_authors,
       work_id, title, type, publication_date, publication_year, is_paratext, pl_source_type, pl_source_name,
       doi, authors_count, has_published_location,
       round(jaccard, 4) AS jaccard,
       round(1 - levenshtein_distance(ka, kb) * 1.0 / greatest(length(ka), length(kb), 1), 4) AS lev_sim,
       ka = kb AS exact_title
FROM scored
WHERE jaccard >= 0.5
   OR (jaccard >= 0.3 AND 1 - levenshtein_distance(ka, kb) * 1.0 / greatest(length(ka), length(kb), 1) >= 0.7)
