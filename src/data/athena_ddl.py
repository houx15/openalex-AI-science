"""Generate Athena (Hive) DDL for OpenAlex snapshot tables from a Parquet file's schema.

Deriving the DDL from the files themselves keeps column types exact; hand-written
nested struct types drift from the snapshot.

Usage:
    python -m src.data.athena_ddl works s3://openalex/data/parquet/works/updated_date=.../part_0000.parquet
"""

import sys

import pyarrow as pa
import pyarrow.parquet as pq
from pyarrow import fs

import yaml

PARTITION_COL = "updated_date"


def hive_type(t: pa.DataType) -> str:
    if pa.types.is_string(t) or pa.types.is_large_string(t):
        return "string"
    if pa.types.is_boolean(t):
        return "boolean"
    if pa.types.is_int8(t) or pa.types.is_int16(t) or pa.types.is_int32(t):
        return "int"
    if pa.types.is_int64(t):
        return "bigint"
    if pa.types.is_float32(t):
        return "float"
    if pa.types.is_float64(t):
        return "double"
    if pa.types.is_date32(t) or pa.types.is_date64(t):
        return "date"
    if pa.types.is_timestamp(t):
        return "timestamp"
    if pa.types.is_list(t) or pa.types.is_large_list(t):
        return f"array<{hive_type(t.value_type)}>"
    if pa.types.is_map(t):
        return f"map<{hive_type(t.key_type)},{hive_type(t.item_type)}>"
    if pa.types.is_struct(t):
        fields = ",".join(f"`{f.name}`:{hive_type(f.type)}" for f in t)
        return f"struct<{fields}>"
    raise TypeError(f"unhandled Arrow type: {t}")


def read_schema(s3_url: str) -> pa.Schema:
    s3 = fs.S3FileSystem(anonymous=True, region="us-east-1")
    return pq.read_schema(s3_url.removeprefix("s3://"), filesystem=s3)


def create_table_sql(entity: str, schema: pa.Schema, database: str) -> str:
    cols = ",\n".join(
        f"  `{f.name}` {hive_type(f.type)}" for f in schema if f.name != PARTITION_COL
    )
    table = entity.replace("-", "_")
    return (
        f"CREATE EXTERNAL TABLE IF NOT EXISTS {database}.{table} (\n{cols}\n)\n"
        f"PARTITIONED BY (`{PARTITION_COL}` string)\n"
        f"STORED AS PARQUET\n"
        f"LOCATION 's3://openalex/data/parquet/{entity}/'\n"
    )


def main(entity: str, sample_url: str) -> None:
    with open("config/project.yml") as f:
        database = yaml.safe_load(f)["aws"]["glue_database"]
    print(create_table_sql(entity, read_schema(sample_url), database))


if __name__ == "__main__":
    main(*sys.argv[1:3])
