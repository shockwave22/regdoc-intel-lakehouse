import csv

from regdoc_intel.ingestion.file_generator import METADATA_COLUMNS, generate_synthetic_dataset


def test_generate_synthetic_dataset_creates_expected_files(tmp_path):
    docs_path, metadata_path = generate_synthetic_dataset(tmp_path, num_docs=4, seed=11)

    assert docs_path.exists()
    assert metadata_path.exists()
    assert len(list(docs_path.glob("*.txt"))) == 4

    with metadata_path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    assert reader.fieldnames == METADATA_COLUMNS
    assert len(rows) == 4
    assert all(row["document_id"].startswith("DOC-") for row in rows)
    assert all(row["owner_email"].endswith("@example.com") for row in rows)
