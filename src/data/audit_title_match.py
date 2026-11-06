"""Phase 0 audit: classify exact-title candidates for unlinked published versions.

Input is the CSV from sql/audit_title_match_unlinked.sql: (arXiv paper with no published work,
OpenAlex work with the same normalized title) pairs. A pair is author-confirmed when at least one
arXiv author name is compatible with an OpenAlex author name (same last name, first names equal
or one an initial of the other; src/data/audit_author_bridge.py). A confirmed pair counts as a
publication when the work is a formal-output type with a published journal/conference location
or a journal/conference primary source.

Usage:
    python -m src.data.audit_title_match PAIRS_CSV OUT_CSV
"""

import sys

import pandas as pd

from src.data.audit_author_bridge import arxiv_author_keys, compatible, name_key

FORMAL_TYPES = {"article", "conference-paper", "book-chapter", "review", "letter", "book"}


def authors_agree(arxiv_authors, oa_authors):
    """True/False when both sides list authors; None when OpenAlex has none."""
    if not isinstance(oa_authors, str) or not oa_authors:
        return None
    ours = arxiv_author_keys(arxiv_authors)
    theirs = [k for k in map(name_key, oa_authors.split("|")) if k]
    return any(compatible(a, b) for a in ours for b in theirs)


def is_publication(row):
    return (row.type in FORMAL_TYPES and not row.is_xpac and not row.is_paratext
            and (row.has_published_location or row.pl_source_type in ("journal", "conference", "book series")))


def main(pairs_csv, out_csv):
    p = pd.read_csv(pairs_csv, dtype=str, keep_default_na=False, na_values=[""])
    for c in ["is_xpac", "is_paratext", "has_published_location", "has_arxiv_id", "pl_is_published"]:
        p[c] = p[c] == "true"
    p["v1_date"] = pd.to_datetime(p.v1_date, utc=True)
    p["publication_date"] = pd.to_datetime(p.publication_date, utc=True, errors="coerce")
    p["v1_year"] = p.v1_date.dt.year
    p["cs_math"] = p.primary_category.str.split(".").str[0].isin(["cs", "math", "stat", "eess"])
    p["authors_agree"] = [authors_agree(a, b) for a, b in zip(p.arxiv_authors, p.oa_authors)]
    p["publication"] = p.apply(is_publication, axis=1)
    p["days_after_v1"] = (p.publication_date - p.v1_date.dt.normalize()).dt.days
    p["n_candidates"] = p.groupby("arxiv_id").work_id.transform("nunique")
    p["linked_to_other_arxiv"] = p.linked_arxiv_ids.notna()
    p.to_csv(out_csv, index=False)

    print(f"{len(p):,} pairs, {p.arxiv_id.nunique():,} arXiv papers")
    print("\nauthors_agree x publication (pairs):")
    print(pd.crosstab(p.authors_agree.astype(str), p.publication, margins=True).to_string())
    print("\ntype x pl_source_type, author-confirmed pairs:")
    ok = p[p.authors_agree == True]  # noqa: E712
    print(ok.groupby(["type", "pl_source_type"], dropna=False).size().sort_values(ascending=False).head(15).to_string())
    hit = ok[ok.publication]
    print(f"\nconfirmed publications: {len(hit):,} pairs, {hit.arxiv_id.nunique():,} arXiv papers")
    print("of which linked to another arXiv ID:", hit.linked_to_other_arxiv.sum(),
          "| work carries an arXiv ID:", hit.has_arxiv_id.sum(),
          "| >1 candidate:", (hit.n_candidates > 1).sum())
    papers = hit.groupby("arxiv_id").agg(v1_year=("v1_year", "first"), cs_math=("cs_math", "first"),
                                         days=("days_after_v1", "min"))
    print("\nconfirmed papers by v1 year x cs_math:")
    print(papers.groupby(["v1_year", "cs_math"]).size().to_string())
    print("\ndays from v1 to publication (quantiles):")
    print(papers.days.quantile([0, .05, .25, .5, .75, .95, 1]).to_string())


if __name__ == "__main__":
    main(*sys.argv[1:3])
