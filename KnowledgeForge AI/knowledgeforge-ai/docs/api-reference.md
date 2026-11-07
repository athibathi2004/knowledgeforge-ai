# KnowledgeForge AI - REST API Reference

All API routes are served under prefix `/api/v1`. Interactive OpenAPI documentation is accessible at `/docs` (Swagger UI) and `/redoc` (ReDoc).

---

## 1. System Health & Diagnostics

### `GET /api/v1/health`
Inspect database connectivity, embedding model readiness, and LLM gateway availability.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "app_name": "KnowledgeForge AI",
  "version": "1.0.0",
  "environment": "development",
  "components": {
    "database": {
      "status": "healthy",
      "details": "Connected (sqlite)"
    },
    "embedding_service": {
      "provider": "mock",
      "model": "all-MiniLM-L6-v2",
      "dimension": 384,
      "ready": true
    },
    "llm_gateway": {
      "provider": "mock",
      "model": "mistral",
      "ready": true
    }
  }
}
```

---

## 2. Document Management Endpoints

### `POST /api/v1/documents/upload`
Upload a document (`.pdf`, `.docx`, `.txt`, `.md`) for parsing, intelligent chunking, embedding generation, and indexing.

**Form Data Parameters:**
- `file` (binary, required): The document file.
- `chunk_size` (integer, optional): Maximum characters per chunk (default: 600).
- `chunk_overlap` (integer, optional): Overlap between chunks (default: 120).
- `chunking_strategy` (string, optional): `"recursive"`, `"fixed"`, or `"sliding_window"`.

**Response (201 Created):**
```json
{
  "id": "e4c703b4-4e9b-443b-b27e-8519de5c1b68",
  "title": "Cloud Architecture Guide",
  "filename": "cloud_architecture_guide.md",
  "file_type": "markdown",
  "file_size": 2780,
  "file_hash": "a823b49c7...",
  "doc_metadata": {
    "character_count": 2780,
    "line_count": 68
  },
  "status": "indexed",
  "error_message": null,
  "chunk_count": 8,
  "created_at": "2026-11-07T10:00:00Z",
  "updated_at": "2026-11-07T10:00:00Z"
}
```

### `GET /api/v1/documents`
List all indexed documents with pagination.

**Query Parameters:**
- `limit` (int, default: 100)
- `offset` (int, default: 0)

### `GET /api/v1/documents/{document_id}`
Retrieve complete document record along with all extracted chunks and metadata.

### `DELETE /api/v1/documents/{document_id}`
Delete a document and purge all associated chunks from the index.

---

## 3. RAG Question Answering & Retrieval

### `POST /api/v1/chat`
Execute grounded question answering over the indexed knowledge base.

**Request Body:**
```json
{
  "query": "What is the Recovery Time Objective (RTO) for Tier 1 services?",
  "conversation_id": null,
  "top_k": 5,
  "enable_reranking": true,
  "filters": {
    "file_types": ["markdown", "pdf"]
  }
}
```

**Response (200 OK):**
```json
{
  "answer": "The Recovery Time Objective (RTO) for Tier 1 mission-critical services is 15 minutes [Doc: cloud_architecture_guide.md, Chunk: 0].",
  "conversation_id": "c71a39d8-912b-45e3-99b5-c0d1e2f3a4b5",
  "message_id": "m19a4e21-0021-4f11-9a71-112233445566",
  "citations": [
    {
      "source_id": "chunk-uuid-001",
      "document_id": "doc-uuid-001",
      "document_title": "cloud_architecture_guide.md",
      "chunk_index": 0,
      "page_number": 1,
      "section_header": "High Availability",
      "snippet": "Recovery Time Objective (RTO): Maximum 15 minutes. Recovery Point Objective (RPO): Under 1 minute...",
      "relevance_score": 0.94
    }
  ],
  "sources": [ ... ],
  "latency": {
    "retrieval_ms": 14.2,
    "rerank_ms": 3.8,
    "generation_ms": 112.5,
    "total_ms": 130.5
  },
  "is_grounded": true
}
```

### `POST /api/v1/retrieval/search`
Direct diagnostic search endpoint to inspect vector, BM25, and hybrid candidate scores.

---

## 4. Conversation Management

### `GET /api/v1/conversations`
List previous conversation sessions with message counts.

### `GET /api/v1/conversations/{conversation_id}`
Retrieve entire turn history for a conversation thread.

### `DELETE /api/v1/conversations/{conversation_id}`
Clear an existing conversation thread.

---

## 5. Evaluation Benchmarking

### `POST /api/v1/evaluations/run`
Trigger automated RAGAS-compatible evaluation run.

**Request Body:**
```json
{
  "dataset_path": "sample-data/eval_dataset.json",
  "top_k": 5,
  "enable_reranking": true
}
```

**Response (201 Created):**
```json
{
  "id": "run-uuid-01",
  "dataset_name": "KnowledgeForge Enterprise Benchmark Suite v1.0",
  "sample_count": 10,
  "context_precision": 0.8500,
  "context_recall": 0.9000,
  "faithfulness": 1.0000,
  "answer_relevance": 0.8200,
  "mean_retrieval_latency_ms": 12.4,
  "mean_generation_latency_ms": 85.1,
  "created_at": "2026-11-07T10:05:00Z"
}
```

### `GET /api/v1/evaluations/results`
List previous benchmark execution runs.

### `GET /api/v1/evaluations/results/{run_id}`
Get sample-by-sample breakdown of an evaluation run.

