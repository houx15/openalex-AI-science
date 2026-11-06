-- Phase 0 subset: works_core (SPEC §10 Phase 0 task 4).
-- All works with publication_year >= 2012 (2012-2017 for pseudo-timeline only), all types, xpac kept
-- with its flag so eligibility filters stay in versioned code, not in the extract. Abstracts omitted.
-- Locations reduced to fields needed for type/version/preprint checks; arXiv IDs derived from
-- arXiv landing/pdf URLs and 10.48550 DOIs, for the paper_family crosswalk.
-- ${RUN_ID} is substituted by the runner. Output goes to the workgroup-enforced location
-- s3://oaai-phase0-596131721388/athena-results/tables/<query_id>/ (immutable per query; see cost log).
CREATE TABLE works_core_${RUN_ID}
WITH (
  format = 'PARQUET',
  write_compression = 'ZSTD',
  partitioned_by = ARRAY['publication_year']
) AS
SELECT
  id,
  doi,
  title,
  publication_date,
  language,
  type,
  is_xpac,
  is_paratext,
  is_retracted,
  authors_count,
  ids,
  primary_location.source.id            AS pl_source_id,
  primary_location.source.type          AS pl_source_type,
  primary_location.source.display_name  AS pl_source_name,
  primary_location.raw_type             AS pl_raw_type,
  primary_location.raw_source_name      AS pl_raw_source_name,
  primary_location.version              AS pl_version,
  primary_location.is_published         AS pl_is_published,
  locations_count,
  transform(locations, l -> CAST(ROW(l.source.id, l.source.type, l.version, l.is_published,
                                     l.is_accepted, l.raw_type, l.doi)
    AS ROW(source_id varchar, source_type varchar, version varchar, is_published boolean,
           is_accepted boolean, raw_type varchar, doi varchar)))      AS locs,
  array_distinct(filter(
    transform(locations, l -> coalesce(
      regexp_extract(lower(coalesce(l.landing_page_url, '') || ' ' || coalesce(l.pdf_url, '')),
                     'arxiv\.org/(?:abs|pdf)/([a-z\-]+(?:\.[a-z]{2})?/\d{7}|\d{4}\.\d{4,5})', 1),
      regexp_extract(lower(coalesce(l.doi, '')), '10\.48550/arxiv\.([a-z\-]+(?:\.[a-z]{2})?/\d{7}|\d{4}\.\d{4,5})', 1))),
    x -> x IS NOT NULL))                                             AS arxiv_ids,
  primary_topic.id                      AS topic_id,
  primary_topic.subfield.id             AS subfield_id,
  primary_topic.field.id                AS field_id,
  primary_topic.domain.id               AS domain_id,
  primary_topic.score                   AS topic_score,
  transform(topics, t -> CAST(ROW(t.id, t.subfield.id, t.field.id, t.score)
    AS ROW(topic_id varchar, subfield_id varchar, field_id varchar, score real))) AS topics,
  has_content.pdf                       AS has_content_pdf,
  has_content.grobid_xml                AS has_content_grobid,
  cited_by_count,
  counts_by_year,
  referenced_works_count,
  created_date,
  publication_year
FROM works
WHERE publication_year >= 2012
