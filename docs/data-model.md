# Data Model

This document defines key Unity Catalog tables for the `regdoc_intel` catalog.

## `raw.bronze_documents`

Raw ingestion table storing immutable source payload metadata and storage pointers.

| Column | Type | Description |
|---|---|---|
| `document_id` | STRING | Stable document identifier (UUID or source composite key). |
| `source_system` | STRING | Originating system (e.g., SharePoint, S3, email). |
| `source_uri` | STRING | Source location or object URI at ingestion time. |
| `ingestion_ts` | TIMESTAMP | Ingestion timestamp in UTC. |
| `file_name` | STRING | Original file name. |
| `mime_type` | STRING | MIME type detected or provided by source. |
| `file_size_bytes` | BIGINT | Raw file size in bytes. |
| `content_sha256` | STRING | Hash for duplicate detection and integrity. |
| `storage_path` | STRING | Managed location path for raw binary. |
| `sensitivity_level` | STRING | Initial sensitivity label (public/internal/confidential/restricted). |
| `business_unit` | STRING | Owning or relevant business unit. |
| `ingestion_run_id` | STRING | Pipeline run identifier for lineage. |

## `curated.silver_documents`

Document-level normalized metadata and extraction summary.

| Column | Type | Description |
|---|---|---|
| `document_id` | STRING | Foreign key to bronze document identifier. |
| `doc_title` | STRING | Normalized or extracted title. |
| `doc_type` | STRING | Classification (policy, contract, procedure, etc.). |
| `language_code` | STRING | ISO language code from detection. |
| `effective_date` | DATE | Parsed policy/contract effective date when available. |
| `version_label` | STRING | Source or inferred version identifier. |
| `owner_org` | STRING | Owning function/team. |
| `extraction_status` | STRING | Success/partial/failure status. |
| `page_count` | INT | Number of pages after extraction. |
| `char_count` | BIGINT | Total extracted character count. |
| `sensitivity_level` | STRING | Curated sensitivity level. |
| `business_unit` | STRING | Curated business unit mapping. |
| `quality_score` | DOUBLE | Heuristic extraction quality score (0-1). |
| `silver_updated_ts` | TIMESTAMP | Last update timestamp for this silver row. |

## `curated.silver_document_pages`

Page-level extracted text and OCR diagnostics.

| Column | Type | Description |
|---|---|---|
| `document_id` | STRING | Parent document identifier. |
| `page_number` | INT | 1-based page number. |
| `page_text` | STRING | Full extracted text for page. |
| `ocr_confidence` | DOUBLE | OCR confidence (0-1) when applicable. |
| `rotation_degrees` | INT | Rotation correction applied to page. |
| `has_tables` | BOOLEAN | Whether tabular content was detected. |
| `has_signatures` | BOOLEAN | Whether signature-like patterns were detected. |
| `extraction_engine` | STRING | Parser/OCR engine used. |
| `extraction_ts` | TIMESTAMP | Page extraction timestamp. |

## `curated.silver_document_sections`

Logical sections derived from structural parsing.

| Column | Type | Description |
|---|---|---|
| `document_id` | STRING | Parent document identifier. |
| `section_id` | STRING | Stable section identifier within document. |
| `section_title` | STRING | Extracted heading/title. |
| `section_level` | INT | Hierarchy depth (1=top level). |
| `section_order` | INT | Ordered index in document flow. |
| `start_page` | INT | Start page number. |
| `end_page` | INT | End page number. |
| `section_text` | STRING | Section body text. |
| `norm_section_type` | STRING | Normalized semantic type (scope, controls, definitions, etc.). |
| `sensitivity_level` | STRING | Section-level sensitivity, if stricter than document. |

## `semantic.gold_chunks`

Retrieval-ready text chunks enriched with metadata.

