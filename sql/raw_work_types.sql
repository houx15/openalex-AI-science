CREATE EXTERNAL TABLE IF NOT EXISTS openalex_2026_10.work_types (
  `id` string,
  `works_api_url` string,
  `display_name` string,
  `description` string,
  `works_count` bigint,
  `cited_by_count` bigint,
  `created_date` timestamp
)
PARTITIONED BY (`updated_date` string)
STORED AS PARQUET
LOCATION 's3://openalex/data/parquet/work-types/'
