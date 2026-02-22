import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
# Databricks notebook source
"""Silver transformation notebook for extracted regulatory document content."""

from pyspark.sql import SparkSession

from regdoc_intel.transforms.silver_transforms import build_silver_dataframes

spark = SparkSession.builder.appName("regdoc-silver-build").getOrCreate()

try:
    dbutils.widgets.text("bronze_table", "regdoc_intel.raw.bronze_documents", "bronze_table")
    dbutils.widgets.text("metadata_csv_path", "/dbfs/tmp/regdoc_synthetic/metadata.csv", "metadata_csv_path")
    dbutils.widgets.text("catalog", "regdoc_intel", "catalog")
    dbutils.widgets.text("schema", "curated", "schema")

    bronze_table = dbutils.widgets.get("bronze_table")
    metadata_csv_path = dbutils.widgets.get("metadata_csv_path")
    catalog = dbutils.widgets.get("catalog")
    schema = dbutils.widgets.get("schema")
except NameError:
    bronze_table = "regdoc_intel.raw.bronze_documents"
    metadata_csv_path = "./synthetic_data/metadata.csv"
    catalog = "regdoc_intel"
    schema = "curated"

bronze_documents = spark.table(bronze_table)

silver_documents, silver_document_pages, silver_document_sections = build_silver_dataframes(
    spark=spark,
    bronze_documents_df=bronze_documents,
    metadata_csv_path=metadata_csv_path,
)

silver_documents.write.format("delta").mode("overwrite").saveAsTable(f"{catalog}.{schema}.silver_documents")
silver_document_pages.write.format("delta").mode("overwrite").saveAsTable(f"{catalog}.{schema}.silver_document_pages")
silver_document_sections.write.format("delta").mode("overwrite").saveAsTable(f"{catalog}.{schema}.silver_document_sections")

print(
    "Silver build complete:",
    {
        "documents": silver_documents.count(),
        "pages": silver_document_pages.count(),
        "sections": silver_document_sections.count(),
    },
)
