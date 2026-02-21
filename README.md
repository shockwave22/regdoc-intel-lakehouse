# regdoc-intel-lakehouse

The Regulatory Document Intelligence Platform is a Databricks-native Lakehouse project that ingests unstructured regulatory content, standardizes and governs it with medallion data engineering patterns, and enables trusted RAG experiences for compliance, legal, and risk teams.

## Tech stack checklist

- [x] Delta Lake
- [x] Unity Catalog (UC)
- [x] Delta Live Tables (DLT)
- [x] MLflow
- [x] Databricks Vector Search
- [x] Retrieval-Augmented Generation (RAG)

## High-level architecture

The platform follows a Medallion + RAG flow:

1. **Bronze**: ingest raw regulatory documents and source metadata.
2. **Silver**: normalize text, parse structure, and enrich with standardized metadata.
3. **Gold**: curate analytics- and policy-ready datasets with governance controls.
4. **RAG**: build chunked, embedded, and indexed knowledge assets for retrieval and grounded response generation.

## Quickstart

### Run tests and checks locally

```bash
python -m pip install --upgrade pip
pip install black ruff pytest
black --check .
ruff check .
pytest
```

### Open notebooks in Databricks

1. Connect this repository to a Databricks workspace using Databricks Repos.
2. Open the `notebooks/` directory in the Databricks workspace UI.
3. Start with `notebooks/00_setup.py` to validate the environment and bootstrap your workspace-specific settings.
