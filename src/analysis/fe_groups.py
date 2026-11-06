"""Fixed-effect grouping shared by the Phase 0 simulations.

SPEC §9 specifies field x career bin x half-year fixed effects. With pyfixest 0.60.0 the PPML
demeaning did not converge with that three-way interaction on several samples (10,000-20,000
iterations; 2026-11-06), while additive field x half + career bin x half effects converged in
seconds. The simulations therefore use the additive version (docs/DEVIATIONS.md). The three-way
version is to be re-tested with another PPML implementation before the pre-analysis plan.
Fields with fewer than MIN_AUTHORS authors in the sample use their OpenAlex domain (SPEC §7).
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
PERIOD_FE = "fh + ch"


def field_group(field_by_author, min_authors=MIN_AUTHORS):
    """Map each author's modal field URL to its id, or to 'domain/<id>' when the field is small."""
    fid = field_by_author.fillna("none").astype(str).str.rsplit("/", n=1).str[-1]
    size = fid.map(fid.value_counts())
    domain = "domain/" + fid.map(FIELD_DOMAIN).fillna("none")
    return pd.Series(fid.where(size >= min_authors, domain), index=field_by_author.index)


def add_period_fe(d, min_authors=MIN_AUTHORS):
    """Set d['fh'] = field group x half-year and d['ch'] = career bin x half-year."""
    g = d.author_id.map(field_group(d.groupby("author_id").field.first(), min_authors))
    d["fh"] = g + "|" + d.half.astype(str)
    d["ch"] = d.career + "|" + d.half.astype(str)
    return d
