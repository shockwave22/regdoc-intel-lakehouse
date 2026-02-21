# AGENTS.md

## Project Summary
Regulatory Document Intelligence Platform is a Databricks Lakehouse project focused on ingesting and governing regulatory content, then enabling Retrieval-Augmented Generation (RAG) experiences for compliance and risk workflows.

## Coding Standards
- Use Python 3.11.
- Add type hints where reasonable.
- Keep code style compatible with `ruff` and `black`.
- Write tests with `pytest`.

## Repository Layout Conventions
- `docs/` for architecture, data model, governance, and operational documentation.
- `src/` for reusable application and pipeline code.
- `notebooks/` for Databricks notebook orchestration and exploration.
- `dlt/` for Delta Live Tables pipeline definitions.
- `jobs/` for Databricks job definitions and deployment assets.
- `tests/` for automated tests.

## Databricks Style Guidelines
- Keep business logic in `src/` modules.
- Keep notebooks thin and focused on orchestration, parameterization, and execution flow.

## Review Guidelines
- New or changed core logic should include tests.
- New features should include corresponding documentation updates.