| Column | Type | Description |
|---|---|---|
| `chunk_id` | STRING | Stable chunk identifier. |
| `document_id` | STRING | Parent document identifier. |
| `section_id` | STRING | Parent section identifier when available. |
| `chunk_index` | INT | Sequence index within document. |
| `chunk_text` | STRING | Chunk content sent to embedding/retrieval. |
| `token_count` | INT | Token count for chunk content. |
| `start_char_offset` | INT | Start offset in source normalized text. |
| `end_char_offset` | INT | End offset in source normalized text. |
| `citation_label` | STRING | Human-readable citation (e.g., "Policy A §3, p.12"). |
| `sensitivity_level` | STRING | Effective sensitivity label. |
| `business_unit` | STRING | Effective business unit scope. |
| `gold_created_ts` | TIMESTAMP | Chunk generation timestamp. |

## `semantic.gold_chunk_embeddings`

Embedding vectors and retrieval metadata for each chunk.

| Column | Type | Description |
|---|---|---|
| `chunk_id` | STRING | Foreign key to `semantic.gold_chunks`. |
| `document_id` | STRING | Parent document identifier for partition pruning. |
| `embedding_model` | STRING | Embedding model name/version. |
| `embedding_dim` | INT | Number of vector dimensions. |
| `embedding_vector` | ARRAY<DOUBLE> | Dense embedding vector. |
| `vector_norm` | DOUBLE | Precomputed norm for cosine similarity optimization. |
| `index_status` | STRING | Indexing status (ready/pending/error). |
| `indexed_ts` | TIMESTAMP | Timestamp when indexed or refreshed. |

## `semantic.gold_doc_analytics`

Aggregated analytics for compliance/reporting use cases.

| Column | Type | Description |
|---|---|---|
| `document_id` | STRING | Parent document identifier. |
| `doc_type` | STRING | Document type classification. |
| `policy_domain` | STRING | Domain/topic classification. |
| `control_count` | INT | Number of detected controls/obligations. |
| `obligation_count` | INT | Number of explicit obligations extracted. |
| `risk_score` | DOUBLE | Model-derived risk score. |
| `staleness_days` | INT | Days since last effective update/review. |
| `coverage_score` | DOUBLE | Downstream retrieval/metadata coverage score. |
| `analytics_ts` | TIMESTAMP | Analytics computation timestamp. |

## `serving.rag_queries`

Operational log for RAG interactions and answer provenance.

| Column | Type | Description |
|---|---|---|
| `query_id` | STRING | Unique query identifier. |
| `query_ts` | TIMESTAMP | Request timestamp in UTC. |
| `requester_principal` | STRING | User/service principal issuing query. |
| `requester_role` | STRING | Effective UC/app role used for authorization. |
| `business_unit` | STRING | Request scope for row filtering. |
| `sensitivity_level` | STRING | Maximum sensitivity permitted for response context. |
| `question_text` | STRING | User question. |
| `retrieval_strategy` | STRING | Retrieval mode (`cosine_sql`, `vector_index`, hybrid). |
| `top_k` | INT | Number of retrieved chunks requested. |
| `retrieved_chunk_ids` | ARRAY<STRING> | Chunk IDs included in prompt context. |
| `response_text` | STRING | Final assistant response. |
| `citation_payload` | STRING | Serialized citations returned to client. |
| `latency_ms` | INT | End-to-end response latency. |
| `feedback_rating` | INT | Optional user rating (e.g., 1-5). |

## `serving.rag_eval_samples`

Evaluation dataset used for quality monitoring and regression checks.

| Column | Type | Description |
|---|---|---|
| `eval_sample_id` | STRING | Unique evaluation sample identifier. |
| `created_ts` | TIMESTAMP | Sample creation timestamp. |
| `query_id` | STRING | Related query ID when sample comes from production. |
| `question_text` | STRING | Evaluation prompt/question. |
| `expected_answer` | STRING | Reference answer or policy-backed expectation. |
| `expected_citations` | ARRAY<STRING> | Expected source citations/chunk IDs. |
| `actual_answer` | STRING | Model-produced answer at evaluation time. |
| `actual_citations` | ARRAY<STRING> | Retrieved citations for evaluated run. |
| `groundedness_score` | DOUBLE | Groundedness metric (0-1). |
| `relevance_score` | DOUBLE | Relevance metric (0-1). |
| `compliance_score` | DOUBLE | Policy/compliance adherence metric (0-1). |
| `review_status` | STRING | Pending/approved/rejected/manual-escalation. |
| `reviewer` | STRING | Human reviewer principal when applicable. |
