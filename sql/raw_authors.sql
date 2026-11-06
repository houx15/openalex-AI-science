CREATE EXTERNAL TABLE IF NOT EXISTS openalex_2026_10.authors (
  `id` string,
  `display_name` string,
  `display_name_alternatives` array<string>,
  `raw_author_names` array<string>,
  `full_name` string,
  `orcid` string,
  `observed_orcids` array<string>,
  `works_count` int,
  `cited_by_count` int,
  `summary_stats` struct<`2yr_mean_citedness`:double,`h_index`:int,`i10_index`:int>,
  `ids` struct<`openalex`:string,`orcid`:string,`observed_orcids`:array<string>>,
  `affiliations` array<struct<`institution`:struct<`id`:string,`ror`:string,`display_name`:string,`country_code`:string,`type`:string,`lineage`:array<string>>,`years`:array<int>>>,
  `last_known_institutions` array<struct<`id`:string,`ror`:string,`display_name`:string,`country_code`:string,`type`:string,`lineage`:array<string>>>,
  `topics` array<struct<`id`:string,`display_name`:string,`count`:int,`subfield`:struct<`id`:string,`display_name`:string>,`field`:struct<`id`:string,`display_name`:string>,`domain`:struct<`id`:string,`display_name`:string>>>,
  `topic_share` array<struct<`id`:string,`display_name`:string,`value`:double,`subfield`:struct<`id`:string,`display_name`:string>,`field`:struct<`id`:string,`display_name`:string>,`domain`:struct<`id`:string,`display_name`:string>>>,
  `x_concepts` array<struct<`id`:string,`wikidata`:string,`display_name`:string,`level`:int,`score`:float,`count`:int>>,
  `sources` array<struct<`id`:string,`display_name`:string,`issn_l`:string,`issn`:array<string>,`is_oa`:boolean,`is_in_doaj`:boolean,`is_core`:boolean,`listed_in`:array<string>,`host_organization`:string,`host_organization_name`:string,`host_organization_lineage`:array<string>,`host_organization_lineage_names`:array<string>,`type`:string>>,
  `counts_by_year` array<struct<`year`:int,`works_count`:int,`oa_works_count`:int,`cited_by_count`:int>>,
  `works_api_url` string,
  `created_date` timestamp
)
PARTITIONED BY (`updated_date` string)
STORED AS PARQUET
LOCATION 's3://openalex/data/parquet/authors/'
