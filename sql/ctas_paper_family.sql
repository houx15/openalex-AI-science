-- Phase 0: paper_family crosswalk, arXiv paper -> OpenAlex work(s) (SPEC §7 "Important checks").
-- One row per (arxiv_id, work_id) link, plus one row with work_id NULL for every arXiv paper that
-- matched nothing, so match rates come straight from this table.
-- Match methods, in priority order:
--   arxiv_id : the work's locations or DOI carry the arXiv ID (arXiv URL or 10.48550 DOI)
--   doi      : a DOI listed on the arXiv record equals the work's DOI
-- A title/author/date fallback is a later step, run only on arXiv papers unmatched here.
-- link_flag (audit 2026-11-06, reports/phase0/crosswalk_audit_sample.csv):
--   exclude_peer_review : SciPost-style referee reports carry the arXiv ID but are not the paper;
--                         drop from families
--   published_before_v1 : work published 2+ years before the arXiv v1; the link is correct (an old
--                         paper posted late) but the text predates the v1 date (exposure question
--                         for the PI at the Phase 0 gate)
-- Old-style IDs are normalized by dropping the subject class ("math.ag/0101001" -> "math/0101001").
CREATE TABLE paper_family_${RUN_ID}
WITH (format = 'PARQUET', write_compression = 'ZSTD') AS
WITH arxiv AS (
  SELECT arxiv_id, v1_date, primary_category, n_versions, doi AS arxiv_doi_raw, journal_ref
  FROM arxiv_versions_kaggle_v21506946
),
w AS (
  SELECT id AS work_id,
         lower(regexp_replace(doi, '^https://doi\.org/', '')) AS work_doi,
         arxiv_ids, type, is_xpac, is_paratext, is_retracted, pl_source_id, pl_source_type,
         pl_is_published, publication_date, publication_year, field_id, domain_id, authors_count,
         any_match(locs, l -> l.is_published AND l.source_type IN ('journal', 'conference')) AS has_published_location
  FROM works_core_${WORKS_RUN_ID}
),
by_id AS (
  SELECT DISTINCT regexp_replace(x, '^([a-z\-]+)\.[a-z]{2}/', '$1/') AS arxiv_id, work_id, 'arxiv_id' AS method
  FROM w CROSS JOIN UNNEST(arxiv_ids) AS t(x)
  WHERE cardinality(arxiv_ids) > 0
),
arxiv_doi AS (
  SELECT DISTINCT arxiv_id, lower(d) AS doi
  FROM arxiv CROSS JOIN UNNEST(split(trim(arxiv_doi_raw), ' ')) AS t(d)
  WHERE arxiv_doi_raw IS NOT NULL AND d <> ''
),
by_doi AS (
  SELECT DISTINCT a.arxiv_id, w.work_id, 'doi' AS method
  FROM arxiv_doi a JOIN w ON w.work_doi = a.doi
),
links AS (
  SELECT arxiv_id, work_id, array_sort(array_agg(DISTINCT method)) AS methods
  FROM (SELECT * FROM by_id UNION ALL SELECT * FROM by_doi)
  GROUP BY 1, 2
)
SELECT
  a.arxiv_id, a.v1_date, a.primary_category, a.n_versions, a.journal_ref,
  l.work_id, l.methods,
  w.work_doi, w.type, w.is_xpac, w.is_paratext, w.is_retracted,
  w.pl_source_id, w.pl_source_type, w.pl_is_published, w.has_published_location,
  w.pl_source_id = 'https://openalex.org/S4306400194' AS is_arxiv_primary,
  w.publication_date, w.publication_year, w.field_id, w.domain_id, w.authors_count,
  CASE WHEN w.type = 'peer-review' THEN 'exclude_peer_review'
       WHEN w.publication_year < year(a.v1_date) - 1 THEN 'published_before_v1'
  END AS link_flag
FROM arxiv a
LEFT JOIN links l ON l.arxiv_id = a.arxiv_id
LEFT JOIN w ON w.work_id = l.work_id
