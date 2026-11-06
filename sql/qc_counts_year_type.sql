-- Phase 0 QC: reconcile works row counts with manifest.json (464,765,485 records) and
-- profile publication_year x type x is_xpac. Reads only small scalar columns.
SELECT publication_year, type, is_xpac, count(*) AS n
FROM works
GROUP BY 1, 2, 3
