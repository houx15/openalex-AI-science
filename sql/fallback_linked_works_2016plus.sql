-- Works published 2016 or later that are already linked (by arXiv ID or DOI) to some arXiv paper.
-- Input to src/data/paper_family_fallback.py: a fuzzy link to such a work is rejected because the
-- work is another paper's published version. No outcomes, no scores.
SELECT work_id, array_join(array_agg(DISTINCT arxiv_id), '|') AS linked_arxiv_ids
FROM paper_family_r20261106b
WHERE work_id IS NOT NULL AND publication_date >= DATE '2016-01-01'
GROUP BY 1
