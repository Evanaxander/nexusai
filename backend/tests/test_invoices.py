from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_list_documents_empty():
    response = client.get("/api/v1/documents/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_nonexistent_document():
    response = client.get("/api/v1/documents/99999")
    assert response.status_code == 404


def test_upload_non_pdf():
    """Uploading a non-PDF should return 400."""
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.txt", b"not a pdf", "text/plain")},
        data={"uploaded_by": "test"}
    )
    assert response.status_code == 400

def test_agent_invoice_query():
    """Agent should route expense questions to invoice agent."""
    response = client.post(
        "/api/v1/agent/chat",
        json={"message": "What did I spend this week?"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "final_answer" in data
    assert data["agents_used"]["invoice"] is True


def test_agent_document_query():
    """Agent should route document questions to document agent."""
    response = client.post(
        "/api/v1/agent/chat",
        json={"message": "What does my contract say about payment terms?"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "final_answer" in data
    assert data["agents_used"]["document"] is True