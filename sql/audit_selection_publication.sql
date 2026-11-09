-- Phase 0 audit §4 rerun: selection on publication status with fallback-augmented families.
-- arXiv papers with v1 in 2023-2024. pub0 = published by arXiv-ID/DOI links only (the original
-- §4 definition); pub1 = pub0 or a title + author fallback link (paper_family_fallback_r20261106a).
-- Unit: distinct (paper, OpenAlex author) pairs on the paper's non-xpac family works. Established =
-- author has >= 4 article/conference works in 2018-2021. Metadata only; no outcomes, no scores.
WITH fb AS (SELECT DISTINCT arxiv_id FROM paper_family_fallback_r20261106a),
fam AS (
  SELECT arxiv_id, arbitrary(primary_category) AS primary_category, max(authors_count) AS max_authors,
         bool_or(NOT coalesce(is_arxiv_primary, true) AND NOT coalesce(is_xpac, false) AND link_flag IS NULL) AS pub0
  FROM paper_family_r20261106b
  WHERE year(v1_date) IN (2023, 2024) AND work_id IS NOT NULL AND coalesce(link_flag, '') <> 'exclude_peer_review'
  GROUP BY 1
),
fam2 AS (
  SELECT f.*, f.pub0 OR fb.arxiv_id IS NOT NULL AS pub1,
         split_part(f.primary_category, '.', 1) IN ('cs', 'math', 'stat', 'eess') AS cs_math
  FROM fam f LEFT JOIN fb ON fb.arxiv_id = f.arxiv_id
),
links AS (
  SELECT DISTINCT arxiv_id, work_id FROM paper_family_r20261106b
  WHERE year(v1_date) IN (2023, 2024) AND work_id IS NOT NULL AND NOT coalesce(is_xpac, false) AND link_flag IS NULL
),
pairs AS (
  SELECT l.arxiv_id, a.author_id, bool_or(a.orcid IS NOT NULL) AS has_orcid
  FROM links l JOIN authorship_long_r20261106b a ON a.work_id = l.work_id
  WHERE a.publication_year_bin IN ('2022', '2023', '2024', '2025', '2026') AND NOT a.is_xpac AND a.author_id IS NOT NULL
  GROUP BY 1, 2
),
base AS (
  SELECT author_id FROM authorship_long_r20261106b
  WHERE publication_year_bin IN ('2018', '2019', '2020', '2021') AND NOT is_xpac
    AND type IN ('article', 'conference-paper') AND author_id IS NOT NULL
  GROUP BY 1 HAVING count(*) >= 4
)
SELECT f.pub0, f.pub1, f.cs_math, coalesce(f.max_authors, 0) <= 50 AS small_team, p.has_orcid,
       count(*) AS pairs, count(b.author_id) AS established, count(DISTINCT f.arxiv_id) AS papers
FROM fam2 f
JOIN pairs p ON p.arxiv_id = f.arxiv_id
LEFT JOIN base b ON b.author_id = p.author_id
GROUP BY 1, 2, 3, 4, 5
