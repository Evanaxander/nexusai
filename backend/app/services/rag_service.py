import logging
import uuid
from typing import Generator
from pathlib import Path

from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchAny,
)
from groq import Groq
import httpx

from app.core.config import get_settings
from app.core.observability import track_llm_call

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Constants ─────────────────────────────────────────────────────────────────

# The embedding model converts text → vectors
# all-MiniLM-L6-v2 produces 384-dimensional vectors
# Fast, small, good quality for semantic search
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
VECTOR_SIZE = 384

# Qdrant collection name — think of it as a table for vectors
COLLECTION_NAME = "nexusai_documents"

# Chunking parameters
# CHUNK_SIZE: characters per chunk (not tokens)
# CHUNK_OVERLAP: characters shared between adjacent chunks
# Why overlap? A sentence crossing a chunk boundary appears
# fully in at least one chunk, preventing missed context
CHUNK_SIZE = 512
CHUNK_OVERLAP = 64

# LLM for answer generation
GROQ_MODEL = "llama-3.3-70b-versatile"

# ── System prompt for answer generation ───────────────────────────────────────
# This prompt tells the LLM exactly how to behave:
# - answer only from context (prevents hallucination)
# - cite sources (traceability)
# - admit when information isn't available
RAG_SYSTEM_PROMPT = """You are a precise document analysis assistant for business users.

You answer questions using ONLY the provided document excerpts.

Rules:
1. Base your answer entirely on the provided context
2. Cite your sources like this: [Doc: filename, Page: X]
3. If the answer cannot be found AT ALL in the context, only then say:
   \"This information was not found in the provided documents.\""
4. Never invent or assume information not in the context
5. Be concise but complete
6. Use bullet points for lists, plain text for explanations"""


# ── Singleton instances ────────────────────────────────────────────────────────
# These are loaded ONCE when the module is first imported
# Loading the embedding model takes ~2 seconds
# We don't want that delay on every API call

_embedding_model: SentenceTransformer | None = None
_qdrant_client: QdrantClient | None = None


def get_embedding_model() -> SentenceTransformer:
    """Returns the embedding model, loading it on first call."""
    global _embedding_model
    if _embedding_model is None:
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        logger.info("Embedding model loaded")
    return _embedding_model


def get_qdrant_client() -> QdrantClient:
    """Returns the Qdrant client, connecting on first call."""
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port
        )
        logger.info(
            f"Connected to Qdrant at "
            f"{settings.qdrant_host}:{settings.qdrant_port}"
        )
    return _qdrant_client


# ── Collection setup ──────────────────────────────────────────────────────────

def ensure_collection_exists() -> None:
    """
    Creates the Qdrant collection if it doesn't exist.
    Safe to call repeatedly — checks before creating.
    
    A Qdrant collection is like a table in PostgreSQL,
    but instead of rows, it stores vectors with metadata (payload).
    
    Distance.COSINE: vectors are compared by angle between them.
    Cosine similarity of 1.0 = identical direction = identical meaning.
    Cosine similarity of 0.0 = perpendicular = unrelated meaning.
    """
    client = get_qdrant_client()
    existing = [c.name for c in client.get_collections().collections]

    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE
            )
        )
        logger.info(f"Created Qdrant collection: {COLLECTION_NAME}")
    else:
        logger.info(f"Qdrant collection exists: {COLLECTION_NAME}")


# ── PDF Processing ─────────────────────────────────────────────────────────────

def extract_text_from_pdf(file_path: str) -> list[dict]:
    """
    Reads a PDF and returns a list of page objects.
    
    Returns:
        [{"page_number": 1, "text": "full page text"}, ...]
    
    Why page by page?
    We preserve page numbers so citations can point to
    the exact page. "See page 4" is more useful than
    "see somewhere in the document".
    """
    reader = PdfReader(file_path)
    pages = []

    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text and text.strip():  # skip blank pages
            pages.append({
                "page_number": i + 1,
                "text": text.strip()
            })

    logger.info(
        f"Extracted {len(pages)} pages from {Path(file_path).name}"
    )
    return pages


