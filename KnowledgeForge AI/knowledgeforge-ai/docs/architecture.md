# KnowledgeForge AI - System Architecture

## 1. Overview & Architectural Philosophy

**KnowledgeForge AI** is an independently developed, modular, enterprise-grade Knowledge Intelligence Platform built around advanced Retrieval-Augmented Generation (RAG). The system transforms heterogeneous corporate documentation into structured, high-dimensional semantic vector spaces, enabling contextual natural-language inquiry with verifiable source citations, anti-hallucination guardrails, and systematic evaluation benchmarking.

```
                              ┌──────────────────────────────────────────────┐
                              │           KnowledgeForge Web UI / API        │
                              └──────────────────────┬───────────────────────┘
                                                     │
                                                     ▼
                                      ┌──────────────────────────────┐
                                      │      FastAPI Router Layer    │
                                      └──────────────┬───────────────┘
                                                     │
                     ┌───────────────────────────────┴───────────────────────────────┐
                     ▼                                                               ▼
        ┌──────────────────────────────┐                              ┌──────────────────────────────┐
        │   Document Ingestion Flow    │                              │     RAG Query Flow           │
        └────────────┬─────────────────┘                              └──────────────┬───────────────┘
                     │                                                               │
                     ├─► Document Validation & Hashing                               ├─► Session Context Management
                     ├─► Parsers (PDF, DOCX, TXT, MD)                                ├─► Query Analysis
                     ├─► Text Normalization (NFKC)                                   ├─► Hybrid Retrieval
                     ├─► Intelligent Chunking Engine                                 │   ├─► Vector Similarity (Cosine)
                     │   (Recursive, Fixed, Sliding)                                 │   └─► Lexical Search (BM25)
                     ├─► Batch Vector Embeddings                                     ├─► Score Fusion (RRF / Weighted)
                     │                                                               ├─► Cross-Encoder / Ensemble Rerank
                     ▼                                                               ├─► Context Grounding Gate
        ┌──────────────────────────────┐                                             ├─► Prompt Assembly with Isolation
        │      Persistent Storage      │◄────────────────────────────────────────────┼─► LLM Gateway (Ollama, OpenAI, Mock)
        │  PostgreSQL / pgvector / SQLite                                            ├─► Citation Extraction & Mapping
        └──────────────────────────────┘                                             └─► Quality Evaluation (RAGAS)
```

---

## 2. Component Decoupling & Modular Organization

The architecture emphasizes clean separation of concerns and dependency inversion:

1. **Document Ingestion Service (`app/services/ingestion.py`)**:
   - Manages file validation, deduplication via SHA-256 fingerprinting, structural parsing, preprocessing, and chunk indexing.
2. **Parsing Subsystem (`app/services/parser.py`)**:
   - `PDFDocumentParser`: Extracts text and page numbers via `pypdf`.
   - `DocxDocumentParser`: Extracts hierarchical headings, paragraphs, and tables via `python-docx`.
   - `TextDocumentParser`: Handles UTF-8 and Latin-1 plain text and Markdown.
3. **Chunking Engine (`app/services/chunking.py`)**:
   - `RecursiveCharacterChunker`: Hierarchical paragraph, sentence, and phrase boundary chunking.
   - `FixedSizeChunker`: Character window chunking with calibrated overlap.
   - `SlidingWindowChunker`: Token-aware sliding window splitting.
4. **Embedding Abstraction (`app/embeddings/`)**:
   - Unified interface `BaseEmbeddingService` with pluggable adapters:
     - `MockEmbeddingService`: Offline, deterministic hash projection for zero-dependency testing.
     - `SentenceTransformersEmbeddingService`: Local HuggingFace embeddings (`all-MiniLM-L6-v2`).
     - `OllamaEmbeddingService`: Self-hosted open-source embeddings (`nomic-embed-text`).
     - `OpenAICompatEmbeddingService`: OpenAI-compatible remote gateways.
5. **Retrieval Engine (`app/retrieval/`)**:
   - Dual-engine architecture:
     - `VectorStore`: Cosine similarity over normalized float vectors (pgvector or NumPy).
     - `BM25Retriever`: Lexical term frequency and inverse document frequency scoring.
     - `HybridRetriever`: Reciprocal Rank Fusion (RRF) and linear weighted combination.
     - `EnsembleReranker`: Multi-factor query coverage, phrase bonus, and lexical density scoring.
6. **LLM Gateway (`app/llm/`)**:
   - `OllamaLLMService`: Local Mistral/Llama models via Ollama.
   - `OpenAICompatLLMService`: Standard OpenAI-compatible inference servers (vLLM, LMStudio).
   - `MockLLMService`: Grounded test synthesizer.
7. **RAG Orchestrator (`app/rag/`)**:
   - `RAGOrchestrator`: Assembles retrieved contexts, enforces groundedness, and manages citations.
   - `CitationManager`: Extracts verified inline citations and maps snippets back to original chunk offsets.
8. **Evaluation Framework (`app/evaluation/`)**:
   - Computes Context Precision, Context Recall, Faithfulness, Answer Relevance, and Latencies.

---

## 3. Data Storage & Schema Design

```sql
-- Core Relational Schema

CREATE TABLE documents (
    id VARCHAR(36) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size INTEGER NOT NULL,
    file_hash VARCHAR(64) NOT NULL UNIQUE,
    doc_metadata JSON,
    status VARCHAR(50) NOT NULL,
    error_message TEXT,
    chunk_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE document_chunks (
    id VARCHAR(36) PRIMARY KEY,
    document_id VARCHAR(36) REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    token_count INTEGER DEFAULT 0,
    start_char INTEGER DEFAULT 0,
    end_char INTEGER DEFAULT 0,
    chunk_metadata JSON,
    embedding JSON, -- Stored as Vector(dim) in PostgreSQL pgvector deployments
    created_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE conversations (
    id VARCHAR(36) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE conversation_messages (
    id VARCHAR(36) PRIMARY KEY,
    conversation_id VARCHAR(36) REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    citations JSON,
    retrieval_metadata JSON,
    created_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE evaluation_runs (
    id VARCHAR(36) PRIMARY KEY,
    dataset_name VARCHAR(255) NOT NULL,
    sample_count INTEGER NOT NULL,
    context_precision FLOAT DEFAULT 0.0,
    context_recall FLOAT DEFAULT 0.0,
    faithfulness FLOAT DEFAULT 0.0,
    answer_relevance FLOAT DEFAULT 0.0,
    mean_retrieval_latency_ms FLOAT DEFAULT 0.0,
    mean_generation_latency_ms FLOAT DEFAULT 0.0,
    detailed_results JSON,
    created_at TIMESTAMP WITH TIME ZONE
);
```

