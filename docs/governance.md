# Governance

This project relies on Unity Catalog to enforce least-privilege access, sensitive-data controls, and auditable RAG serving.

## Unity Catalog roles

Recommended principal groups:

- **`regdoc_admin`**
  - Platform administration for catalog, schema, table lifecycle, and grants.
  - Manages service principals and policy deployment.
- **`regdoc_compliance_officer`**
  - Read access to curated/semantic data across business units (subject to sensitivity policy).
  - Can review RAG logs and approve evaluation samples.
- **`regdoc_analyst`**
  - Analytical read access scoped to assigned business unit and approved sensitivity levels.
  - No direct write access to governance/serving logs except designated feedback fields.
- **`regdoc_llm_app`**
  - Service principal used by the RAG application.
  - Read semantic retrieval tables and append to serving logs/evaluation tables.

## Example GRANT statements (table + column controls)

```sql
-- Catalog and schema access
GRANT USE CATALOG ON CATALOG regdoc_intel TO `regdoc_admin`;
GRANT USE SCHEMA ON SCHEMA regdoc_intel.curated TO `regdoc_compliance_officer`, `regdoc_analyst`;
GRANT USE SCHEMA ON SCHEMA regdoc_intel.semantic TO `regdoc_llm_app`, `regdoc_compliance_officer`;
GRANT USE SCHEMA ON SCHEMA regdoc_intel.serving TO `regdoc_llm_app`, `regdoc_compliance_officer`;

-- Table-level privileges
GRANT SELECT ON TABLE regdoc_intel.semantic.gold_chunks TO `regdoc_llm_app`;
GRANT SELECT ON TABLE regdoc_intel.semantic.gold_chunk_embeddings TO `regdoc_llm_app`;
GRANT SELECT ON TABLE regdoc_intel.semantic.gold_doc_analytics TO `regdoc_compliance_officer`, `regdoc_analyst`;

GRANT INSERT ON TABLE regdoc_intel.serving.rag_queries TO `regdoc_llm_app`;
GRANT INSERT ON TABLE regdoc_intel.serving.rag_eval_samples TO `regdoc_llm_app`;
GRANT SELECT ON TABLE regdoc_intel.serving.rag_queries TO `regdoc_compliance_officer`;
GRANT SELECT ON TABLE regdoc_intel.serving.rag_eval_samples TO `regdoc_compliance_officer`;

-- Column-level controls (limit sensitive columns for analyst role)
GRANT SELECT (document_id, doc_type, owner_org, quality_score)
ON TABLE regdoc_intel.curated.silver_documents
TO `regdoc_analyst`;

GRANT SELECT (query_id, query_ts, business_unit, question_text, feedback_rating)
ON TABLE regdoc_intel.serving.rag_queries
TO `regdoc_analyst`;
```

## Row filter and masking pattern

Use dynamic views or table policies so users only see rows they are authorized to access.

### Example row filter on `sensitivity_level` and `business_unit`

```sql
CREATE OR REPLACE VIEW regdoc_intel.semantic.v_gold_chunks_secured AS
SELECT *
FROM regdoc_intel.semantic.gold_chunks
WHERE
  -- Business unit scope
  (
    is_account_group_member('regdoc_admin') OR
    is_account_group_member('regdoc_compliance_officer') OR
    business_unit = current_user()
  )
  AND
  -- Sensitivity scope
  (
    is_account_group_member('regdoc_admin') OR
    (is_account_group_member('regdoc_compliance_officer') AND sensitivity_level IN ('internal','confidential','restricted')) OR
    (is_account_group_member('regdoc_analyst') AND sensitivity_level IN ('public','internal')) OR
    (is_account_group_member('regdoc_llm_app') AND sensitivity_level IN ('public','internal','confidential'))
  );
```

> In production, replace `business_unit = current_user()` with a join against an identity entitlement mapping table (for example, `governance.user_entitlements`) that maps user/group to allowed business units.

### Example masking pattern for sensitive text

```sql
CREATE OR REPLACE VIEW regdoc_intel.curated.v_silver_documents_masked AS
SELECT
  document_id,
  doc_title,
  doc_type,
  owner_org,
  business_unit,
  sensitivity_level,
  CASE
    WHEN is_account_group_member('regdoc_admin') THEN doc_title
    WHEN is_account_group_member('regdoc_compliance_officer') THEN doc_title
    WHEN sensitivity_level IN ('public','internal') THEN doc_title
    ELSE '[MASKED_TITLE]'
  END AS doc_title_masked,
  CASE
    WHEN is_account_group_member('regdoc_admin') THEN cast(NULL AS STRING)
    WHEN is_account_group_member('regdoc_compliance_officer') THEN cast(NULL AS STRING)
    WHEN sensitivity_level IN ('public','internal') THEN cast(NULL AS STRING)
    ELSE 'TITLE_REDACTED_BY_POLICY'
  END AS masking_reason
FROM regdoc_intel.curated.silver_documents;
```

This pattern allows controlled disclosure while preserving a usable analytics and retrieval surface.
