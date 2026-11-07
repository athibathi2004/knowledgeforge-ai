# Corporate Responsible AI, LLM Security & Data Governance Policy

## 1. Purpose and Scope

This policy governs the ethical deployment, data boundary protection, security compliance, and safe usage of Generative AI, Retrieval-Augmented Generation (RAG), and Large Language Models (LLMs) across all KnowledgeForge enterprise environments.

## 2. Customer Data Privacy and Foundation Model Training

- **Strict Training Prohibition**: Customer data, uploaded corporate documents, proprietary source code, and employee prompts are strictly prohibited from being used to train, retrain, or fine-tune public foundation models or third-party commercial LLMs.
- **Opt-In Exception**: Use of proprietary customer data for private, dedicated model fine-tuning requires explicit, affirmative written contractual consent and total tenant isolation.
- **Data Retention for Inference**: When interacting with external inference APIs, zero-data-retention (ZDR) agreements must be legally executed ensuring that API providers retain inference payloads for zero seconds post-completion.

## 3. Grounding and Anti-Hallucination Controls

- All enterprise automated decision-support assistants must implement grounded RAG pipelines.
- Language models must be explicitly instructed through system prompts to state when sufficient supporting evidence is absent from retrieved knowledge chunks rather than speculating or fabricating responses.
- Any generated response must provide verified source citations identifying document title, chunk index, and page number to guarantee traceability and auditability.

## 4. Prompt Injection and Security Safeguards

- **Input Sanitization**: User inputs must be scanned for prompt injection attacks, jailbreak patterns, and system delimiter overrides prior to retrieval and LLM context assembly.
- **Context Isolation**: Retrieved knowledge passages must be encapsulated in neutral delimiters (`--- RETRIEVED CONTEXT START ---`) to prevent document-borne adversarial prompts from hijacking execution logic.
- **Audit Logging**: All queries, retrieved chunk identifiers, generated citations, and refusal occurrences must be logged with immutable timestamps for compliance auditing.

