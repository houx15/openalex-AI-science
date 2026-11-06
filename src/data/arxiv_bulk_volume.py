"""Phase 0: arXiv full-text volume, bulk (S3 tars) vs per-paper.

Summarizes the arXiv requester-pays bulk manifests (src and pdf tars, one entry per tar with
yymm, item count and bytes) for the month ranges each analysis needs, and the per-paper v1 source
sizes sampled by src/data/sample_arxiv_sizes.py.

Usage:
    python -m src.data.arxiv_bulk_volume SRC_MANIFEST PDF_MANIFEST SIZE_SAMPLE_CSV
"""

import sys

import pandas as pd
from defusedxml import ElementTree as ET

WINDOWS = {
    "main exposure 2023-01..2024-12": ("2301", "2412"),
    "calibration 2019-01..2022-10": ("1901", "2210"),
    "placebo 2017-01..2018-12": ("1701", "1812"),
}


def read_manifest(path):
    root = ET.parse(path).getroot()
    rows = [{c.tag: c.text for c in f} for f in root.iter("file")]
    m = pd.DataFrame(rows)
    m["size"] = m["size"].astype(int)
    m["num_items"] = m["num_items"].astype(int)
    return m


def summarize(m, label):
    out = []
    for name, (lo, hi) in WINDOWS.items():
        w = m[(m.yymm >= lo) & (m.yymm <= hi)]
        out.append({"kind": label, "window": name, "tars": len(w), "items": w.num_items.sum(),
                    "GB": round(w["size"].sum() / 1e9, 1),
                    "MB_per_item": round(w["size"].sum() / max(w.num_items.sum(), 1) / 1e6, 2)})
    return out


def main(src_manifest, pdf_manifest, size_csv):
    rows = summarize(read_manifest(src_manifest), "src") + summarize(read_manifest(pdf_manifest), "pdf")
    print(pd.DataFrame(rows).to_string(index=False))
    s = pd.read_csv(size_csv, dtype={"arxiv_id": str})
    ok = s[s.v1_size_bytes.notna()]
    print(f"\nper-paper v1 source size: n={len(ok)} of {len(s)} sampled")
    print((ok.v1_size_bytes / 1e6).describe(percentiles=[.25, .5, .75, .9, .99]).round(2).to_string())
    print("by source:", ok.source.value_counts().to_dict())


if __name__ == "__main__":
    main(*sys.argv[1:4])
