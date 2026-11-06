"""Phase 0 audit: author bridge between arXiv papers and OpenAlex author profiles.

For each sampled author (sql/audit_author_bridge_sample.sql), find their 2023-24 arXiv papers
independently of OpenAlex attribution: the paper lists a name compatible with the author's AND
names compatible with their 2018-2022 coauthors (one full-first-name match, or two matches of
any kind). Names are compatible when last names agree and first names agree, or one is an
initial of the other. Then measure the share of those papers OpenAlex attributes to the
author's profile, by publication status.

Usage:
    python -m src.data.audit_author_bridge SAMPLE_CSV PUBLISHED_CSV ARXIV_META_PARQUET OUT_CSV
"""

import re
import sys
import unicodedata

import duckdb
import pandas as pd

PAREN = re.compile(r"\([^)]*\)")
SPLIT = re.compile(r",|\band\b|;")


def name_key(name):
    """(last name, first name or initial) with accents, punctuation and case removed; None if unusable."""
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"['’`]", "", s)
    tokens = re.sub(r"[^a-z\s-]", " ", s).split()
    if len(tokens) < 2:
        return None
    return tokens[-1], tokens[0]


def compatible(a, b):
    if a[0] != b[0]:
        return False
    fa, fb = a[1], b[1]
    if len(fa) > 1 and len(fb) > 1:
        return fa == fb
    return fa[0] == fb[0]


def is_full(key):
    return len(key[1]) > 1


def confirm(paper_keys, own, co):
    """Return (author on paper?, n full-name coauthor matches, n coauthor matches)."""
    me = [k for k in paper_keys if any(compatible(k, o) for o in own)]
    if not me:
        return False, 0, 0
    others = [k for k in paper_keys if k not in me]
    hits = [k for k in others if any(compatible(k, c) for c in co.get(k[0], ()))]
    full = [k for k in hits if is_full(k) and any(compatible(k, c) and is_full(c) for c in co.get(k[0], ()))]
    return True, len(set(full)), len(set(hits))


def arxiv_author_keys(authors):
    names = SPLIT.split(PAREN.sub(" ", authors or ""))
    return [k for k in (name_key(n) for n in names if n.strip()) if k]


def author_keys(row):
    names = [row.display_name] + (row.name_alternatives.split("|") if isinstance(row.name_alternatives, str) else [])
    return {k for k in map(name_key, names) if k}


def main(sample_csv, published_csv, meta_parquet, out_csv):
    sample = pd.read_csv(sample_csv, dtype=str)
    sample["has_orcid"] = sample.has_orcid == "true"
    sample["cs_math_major"] = sample.cs_math_major == "true"
    pub = pd.read_csv(published_csv, dtype=str)
    published = dict(zip(pub.arxiv_id, pub.published == "true"))
    papers = duckdb.sql(f"""
        SELECT arxiv_id, authors FROM read_parquet('{meta_parquet}')
        WHERE v1_date >= TIMESTAMPTZ '2023-01-01 00:00:00+00' AND v1_date < TIMESTAMPTZ '2025-01-01 00:00:00+00'
    """).df()
    papers["keys"] = papers.authors.map(arxiv_author_keys)

    # index papers by last name for speed
    by_last = {}
    for i, keys in enumerate(papers["keys"]):
        for k in set(keys):
            by_last.setdefault(k[0], []).append(i)

    rows = []
    for a in sample.itertuples():
        own = author_keys(a)
        co = {}
        for k in map(name_key, str(a.coauthor_names).split("|")):
            if k and not any(compatible(k, o) for o in own):
                co.setdefault(k[0], set()).add(k)
        attributed = set(str(a.attributed_arxiv_ids).split("|")) if isinstance(a.attributed_arxiv_ids, str) else set()
        candidates = {i for k in own for i in by_last.get(k[0], [])}
        for i in candidates:
            keys = papers.at[i, "keys"]
            on_paper, n_full, n_co = confirm(keys, own, co)
            if not on_paper or not (n_full >= 1 or n_co >= 2):
                continue
            arxiv_id = papers.at[i, "arxiv_id"]
            rows.append({
                "author_id": a.author_id, "display_name": a.display_name, "has_orcid": a.has_orcid,
                "cs_math_major": a.cs_math_major, "arxiv_id": arxiv_id, "n_coauthor_matches": n_co, "n_full_matches": n_full,
                "n_authors": len(keys), "published": published.get(arxiv_id),
                "attributed": arxiv_id in attributed, "arxiv_authors": papers.at[i, "authors"],
            })
        # attributed papers the matcher did not find (for the record)
        found = {r["arxiv_id"] for r in rows if r["author_id"] == a.author_id}
        for arxiv_id in attributed - found:
            rows.append({
                "author_id": a.author_id, "display_name": a.display_name, "has_orcid": a.has_orcid,
                "cs_math_major": a.cs_math_major, "arxiv_id": arxiv_id, "n_coauthor_matches": 0, "n_full_matches": 0,
                "n_authors": None, "published": published.get(arxiv_id), "attributed": True,
                "arxiv_authors": None,
            })
    out = pd.DataFrame(rows)
    out.to_csv(out_csv, index=False)
    m = out[out.n_coauthor_matches > 0]
    print(f"{sample.author_id.nunique()} authors; {len(m)} matcher-confirmed (author, paper) pairs")
    print(m.groupby(["has_orcid", "published"]).attributed.agg(["size", "mean"]).round(3).to_string())


if __name__ == "__main__":
    main(*sys.argv[1:5])
