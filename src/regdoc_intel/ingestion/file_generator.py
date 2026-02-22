from __future__ import annotations

import argparse
import csv
import random
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Iterable

METADATA_COLUMNS = [
    "document_id",
    "file_name",
    "source_system",
    "business_unit",
    "regulatory_domain",
    "document_type",
    "sensitivity_level",
    "effective_date",
    "expiration_date",
    "owner_name",
    "owner_email",
]

SOURCE_SYSTEMS = ["sharepoint", "confluence", "network_drive", "policy_center"]
BUSINESS_UNITS = ["Compliance", "Risk", "Legal", "Operations"]
REGULATORY_DOMAINS = ["GDPR", "SOX", "HIPAA", "PCI-DSS", "ISO-27001"]
DOCUMENT_TYPES = ["policy", "procedure", "contract", "control-narrative"]
SENSITIVITY_LEVELS = ["public", "internal", "confidential", "restricted"]
OWNERS = [
    ("Alex Carter", "alex.carter@example.com"),
    ("Priya Shah", "priya.shah@example.com"),
    ("Jordan Lee", "jordan.lee@example.com"),
    ("Mina Alvarez", "mina.alvarez@example.com"),
]


@dataclass(frozen=True)
class DocumentSpec:
    document_id: str
    file_name: str
    source_system: str
    business_unit: str
    regulatory_domain: str
    document_type: str
    sensitivity_level: str
    effective_date: str
    expiration_date: str
    owner_name: str
    owner_email: str

    def to_row(self) -> dict[str, str]:
        return {
            "document_id": self.document_id,
            "file_name": self.file_name,
            "source_system": self.source_system,
            "business_unit": self.business_unit,
            "regulatory_domain": self.regulatory_domain,
            "document_type": self.document_type,
            "sensitivity_level": self.sensitivity_level,
            "effective_date": self.effective_date,
            "expiration_date": self.expiration_date,
            "owner_name": self.owner_name,
            "owner_email": self.owner_email,
        }


def _build_document_body(spec: DocumentSpec) -> str:
    return (
        f"# {spec.document_type.title()} Document\n\n"
        f"Document ID: {spec.document_id}\n"
        f"Business Unit: {spec.business_unit}\n"
        f"Regulatory Domain: {spec.regulatory_domain}\n"
        f"Sensitivity: {spec.sensitivity_level}\n"
        f"Owner: {spec.owner_name} ({spec.owner_email})\n"
        f"Effective Date: {spec.effective_date}\n"
        f"Expiration Date: {spec.expiration_date}\n\n"
        "## Purpose\n"
        "This is synthetic content generated for Lakehouse ingestion and testing.\n\n"
        "## Control Requirements\n"
        "- Annual review is required.\n"
        "- Exceptions must be approved in writing.\n"
        "- Evidence must be retained for seven years.\n"
    )


def _generate_specs(num_docs: int, rng: random.Random) -> Iterable[DocumentSpec]:
    start_date = date.today() - timedelta(days=365)
    for index in range(1, num_docs + 1):
        doc_id = f"DOC-{index:05d}"
        file_name = f"{doc_id.lower()}.txt"
        owner_name, owner_email = rng.choice(OWNERS)
        effective = start_date + timedelta(days=rng.randint(0, 365))
        expiration = effective + timedelta(days=365 * rng.randint(1, 3))

        yield DocumentSpec(
            document_id=doc_id,
            file_name=file_name,
            source_system=rng.choice(SOURCE_SYSTEMS),
            business_unit=rng.choice(BUSINESS_UNITS),
            regulatory_domain=rng.choice(REGULATORY_DOMAINS),
            document_type=rng.choice(DOCUMENT_TYPES),
            sensitivity_level=rng.choice(SENSITIVITY_LEVELS),
            effective_date=effective.isoformat(),
            expiration_date=expiration.isoformat(),
            owner_name=owner_name,
            owner_email=owner_email,
        )


def generate_synthetic_dataset(output_dir: str | Path, num_docs: int, seed: int = 7) -> tuple[Path, Path]:
    """Generate synthetic text documents and a metadata CSV.

    Returns a tuple of (documents_dir, metadata_csv_path).
    """

    base_path = Path(output_dir)
    docs_path = base_path / "documents"
    metadata_path = base_path / "metadata.csv"
    docs_path.mkdir(parents=True, exist_ok=True)

    rng = random.Random(seed)
    specs = list(_generate_specs(num_docs=num_docs, rng=rng))

    for spec in specs:
        (docs_path / spec.file_name).write_text(_build_document_body(spec), encoding="utf-8")

    with metadata_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=METADATA_COLUMNS)
        writer.writeheader()
        for spec in specs:
            writer.writerow(spec.to_row())

    return docs_path, metadata_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic regulatory documents.")
    parser.add_argument("--output-dir", default="./synthetic_data", help="Output directory for generated files.")
    parser.add_argument("--num-docs", type=int, default=10, help="Number of synthetic documents to generate.")
    parser.add_argument("--seed", type=int, default=7, help="Random seed for deterministic generation.")
    args = parser.parse_args()

    docs_path, metadata_path = generate_synthetic_dataset(args.output_dir, args.num_docs, args.seed)
    print(f"Generated {args.num_docs} synthetic files in: {docs_path}")
    print(f"Generated metadata CSV at: {metadata_path}")


if __name__ == "__main__":
    main()
