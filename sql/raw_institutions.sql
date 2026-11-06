CREATE EXTERNAL TABLE IF NOT EXISTS openalex_2026_10.institutions (
  `id` string,
  `ror` string,
  `display_name` string,
  `country_code` string,
  `type` string,
  `lineage` array<string>,
  `is_super_system` boolean,
  `type_id` string,
  `homepage_url` string,
  `image_url` string,
  `image_thumbnail_url` string,
  `display_name_acronyms` array<string>,
  `display_name_alternatives` array<string>,
  `works_count` int,
  `cited_by_count` int,
  `ids` struct<`openalex`:string,`ror`:string,`grid`:string,`wikipedia`:string,`wikidata`:string>,
  `roles` array<struct<`role`:string,`id`:string,`works_count`:int>>,
  `repositories` array<struct<`id`:string,`display_name`:string,`host_organization`:string,`host_organization_name`:string,`host_organization_lineage`:array<string>>>,
  `geo` struct<`city`:string,`geonames_city_id`:string,`region`:string,`country_code`:string,`country`:string,`latitude`:double,`longitude`:double>,
  `topics` array<struct<`id`:string,`display_name`:string,`count`:int,`score`:float,`subfield`:struct<`id`:string,`display_name`:string>,`field`:struct<`id`:string,`display_name`:string>,`domain`:struct<`id`:string,`display_name`:string>>>,
  `topic_share` array<struct<`id`:string,`display_name`:string,`value`:double,`subfield`:struct<`id`:string,`display_name`:string>,`field`:struct<`id`:string,`display_name`:string>,`domain`:struct<`id`:string,`display_name`:string>>>,
  `associated_institutions` array<struct<`id`:string,`ror`:string,`display_name`:string,`country_code`:string,`type`:string,`relationship`:string>>,
  `counts_by_year` array<struct<`year`:int,`works_count`:int,`oa_works_count`:int,`cited_by_count`:int>>,
  `summary_stats` struct<`2yr_mean_citedness`:double,`h_index`:int,`i10_index`:int>,
  `status` string,
  `works_api_url` string,
  `created_date` timestamp
)
PARTITIONED BY (`updated_date` string)
STORED AS PARQUET
LOCATION 's3://openalex/data/parquet/institutions/'
