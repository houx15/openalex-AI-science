-- Phase 0: paper_family title + author fallback, exact-title candidates. Same as
-- sql/audit_title_match_unlinked.sql but for ALL arXiv papers with v1 in 2023-2024 (published
-- families too, to catch extra unlinked versions). Finds OpenAlex works published 2022-2026 with
-- the same normalized title (lowercase, accents folded, only [a-z0-9] kept, >= 25 characters) that
-- are not already in the family. Returns OpenAlex author names so author agreement and precision
-- are checked locally (src/data/paper_family_fallback.py). No outcomes, no scores.
WITH fam AS (
  SELECT arxiv_id, arbitrary(v1_date) AS v1_date, arbitrary(primary_category) AS primary_category,
         bool_or(NOT coalesce(is_arxiv_primary, true) AND NOT coalesce(is_xpac, false) AND link_flag IS NULL) AS published,
         array_agg(work_id) FILTER (WHERE work_id IS NOT NULL) AS family_works
  FROM paper_family_r20261106b
  WHERE year(v1_date) IN (2023, 2024) AND coalesce(link_flag, '') <> 'exclude_peer_review'
  GROUP BY 1
),
ax AS (
  SELECT DISTINCT f.arxiv_id, f.v1_date, f.primary_category, f.published AS family_published, coalesce(f.family_works, ARRAY[]) AS family_works,
         a.title AS arxiv_title, a.authors AS arxiv_authors,
         regexp_replace(lower(normalize(a.title, NFKD)), '[^a-z0-9]', '') AS tkey
  FROM fam f JOIN arxiv_versions_kaggle_v21506946 a ON a.arxiv_id = f.arxiv_id
),
w AS (
  SELECT id AS work_id, title, type, publication_date, publication_year, is_xpac, is_paratext,
         pl_source_id, pl_source_type, pl_source_name, pl_is_published, doi, authors_count,
         any_match(locs, l -> l.is_published AND l.source_type IN ('journal', 'conference')) AS has_published_location,
         cardinality(arxiv_ids) > 0 AS has_arxiv_id,
         regexp_replace(lower(normalize(title, NFKD)), '[^a-z0-9]', '') AS tkey
  FROM works_core_r20261106a
  WHERE publication_year BETWEEN 2022 AND 2026 AND title IS NOT NULL
    AND type NOT IN ('dataset', 'peer-review')
    AND coalesce(pl_source_id, '') <> 'https://openalex.org/S4306400194'
),
pairs AS (
  SELECT ax.arxiv_id, ax.v1_date, ax.primary_category, ax.family_published, ax.arxiv_title, ax.arxiv_authors,
         w.work_id, w.title, w.type, w.publication_date, w.publication_year, w.is_xpac, w.is_paratext,
         w.pl_source_id, w.pl_source_type, w.pl_source_name, w.pl_is_published, w.doi, w.authors_count,
         w.has_published_location, w.has_arxiv_id
  FROM ax JOIN w ON w.tkey = ax.tkey
  WHERE length(ax.tkey) >= 25 AND NOT contains(ax.family_works, w.work_id)
),
names AS (
  SELECT p.arxiv_id, p.work_id, array_join(array_agg(DISTINCT au.display_name), '|') AS oa_authors
  FROM pairs p
  JOIN authorship_long_r20261106b al ON al.work_id = p.work_id
  JOIN authors au ON au.id = al.author_id
  WHERE al.publication_year_bin IN ('2022', '2023', '2024', '2025', '2026')
  GROUP BY 1, 2
),
other_arxiv AS (
  SELECT work_id, array_join(array_agg(DISTINCT arxiv_id), '|') AS linked_arxiv_ids
  FROM paper_family_r20261106b
  WHERE work_id IN (SELECT work_id FROM pairs)
  GROUP BY 1
)
SELECT p.*, n.oa_authors, o.linked_arxiv_ids
FROM pairs p
LEFT JOIN names n ON n.arxiv_id = p.arxiv_id AND n.work_id = p.work_id
LEFT JOIN other_arxiv o ON o.work_id = p.work_id
