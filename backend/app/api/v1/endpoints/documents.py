import logging
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.models.document import Document
from app.schemas.document import DocumentOut, QueryRequest, QueryResponse, RetrievedChunk
from app.services.rag_service import index_document, retrieve_chunks, generate_answer, generate_answer_stream
from app.core.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])
settings = get_settings()


@router.post(
    "/upload",
    response_model=DocumentOut,
    summary="Upload a PDF and index it for Q&A"
)
async def upload_document(
    file: UploadFile = File(..., description="PDF document"),
    uploaded_by: str = Form(default="api"),
    db: Session = Depends(get_db)
):
    """
    Full document ingestion pipeline:
    1. Validate it's a PDF
    2. Save to disk
    3. Create PostgreSQL record
    4. Run indexing — extract, chunk, embed, store in Qdrant
    5. Update PostgreSQL with chunk count
    6. Return document metadata
    """
    # Validate file type
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )

    # Read file
    pdf_bytes = await file.read()

    # Validate size
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(pdf_bytes) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max: {settings.max_upload_size_mb}MB"
        )

    # Save to disk
    upload_dir = Path(settings.upload_dir) / "documents"
    upload_dir.mkdir(parents=True, exist_ok=True)

    safe_filename = f"{uuid.uuid4().hex}.pdf"
    file_path = upload_dir / safe_filename

    with open(file_path, "wb") as f:
        f.write(pdf_bytes)

    # Create PostgreSQL record first (we need the ID for Qdrant)
    doc = Document(
        filename=safe_filename,
        original_name=file.filename,
        file_path=str(file_path),
        uploaded_by=uploaded_by,
        is_indexed=False
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Index the document
    try:
        total_chunks = index_document(
            file_path=str(file_path),
            document_id=doc.id,
            document_name=file.filename
        )

        # Update record with indexing results
        doc.total_chunks = total_chunks
        doc.is_indexed = True

        # Count pages
        from pypdf import PdfReader
        reader = PdfReader(str(file_path))
        doc.total_pages = len(reader.pages)

        db.commit()
        db.refresh(doc)

        logger.info(
            f"Document #{doc.id} indexed: "
            f"{total_chunks} chunks, {doc.total_pages} pages"
        )

    except Exception as e:
        # Mark as failed but don't delete — user can retry
        logger.error(f"Indexing failed for document #{doc.id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Document saved but indexing failed: {str(e)}"
        )

    return doc


@router.post(
    "/query",
    summary="Ask a question about uploaded documents"
)
def query_documents(
    request: QueryRequest,
    db: Session = Depends(get_db)
):
    """
    RAG query pipeline:
    1. Retrieve top-k relevant chunks from Qdrant
    2. Generate answer using Groq LLM
    3. Return answer with source citations

    If stream=True, returns Server-Sent Events (SSE)
    where tokens appear one by one in real time.
    If stream=False, returns complete JSON response.
    """
    # Retrieve relevant chunks
    chunks = retrieve_chunks(
        question=request.question,
        top_k=request.top_k,
        document_ids=request.document_ids
    )

    # Streaming response
    if request.stream:
        def event_stream():
            """
            SSE format: each message starts with "data: "
            and ends with double newline.
            The client reads these events and appends tokens
            to build the full answer progressively.
            """
            for token in generate_answer_stream(request.question, chunks):
                yield f"data: {token}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no"  # disable nginx buffering
            }
        )

    # Standard JSON response
    answer = generate_answer(request.question, chunks)

    return QueryResponse(
        question=request.question,
        answer=answer,
        sources=[RetrievedChunk(**c) for c in chunks],
        total_chunks_searched=len(chunks)
    )


@router.get(
    "/",
    response_model=list[DocumentOut],
    summary="List all uploaded documents"
)
def list_documents(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    return db.scalars(
        select(Document)
        .order_by(Document.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()


@router.get(
    "/{document_id}",
    response_model=DocumentOut,
    summary="Get a single document"
)
def get_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.delete(
    "/{document_id}",
    summary="Delete a document and its vectors"
)
def delete_document(document_id: int, db: Session = Depends(get_db)):
    """
    Deletes document from both PostgreSQL AND Qdrant.
    If we only delete from PostgreSQL, orphaned vectors
    remain in Qdrant wasting space and polluting search results.
    """
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete vectors from Qdrant
    from app.services.rag_service import get_qdrant_client, COLLECTION_NAME
    from qdrant_client.models import Filter, FieldCondition, MatchValue

    try:
        client = get_qdrant_client()
        client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id)
                    )
                ]
            )
        )
        logger.info(f"Deleted Qdrant vectors for document #{document_id}")
    except Exception as e:
        logger.warning(f"Could not delete Qdrant vectors: {e}")

    # Delete from PostgreSQL
    db.delete(doc)
    db.commit()

    return {"message": f"Document #{document_id} deleted"}