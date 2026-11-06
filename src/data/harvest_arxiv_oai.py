"""Harvest arXiv metadata (arXivRaw, full version history) via OAI-PMH into Parquet.

Builds the input for `arxiv_versions` (SPEC §5, §10 Phase 0 task 4). Every page is parsed in
memory and written straight to Parquet; raw XML is never kept. Resumable: the resumption token
and page counter are saved after each written batch, so rerunning the same command continues.

OAI datestamps are last-modified dates, not v1 dates, so the harvest takes the whole archive and
v1 filtering happens downstream. An unfiltered ListRecords times out server-side, so the archive
is walked in contiguous monthly datestamp windows from the repository's earliest datestamp.
A record modified mid-harvest can appear in two windows; downstream dedup keeps the row with the
latest oai_datestamp. The current month is harvested last, so no record is missed.

Usage:
    python -m src.data.harvest_arxiv_oai --out data/raw/arxiv_oai/run=r20261106a [--max-pages N]
"""

import argparse
import json
import shutil
import sys
import time
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import requests
from defusedxml import ElementTree as ET

ENDPOINT = "https://oaipmh.arxiv.org/oai"
USER_AGENT = "openalex-AI-science research harvester (contact: sandyhou661@gmail.com)"
NS = {"oai": "http://www.openarchives.org/OAI/2.0/", "raw": "http://arxiv.org/OAI/arXivRaw/"}
EARLIEST_DATESTAMP = date(2005, 9, 16)  # from verb=Identify, 2026-11-06
PAUSE_SECONDS = 3
PAGES_PER_PART = 20
MAX_OUT_BYTES = 8 * 1024**3  # PI limit: stay well under 10 GB on the Mac

META_SCHEMA = pa.schema([
    ("arxiv_id", pa.string()),
    ("oai_datestamp", pa.string()),
    ("is_deleted", pa.bool_()),
    ("versions", pa.list_(pa.struct([
        ("version", pa.string()),
        ("date", pa.timestamp("s", tz="UTC")),
        ("size", pa.string()),
        ("source_type", pa.string()),
    ]))),
    ("v1_date", pa.timestamp("s", tz="UTC")),
    ("n_versions", pa.int32()),
    ("title", pa.string()),
    ("authors", pa.string()),
    ("categories", pa.string()),
    ("primary_category", pa.string()),
    ("comments", pa.string()),
    ("journal_ref", pa.string()),
    ("doi", pa.string()),
    ("report_no", pa.string()),
    ("license", pa.string()),
])
ABSTRACT_SCHEMA = pa.schema([("arxiv_id", pa.string()), ("abstract", pa.string())])


def text(el, tag):
    child = el.find(f"raw:{tag}", NS)
    return " ".join(child.text.split()) if child is not None and child.text else None


def parse_page(xml_bytes):
    root = ET.fromstring(xml_bytes)
    error = root.find("oai:error", NS)
    if error is not None:
        if error.get("code") == "noRecordsMatch":
            return [], [], None
        raise RuntimeError(f"OAI error {error.get('code')}: {error.text}")
    list_records = root.find("oai:ListRecords", NS)
    meta, abstracts = [], []
    for rec in list_records.findall("oai:record", NS):
        header = rec.find("oai:header", NS)
        identifier = header.find("oai:identifier", NS).text.removeprefix("oai:arXiv.org:")
        datestamp = header.find("oai:datestamp", NS).text
        if header.get("status") == "deleted":
            meta.append({"arxiv_id": identifier, "oai_datestamp": datestamp, "is_deleted": True,
                         "versions": [], "n_versions": 0})
            continue
        raw = rec.find("oai:metadata/raw:arXivRaw", NS)
        versions = []
        for v in raw.findall("raw:version", NS):
            date = v.find("raw:date", NS)
            versions.append({
                "version": v.get("version"),
                "date": parsedate_to_datetime(date.text).astimezone(timezone.utc) if date is not None else None,
                "size": text(v, "size"),
                "source_type": text(v, "source_type"),
            })
        v1 = next((v["date"] for v in versions if v["version"] == "v1"), None)
        categories = text(raw, "categories")
        meta.append({
            "arxiv_id": text(raw, "id") or identifier,
            "oai_datestamp": datestamp,
            "is_deleted": False,
            "versions": versions,
            "v1_date": v1,
            "n_versions": len(versions),
            "title": text(raw, "title"),
            "authors": text(raw, "authors"),
            "categories": categories,
            "primary_category": categories.split()[0] if categories else None,
            "comments": text(raw, "comments"),
            "journal_ref": text(raw, "journal-ref"),
            "doi": text(raw, "doi"),
            "report_no": text(raw, "report-no"),
            "license": text(raw, "license"),
        })
        abstracts.append({"arxiv_id": meta[-1]["arxiv_id"], "abstract": text(raw, "abstract")})
    token_el = list_records.find("oai:resumptionToken", NS)
    token = token_el.text.strip() if token_el is not None and token_el.text and token_el.text.strip() else None
    return meta, abstracts, token