def chunk_text(text: str, page_number: int) -> list[dict]:
    """
    Splits a page's text into overlapping chunks.
    
    Why not split by sentences?
    Sentence splitting is language-dependent and fails on
    Bangla, mixed-language text, and poorly formatted PDFs.
    Character-based chunking is simpler and more robust.
    
    Args:
        text: full page text
        page_number: which page this came from
    
    Returns:
        [{"text": "chunk text", "page_number": 1, "chunk_index": 0}, ...]
    """
    chunks = []
    start = 0
    chunk_index = 0

    while start < len(text):
        end = start + CHUNK_SIZE
        chunk_text = text[start:end]

        if chunk_text.strip():  # skip whitespace-only chunks
            chunks.append({
                "text": chunk_text.strip(),
                "page_number": page_number,
                "chunk_index": chunk_index
            })
            chunk_index += 1

        # Move forward by (CHUNK_SIZE - CHUNK_OVERLAP)
        # The overlap means adjacent chunks share 64 characters
        start += CHUNK_SIZE - CHUNK_OVERLAP

    return chunks


# ── Indexing ──────────────────────────────────────────────────────────────────

def index_document(
    file_path: str,
    document_id: int,
    document_name: str
) -> int:
    """
    Full document indexing pipeline:
    1. Extract text from PDF page by page
    2. Chunk each page into overlapping segments
    3. Embed all chunks into vectors (batched)
    4. Store vectors + metadata in Qdrant
    
    Args:
        file_path: path to the PDF on disk
        document_id: PostgreSQL ID (for filtering later)
        document_name: original filename (for citations)
    
    Returns:
        total number of chunks indexed
    """
    ensure_collection_exists()
    model = get_embedding_model()
    client = get_qdrant_client()

    # Step 1: Extract pages
    pages = extract_text_from_pdf(file_path)
    if not pages:
        raise ValueError("PDF contains no extractable text")

    # Step 2: Chunk all pages
    all_chunks = []
    for page in pages:
        chunks = chunk_text(page["text"], page["page_number"])
        all_chunks.extend(chunks)

    if not all_chunks:
        raise ValueError("No chunks generated from PDF")

    logger.info(
        f"Indexing {len(all_chunks)} chunks "
        f"from document #{document_id}"
    )

    # Step 3: Embed all chunks in one batch
    # Batching is faster than embedding one by one
    texts = [c["text"] for c in all_chunks]
    vectors = model.encode(
        texts,
        batch_size=32,        # process 32 chunks at once
        show_progress_bar=False,
        normalize_embeddings=True  # normalize for cosine similarity
    )

    # Step 4: Build Qdrant points
    # Each point = one vector + payload (metadata)
    # The payload is what gets returned with search results
    points = []
    for i, (chunk, vector) in enumerate(zip(all_chunks, vectors)):
        points.append(
            PointStruct(
                id=str(uuid.uuid4()),  # unique ID for each chunk
                vector=vector.tolist(),
                payload={
                    "document_id": document_id,
                    "document_name": document_name,
                    "page_number": chunk["page_number"],
                    "chunk_index": chunk["chunk_index"],
                    "text": chunk["text"]
                }
            )
        )

    # Step 5: Upload to Qdrant in batches of 100
    batch_size = 100
    for i in range(0, len(points), batch_size):
        batch = points[i:i + batch_size]
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=batch
        )

    logger.info(
        f"Indexed {len(points)} chunks for document #{document_id}"
    )
    return len(points)


# ── Retrieval ─────────────────────────────────────────────────────────────────

