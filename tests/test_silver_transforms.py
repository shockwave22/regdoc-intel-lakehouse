import pytest

pytest.importorskip("pyspark")

from pyspark.sql import SparkSession

from regdoc_intel.transforms.silver_transforms import (
    SILVER_DOCUMENT_COLUMNS,
    SILVER_PAGE_COLUMNS,
    SILVER_SECTION_COLUMNS,
    build_silver_dataframes,
)


@pytest.fixture(scope="module")
def spark_session():
    spark = SparkSession.builder.master("local[1]").appName("regdoc-silver-tests").getOrCreate()
    yield spark
    spark.stop()


def test_build_silver_dataframes_outputs_expected_shapes(tmp_path, spark_session):
    docs_dir = tmp_path / "documents"
    docs_dir.mkdir()

    doc1_path = docs_dir / "doc-1.txt"
    doc1_path.write_text("TITLE\nhello world", encoding="utf-8")

    doc2_path = docs_dir / "doc-2.txt"
    doc2_path.write_text("POLITICA\fALCANCE\nTexto para control", encoding="utf-8")

    metadata_csv = tmp_path / "metadata.csv"
    metadata_csv.write_text(
        "\n".join(
            [
                "document_id,file_name,source_system,business_unit,regulatory_domain,document_type,sensitivity_level,effective_date,expiration_date,owner_name,owner_email",
                "DOC-1,doc-1.txt,sharepoint,Compliance,SOX,policy,internal,2024-01-01,2025-01-01,Alex Carter,alex@example.com",
                "DOC-2,doc-2.txt,confluence,Legal,GDPR,procedure,confidential,2024-02-02,2025-02-02,Priya Shah,priya@example.com",
            ]
        ),
        encoding="utf-8",
    )

    bronze_rows = [
        {"document_id": "DOC-1", "file_name": "doc-1.txt", "content_path": str(doc1_path)},
        {"document_id": "DOC-2", "file_name": "doc-2.txt", "content_path": str(doc2_path)},
    ]
    bronze_df = spark_session.createDataFrame(bronze_rows)

    silver_documents, silver_pages, silver_sections = build_silver_dataframes(
        spark=spark_session,
        bronze_documents_df=bronze_df,
        metadata_csv_path=str(metadata_csv),
    )

    assert silver_documents.columns == SILVER_DOCUMENT_COLUMNS
    assert silver_pages.columns == SILVER_PAGE_COLUMNS
    assert silver_sections.columns == SILVER_SECTION_COLUMNS

    assert silver_documents.count() == 2
    assert silver_pages.count() == 3
    assert silver_sections.count() >= 2

    languages = {row["document_id"]: row["doc_language"] for row in silver_documents.select("document_id", "doc_language").collect()}
    assert languages["DOC-1"] == "en"
    assert languages["DOC-2"] in {"en", "es"}
