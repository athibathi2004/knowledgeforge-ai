# KnowledgeForge AI

**Enterprise Knowledge Intelligence Platform with Advanced RAG, Intelligent Ingestion, Semantic Retrieval, and RAGAS Evaluation**

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style](https://img.shields.io/badge/code%20style-pep8-green.svg)](https://pep8.org/)

---

## 1. Project Introduction

**KnowledgeForge AI** is an independently developed, modular, open-source enterprise knowledge intelligence engine designed to turn unstructured corporate documents into actionable, verifiable intelligence. It features a complete end-to-end Retrieval-Augmented Generation (RAG) architecture: multi-format document ingestion, semantic chunking, dual-engine hybrid retrieval (dense vector embeddings combined with sparse BM25 keyword matching), multi-factor reranking, strict anti-hallucination prompt control, citation extraction with source provenance, and an automated RAGAS-compatible evaluation framework.

This project is an independent public reference demonstration using synthetic documents and open benchmark datasets. It contains no proprietary corporate code, data, prompts, or confidential internal architectures.

---

## 2. Problem Statement

Modern enterprise knowledge repositories frequently suffer from critical architectural failure modes:
1. **Hallucination & Lack of Attribution**: Standard LLMs answer inquiries authoritatively even when information is missing or outdated, offering no audit trail to verifiable source documents.
2. **Naive Keyword vs. Vector Disconnect**: Pure keyword search (BM25) fails to capture semantic synonyms and conceptual paraphrasing; pure vector similarity search regularly misses exact technical identifiers (e.g., *AES-256*, *RTO/RPO targets*, *RFC references*, error codes).
3. **Rigid Ingestion Pipelines**: Many RAG tutorials use arbitrary character chunking that splits sentences mid-word or divorces content from page and section headings.
4. **Absence of Quantitative Verification**: Teams deploy generative search without quantitative metrics to measure context precision, context recall, faithfulness, or retrieval latency.

---

## 3. Solution Overview

KnowledgeForge AI resolves these limitations through a clean, decoupled architecture:
- **Intelligent Multi-Format Ingestion**: Native extraction for PDF, DOCX, TXT, and Markdown preserving structural segment headers, page numbers, and document metadata.
- **Configurable Chunking Engine**: Implements recursive character splitting (paragraph and sentence boundary preservation), fixed windowing, and token-based sliding windows.
- **Hybrid Retrieval & RRF Fusion**: Combines dense vector cosine similarity (via pgvector or in-memory vector storage) and sparse BM25 lexical scoring using Reciprocal Rank Fusion (RRF) and weighted linear fusion.
- **Multi-Factor Reranker**: Refines candidate quality using exact phrase matching, query term coverage, lexical density, and section header alignment.
- **Grounded Synthesis & Citation Provenance**: Generates answers strictly bound to retrieved context blocks, refusing to answer when context is insufficient, and mapping verified citation tags `[Doc: <title>, Chunk: <idx>]` directly back to original document text snippets.
- **Automated RAGAS Evaluation**: Programmatically calculates Context Precision, Context Recall, Faithfulness, and Answer Relevance against standardized test datasets.
- **Integrated Web Dashboard**: Clean, responsive frontend for interactive chatting, file uploads, chunk inspection, retrieval experimentation, and evaluation reporting.

---

## 4. Feature List

- **Document Management**:
  - Multi-format ingestion: `.pdf`, `.docx`, `.txt`, `.md`.
  - Content deduplication using SHA-256 hash checks.
  - File size and MIME type validation.
  - Page-level and section-level metadata tracking.
  - Document chunk viewer and document deletion cascading to all chunks.
- **Advanced Retrieval**:
  - Dense vector similarity search (cosine distance).
  - Sparse lexical search (BM25Okapi with small-corpus stabilization).
  - Reciprocal Rank Fusion (RRF) and linear weighted combination ($0.0 \le \alpha \le 1.0$).
  - Multi-factor reranking with query phrase bonus and term coverage.
  - Metadata filtering by document ID, file type, or custom tags.
- **Grounded Question Answering**:
  - Contextual prompt assembly with neutral delimiter isolation to prevent prompt injection.
  - Explicit refusal behavior when context relevance falls below threshold ($MIN\_SCORE = 0.20$).
  - Verification of citations with exact character snippet previews.
  - Multi-turn conversation state tracking without treating prior assistant outputs as authoritative evidence.
- **Evaluation & Diagnostics**:
  - Benchmark runner with synthetic ground-truth dataset (`sample-data/eval_dataset.json`).
  - Automated calculation of Context Precision, Context Recall, Faithfulness, and Answer Relevance.
  - Granular latency breakdown tracking (retrieval time, reranking time, generation time).
  - Exportable Markdown scorecard reports (`docs/evaluation_report.md`).
- **Developer Experience**:
  - 100% executable offline test suite (35 automated tests covering unit and integration layers).
  - Pluggable provider architecture (Mock, Ollama, HuggingFace Sentence Transformers, OpenAI-compatible).
  - Interactive Swagger API documentation at `/docs`.

---

## 5. Technical Architecture

```
 knowledgeforge-ai/
 ├── app/
 │   ├── api/v1/endpoints/  # REST API: health, documents, chat, conversations, evaluations
 │   ├── core/              # Domain exceptions, structured logging
 │   ├── db/                # SQLAlchemy session, engine, schema initialization
 │   ├── models/            # SQLAlchemy ORM models (Document, DocumentChunk, Conversation, etc.)
 │   ├── schemas/           # Pydantic v2 validation schemas
 │   ├── services/          # Parsers (PDF, DOCX, TXT), Preprocessing, Chunking, Ingestion
 │   ├── embeddings/        # Base interface, Mock, SentenceTransformers, Ollama, OpenAI adapters
 │   ├── retrieval/         # VectorStore, BM25Retriever, HybridRetriever, EnsembleReranker
 │   ├── llm/               # Base interface, Ollama, OpenAI-compatible, Mock grounded synthesizer
 │   ├── rag/               # Orchestrator, system prompts, citation verification
 │   └── evaluation/        # RAGAS metrics, dataset loader, benchmark evaluator
 ├── frontend/              # Web UI: Chat, Document Hub, Retrieval Playground, Evaluation Dashboard
 ├── sample-data/           # Synthetic enterprise guides (PDF, DOCX, MD) and eval dataset JSON
 ├── tests/                 # Complete unit and integration test suite
 ├── scripts/               # CLI tools: init_db.py, ingest_samples.py, run_eval.py
 ├── docs/                  # Architectural docs, API reference, RAG pipeline, evaluation methodology
 ├── .env.example           # Environment template
 ├── requirements.txt       # Python dependencies
 ├── pyproject.toml         # Build specification
 ├── docker-compose.yml     # Multi-container orchestration (PostgreSQL+pgvector, App, Ollama)
 ├── Dockerfile             # Production multi-stage container build
 └── README.md
```

---

## 6. RAG Workflow

```
[1. User Inquiry]
       │
       ▼
[2. Conversation Context] ──► Preserves multi-turn state (User/Assistant history)
       │
       ▼
[3. Hybrid Retrieval] ────► Vector Search (Dense) + BM25 (Sparse)
       │
       ▼
[4. Score Fusion] ────────► Reciprocal Rank Fusion (RRF with k=60)
       │
       ▼
[5. Reranking] ───────────► Lexical density, exact phrase match, and title alignment
       │
       ▼
[6. Relevance Gating] ────► If top score < 0.20: Refuse gracefully ("Insufficient Info")
       │
       ▼
[7. Prompt Assembly] ─────► Isolate passages in delimiters, enforce inline citation tags
       │
       ▼
[8. LLM Gateway] ─────────► Ollama (Mistral/Llama3), OpenAI-compatible, or Mock synthesizer
       │
       ▼
[9. Citation Mapping] ────► Extract [Doc: X, Chunk: Y] tags & generate snippet previews
```

---

## 7. Technology Stack

- **Backend Framework**: Python 3.11+, FastAPI, Pydantic v2, Uvicorn
- **ORM & Database**: SQLAlchemy 2.0, PostgreSQL with `pgvector` (or zero-dependency SQLite fallback)
- **Lexical Retrieval**: `rank-bm25` (BM25Okapi algorithm)
- **Document Parsers**: `pypdf` (PDF), `python-docx` (DOCX), standard library Unicode normalization
- **Binary Generation**: `reportlab`
- **Embedding Adapters**: HuggingFace (`sentence-transformers`), Ollama, OpenAI-compatible
- **LLM Gateway**: Ollama HTTP API, OpenAI-compatible REST API, deterministic mock provider
- **Testing**: `pytest`, `pytest-asyncio`, `httpx`
- **Frontend**: Responsive vanilla HTML5, CSS3 with CSS variables, asynchronous JavaScript

---

## 8. Installation Instructions

### Prerequisites
- Python 3.11 or higher
- Git
- (Optional) Docker and Docker Compose
- (Optional) Ollama for running local LLMs

### Clone and Setup Virtual Environment

```bash
# 1. Clone repository
git clone https://github.com/your-username/knowledgeforge-ai.git
cd knowledgeforge-ai

# 2. Create Python virtual environment
python -m venv .venv

# On Linux/macOS:
source .venv/bin/activate

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt
```

---

## 9. Environment Configuration

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Key environment configuration variables:

```ini
# Database (defaults to local SQLite; uncomment PostgreSQL for production)
DATABASE_URL="sqlite:///./knowledgeforge.db"
# DATABASE_URL="postgresql://postgres:postgrespassword@localhost:5432/knowledgeforge"

# Embedding Provider: "mock", "sentence_transformers", "ollama", "openai"
EMBEDDING_PROVIDER="mock"
EMBEDDING_MODEL="all-MiniLM-L6-v2"

# LLM Gateway Provider: "mock", "ollama", "openai"
LLM_PROVIDER="mock"
LLM_MODEL="mistral"
LLM_BASE_URL="http://localhost:11434"

# Retrieval Settings
DEFAULT_TOP_K=5
HYBRID_ALPHA=0.60
ENABLE_RERANKING=true
MIN_RELEVANCE_SCORE=0.20
```

---

## 10. Database Setup

KnowledgeForge AI initializes database tables automatically upon server launch. To initialize manually via CLI:

```bash
python scripts/init_db.py
```

### Using PostgreSQL with pgvector (Optional)
To use PostgreSQL with native pgvector vector indexing:
1. Start PostgreSQL with pgvector via Docker:
   ```bash
   docker compose up -d db
   ```
2. Update `DATABASE_URL` in `.env`:
   ```ini
   DATABASE_URL="postgresql://postgres:postgrespassword@localhost:5432/knowledgeforge"
   ```
3. Run `python scripts/init_db.py` to create the `vector` extension and tables.

---

## 11. Model Setup

### Option A: Out-of-the-Box Mock / Deterministic Mode (Default)
Requires no GPU, no network access, and zero external downloads.
```ini
EMBEDDING_PROVIDER="mock"
LLM_PROVIDER="mock"
```

### Option B: Local Ollama (Mistral or Llama 3)
1. Install and start [Ollama](https://ollama.ai/):
   ```bash
   ollama serve
   ```
2. Pull required models:
   ```bash
   ollama pull mistral
   ollama pull nomic-embed-text
   ```
3. Configure `.env`:
   ```ini
   EMBEDDING_PROVIDER="ollama"
   EMBEDDING_MODEL="nomic-embed-text"
   LLM_PROVIDER="ollama"
   LLM_MODEL="mistral"
   ```

### Option C: Local HuggingFace Sentence Transformers
Install `sentence-transformers`:
```bash
pip install sentence-transformers
```
Configure `.env`:
```ini
EMBEDDING_PROVIDER="sentence_transformers"
EMBEDDING_MODEL="all-MiniLM-L6-v2"
```

---

## 12. Quick Start & Execution

### 1. Ingest Synthetic Sample Documents
Ingest synthetic enterprise policies, cloud architecture guides, and SOPs:

```bash
python scripts/ingest_samples.py
```

### 2. Start Application Server
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Access Interfaces
- **Web Dashboard**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### 4. Run Evaluation Benchmark
Execute the automated RAGAS quality benchmark:

```bash
python scripts/run_eval.py --top-k 5
```

---

## 13. API Documentation Overview

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/health` | System health and component readiness diagnostics |
| `POST` | `/api/v1/documents/upload` | Upload & index document (`.pdf`, `.docx`, `.txt`, `.md`) |
| `GET` | `/api/v1/documents` | List all indexed documents with chunk count summaries |
| `GET` | `/api/v1/documents/{id}` | Retrieve document details and extracted chunks |
| `DELETE` | `/api/v1/documents/{id}` | Delete document and purge vector chunks |
| `POST` | `/api/v1/chat` | Contextual question answering with citations & provenance |
| `POST` | `/api/v1/retrieval/search` | Direct diagnostic search across vector & BM25 indices |
| `GET` | `/api/v1/conversations` | List conversation sessions |
| `GET` | `/api/v1/conversations/{id}` | Get conversation turn history |
| `POST` | `/api/v1/evaluations/run` | Execute automated benchmark run |
| `GET` | `/api/v1/evaluations/results` | List historical benchmark runs |

See [`docs/api-reference.md`](docs/api-reference.md) for complete schemas and example JSON payloads.

---

## 14. Testing Instructions

The codebase includes 35 comprehensive automated tests covering document validation, text extraction, chunking engines, vector embeddings, hybrid retrieval, reranking, citation extraction, RAGAS metrics, and API endpoints.

To run the full test suite:

```bash
pytest tests -v
```

All tests are designed to execute completely offline without requiring external network connectivity or running external server instances.

---

## 15. Known Limitations

1. **OCR Support**: The current PDF parser processes text-based PDF streams via `pypdf`. Scanned image-only PDFs require an upstream OCR engine (e.g., Tesseract).
2. **Complex Table Parsing**: Multi-page merged table structures in DOCX and PDF documents are serialized into linear text blocks; complex multi-dimensional table reasoning requires specialized tabular parser adapters.
3. **Local Embedding Memory**: When switching from `mock` to `sentence-transformers`, downloading the initial PyTorch model weights requires ~400MB of disk storage and internet access during first-time download.

---

## 16. Future Improvements

- **Parent-Child Chunking**: Store smaller semantic chunks for retrieval while feeding the larger parent paragraph to the LLM for expanded context.
- **Hypothetical Document Embeddings (HyDE)**: Generate pseudo-answers to expand exploratory queries before vector retrieval.
- **Multi-Modal Document Ingestion**: Ingest embedded charts, diagrams, and figures using vision-language models.
- **Granular Role-Based Access Control (RBAC)**: Enforce user-level and group-level permission filters during vector similarity search.
- **Asynchronous Ingestion Worker**: Offload large document batch uploads to a Celery/Redis queue for background workers.

---

## 17. License

Distributed under the MIT License. See [`LICENSE`](LICENSE) for more information.

