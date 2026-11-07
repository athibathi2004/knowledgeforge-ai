"""CLI script to execute RAG evaluation benchmark and export scorecard."""

import argparse
from pathlib import Path
import sys

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from app.core.logging import logger
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.embeddings import get_embedding_service
from app.evaluation.dataset import EvaluationDataset
from app.evaluation.evaluator import RAGEvaluator
from app.llm import get_llm_service
from app.rag.orchestrator import RAGOrchestrator


def main():
    parser = argparse.ArgumentParser(description="Run KnowledgeForge AI Evaluation Benchmark")
    parser.add_argument(
        "--dataset",
        type=str,
        default=str(root_dir / "sample-data" / "eval_dataset.json"),
        help="Path to evaluation dataset JSON",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(root_dir / "docs" / "evaluation_report.md"),
        help="Path to export evaluation markdown report",
    )
    parser.add_argument("--top-k", type=int, default=5, help="Number of retrieved chunks")
    args = parser.parse_args()

    init_db()
    db = SessionLocal()
    try:
        dataset = EvaluationDataset.from_json(args.dataset)
        emb_service = get_embedding_service()
        llm_service = get_llm_service()
        orchestrator = RAGOrchestrator(
            db=db,
            embedding_service=emb_service,
            llm_service=llm_service,
        )
        evaluator = RAGEvaluator(db=db, orchestrator=orchestrator)

        print("\n=======================================================")
        print(f" KnowledgeForge AI - Benchmark Evaluation Runner")
        print(f"=======================================================")
        print(f"Dataset: {dataset.name} ({len(dataset.samples)} samples)")
        print(f"Top-K Retrieval: {args.top_k} | Reranking: Enabled\n")

        eval_run = evaluator.evaluate_dataset(
            dataset=dataset,
            top_k=args.top_k,
            enable_reranking=True,
        )

        print("-------------------------------------------------------")
        print(f" EVALUATION SCORECARD (RAGAS-Compatible Metrics)")
        print("-------------------------------------------------------")
        print(f" Context Precision      : {eval_run.context_precision:.4f}")
        print(f" Context Recall         : {eval_run.context_recall:.4f}")
        print(f" Faithfulness           : {eval_run.faithfulness:.4f}")
        print(f" Answer Relevance       : {eval_run.answer_relevance:.4f}")
        print(f" Mean Retrieval Latency : {eval_run.mean_retrieval_latency_ms:.2f} ms")
        print(f" Mean Generation Latency: {eval_run.mean_generation_latency_ms:.2f} ms")
        print("-------------------------------------------------------")

        RAGEvaluator.export_markdown_report(eval_run, args.output)
        print(f"Detailed Markdown report exported to: {args.output}\n")

    finally:
        db.close()


if __name__ == "__main__":
    main()

