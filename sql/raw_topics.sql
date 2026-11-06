CREATE EXTERNAL TABLE IF NOT EXISTS openalex_2026_10.topics (
  `id` string,
  `display_name` string,
  `description` string,
  `keywords` array<struct<`id`:string,`display_name`:string,`score`:double>>,
  `legacy_keywords` string,
  `ids` struct<`openalex`:string,`wikipedia`:string>,
  `subfield` struct<`id`:string,`display_name`:string>,
  `field` struct<`id`:string,`display_name`:string>,
  `domain` struct<`id`:string,`display_name`:string>,
  `siblings` array<struct<`id`:string,`display_name`:string>>,
  `works_count` int,
  `cited_by_count` int,
  `works_api_url` string,
  `created_date` timestamp
)
PARTITIONED BY (`updated_date` string)
STORED AS PARQUET
LOCATION 's3://openalex/data/parquet/topics/'
