"""Benchmark evaluation runner and reporting engine."""

import json
from pathlib import Path
import statistics
import time
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.config import settings
from app.core.logging import logger
from app.evaluation.dataset import EvaluationDataset, EvaluationSample
from app.evaluation.metrics import RAGMetrics
from app.models.evaluation import EvaluationRun
from app.rag.orchestrator import RAGOrchestrator
from app.schemas.chat import ChatRequest
from app.schemas.evaluation import EvaluationRunResponse, EvaluationSampleResult


class RAGEvaluator:
    """Executes evaluation benchmarks and generates RAGAS-compatible scorecards."""

    def __init__(self, db: Session, orchestrator: RAGOrchestrator):
        self.db = db
        self.orchestrator = orchestrator

    def evaluate_dataset(
        self,
        dataset: EvaluationDataset,
        top_k: int = 5,
        enable_reranking: bool = True,
    ) -> EvaluationRun:
        """Run end-to-end evaluation benchmark over the given dataset."""
        logger.info(f"Starting evaluation run on '{dataset.name}' ({len(dataset.samples)} samples)...")

        sample_results: List[Dict[str, Any]] = []
        precisions: List[float] = []
        recalls: List[float] = []
        faithfulness_scores: List[float] = []
        relevance_scores: List[float] = []
        retrieval_latencies: List[float] = []
        generation_latencies: List[float] = []

        for sample in dataset.samples:
            chat_req = ChatRequest(
                query=sample.question,
                top_k=top_k,
                enable_reranking=enable_reranking,
            )

            response = self.orchestrator.answer_query(chat_req)
            retrieved_texts = [s.content for s in response.sources]
            retrieved_ids = [s.chunk_id for s in response.sources]

            # Compute RAGAS-compatible metrics
            c_prec = RAGMetrics.compute_context_precision(
                retrieved_contexts=retrieved_texts,
                ground_truth_facts=sample.ground_truth_facts,
            )
            c_rec = RAGMetrics.compute_context_recall(
                retrieved_contexts=retrieved_texts,
                ground_truth_facts=sample.ground_truth_facts,
            )
            faith = RAGMetrics.compute_faithfulness(
                generated_answer=response.answer,
                retrieved_contexts=retrieved_texts,
            )
            relev = RAGMetrics.compute_answer_relevance(
                question=sample.question,
                generated_answer=response.answer,
            )

            precisions.append(c_prec)
            recalls.append(c_rec)
            faithfulness_scores.append(faith)
            relevance_scores.append(relev)
            retrieval_latencies.append(response.latency.retrieval_ms)
            generation_latencies.append(response.latency.generation_ms)

            sample_results.append(
                {
                    "sample_id": sample.id,
                    "question": sample.question,
                    "ground_truth_answer": sample.ground_truth_answer,
                    "generated_answer": response.answer,
                    "context_precision": c_prec,
                    "context_recall": c_rec,
                    "faithfulness": faith,
                    "answer_relevance": relev,
                    "retrieval_latency_ms": response.latency.retrieval_ms,
                    "generation_latency_ms": response.latency.generation_ms,
                    "retrieved_chunk_ids": retrieved_ids,
                    "citations_count": len(response.citations),
                }
            )

        mean_precision = round(statistics.mean(precisions), 4) if precisions else 0.0
        mean_recall = round(statistics.mean(recalls), 4) if recalls else 0.0
        mean_faithfulness = round(statistics.mean(faithfulness_scores), 4) if faithfulness_scores else 0.0
        mean_relevance = round(statistics.mean(relevance_scores), 4) if relevance_scores else 0.0
        mean_retrieval_ms = round(statistics.mean(retrieval_latencies), 2) if retrieval_latencies else 0.0
        mean_gen_ms = round(statistics.mean(generation_latencies), 2) if generation_latencies else 0.0

        eval_run = EvaluationRun(
            dataset_name=dataset.name,
            sample_count=len(dataset.samples),
            context_precision=mean_precision,
            context_recall=mean_recall,
            faithfulness=mean_faithfulness,
            answer_relevance=mean_relevance,
            mean_retrieval_latency_ms=mean_retrieval_ms,
            mean_generation_latency_ms=mean_gen_ms,
            detailed_results={"samples": sample_results},
        )

        self.db.add(eval_run)
        self.db.commit()
        self.db.refresh(eval_run)

        logger.info(
            f"Evaluation run completed (ID: {eval_run.id}). "
            f"Precision={mean_precision}, Recall={mean_recall}, Faithfulness={mean_faithfulness}"
        )
        return eval_run

    @staticmethod
    def export_markdown_report(eval_run: EvaluationRun, output_path: str | Path) -> None:
        """Export evaluation scorecard as formatted Markdown."""
        lines = [
            f"# KnowledgeForge AI - Evaluation Benchmark Report",
            f"",
            f"**Run ID**: `{eval_run.id}`  ",
            f"**Dataset**: `{eval_run.dataset_name}`  ",
            f"**Samples Evaluated**: `{eval_run.sample_count}`  ",
            f"**Timestamp**: `{eval_run.created_at}`  ",
            f"",
            f"## Aggregate RAGAS Metrics",
            f"",
            f"| Metric | Score | Description |",
            f"| :--- | :--- | :--- |",
            f"| **Context Precision** | **{eval_run.context_precision:.4f}** | Ratio of relevant retrieved chunks to total retrieved chunks |",
            f"| **Context Recall** | **{eval_run.context_recall:.4f}** | Coverage of ground-truth statements within retrieved context |",
            f"| **Faithfulness** | **{eval_run.faithfulness:.4f}** | Groundedness of generated statements (anti-hallucination score) |",
            f"| **Answer Relevance** | **{eval_run.answer_relevance:.4f}** | Semantic fidelity between question and answer |",
            f"| **Mean Retrieval Latency** | **{eval_run.mean_retrieval_latency_ms:.2f} ms** | Time spent searching vector store and BM25 |",
            f"| **Mean Generation Latency** | **{eval_run.mean_generation_latency_ms:.2f} ms** | Time spent synthesizing LLM response |",
            f"",
            f"## Sample-by-Sample Breakdown",
            f"",
        ]

        samples = eval_run.detailed_results.get("samples", [])
        for idx, s in enumerate(samples, start=1):
            lines.extend(
                [
                    f"### Sample {idx}: {s['question']}",
                    f"- **Generated Answer**: {s['generated_answer']}",
                    f"- **Ground Truth**: {s['ground_truth_answer']}",
                    f"- **Precision**: `{s['context_precision']:.2f}` | **Recall**: `{s['context_recall']:.2f}` | **Faithfulness**: `{s['faithfulness']:.2f}` | **Relevance**: `{s['answer_relevance']:.2f}`",
                    f"- **Latency**: Retrieval `{s['retrieval_latency_ms']:.1f}ms`, Generation `{s['generation_latency_ms']:.1f}ms`",
                    f"",
                ]
            )

        Path(output_path).write_text("\n".join(lines), encoding="utf-8")

