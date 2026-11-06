"""Phase 0: v1 source size for a fixed-seed sample of papers to score (full-text volume estimate).

Reads the main-sample paper list (arxiv_id, selected_k3, ...), draws N selected papers with a fixed
seed, and asks arXiv OAI-PMH (GetRecord, arXivRaw) for each paper's version list. Records v1 size
(arXiv reports the source package size, e.g. "372kb") and source_type when present. One request
every 3 seconds, per arXiv's OAI-PMH guidance. Resumable: already-fetched IDs are skipped.

Usage:
    python -m src.data.sample_arxiv_sizes PAPERS_CSV OUT_CSV [N] [SEED]
"""

import csv
import sys
import time
from pathlib import Path

import pandas as pd
import requests
from defusedxml import ElementTree as ET

URL = "https://oaipmh.arxiv.org/oai"
NS = {"oai": "http://www.openarchives.org/OAI/2.0/", "raw": "http://arxiv.org/OAI/arXivRaw/"}
UNITS = {"kb": 1e3, "mb": 1e6, "gb": 1e9, "b": 1}


def parse_size(s):
    s = (s or "").strip().lower()
    for u in ("kb", "mb", "gb", "b"):
        if s.endswith(u):
            return float(s[: -len(u)]) * UNITS[u]
    return None


def fetch(arxiv_id):
    r = requests.get(URL, params={"verb": "GetRecord", "identifier": f"oai:arXiv.org:{arxiv_id}",
                                  "metadataPrefix": "arXivRaw"}, timeout=60)
    r.raise_for_status()
    root = ET.fromstring(r.content)
    for v in root.iter(f"{{{NS['raw']}}}version"):
        if v.get("version") == "v1":
            return {"v1_size_bytes": parse_size(v.findtext("raw:size", namespaces=NS)),
                    "v1_source_type": v.findtext("raw:source_type", namespaces=NS)}
    return {"v1_size_bytes": None, "v1_source_type": None}


def main(papers_csv, out_csv, n=400, seed=20261106):
    papers = pd.read_csv(papers_csv, dtype=str)
    sample = papers[papers.selected_k3 == "true"].sample(int(n), random_state=int(seed))
    out = Path(out_csv)
    done = set(pd.read_csv(out, dtype=str).arxiv_id) if out.exists() else set()
    with out.open("a", newline="") as f:
        w = csv.DictWriter(f, ["arxiv_id", "primary_category", "v1_size_bytes", "v1_source_type", "error"])
        if not done:
            w.writeheader()
        for row in sample.itertuples():
            if row.arxiv_id in done:
                continue
            try:
                rec = {**fetch(row.arxiv_id), "error": None}
            except Exception as e:  # keep going; failures are reported
                rec = {"v1_size_bytes": None, "v1_source_type": None, "error": type(e).__name__}
            w.writerow({"arxiv_id": row.arxiv_id, "primary_category": row.primary_category, **rec})
            f.flush()
            time.sleep(3)


if __name__ == "__main__":
    main(*sys.argv[1:5])
