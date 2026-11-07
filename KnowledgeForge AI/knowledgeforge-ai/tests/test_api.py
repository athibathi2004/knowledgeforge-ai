"""Integration tests for FastAPI REST API endpoints."""

import io
import pytest


def test_health_endpoint(client):
    """Verify health endpoint returns status and component diagnostics."""
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ("healthy", "degraded")
    assert "components" in data
    assert "database" in data["components"]
    assert "embedding_service" in data["components"]
    assert "llm_gateway" in data["components"]


def test_document_lifecycle(client):
    """Test full document upload, retrieval, and deletion lifecycle."""
    # 1. Upload Document
    doc_content = b"# Enterprise Security Policy\n\nAll databases require encrypted volume backings."
    file_payload = {"file": ("sec_policy.md", io.BytesIO(doc_content), "text/markdown")}
    upload_res = client.post("/api/v1/documents/upload", files=file_payload)
    assert upload_res.status_code == 201
    doc_data = upload_res.json()
    doc_id = doc_data["id"]
    assert doc_data["chunk_count"] >= 1
    assert doc_data["status"] == "indexed"

    # 2. List Documents
    list_res = client.get("/api/v1/documents")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] >= 1
    assert any(d["id"] == doc_id for d in list_data["documents"])

    # 3. Get Document Details with Chunks
    get_res = client.get(f"/api/v1/documents/{doc_id}")
    assert get_res.status_code == 200
    detail_data = get_res.json()
    assert len(detail_data["chunks"]) >= 1

    # 4. Delete Document
    del_res = client.delete(f"/api/v1/documents/{doc_id}")
    assert del_res.status_code == 200

    # 5. Verify 404 on deleted document
    get_after_del = client.get(f"/api/v1/documents/{doc_id}")
    assert get_after_del.status_code == 404


def test_chat_and_conversation_flow(client):
    """Test chat query answering, multi-turn conversation, and history retrieval."""
    # Ingest reference document first
    doc_content = (
        "Enterprise Architecture\n\n"
        "Recovery Time Objective (RTO) for Tier 1 services is exactly 15 minutes."
    ).encode("utf-8")
    client.post(
        "/api/v1/documents/upload",
        files={"file": ("rto.txt", io.BytesIO(doc_content), "text/plain")},
    )

    # Ask grounded question
    chat_res = client.post(
        "/api/v1/chat",
        json={"query": "What is the RTO for Tier 1 services?", "top_k": 3},
    )
    assert chat_res.status_code == 200
    chat_data = chat_res.json()
    assert "answer" in chat_data
    assert chat_data["conversation_id"] is not None
    conv_id = chat_data["conversation_id"]

    # Verify conversation history
    conv_res = client.get(f"/api/v1/conversations/{conv_id}")
    assert conv_res.status_code == 200
    conv_data = conv_res.json()
    assert len(conv_data["messages"]) >= 2  # user + assistant turns


def test_evaluation_run_api(client):
    """Test triggering automated benchmark evaluation run via API."""
    run_res = client.post(
        "/api/v1/evaluations/run",
        json={"top_k": 3, "enable_reranking": True},
    )
    assert run_res.status_code == 201
    run_data = run_res.json()
    assert "context_precision" in run_data
    assert "faithfulness" in run_data
    assert run_data["sample_count"] > 0

    # List evaluation results
    results_res = client.get("/api/v1/evaluations/results")
    assert results_res.status_code == 200
    results_data = results_res.json()
    assert results_data["total"] >= 1

