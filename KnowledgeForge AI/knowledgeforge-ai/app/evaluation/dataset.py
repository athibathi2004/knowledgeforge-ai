"""Evaluation dataset loader and schema representation."""

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import List, Optional
from app.core.logging import logger


@dataclass
class EvaluationSample:
    """Represents a benchmark question with ground truth facts and target sources."""

    id: str
    question: str
    ground_truth_answer: str
    ground_truth_facts: List[str] = field(default_factory=list)
    relevant_sources: List[str] = field(default_factory=list)


class EvaluationDataset:
    """Loads and manages benchmark evaluation test cases."""

    def __init__(self, samples: List[EvaluationSample], name: str = "KnowledgeForge Benchmark"):
        self.samples = samples
        self.name = name

    @classmethod
    def from_json(cls, filepath: str | Path) -> "EvaluationDataset":
        """Load benchmark samples from a JSON dataset file."""
        path = Path(filepath)
        if not path.exists():
            logger.warning(f"Evaluation dataset file not found at {path}. Using default dataset.")
            return cls.get_default_dataset()

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            samples_data = data.get("samples", []) if isinstance(data, dict) else data
            name = data.get("name", "KnowledgeForge Benchmark") if isinstance(data, dict) else "Benchmark"

            parsed_samples = []
            for item in samples_data:
                parsed_samples.append(
                    EvaluationSample(
                        id=str(item.get("id", len(parsed_samples) + 1)),
                        question=item["question"],
                        ground_truth_answer=item.get("ground_truth_answer", ""),
                        ground_truth_facts=item.get("ground_truth_facts", []),
                        relevant_sources=item.get("relevant_sources", []),
                    )
                )

            return cls(samples=parsed_samples, name=name)
        except Exception as e:
            logger.error(f"Error loading evaluation dataset from {path}: {e}")
            return cls.get_default_dataset()

    @classmethod
    def get_default_dataset(cls) -> "EvaluationDataset":
        """Built-in default evaluation dataset based on synthetic enterprise documents."""
        default_samples = [
            EvaluationSample(
                id="eval-01",
                question="What is the Recovery Time Objective (RTO) for Tier 1 mission-critical services?",
                ground_truth_answer="The Recovery Time Objective (RTO) for Tier 1 services is 15 minutes.",
                ground_truth_facts=[
                    "Recovery Time Objective (RTO) for Tier 1 services is 15 minutes",
                    "RPO is under 1 minute for Tier 1",
                ],
                relevant_sources=["cloud_architecture_guide.md"],
            ),
            EvaluationSample(
                id="eval-02",
                question="What encryption standards are mandatory for data at rest and data in transit?",
                ground_truth_answer="AES-256 is mandatory for data at rest, and TLS 1.3 is mandatory for data in transit.",
                ground_truth_facts=[
                    "AES-256 encryption required for all persistent storage volumes",
                    "TLS 1.3 with strict forward secrecy required for data in transit",
                ],
                relevant_sources=["cloud_architecture_guide.md", "ai_governance_policy.md"],
            ),
            EvaluationSample(
                id="eval-03",
                question="Under what circumstances is customer data permitted to be used for LLM foundation model training?",
                ground_truth_answer="Customer data is strictly prohibited from being used to train or fine-tune public foundation models without explicit contractual consent.",
                ground_truth_facts=[
                    "Customer data is strictly prohibited from being used for LLM model training",
                    "Explicit, affirmative opt-in consent and tenant isolation are required",
                ],
                relevant_sources=["ai_governance_policy.md"],
            ),
            EvaluationSample(
                id="eval-04",
                question="Who has the authority to declare a Severity-1 outage and what is the maximum escalation time?",
                ground_truth_answer="The Incident Commander (IC) or on-call Lead Engineer has the authority to declare a Sev-1 outage, and the escalation bridge must be opened within 5 minutes.",
                ground_truth_facts=[
                    "Incident Commander or Lead SRE declares Severity-1",
                    "Command bridge convened within 5 minutes",
                ],
                relevant_sources=["incident_response_sop.md"],
            ),
            EvaluationSample(
                id="eval-05",
                question="What is the internal recipe for Quantum Hyperdrive fusion fuel?",
                ground_truth_answer="I do not have sufficient information to answer this question.",
                ground_truth_facts=["sufficient information"],
                relevant_sources=[],
            ),
        ]
        return cls(samples=default_samples, name="Default KnowledgeForge Benchmark")

