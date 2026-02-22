# Databricks notebook source
"""Bronze ingestion notebook for synthetic regulatory documents.

TODO: Replace manual batch write with Delta Live Tables orchestration.
"""

from pyspark.sql import SparkSession

from regdoc_intel.ingestion.file_ingestor import build_bronze_dataframe

spark = SparkSession.builder.appName("regdoc-bronze-ingestion").getOrCreate()

# Databricks widgets (fallback to local defaults)
try:
    dbutils.widgets.text("source_folder", "/dbfs/tmp/regdoc_synthetic", "source_folder")
    dbutils.widgets.text("table_name", "regdoc_intel.raw.bronze_documents", "table_name")
    dbutils.widgets.text("delta_path", "", "delta_path")

    source_folder = dbutils.widgets.get("source_folder")
    table_name = dbutils.widgets.get("table_name")
    delta_path = dbutils.widgets.get("delta_path")
except NameError:
    source_folder = "./synthetic_data"
    table_name = "regdoc_intel.raw.bronze_documents"
    delta_path = ""

bronze_df = build_bronze_dataframe(spark=spark, source_folder=source_folder)

writer = bronze_df.write.format("delta").mode("append")
if delta_path:
    writer.save(delta_path)
else:
    writer.saveAsTable(table_name)

print(f"Bronze ingestion completed. Rows written: {bronze_df.count()}")
