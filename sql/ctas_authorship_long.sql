-- Phase 0 subset: authorship_long (SPEC §10 Phase 0 task 4). One row per (work, author).
-- Non-xpac works, ALL years, so author_first_year (career age) can be derived from this table
-- without a second scan of authorships. Interpretation: career age counts non-xpac works only
-- (logged in docs/DECISIONS.md for PI review).
CREATE TABLE authorship_long_${RUN_ID}
WITH (
  format = 'PARQUET',
  write_compression = 'ZSTD',
  partitioned_by = ARRAY['publication_year_bin']
) AS
SELECT
  w.id                                   AS work_id,
  w.publication_date,
  w.publication_year,
  w.type,
  a.author.id                            AS author_id,
  a.author.orcid                         AS orcid,
  a.author_position,
  a.is_corresponding,
  a.countries,
  transform(a.institutions, i -> i.id)   AS institution_ids,
  transform(a.institutions, i -> i.country_code) AS institution_countries,
  CASE WHEN w.publication_year IS NULL THEN 'null'
       WHEN w.publication_year < 2012 THEN 'pre2012'
       ELSE CAST(w.publication_year AS varchar) END AS publication_year_bin
FROM works w
CROSS JOIN UNNEST(w.authorships) AS t(a)
WHERE NOT w.is_xpac
