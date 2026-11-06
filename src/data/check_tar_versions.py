"""Phase 0: which arXiv version does a bulk source tar hold for each paper?

Reads one arXiv bulk source tar without extracting anything to disk. For each member (one gzip,
tar.gz or PDF per paper) it records the member's mtime and size and the gzip header's mtime, then
compares them with the paper's version dates from arxiv_versions (Kaggle metadata). A member
written after version k's date and before version k+1's date is taken to be version k.

Usage:
    python -m src.data.check_tar_versions TAR META_PARQUET OUT_CSV
"""

import struct
import sys
import tarfile
from datetime import datetime, timezone

import duckdb
import pandas as pd


def gzip_mtime(head):
    if head[:2] != b"\x1f\x8b":
        return None
    t = struct.unpack("<I", head[4:8])[0]
    return datetime.fromtimestamp(t, tz=timezone.utc) if t else None


def main(tar_path, meta_parquet, out_csv):
    rows = []
    with tarfile.open(tar_path) as tf:
        for m in tf:
            if not m.isfile():
                continue
            name = m.name.rsplit("/", 1)[-1]
            arxiv_id = name.rsplit(".", 1)[0] if name.endswith((".gz", ".pdf")) else name
            head = tf.extractfile(m).read(10)
            rows.append({"arxiv_id": arxiv_id, "member": name, "bytes": m.size,
                         "tar_mtime": datetime.fromtimestamp(m.mtime, tz=timezone.utc),
                         "gzip_mtime": gzip_mtime(head), "is_pdf": head[:4] == b"%PDF"})
    t = pd.DataFrame(rows)
    ids = ",".join(f"'{i}'" for i in t.arxiv_id)
    v = duckdb.sql(f"""
        SELECT arxiv_id, n_versions, list_transform(versions, x -> x.date) AS dates
        FROM read_parquet('{meta_parquet}') WHERE arxiv_id IN ({ids})""").df()
    t = t.merge(v, on="arxiv_id", how="left")

    def version_at(row):
        stamp = row.gzip_mtime if pd.notna(row.gzip_mtime) else row.tar_mtime
        dates = sorted(pd.Timestamp(d).tz_localize("UTC") if pd.Timestamp(d).tzinfo is None else pd.Timestamp(d) for d in row.dates)
        stamp = pd.Timestamp(stamp)
        k = sum(d <= stamp + pd.Timedelta(hours=12) for d in dates)
        return max(k, 1)

    t["version_in_tar"] = t.apply(version_at, axis=1)
    t["is_v1"] = t.version_in_tar == 1
    t.drop(columns="dates").to_csv(out_csv, index=False)
    print(f"{len(t)} members; pdf-only {t.is_pdf.sum()}; papers with >1 version {(t.n_versions > 1).sum()}")
    print("version in tar:", t.version_in_tar.value_counts().sort_index().to_dict())
    multi = t[t.n_versions > 1]
    print(f"among multi-version papers: v1 in tar {multi.is_v1.mean():.1%}, latest in tar "
          f"{(multi.version_in_tar == multi.n_versions).mean():.1%}")
    print("tar_mtime range:", t.tar_mtime.min(), "->", t.tar_mtime.max())


if __name__ == "__main__":
    main(*sys.argv[1:4])
