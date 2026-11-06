-- arXiv metadata with full version history (Kaggle Cornell-University/arxiv, dataset version 21506946,
-- snapshot file dated 2026-11-01). Built by src/data/arxiv_kaggle_to_parquet.py. Timestamps are UTC.
CREATE EXTERNAL TABLE IF NOT EXISTS openalex_2026_10.arxiv_versions_kaggle_v21506946 (
  `arxiv_id` string,
  `oai_datestamp` string,
  `is_deleted` boolean,
  `versions` array<struct<`version`:string,`date`:timestamp,`size`:string,`source_type`:string>>,
  `v1_date` timestamp,
  `n_versions` int,
  `title` string,
  `authors` string,
  `categories` string,
  `primary_category` string,
  `comments` string,
  `journal_ref` string,
  `doi` string,
  `report_no` string,
  `license` string
)
STORED AS PARQUET
LOCATION 's3://oaai-phase0-596131721388/derived/arxiv_versions/source=kaggle_v21506946/'
