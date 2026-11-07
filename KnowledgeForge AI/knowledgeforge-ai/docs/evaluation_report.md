# KnowledgeForge AI - Evaluation Benchmark Report

**Run ID**: `6894c7c8-d7a5-4c9d-867d-0e64a84e9026`  
**Dataset**: `KnowledgeForge Enterprise Benchmark Suite v1.0`  
**Samples Evaluated**: `10`  
**Timestamp**: `2026-11-07 04:52:26.029072`  

## Aggregate RAGAS Metrics

| Metric | Score | Description |
| :--- | :--- | :--- |
| **Context Precision** | **0.7333** | Ratio of relevant retrieved chunks to total retrieved chunks |
| **Context Recall** | **0.8500** | Coverage of ground-truth statements within retrieved context |
| **Faithfulness** | **1.0000** | Groundedness of generated statements (anti-hallucination score) |
| **Answer Relevance** | **0.1511** | Semantic fidelity between question and answer |
| **Mean Retrieval Latency** | **4.41 ms** | Time spent searching vector store and BM25 |
| **Mean Generation Latency** | **0.12 ms** | Time spent synthesizing LLM response |

## Sample-by-Sample Breakdown

### Sample 1: What is the Recovery Time Objective (RTO) for Tier 1 mission-critical services?
- **Generated Answer**: Incident Severity Definitions
Severity-1 (Critical Outage): Core user-facing functionality is fully unavailable.
The escalation bridge must be convened within 5 minutes.
Executive leadership notification is required within 15 minutes.
Status page public updates must occur every 20 minutes until resolved.
Severity-2 (Major Impairment): Critical feature degraded with significant impact.
The escalation bridge must be convened within 15 minutes. [Doc: untitled, Chunk: 0, Page: 1]
- **Ground Truth**: The Recovery Time Objective (RTO) for Tier 1 services is 15 minutes.
- **Precision**: `1.00` | **Recall**: `1.00` | **Faithfulness**: `1.00` | **Relevance**: `0.19`
- **Latency**: Retrieval `6.6ms`, Generation `0.5ms`

### Sample 2: What encryption standards are mandatory for data at rest and data in transit?
- **Generated Answer**: Based on the provided documents, I do not have sufficient information to answer this question.
- **Ground Truth**: AES-256 is mandatory for data at rest, and TLS 1.3 is mandatory for data in transit.
- **Precision**: `0.92` | **Recall**: `1.00` | **Faithfulness**: `1.00` | **Relevance**: `0.00`
- **Latency**: Retrieval `4.2ms`, Generation `0.1ms`

### Sample 3: Under what circumstances is customer data permitted to be used for LLM foundation model training?
- **Generated Answer**: Based on the provided documents, I do not have sufficient information to answer this question.
- **Ground Truth**: Customer data is strictly prohibited from being used to train or fine-tune public foundation models without explicit contractual consent.
- **Precision**: `1.00` | **Recall**: `1.00` | **Faithfulness**: `1.00` | **Relevance**: `0.06`
- **Latency**: Retrieval `4.0ms`, Generation `0.1ms`

### Sample 4: Who has the authority to declare a Severity-1 outage and what is the maximum escalation bridge time?
- **Generated Answer**: Command Authority and Roles
The Incident Commander (IC) or Lead SRE has single-point operational authority
to declare a Severity-1 incident, order service rollbacks, and direct response teams.
A blameless root-cause analysis (RCA) must be published within 72 hours of closure,
including a chronological timeline, contributing causes, and preventive action items. [Doc: untitled, Chunk: 2, Page: 2]
- **Ground Truth**: The Incident Commander (IC) or on-call Lead SRE has authority to declare a Sev-1 outage, and the escalation bridge must be convened within 5 minutes.
- **Precision**: `0.50` | **Recall**: `0.50` | **Faithfulness**: `1.00` | **Relevance**: `0.36`
- **Latency**: Retrieval `4.1ms`, Generation `0.1ms`

### Sample 5: How often must cloud KMS encryption keys be rotated?
- **Generated Answer**: Based on the provided documents, I do not have sufficient information to answer this question.
- **Ground Truth**: Encryption keys must be rotated automatically every 90 days using a cloud Key Management Service (KMS).
- **Precision**: `1.00` | **Recall**: `1.00` | **Faithfulness**: `1.00` | **Relevance**: `0.00`
- **Latency**: Retrieval `3.8ms`, Generation `0.1ms`

### Sample 6: Within how many hours must a blameless post-mortem be published following incident closure?
- **Generated Answer**: Command Authority and Roles
The Incident Commander (IC) or Lead SRE has single-point operational authority
to declare a Severity-1 incident, order service rollbacks, and direct response teams.
A blameless root-cause analysis (RCA) must be published within 72 hours of closure,
including a chronological timeline, contributing causes, and preventive action items. [Doc: untitled, Chunk: 2, Page: 2]
- **Ground Truth**: A blameless post-mortem root-cause analysis (RCA) must be published within 72 hours of incident closure.
- **Precision**: `1.00` | **Recall**: `1.00` | **Faithfulness**: `1.00` | **Relevance**: `0.48`
- **Latency**: Retrieval `4.0ms`, Generation `0.1ms`

### Sample 7: What vector indexing parameters are specified for pgvector to achieve sub-50ms retrieval?
- **Generated Answer**: Based on the provided documents, I do not have sufficient information to answer this question.
- **Ground Truth**: Vector embeddings are indexed using HNSW with parameters m=16 and ef_construction=64.
- **Precision**: `1.00` | **Recall**: `1.00` | **Faithfulness**: `1.00` | **Relevance**: `0.07`
- **Latency**: Retrieval `5.3ms`, Generation `0.1ms`

### Sample 8: What neutral delimiters are mandated to isolate retrieved context and prevent prompt injection?
- **Generated Answer**: Based on the provided documents, I do not have sufficient information to answer this question.
- **Ground Truth**: Retrieved context passages must be encapsulated within '--- RETRIEVED CONTEXT START ---' neutral delimiters.
- **Precision**: `0.50` | **Recall**: `1.00` | **Faithfulness**: `1.00` | **Relevance**: `0.07`
- **Latency**: Retrieval `4.2ms`, Generation `0.1ms`

### Sample 9: What is the secret recipe for dark matter antigravity propulsion crystals?
- **Generated Answer**: Incident Severity Definitions
Severity-1 (Critical Outage): Core user-facing functionality is fully unavailable.
The escalation bridge must be convened within 5 minutes.
Executive leadership notification is required within 15 minutes.
Status page public updates must occur every 20 minutes until resolved.
Severity-2 (Major Impairment): Critical feature degraded with significant impact.
The escalation bridge must be convened within 15 minutes. [Doc: untitled, Chunk: 0, Page: 1]
- **Ground Truth**: Based on the provided documents, I do not have sufficient information to answer this question.
- **Precision**: `0.00` | **Recall**: `0.00` | **Faithfulness**: `1.00` | **Relevance**: `0.14`
- **Latency**: Retrieval `3.9ms`, Generation `0.1ms`

### Sample 10: What is the capital city of Atlantis according to enterprise policy?
- **Generated Answer**: Based on the provided documents, I do not have sufficient information to answer this question.
- **Ground Truth**: Based on the provided documents, I do not have sufficient information to answer this question.
- **Precision**: `0.42` | **Recall**: `1.00` | **Faithfulness**: `1.00` | **Relevance**: `0.15`
- **Latency**: Retrieval `4.0ms`, Generation `0.1ms`
