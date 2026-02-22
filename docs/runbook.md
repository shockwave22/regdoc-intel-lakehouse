# Runbook

## 1) Generate synthetic documents locally

From the repository root:

```bash
python -m regdoc_intel.ingestion.file_generator --output-dir ./synthetic_data --num-docs 25 --seed 7
```

Output structure:

- `synthetic_data/documents/*.txt`
- `synthetic_data/metadata.csv`

## 2) Run Bronze ingestion notebook in Databricks

1. Import `notebooks/01_bronze_ingest.py` into Databricks.
2. Set notebook widgets:
   - `source_folder` (e.g., `/dbfs/tmp/regdoc_synthetic`)
   - `table_name` (e.g., `regdoc_intel.raw.bronze_documents`)
   - `delta_path` (optional external Delta path; leave blank to use `table_name`)
3. Run all cells.

The notebook calls shared ingestion logic from `src/regdoc_intel/ingestion/file_ingestor.py` and writes with standard Delta APIs.

## 3) Run Silver build notebook in Databricks

1. Import `notebooks/02_silver_build.py` into Databricks.
2. Set notebook widgets:
   - `bronze_table` (default: `regdoc_intel.raw.bronze_documents`)
   - `metadata_csv_path` (e.g., `/dbfs/tmp/regdoc_synthetic/metadata.csv`)
   - `catalog` (default: `regdoc_intel`)
   - `schema` (default: `curated`)
3. Run all cells.

The notebook reads `raw.bronze_documents` and writes the following Delta tables:

- `regdoc_intel.curated.silver_documents`
- `regdoc_intel.curated.silver_document_pages`
- `regdoc_intel.curated.silver_document_sections`

## 4) Run Bronze ingestion locally with PySpark

```bash
python - <<'PY'
from pyspark.sql import SparkSession
from regdoc_intel.ingestion.file_ingestor import build_bronze_dataframe

spark = SparkSession.builder.master("local[*]").appName("local-bronze-ingest").getOrCreate()
bronze_df = build_bronze_dataframe(spark=spark, source_folder="./synthetic_data")
bronze_df.show(truncate=False)
bronze_df.write.format("delta").mode("append").save("./tmp/delta/bronze_documents")
spark.stop()
PY
```

## 5) Run tests

```bash
pytest -q
```
