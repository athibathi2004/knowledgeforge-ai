# KnowledgeForge AI - RAG Pipeline & Retrieval Strategies

## 1. End-to-End Pipeline Workflow

The Retrieval-Augmented Generation (RAG) pipeline in KnowledgeForge AI consists of 7 sequential phases engineered for high precision, hallucination avoidance, and strict factual attribution:

```
User Query
   │
   ▼
[1. Query Analysis & History Enrichment] 
   │
   ▼
[2. Dual-Engine Retrieval] 
   ├── Vector Similarity Search (Dense Embeddings, Cosine Distance)
   └── BM25 Keyword Search (Sparse Lexical Inverted Index)
   │
   ▼
[3. Reciprocal Rank Fusion (RRF)] 
   │
   ▼
[4. Multi-Factor Reranking (Ensemble / Cross-Encoder)]
   │
   ▼
[5. Relevance Gating & Anti-Hallucination Guardrail]
   ├── Score >= Threshold (0.20): Proceed to Prompt Assembly
   └── Score < Threshold: Immediate Grounded Refusal ("Insufficient Information")
   │
   ▼
[6. Context Assembly & LLM Synthesis]
   ├── Context Encapsulated with Neutral Delimiters
   └── Strict System Instructions Enforcing Inline Provenance
   │
   ▼
[7. Citation Verification & Provenance Mapping]
   └── Extract [Doc: ..., Chunk: ...] Tags & Map to Snippets
```

---

## 2. Ingestion & Intelligent Chunking Strategies

Raw documents vary significantly in structure. KnowledgeForge AI avoids naive fixed-character chunking by providing three configurable strategies:

### A. Recursive Character Chunking (`recursive`)
Recursively explores a hierarchy of natural linguistic boundaries:
`["\n\n", "\n", ". ", "? ", "! ", "; ", " ", ""]`
- **Paragraph splits (`\n\n`)** retain complete topical thoughts.
- **Sentence splits (`. `, `? `)** preserve grammatical propositions.
- **Word splits (` `)** prevent mid-word truncation.
- Configured with `chunk_size` (default: 600 characters) and `chunk_overlap` (default: 120 characters).

### B. Fixed Size Chunking (`fixed`)
A sliding character window with constant step size `(chunk_size - chunk_overlap)`. Useful for tabular documentation or uniform logs where semantic paragraph breaks do not exist.

### C. Sliding Window Chunking (`sliding_window`)
Token/word-aware chunker that moves a sliding window of target words with specified overlap across the document stream.

---

## 3. Hybrid Retrieval: Vector + BM25 Fusion

Pure vector search struggles with exact keywords (acronyms like *RTO*, *AES-256*, error codes like *HTTP 503*), while pure keyword search fails on semantic paraphrasing. KnowledgeForge AI bridges this using hybrid retrieval.

### Reciprocal Rank Fusion (RRF)
Given rankings from Vector search ($R_{vec}$) and BM25 ($R_{bm25}$):

$$RRF(d) = \frac{\alpha}{k + \text{rank}_{vec}(d)} + \frac{1 - \alpha}{k + \text{rank}_{bm25}(d)}$$

Where:
- $k = 60$ (standard smoothing constant preventing top ranks from dominating).
- $\alpha = 0.60$ (configurable weight balancing vector vs. keyword importance).

---

## 4. Multi-Factor Reranking Engine

Top candidates from hybrid retrieval undergo deep query-document reranking using `EnsembleReranker` (or optional `CrossEncoderReranker`):

1. **Exact Phrase Bonus**: Boosts candidates containing the verbatim query sequence.
2. **Query Word Recall / Coverage**: Fraction of query terms present in the candidate passage.
3. **Term Density**: Frequency of query terms normalized by passage length.
4. **Header & Title Alignment**: Bonus if query terms match the document title or section heading.
5. **Calibrated Score Output**: Final score in $[0.0, 1.0]$ used for citation attribution.

---

## 5. Anti-Hallucination & Provenance Mechanics

To avoid LLM hallucinations:
1. **Relevance Gating**: If the highest reranked candidate score falls below `MIN_RELEVANCE_SCORE` (0.20), the LLM is not prompted with random noise; the system immediately responds:
   > *"Based on the provided documents, I do not have sufficient information to answer this question."*
2. **Context Isolation**: Passages are wrapped inside `--- RETRIEVED CONTEXT START ---` delimiters to neutralize potential prompt injection from user-uploaded files.
3. **Citation Manager**: Verifies inline citation tags `[Doc: <title>, Chunk: <idx>]` against retrieved candidate IDs, extracting verbatim snippet previews.

