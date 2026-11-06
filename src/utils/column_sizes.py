"""Sum compressed bytes per Parquet leaf column across every file of a snapshot entity.

Athena bills on bytes scanned, and Parquet lets it read only the leaf columns a
query touches, so these totals give a pre-query cost estimate (SPEC §4, §10 Phase 0).

Usage:
    python -m src.utils.column_sizes works reports/phase0/works_column_sizes.csv
"""

import csv
import json
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

import pyarrow.parquet as pq
from pyarrow import fs

S3 = fs.S3FileSystem(anonymous=True, region="us-east-1")
MANIFEST = "openalex/data/parquet/manifest.json"


def entity_files(entity: str) -> list[str]:
    with S3.open_input_stream(MANIFEST) as f:
        manifest = json.load(f)
    (ent,) = [e for e in manifest["entities"] if e["entity"] == entity]
    return [x["url"].removeprefix("s3://") for x in ent["files"]]


def leaf_sizes(path: str) -> dict[str, int]:
    md = pq.ParquetFile(path, filesystem=S3).metadata
    sizes = defaultdict(int)
    for rg in range(md.num_row_groups):
        row_group = md.row_group(rg)
        for c in range(row_group.num_columns):
            col = row_group.column(c)
            sizes[col.path_in_schema] += col.total_compressed_size
    return sizes


def main(entity: str, out_path: str) -> None:
    files = entity_files(entity)
    totals = defaultdict(int)
    with ThreadPoolExecutor(max_workers=32) as pool:
        for sizes in pool.map(leaf_sizes, files):
            for k, v in sizes.items():
                totals[k] += v
    with open(out_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["leaf_column", "compressed_bytes"])
        for k, v in sorted(totals.items(), key=lambda kv: -kv[1]):
            w.writerow([k, v])
    print(f"{len(files)} files, {sum(totals.values()) / 1e9:.1f} GB total -> {out_path}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
