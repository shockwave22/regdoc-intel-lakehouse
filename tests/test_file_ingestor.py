import pytest

pytest.importorskip("pyspark")

from pyspark.sql import SparkSession

from regdoc_intel.ingestion.file_generator import generate_synthetic_dataset
from regdoc_intel.ingestion.file_ingestor import BRONZE_COLUMNS, build_bronze_dataframe


@pytest.fixture(scope="module")
def spark_session():
    spark = SparkSession.builder.master("local[1]").appName("regdoc-ingestion-tests").getOrCreate()
    yield spark
    spark.stop()


def test_build_bronze_dataframe_schema_and_rows(tmp_path, spark_session):
    generate_synthetic_dataset(tmp_path, num_docs=3, seed=1)

    bronze_df = build_bronze_dataframe(spark=spark_session, source_folder=tmp_path)

    assert bronze_df.count() == 3
    assert bronze_df.columns == BRONZE_COLUMNS


def test_build_bronze_dataframe_idempotency(tmp_path, spark_session):
    generate_synthetic_dataset(tmp_path, num_docs=2, seed=2)

    first_df = build_bronze_dataframe(spark=spark_session, source_folder=tmp_path)
    second_df = build_bronze_dataframe(spark=spark_session, source_folder=tmp_path, existing_df=first_df)

    assert first_df.count() == 2
    assert second_df.count() == 2
    assert first_df.select("checksum").distinct().count() == 2
