-- Phase 0 false-positive simulation input: eligible-work counts per pseudo-timeline author and
-- half-year, 2012H1-2020H2 (pseudo-timeline only; nothing dated 2021 or later). n_all counts every
-- eligible work; n_excl drops works whose paper family has arXiv v1 in 2017-2018 (the pseudo
-- exposure-window exclusion; ID/DOI links only, the title fallback covers 2023-24 only).
-- Nonzero cells only; zero-filled locally. No scores.
WITH authors AS (SELECT DISTINCT author_id FROM pseudo_author_papers_r20261106a),
elig AS (
  SELECT id AS work_id, publication_year, publication_date
  FROM works_core_r20261106a
  WHERE publication_year BETWEEN 2012 AND 2020 AND NOT is_xpac AND publication_date IS NOT NULL
    AND type IN ('article', 'conference-paper') AND pl_source_type IN ('journal', 'conference', 'book series')
    AND NOT coalesce(is_paratext, false) AND NOT coalesce(is_retracted, false)
),
exposure_works AS (
  SELECT DISTINCT work_id FROM paper_family_r20261106b
  WHERE year(v1_date) IN (2017, 2018) AND work_id IS NOT NULL AND coalesce(link_flag, '') <> 'exclude_peer_review'
),
aw AS (
  SELECT DISTINCT al.author_id, al.work_id
  FROM authorship_long_r20261106b al JOIN authors a ON a.author_id = al.author_id
  WHERE al.publication_year_bin IN ('2012', '2013', '2014', '2015', '2016', '2017', '2018', '2019', '2020')
)
SELECT aw.author_id,
       e.publication_year * 2 + CASE WHEN CAST(substr(CAST(e.publication_date AS varchar), 6, 2) AS integer) > 6 THEN 1 ELSE 0 END AS half,
       count(*) AS n_all,
       count_if(x.work_id IS NULL) AS n_excl
FROM aw JOIN elig e ON e.work_id = aw.work_id
LEFT JOIN exposure_works x ON x.work_id = aw.work_id
GROUP BY 1, 2
