CREATE EXTERNAL TABLE IF NOT EXISTS openalex_2026_10.fields (
  `id` string,
  `display_name` string,
  `description` string,
  `ids` struct<`openalex`:string,`wikidata`:string,`wikipedia`:string>,
  `display_name_alternatives` array<string>,
  `domain` struct<`id`:string,`display_name`:string>,
  `subfields` array<struct<`id`:string,`display_name`:string>>,
  `siblings` array<struct<`id`:string,`display_name`:string>>,
  `works_count` int,
  `cited_by_count` int,
  `works_api_url` string,
  `created_date` timestamp
)
PARTITIONED BY (`updated_date` string)
STORED AS PARQUET
LOCATION 's3://openalex/data/parquet/fields/'
