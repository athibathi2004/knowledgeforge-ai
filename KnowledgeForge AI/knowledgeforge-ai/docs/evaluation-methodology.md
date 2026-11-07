# KnowledgeForge AI - Evaluation Methodology

## 1. Evaluation Objectives

In enterprise RAG environments, assessing pipeline performance requires objective, repeatable metrics beyond superficial qualitative inspection. KnowledgeForge AI incorporates an automated evaluation framework compatible with the **RAGAS (Retrieval Augmented Generation Assessment)** paradigm.

The framework measures:
1. **Retrieval Quality**: Did the retriever fetch the right documents?
2. **Retrieval Ranking**: Were the best documents placed at the top?
3. **Generation Faithfulness**: Did the LLM stick strictly to the facts in the context?
4. **Answer Relevance**: Did the LLM directly answer the user's inquiry?
5. **System Latency**: How fast did each stage execute?

---

## 2. Core Metrics & Mathematical Formulations

### A. Context Precision (Mean Average Precision)
Measures whether the relevant retrieved chunks appear at the highest ranking positions:

$$\text{Context Precision} = \frac{1}{\text{Hits}} \sum_{k=1}^{K} \left( \frac{\text{Hits}@k}{k} \times \text{IsRelevant}(c_k) \right)$$

- Evaluates the ranking performance of the hybrid retriever and reranker.
- High score indicates that top-ranked chunks directly contain the necessary ground-truth facts.

### B. Context Recall
Measures the proportion of ground-truth statements that can be attributed to the retrieved context chunks:

$$\text{Context Recall} = \frac{|\text{Ground Truth Facts Covered in Context}|}{|\text{Total Ground Truth Facts}|}$$

- Measures retrieval completeness.
- If key evidence was missing during retrieval, context recall decreases.

### C. Faithfulness (Anti-Hallucination Score)
Measures the proportion of claims made in the generated answer that can be inferred directly from the retrieved context passages:

$$\text{Faithfulness} = \frac{|\text{Sentences Supported by Context}|}{|\text{Total Sentences in Answer}|}$$

- If the answer explicitly states that sufficient information is missing (truthful refusal), Faithfulness is scored as $1.0$.
- Any fabricated fact or unsupported assertion lowers this metric.

### D. Answer Relevance
Measures the semantic and lexical alignment between the user's initial question and the generated response:

$$\text{Answer Relevance} = 0.70 \times \text{Overlap}(Q, A) + 0.30 \times \text{Jaccard}(Q, A)$$

- Penalizes evasive, off-topic, or circular responses.

---

## 3. Evaluation Dataset Architecture

Benchmark datasets are structured as JSON files (`sample-data/eval_dataset.json`):

```json
{
  "name": "KnowledgeForge Enterprise Benchmark Suite v1.0",
  "samples": [
    {
      "id": "eval-01",
      "question": "What is the Recovery Time Objective (RTO) for Tier 1 mission-critical services?",
      "ground_truth_answer": "The Recovery Time Objective (RTO) for Tier 1 services is 15 minutes.",
      "ground_truth_facts": [
        "Recovery Time Objective (RTO) for Tier 1 services is 15 minutes",
        "RPO is under 1 minute for Tier 1"
      ],
      "relevant_sources": ["cloud_architecture_guide.md"]
    }
  ]
}
```

The benchmark includes intentionally unanswerable / out-of-domain test cases to verify that the system correctly refuses to hallucinate when context is absent.

---

## 4. Execution & Automated Reporting

The evaluation suite can be triggered through two interfaces:
1. **REST API**: `POST /api/v1/evaluations/run`
2. **CLI Runner**: `python scripts/run_eval.py --top-k 5`

Execution records and sample-by-sample score breakdowns are stored in the database and automatically exported to `docs/evaluation_report.md`.

