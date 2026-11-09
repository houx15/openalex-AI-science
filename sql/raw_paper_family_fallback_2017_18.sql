-- paper_family title + author fallback links (arXiv v1 2017-2018, pseudo-timeline), built by
-- src/data/paper_family_fallback.py from sql/fallback_candidates_author_block_2017_18.sql and
-- sql/fallback_candidates_exact_title_2017_18.sql. One row per extra (arxiv_id, work_id) link not found by
-- arXiv ID or DOI. Production families = paper_family_r20261106b UNION these links.
CREATE EXTERNAL TABLE IF NOT EXISTS openalex_2026_10.paper_family_fallback_2017_18_r20261109a (
  `arxiv_id` string,
  `work_id` string,
  `method` string,
  `jaccard` double,
  `lev_sim` double,
  `shared_authors` double,
  `v1_date` string,
  `publication_date` string,
  `type` string,
  `pl_source_type` string,
  `family_published` boolean
)
STORED AS PARQUET
LOCATION 's3://oaai-phase0-596131721388/derived/paper_family_fallback_2017_18/run=r20261109a/'