def fetch(session, params, log):
    for attempt in range(8):
        try:
            r = session.get(ENDPOINT, params=params, timeout=300)
        except requests.RequestException as e:
            wait = 30 * (attempt + 1)
            log(f"network error {e!r}; retry in {wait}s")
            time.sleep(wait)
            continue
        if r.status_code == 503:
            wait = int(r.headers.get("Retry-After", 30))
            log(f"503 Retry-After {wait}s")
            time.sleep(wait)
            continue
        r.raise_for_status()
        return r.content
    raise RuntimeError("giving up after repeated failures")


def monthly_windows(start, end):
    """Contiguous [from, until] windows (inclusive days) covering start..end."""
    windows, lo = [], start
    while lo <= end:
        nxt = date(lo.year + (lo.month == 12), lo.month % 12 + 1, 1)
        hi = min(nxt - timedelta(days=1), end)
        windows.append((lo.isoformat(), hi.isoformat()))
        lo = nxt
    return windows


def dir_bytes(path):
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--max-pages", type=int, default=None)
    args = ap.parse_args()

    out = args.out
    (out / "meta").mkdir(parents=True, exist_ok=True)
    (out / "abstracts").mkdir(parents=True, exist_ok=True)
    state_path = out / "state.json"
    log_file = open(out / "harvest.log", "a")

    def log(msg):
        line = f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} {msg}"
        print(line, file=log_file, flush=True)
        print(line, flush=True)

    state = json.loads(state_path.read_text()) if state_path.exists() else {
        "windows": monthly_windows(EARLIEST_DATESTAMP, datetime.now(timezone.utc).date()),
        "window_idx": 0, "token": None, "pages": 0, "parts": 0, "records": 0, "done": False,
        "started": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    if state["done"]:
        log("harvest already complete")
        return

    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    buf_meta, buf_abs, pages_this_run = [], [], 0
    token = state["token"]

    def flush(token_after):
        nonlocal buf_meta, buf_abs
        if buf_meta:
            part = f"part_{state['parts']:05d}.parquet"
            pq.write_table(pa.Table.from_pylist(buf_meta, META_SCHEMA), out / "meta" / part, compression="zstd")
            pq.write_table(pa.Table.from_pylist(buf_abs, ABSTRACT_SCHEMA), out / "abstracts" / part, compression="zstd")
            state["parts"] += 1
            state["records"] += len(buf_meta)
        state["token"] = token_after
        tmp = state_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, indent=1))
        shutil.move(tmp, state_path)
        buf_meta, buf_abs = [], []
        size = dir_bytes(out)
        log(f"pages={state['pages']} records={state['records']} parts={state['parts']} disk={size / 1e9:.2f}GB")
        if size > MAX_OUT_BYTES:
            log("STOP: output exceeds disk limit")
            sys.exit(2)

    while True:
        lo, hi = state["windows"][state["window_idx"]]
        params = {"verb": "ListRecords", "resumptionToken": token} if token else \
                 {"verb": "ListRecords", "metadataPrefix": "arXivRaw", "from": lo, "until": hi}
        meta, abstracts, token = parse_page(fetch(session, params, log))
        buf_meta += meta
        buf_abs += abstracts
        state["pages"] += 1
        pages_this_run += 1
        if token is None:
            log(f"window {lo}..{hi} complete")
            state["window_idx"] += 1
            if state["window_idx"] == len(state["windows"]):
                flush(None)
                state["done"] = True
                state["finished"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
                state_path.write_text(json.dumps(state, indent=1))
                log("harvest complete")
                return
        if pages_this_run % PAGES_PER_PART == 0:
            flush(token)
        if args.max_pages and pages_this_run >= args.max_pages:
            flush(token)
            log("stopped at --max-pages")
            return
        time.sleep(PAUSE_SECONDS)


if __name__ == "__main__":
    main()
