"""Fixed-effect grouping shared by the Phase 0 simulations.

SPEC §7: use the OpenAlex domain when a field is too small. Fields with fewer than MIN_AUTHORS
authors in the estimation sample are replaced by their domain, so field x career x half cells are
not tiny (tiny cells made the PPML demeaning fail to converge on subsamples).
"""

import pandas as pd

MIN_AUTHORS = 500
# OpenAlex field id -> domain id (1 Life, 2 Social, 3 Physical, 4 Health Sciences)
FIELD_DOMAIN = {f: d for d, fs in {
    "1": ["11", "13", "24", "28", "30"],
    "2": ["12", "14", "18", "20", "32", "33"],
    "3": ["15", "16", "17", "19", "21", "22", "23", "25", "26", "31"],
    "4": ["27", "29", "34", "35", "36"],
}.items() for f in fs}


def field_group(field_by_author, min_authors=MIN_AUTHORS):
    """Map each author's modal field URL to itself, or to 'domain/<id>' when the field is small."""
    fid = field_by_author.fillna("none").astype(str).str.rsplit("/", n=1).str[-1]
    size = fid.map(fid.value_counts())
    domain = "domain/" + fid.map(FIELD_DOMAIN).fillna("none")
    return pd.Series(fid.where(size >= min_authors, domain), index=field_by_author.index)


def add_fch(d, min_authors=MIN_AUTHORS):
    """Set d['fch'] = field group x career bin x half-year, with field groups from this sample."""
    g = field_group(d.groupby("author_id").field.first(), min_authors)
    d["fch"] = d.author_id.map(g) + "|" + d.career + "|" + d.half.astype(str)
    return d