def retrieve_chunks(
    question: str,
    top_k: int = 5,
    document_ids: list[int] | None = None
) -> list[dict]:
    """
    Finds the most relevant chunks for a question.
    
    Process:
    1. Embed the question into a vector
    2. Search Qdrant for the closest chunk vectors
    3. Optionally filter by document_ids
    4. Return chunks with their metadata and scores
    
    Why filter by document_ids?
    If a user uploads 10 documents but only wants to
    query 2 specific contracts, we filter at the vector
    DB level — much faster than filtering after retrieval.
    """
    model = get_embedding_model()
    client = get_qdrant_client()

    # Embed the question
    query_vector = model.encode(
        question,
        normalize_embeddings=True
    ).tolist()

    # Build optional filter for specific documents
    search_filter = None
    if document_ids:
        search_filter = Filter(
            must=[
                FieldCondition(
                    key="document_id",
                    match=MatchAny(any=document_ids)
                )
            ]
        )

    # Search Qdrant (support multiple client API versions, fallback to REST)
    if hasattr(client, "search"):
        results = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            limit=top_k,
            query_filter=search_filter,
            with_payload=True,  # return the chunk text and metadata
            score_threshold=0.15  # ignore chunks below 15% similarity
        )
    elif hasattr(client, "search_points"):
        results = client.search_points(
            collection_name=COLLECTION_NAME,
            vector=query_vector,
            limit=top_k,
            query_filter=search_filter,
            with_payload=True,
            score_threshold=0.15
        ).result
    else:
        # REST fallback for older clients
        payload = {
            "vector": query_vector,
            "limit": top_k,
            "with_payload": True,
            "score_threshold": 0.15,
        }
        if search_filter is not None:
            payload["filter"] = search_filter.model_dump()

        url = f"http://{settings.qdrant_host}:{settings.qdrant_port}/collections/{COLLECTION_NAME}/points/search"
        with httpx.Client(timeout=10.0) as http:
            resp = http.post(url, json=payload)
            resp.raise_for_status()
            results = resp.json().get("result", [])

    # Format results
    chunks = []
    for result in results:
        payload = result.payload
        chunks.append({
            "document_id": payload["document_id"],
            "document_name": payload["document_name"],
            "page_number": payload["page_number"],
            "chunk_index": payload["chunk_index"],
            "text": payload["text"],
            "score": round(result.score, 4)
        })

    logger.info(
        f"Retrieved {len(chunks)} chunks for: '{question[:50]}...'"
    )
    return chunks


# ── Answer Generation ─────────────────────────────────────────────────────────

def build_context(chunks: list[dict]) -> str:
    """
    Formats retrieved chunks into a context string for the LLM.
    Each chunk is labeled with its source for citation.
    """
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        context_parts.append(
            f"[Source {i}: {chunk['document_name']}, "
            f"Page {chunk['page_number']}]\n"
            f"{chunk['text']}"
        )
    return "\n\n---\n\n".join(context_parts)


@track_llm_call("rag_generate_answer")
def generate_answer(question: str, chunks: list[dict]) -> str:
    """
    Sends retrieved chunks + question to Groq LLM.
    Returns the complete answer as a string.
    
    This is the 'G' in RAG — generation.
    The LLM synthesizes an answer from the retrieved context.
    It cannot use knowledge outside the provided chunks
    because the system prompt explicitly forbids it.
    """
    if not chunks:
        return (
            "No relevant information was found in the "
            "uploaded documents for your question."
        )

    client = Groq(api_key=settings.groq_api_key)
    context = build_context(chunks)

    user_message = (
        f"Context from documents:\n\n{context}\n\n"
        f"Question: {question}\n\n"
        f"Answer based only on the context above:"
    )

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": RAG_SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        max_tokens=1024,
        temperature=0.2  # low = more factual, less creative
    )

    return response.choices[0].message.content


@track_llm_call("rag_generate_stream")
def generate_answer_stream(
    question: str,
    chunks: list[dict]
) -> Generator[str, None, None]:
    """
    Same as generate_answer but streams tokens as they arrive.
    
    Why streaming?
    Groq takes 2-5 seconds to generate a full answer.
    Streaming shows the user tokens appearing in real time
    instead of waiting for the complete response.
    This dramatically improves perceived responsiveness.
    
    Yields individual text tokens as strings.
    The FastAPI endpoint collects these and streams
    them to the client as Server-Sent Events (SSE).
    """
    if not chunks:
        yield "No relevant information was found in the uploaded documents."
        return

    client = Groq(api_key=settings.groq_api_key)
    context = build_context(chunks)

    user_message = (
        f"Context from documents:\n\n{context}\n\n"
        f"Question: {question}\n\n"
        f"Answer based only on the context above:"
    )

    stream = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": RAG_SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        max_tokens=1024,
        temperature=0.2,
        stream=True  # ← this is the only difference
    )

    for chunk in stream:
        token = chunk.choices[0].delta.content
        if token:
            yield token