from __future__ import annotations

from datetime import datetime, timezone
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import types as T

from regdoc_intel.extraction.text_extractor import derive_sections_from_pages, extract_text_from_file


SILVER_DOCUMENT_COLUMNS = [
    "document_id",
    "doc_title",
    "doc_type",
    "doc_language",
    "effective_date",
    "expiration_date",
    "owner_name",
    "owner_email",
    "business_unit",
    "regulatory_domain",
    "sensitivity_level",
    "extraction_status",
    "page_count",
    "char_count",
    "silver_updated_ts",
]

SILVER_PAGE_COLUMNS = [
    "document_id",
    "page_number",
    "page_text",
    "extraction_ts",
]

SILVER_SECTION_COLUMNS = [
    "document_id",
    "section_id",
    "section_title",
    "section_order",
    "section_text",
    "extraction_ts",
]


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


def _infer_doc_language(text: str) -> str:
    lower_text = text.lower()
    spanish_markers = [" el ", " la ", " de ", " y ", " para "]
    if any(marker in f" {lower_text} " for marker in spanish_markers):
        return "es"
    return "en"


def _safe_title_from_pages(pages: list[str], fallback: str) -> str:
    for page in pages:
        for line in page.splitlines():
            value = line.strip()
            if value:
                return value[:255]
    return fallback


def build_silver_dataframes(
    spark: SparkSession,
    bronze_documents_df: DataFrame,
    metadata_csv_path: str,
) -> tuple[DataFrame, DataFrame, DataFrame]:
    """Transform bronze documents into silver document, page, and section tables."""

    metadata_df = spark.read.option("header", True).schema(_metadata_schema()).csv(str(metadata_csv_path))
    metadata_lookup = {
        row["document_id"]: row.asDict()
        for row in metadata_df.select(*[field.name for field in _metadata_schema().fields]).collect()
    }

    docs_rows: list[dict] = []
    page_rows: list[dict] = []
    section_rows: list[dict] = []

    extraction_ts = datetime.now(timezone.utc)

    for row in bronze_documents_df.select("document_id", "file_name", "content_path").collect():
        pages = extract_text_from_file(row["content_path"])
        sections = derive_sections_from_pages(pages)
        doc_text = "\n".join(pages)
        metadata = metadata_lookup.get(row["document_id"], {})

        docs_rows.append(
            {
                "document_id": row["document_id"],
                "doc_title": _safe_title_from_pages(pages, row["file_name"]),
                "doc_type": metadata.get("document_type"),
                "doc_language": _infer_doc_language(doc_text),
                "effective_date": metadata.get("effective_date"),
                "expiration_date": metadata.get("expiration_date"),
                "owner_name": metadata.get("owner_name"),
                "owner_email": metadata.get("owner_email"),
                "business_unit": metadata.get("business_unit"),
                "regulatory_domain": metadata.get("regulatory_domain"),
                "sensitivity_level": metadata.get("sensitivity_level"),
                "extraction_status": "success",
                "page_count": len(pages),
                "char_count": len(doc_text),
                "silver_updated_ts": extraction_ts,
            }
        )

        for page_number, page_text in enumerate(pages, start=1):
            page_rows.append(
                {
                    "document_id": row["document_id"],
                    "page_number": page_number,
                    "page_text": page_text,
                    "extraction_ts": extraction_ts,
                }
            )

        for section in sections:
            section_rows.append(
                {
                    "document_id": row["document_id"],
                    "section_id": section["section_id"],
                    "section_title": section["section_title"],
                    "section_order": section["section_order"],
                    "section_text": section["section_text"],
                    "extraction_ts": extraction_ts,
                }
            )

    documents_schema = T.StructType(
        [
            T.StructField("document_id", T.StringType(), False),
            T.StructField("doc_title", T.StringType(), True),
            T.StructField("doc_type", T.StringType(), True),
            T.StructField("doc_language", T.StringType(), True),
            T.StructField("effective_date", T.StringType(), True),
            T.StructField("expiration_date", T.StringType(), True),
            T.StructField("owner_name", T.StringType(), True),
            T.StructField("owner_email", T.StringType(), True),
            T.StructField("business_unit", T.StringType(), True),
            T.StructField("regulatory_domain", T.StringType(), True),
            T.StructField("sensitivity_level", T.StringType(), True),
            T.StructField("extraction_status", T.StringType(), False),
            T.StructField("page_count", T.IntegerType(), False),
            T.StructField("char_count", T.LongType(), False),
            T.StructField("silver_updated_ts", T.TimestampType(), False),
        ]
    )

    pages_schema = T.StructType(
        [
            T.StructField("document_id", T.StringType(), False),
            T.StructField("page_number", T.IntegerType(), False),
            T.StructField("page_text", T.StringType(), True),
            T.StructField("extraction_ts", T.TimestampType(), False),
        ]
    )

    sections_schema = T.StructType(
        [
            T.StructField("document_id", T.StringType(), False),
            T.StructField("section_id", T.StringType(), False),
            T.StructField("section_title", T.StringType(), True),
            T.StructField("section_order", T.IntegerType(), False),
            T.StructField("section_text", T.StringType(), True),
            T.StructField("extraction_ts", T.TimestampType(), False),
        ]
    )

    silver_documents = spark.createDataFrame(docs_rows, schema=documents_schema).select(*SILVER_DOCUMENT_COLUMNS)
    silver_document_pages = spark.createDataFrame(page_rows, schema=pages_schema).select(*SILVER_PAGE_COLUMNS)
    silver_document_sections = spark.createDataFrame(section_rows, schema=sections_schema).select(*SILVER_SECTION_COLUMNS)

    return silver_documents, silver_document_pages, silver_document_sections
