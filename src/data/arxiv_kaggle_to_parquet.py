"""Convert the Kaggle arXiv metadata snapshot (Cornell-University/arxiv) to Parquet.

Streams the JSON-lines member straight out of the zip, so the ~4.5 GB uncompressed file never
touches disk. Output uses the same schema as the OAI-PMH harvester (src/data/harvest_arxiv_oai.py)
so the two sources can be compared record by record. The Kaggle snapshot has no per-version size
or source_type, and its update_date stands in for the OAI datestamp.

Usage:
    python -m src.data.arxiv_kaggle_to_parquet data/raw/arxiv_kaggle/v21506946/archive.zip \
        data/derived/arxiv_versions/source=kaggle_v21506946
"""

import json
import sys
import zipfile
from datetime import timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from src.data.harvest_arxiv_oai import ABSTRACT_SCHEMA, META_SCHEMA

BATCH = 200_000


def clean(s):
    return " ".join(s.split()) if s else None


def convert(rec):
    versions = [{
        "version": v.get("version"),
        "date": parsedate_to_datetime(v["created"]).astimezone(timezone.utc) if v.get("created") else None,
        "size": None,
        "source_type": None,
    } for v in rec.get("versions") or []]
    categories = clean(rec.get("categories"))
    meta = {
        "arxiv_id": rec["id"],
        "oai_datestamp": rec.get("update_date"),
        "is_deleted": False,
        "versions": versions,
        "v1_date": next((v["date"] for v in versions if v["version"] == "v1"), None),
        "n_versions": len(versions),
        "title": clean(rec.get("title")),
        "authors": clean(rec.get("authors")),
        "categories": categories,
        "primary_category": categories.split()[0] if categories else None,
        "comments": clean(rec.get("comments")),
        "journal_ref": clean(rec.get("journal-ref")),
        "doi": clean(rec.get("doi")),
        "report_no": clean(rec.get("report-no")),
        "license": clean(rec.get("license")),
    }
    return meta, {"arxiv_id": rec["id"], "abstract": clean(rec.get("abstract"))}


def main(zip_path, out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        (member,) = [n for n in zf.namelist() if n.endswith(".json")]
        meta_writer = pq.ParquetWriter(out / "meta.parquet", META_SCHEMA, compression="zstd")
        abs_writer = pq.ParquetWriter(out / "abstracts.parquet", ABSTRACT_SCHEMA, compression="zstd")
        buf_meta, buf_abs, n = [], [], 0
        with zf.open(member) as f:
            for line in f:
                m, a = convert(json.loads(line))
                buf_meta.append(m)
                buf_abs.append(a)
                if len(buf_meta) == BATCH:
                    meta_writer.write_table(pa.Table.from_pylist(buf_meta, META_SCHEMA))
                    abs_writer.write_table(pa.Table.from_pylist(buf_abs, ABSTRACT_SCHEMA))
                    n += len(buf_meta)
                    buf_meta, buf_abs = [], []
                    print(f"{n:,} records", flush=True)
        if buf_meta:
            meta_writer.write_table(pa.Table.from_pylist(buf_meta, META_SCHEMA))
            abs_writer.write_table(pa.Table.from_pylist(buf_abs, ABSTRACT_SCHEMA))
            n += len(buf_meta)
        meta_writer.close()
        abs_writer.close()
    print(f"done: {n:,} records from {member} -> {out}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
