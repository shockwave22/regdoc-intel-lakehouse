from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql import types as T

BRONZE_COLUMNS = [
    "document_id",
    "source_path",
    "file_name",
    "file_extension",
    "ingest_ts",
    "file_size_bytes",
    "source_system",
    "checksum",
    "content_path",
]


def _compute_sha256(file_path: Path) -> str:
    hasher = hashlib.sha256()
    with file_path.open("rb") as file_obj:
        for chunk in iter(lambda: file_obj.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _metadata_schema() -> T.StructType:
    return T.StructType(
        [
            T.StructField("document_id", T.StringType(), False),
            T.StructField("file_name", T.StringType(), False),
            T.StructField("source_system", T.StringType(), True),
            T.StructField("business_unit", T.StringType(), True),
            T.StructField("regulatory_domain", T.StringType(), True),
            T.StructField("document_type", T.StringType(), True),
            T.StructField("sensitivity_level", T.StringType(), True),
            T.StructField("effective_date", T.StringType(), True),
            T.StructField("expiration_date", T.StringType(), True),
            T.StructField("owner_name", T.StringType(), True),
            T.StructField("owner_email", T.StringType(), True),
        ]
    )


def _files_to_dataframe(spark: SparkSession, documents_path: Path) -> DataFrame:
    ingest_ts = datetime.now(timezone.utc)
    rows = []

    for file_path in sorted(documents_path.glob("*")):
        if not file_path.is_file():
            continue

        rows.append(
            {
                "source_path": str(file_path.resolve()),
                "file_name": file_path.name,
                "file_extension": file_path.suffix.lstrip(".").lower(),
                "ingest_ts": ingest_ts,
                "file_size_bytes": file_path.stat().st_size,
                "checksum": _compute_sha256(file_path),
                "content_path": str(file_path.resolve()),
            }
        )

    schema = T.StructType(
        [
            T.StructField("source_path", T.StringType(), False),
            T.StructField("file_name", T.StringType(), False),
            T.StructField("file_extension", T.StringType(), False),
            T.StructField("ingest_ts", T.TimestampType(), False),
            T.StructField("file_size_bytes", T.LongType(), False),
            T.StructField("checksum", T.StringType(), False),
            T.StructField("content_path", T.StringType(), False),
        ]
    )
    return spark.createDataFrame(rows, schema=schema)


def build_bronze_dataframe(
    spark: SparkSession,
    source_folder: str | Path,
    metadata_file: str = "metadata.csv",
    existing_df: DataFrame | None = None,
) -> DataFrame:
    """Read synthetic files + metadata and create a Bronze-compatible DataFrame."""

    source_path = Path(source_folder)
    documents_path = source_path / "documents"
    metadata_path = source_path / metadata_file

    metadata_df = spark.read.option("header", True).schema(_metadata_schema()).csv(str(metadata_path))
    files_df = _files_to_dataframe(spark, documents_path)

    bronze_df = (
        files_df.join(metadata_df.select("document_id", "file_name", "source_system"), on="file_name", how="inner")
        .select(*BRONZE_COLUMNS)
        .dropDuplicates(["document_id", "checksum"])
    )

    if existing_df is not None:
        bronze_df = (
            existing_df.select(*BRONZE_COLUMNS)
            .unionByName(bronze_df.select(*BRONZE_COLUMNS))
            .dropDuplicates(["document_id", "checksum"])
        )

    return bronze_df.withColumn("ingest_ts", F.col("ingest_ts").cast("timestamp"))
