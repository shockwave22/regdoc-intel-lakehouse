# RAG Design

This document defines how retrieval-augmented generation is implemented over the `regdoc_intel` Lakehouse.

## Embedding creation and storage

1. **Chunk preparation**
   - The Silver-to-Gold DLT pipeline assembles normalized text into chunks (`semantic.gold_chunks`).
   - Chunk sizing targets retrieval relevance and model context efficiency (for example, 300-800 tokens with overlap).
2. **Embedding generation**
   - For each chunk, an embedding model is invoked in batch or micro-batch mode.
   - The produced vector is stored in `semantic.gold_chunk_embeddings.embedding_vector`.
3. **Operational metadata**
   - `embedding_model`, `embedding_dim`, and `indexed_ts` are persisted for reproducibility and reindex planning.
   - `index_status` tracks whether each row has been published to vector index infrastructure.

## Retrieval design

At query time, the assistant supports two retrieval strategies:

1. **Top-k via cosine similarity in SQL**
   - Embed the user question into a query vector.
   - Compute cosine similarity against `semantic.gold_chunk_embeddings`.
   - Join back to `semantic.gold_chunks` for readable text and citation metadata.

2. **Top-k via Databricks Vector Search index**
   - Maintain an index sourced from `semantic.gold_chunk_embeddings` and chunk metadata.
   - Send query embedding and filters (`business_unit`, `sensitivity_level`, document type).
   - Retrieve top-k nearest neighbors with score and chunk identifiers.

In both modes, authorization-aware filtering is applied before final context assembly.

## Prompt construction with citations

Prompt orchestration includes:

1. **System instructions**
   - Enforce grounded answering, policy-safe behavior, and citation requirements.
2. **User question**
   - Original user query plus optional constraints (date range, doc type, business unit).
3. **Retrieved context block**
   - Ranked chunks with explicit source markers, e.g. `[CIT-01]`, `[CIT-02]`.
   - Each marker maps to `citation_label`, `document_id`, and chunk/page metadata.
4. **Answer format constraints**
   - Require the LLM to reference citation markers for factual claims.
   - Require uncertainty statements when evidence is insufficient.

Example prompt skeleton:

```text
You are a compliance assistant. Answer only from provided context.
If context is insufficient, say so explicitly.
Return citations for every factual assertion using [CIT-XX].

Question:
{user_question}

Context:
[CIT-01] {chunk_text_1} (source={citation_label_1})
[CIT-02] {chunk_text_2} (source={citation_label_2})
...
```

## Query and evaluation logging

### Query logging

Every production request is recorded in `serving.rag_queries`, including:
- requester identity and effective role,
- retrieval strategy and top-k configuration,
- retrieved chunk IDs and final citations,
- response text and latency,
- optional user feedback rating.

### Evaluation logging

`serving.rag_eval_samples` stores curated and sampled evaluations:
- gold/reference answers and expected citations,
- model outputs and actual citations,
- groundedness, relevance, and compliance scores,
- review workflow status and reviewer attribution.

This log design supports offline benchmarking, drift monitoring, and policy audits.
