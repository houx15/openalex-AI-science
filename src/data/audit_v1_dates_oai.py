"""Phase 0 audit: compare Kaggle-snapshot v1 dates with arXiv's own OAI-PMH arXivRaw records.

The study's exposure and calibration windows are defined by v1 submission date (SPEC §5), taken from
the Kaggle arXiv metadata snapshot (data/derived/arxiv_versions). This draws a fixed-seed sample,
stratified by v1 period plus papers within two days of a year boundary, fetches each record from
export.arxiv.org/oai2 (GetRecord, metadataPrefix=arXivRaw) at one request per 3 s, and records the
v1 date and version count from both sources. Metadata only; no text, no outcomes.

Usage:
    python -m src.data.audit_v1_dates_oai META_PARQUET OUT_CSV
"""

import sys
import time
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

import pandas as pd
import requests

SEED = 20261116
STRATA = [("2023-24", "2023-01-01", "2025-01-01", 150), ("2017-18", "2017-01-01", "2019-01-01", 75),
          ("2019-22", "2019-01-01", "2023-01-01", 75)]
N_BOUNDARY = 30
OAI = "https://export.arxiv.org/oai2"
NS = {"o": "http://www.openarchives.org/OAI/2.0/", "r": "http://arxiv.org/OAI/arXivRaw/"}
HEADERS = {"User-Agent": "oaai-research-pilot/0.1 (Princeton research use; one request per 3 s)"}


def sample(meta):
    m = meta[~meta.is_deleted]
    parts = []
    for label, lo, hi, n in STRATA:
        s = m[(m.v1_date >= pd.Timestamp(lo, tz="UTC")) & (m.v1_date < pd.Timestamp(hi, tz="UTC"))]
        parts.append(s.sample(n, random_state=SEED).assign(stratum=label))
    d = m.v1_date
    near = m[((d.dt.month == 12) & (d.dt.day >= 30)) | ((d.dt.month == 1) & (d.dt.day <= 2))]
    near = near[near.v1_date.dt.year.isin([2017, 2018, 2019, 2022, 2023, 2024, 2025])]
    parts.append(near.sample(N_BOUNDARY, random_state=SEED).assign(stratum="year_boundary"))
    return pd.concat(parts)[["arxiv_id", "stratum", "v1_date", "n_versions"]]


def fetch(session, arxiv_id):
    for attempt in range(5):
        r = session.get(OAI, params={"verb": "GetRecord", "identifier": f"oai:arXiv.org:{arxiv_id}",
                                     "metadataPrefix": "arXivRaw"}, timeout=60)
        if r.status_code == 503:  # OAI asks clients to wait (Retry-After)
            time.sleep(int(r.headers.get("Retry-After", 30)))
            continue
        r.raise_for_status()
        root = ET.fromstring(r.content)
        err = root.find("o:error", NS)
        if err is not None:
            return {"oai_status": err.get("code")}
        vs = root.findall(".//r:arXivRaw/r:version", NS)
        dates = {v.get("version"): parsedate_to_datetime(v.findtext("r:date", namespaces=NS)) for v in vs}
        return {"oai_status": "ok", "oai_v1_date": dates.get("v1"), "oai_n_versions": len(vs)}
    return {"oai_status": "gave_up_503"}


def main(meta_parquet, out_csv):
    meta = pd.read_parquet(meta_parquet, columns=["arxiv_id", "is_deleted", "v1_date", "n_versions"])
    s = sample(meta).reset_index(drop=True)
    sess = requests.Session()
    sess.headers.update(HEADERS)
    rows = []
    for i, r in s.iterrows():
        t0 = time.time()
        try:
            rows.append({**r.to_dict(), **fetch(sess, r.arxiv_id)})
        except Exception as e:  # network errors: record and move on
            rows.append({**r.to_dict(), "oai_status": f"error: {type(e).__name__}"})
        if i % 25 == 0:
            print(i, rows[-1], flush=True)
            pd.DataFrame(rows).to_csv(out_csv, index=False)
        time.sleep(max(0, 3 - (time.time() - t0)))
    d = pd.DataFrame(rows)
    d.to_csv(out_csv, index=False)
    ok = d[d.oai_status == "ok"].copy()
    ok["oai_v1_date"] = pd.to_datetime(ok.oai_v1_date, utc=True)
    ok["diff_s"] = (ok.v1_date - ok.oai_v1_date).dt.total_seconds()
    ok["same_year"] = ok.v1_date.dt.year == ok.oai_v1_date.dt.year
    print(d.oai_status.value_counts().to_string())
    print(ok.groupby("stratum").agg(n=("diff_s", "size"), exact=("diff_s", lambda x: (x == 0).sum()),
                                    within_1d=("diff_s", lambda x: (x.abs() <= 86400).sum()),
                                    same_year=("same_year", "sum"),
                                    same_n_versions=("n_versions", lambda x: (x == ok.loc[x.index, "oai_n_versions"]).sum())))


if __name__ == "__main__":
    main(*sys.argv[1:3])
