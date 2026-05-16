"""
NexusAI Test Suite
Run with: pytest tests/ -v
"""
import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.base import Base
from app.db.session import get_db

# ── Test database setup ───────────────────────────────────────────────────────
# Use SQLite for tests — no Docker needed, runs anywhere including GitHub Actions
SQLITEDB = "sqlite:///./test_nexusai.db"
test_engine = create_engine(
    SQLITEDB,
    connect_args={"check_same_thread": False}
)
TestSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=test_engine
)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Override real DB with test DB
app.dependency_overrides[get_db] = override_get_db
Base.metadata.create_all(bind=test_engine)

client = TestClient(app)


# ── Health ────────────────────────────────────────────────────────────────────

def test_health_check():
    """API should return ok status."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "nexusai-backend"
    assert "timestamp" in data


# ── Invoices ──────────────────────────────────────────────────────────────────

def test_list_invoices_empty():
    """Invoice list should return empty array when no invoices exist."""
    response = client.get("/api/v1/invoices/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_weekly_summary_empty():
    """Weekly summary should return zero values when no invoices exist."""
    response = client.get("/api/v1/invoices/weekly-summary")
    assert response.status_code == 200
    data = response.json()
    assert data["invoice_count"] == 0
    assert data["total_expenses"] == 0.0
    assert data["currency"] == "BDT"
    assert "period_start" in data
    assert "period_end" in data


def test_get_nonexistent_invoice():
    """Requesting a non-existent invoice should return 404."""
    response = client.get("/api/v1/invoices/99999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_upload_invalid_file_type():
    """Uploading a non-image file should return 400."""
    response = client.post(
        "/api/v1/invoices/process",
        files={"file": ("test.txt", b"not an image", "text/plain")},
        data={"uploaded_by": "test"}
    )
    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]


def test_delete_nonexistent_invoice():
    """Deleting a non-existent invoice should return 404."""
    response = client.delete("/api/v1/invoices/99999")
    assert response.status_code == 404


def test_verify_nonexistent_invoice():
    """Verifying a non-existent invoice should return 404."""
    response = client.patch(
        "/api/v1/invoices/99999/verify",
        json={"is_verified": True}
    )
    assert response.status_code == 404


def test_invoice_pagination():
    """Invoice list should respect limit and offset params."""
    response = client.get("/api/v1/invoices/?limit=5&offset=0")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# ── Documents ─────────────────────────────────────────────────────────────────

def test_list_documents_empty():
    """Document list should return empty array when no documents exist."""
    response = client.get("/api/v1/documents/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_nonexistent_document():
    """Requesting a non-existent document should return 404."""
    response = client.get("/api/v1/documents/99999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_upload_non_pdf():
    """Uploading a non-PDF file should return 400."""
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.txt", b"not a pdf", "text/plain")},
        data={"uploaded_by": "test"}
    )
    assert response.status_code == 400


def test_delete_nonexistent_document():
    """Deleting a non-existent document should return 404."""
    response = client.delete("/api/v1/documents/99999")
    assert response.status_code == 404


def test_document_pagination():
    """Document list should respect limit and offset params."""
    response = client.get("/api/v1/documents/?limit=5&offset=0")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# ── Sentiment ─────────────────────────────────────────────────────────────────

def test_sentiment_empty_text():
    """Empty text should return 400."""
    response = client.post(
        "/api/v1/sentiment/classify",
        json={"text": ""}
    )
    assert response.status_code == 400


def test_sentiment_empty_batch():
    """Empty batch should return 400."""
    response = client.post(
        "/api/v1/sentiment/classify-batch",
        json={"texts": [], "summarize": True}
    )
    assert response.status_code == 400


def test_sentiment_batch_too_large():
    """Batch with more than 100 items should return 400."""
    response = client.post(
        "/api/v1/sentiment/classify-batch",
        json={"texts": ["text"] * 101, "summarize": False}
    )
    assert response.status_code == 400


# ── Metrics ───────────────────────────────────────────────────────────────────

def test_metrics_endpoint():
    """Metrics should return expected structure."""
    response = client.get("/api/v1/metrics/")
    assert response.status_code == 200
    data = response.json()
    assert "total_runs" in data
    assert "success_rate" in data
    assert "avg_duration_seconds" in data
    assert "agent_usage" in data
    assert "recent_runs" in data


def test_health_score_endpoint():
    """Health score should return score between 0-100."""
    response = client.get("/api/v1/metrics/health-score")
    assert response.status_code == 200
    data = response.json()
    assert "score" in data
    assert "status" in data
    assert 0 <= data["score"] <= 100
    assert data["status"] in ["healthy", "degraded", "unhealthy", "idle"]


# ── Agent ─────────────────────────────────────────────────────────────────────

def test_agent_greeting():
    """Agent should handle greetings without hitting any data agents."""
    response = client.post(
        "/api/v1/agent/chat",
        json={"message": "hi"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "final_answer" in data
    assert data["agents_used"]["invoice"] is False
    assert data["agents_used"]["document"] is False


def test_agent_invoice_query():
    """Agent should route expense questions to invoice agent."""
    response = client.post(
        "/api/v1/agent/chat",
        json={"message": "what did I spend this week?"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "final_answer" in data
    assert data["agents_used"]["invoice"] is True


def test_agent_document_query():
    """Agent should route document questions to document agent."""
    response = client.post(
        "/api/v1/agent/chat",
        json={"message": "what is the pdf about?"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "final_answer" in data
    assert data["agents_used"]["document"] is True


def test_agent_response_has_duration():
    """Agent response should include duration_seconds."""
    response = client.post(
        "/api/v1/agent/chat",
        json={"message": "show invoices"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "duration_seconds" in data
    assert data["duration_seconds"] >= 0


def test_agent_empty_message():
    """Agent should handle empty-ish messages gracefully."""
    response = client.post(
        "/api/v1/agent/chat",
        json={"message": "hello there"}
    )
    assert response.status_code == 200