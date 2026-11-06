"""paper_family title + author fallback (SPEC §7): accept extra arXiv -> OpenAlex links.

Inputs (arXiv v1 2023-2024; works published 2022-2026; works already in the family excluded):
  author-block candidates  sql/fallback_candidates_author_block.sql  (shared OpenAlex author IDs)
  exact-title candidates   sql/fallback_candidates_exact_title.sql   (any authors; names checked here)
  linked works             works 2022+ already linked to some arXiv paper (to reject a work that is
                           another paper's published version)

Accept rules [PROPOSED; precision audit in reports/phase0_data_audit.md §7]:
  title_exact_id   exact normalized title and >= 1 shared author ID
  title_exact_name exact normalized title, compatible author names, formal-output work
  title_fuzzy_id   >= 1 shared author ID, work not linked to another arXiv paper, published no more
                   than 365 days before v1, and either Levenshtein similarity >= 0.9, or token
                   Jaccard >= 0.8 with the pair being each side's best candidate

Usage:
    python -m src.data.paper_family_fallback AUTHOR_BLOCK_CSV EXACT_TITLE_CSV LINKED_WORKS_CSV OUT_DIR
"""

import sys
from pathlib import Path

import pandas as pd

from src.data.audit_title_match import authors_agree, is_publication

COLS = ["arxiv_id", "work_id", "method", "jaccard", "lev_sim", "shared_authors", "v1_date",
        "publication_date", "type", "pl_source_type", "family_published"]


def accept_author_block(b, linked):
    b = b.copy()
    b["linked_elsewhere"] = b.work_id.isin(linked)
    b["days_after_v1"] = (pd.to_datetime(b.publication_date, utc=True)
                          - pd.to_datetime(b.v1_date, utc=True).dt.normalize()).dt.days
    b["score"] = b.jaccard + b.lev_sim
    b["best_for_arxiv"] = b.score == b.groupby("arxiv_id").score.transform("max")
    b["best_for_work"] = b.score == b.groupby("work_id").score.transform("max")
    fuzzy = (~b.exact_title & ~b.linked_elsewhere & (b.days_after_v1 >= -365)
             & ((b.lev_sim >= 0.9) | ((b.jaccard >= 0.8) & b.best_for_arxiv & b.best_for_work)))
    b["method"] = None
    b.loc[b.exact_title, "method"] = "title_exact_id"
    b.loc[fuzzy, "method"] = "title_fuzzy_id"
    return b


def accept_exact_name(e):
    e = e.copy()
    for c in ["is_xpac", "is_paratext", "has_published_location"]:
        e[c] = e[c] == "true"
    e["agree"] = [authors_agree(a, n) for a, n in zip(e.arxiv_authors, e.oa_authors)]
    e["publication"] = e.apply(is_publication, axis=1)
    e = e[(e.agree == True) & e.publication].copy()  # noqa: E712
    e["method"] = "title_exact_name"
    e["jaccard"], e["lev_sim"], e["shared_authors"] = 1.0, 1.0, None
    e["family_published"] = e.family_published == "true"
    return e


def main(author_block_csv, exact_csv, linked_csv, out_dir):
    b = pd.read_csv(author_block_csv, dtype={"arxiv_id": str})
    e = pd.read_csv(exact_csv, dtype=str, keep_default_na=False, na_values=[""])
    linked = set(pd.read_csv(linked_csv, dtype=str).work_id)

    b = accept_author_block(b, linked)
    ids = b[b.method.notna()][COLS]
    names = accept_exact_name(e)[COLS]
    links = pd.concat([ids, names]).sort_values("method", key=lambda m: m.map(
        {"title_exact_id": 0, "title_exact_name": 1, "title_fuzzy_id": 2}))
    links = links.drop_duplicates(["arxiv_id", "work_id"]).reset_index(drop=True)

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    links.to_parquet(out / "links.parquet", index=False)
    b.to_csv(out / "author_block_decisions.csv", index=False)

    print(f"{len(links):,} links, {links.arxiv_id.nunique():,} arXiv papers, {links.work_id.nunique():,} works")
    print(links.groupby(["method", "family_published"]).agg(links=("work_id", "size"),
                                                         papers=("arxiv_id", "nunique")).to_string())
    print("\nworks linked to >1 arXiv paper by the fallback:", (links.groupby("work_id").arxiv_id.nunique() > 1).sum())


if __name__ == "__main__":
    main(*sys.argv[1:5])
