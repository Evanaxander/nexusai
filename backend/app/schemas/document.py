from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class DocumentOut(BaseModel):
    """Returned after a document is uploaded and indexed."""
    model_config = {"from_attributes": True}

    id: int
    filename: str
    original_name: str
    total_pages: int
    total_chunks: int
    uploaded_by: str
    is_indexed: bool
    created_at: datetime


class QueryRequest(BaseModel):
    """
    What the user sends when asking a question.
    
    question: the natural language query
    document_ids: optional filter — only search these docs.
                  if empty, searches ALL indexed documents.
    top_k: how many chunks to retrieve (default 5)
    stream: if True, response streams token by token
    """
    question: str
    document_ids: Optional[list[int]] = None
    top_k: int = 5
    stream: bool = False


class RetrievedChunk(BaseModel):
    """A single chunk retrieved from Qdrant with its metadata."""
    document_id: int
    document_name: str
    page_number: int
    chunk_index: int
    text: str
    score: float  # similarity score 0.0 to 1.0


class QueryResponse(BaseModel):
    """Full response from the RAG pipeline."""
    question: str
    answer: str
    sources: list[RetrievedChunk]
    total_chunks_searched: int