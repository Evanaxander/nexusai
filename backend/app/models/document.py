from datetime import datetime
from sqlalchemy import Integer, String, Text, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class Document(Base):
    """
    Stores metadata about uploaded PDF documents.
    
    The actual text chunks and their vectors live in Qdrant.
    This table stores the document-level metadata — filename,
    who uploaded it, how many chunks were indexed, etc.
    
    Why separate from Qdrant?
    Qdrant is optimized for vector similarity search.
    PostgreSQL is optimized for filtering, sorting, and
    relational queries. We use both for what they're good at.
    """
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    filename: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    original_name: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    file_path: Mapped[str] = mapped_column(
        String(500), nullable=False
    )
    total_pages: Mapped[int] = mapped_column(
        Integer, default=0
    )
    total_chunks: Mapped[int] = mapped_column(
        Integer, default=0
    )
    uploaded_by: Mapped[str] = mapped_column(
        String(100), default="api"
    )
    is_indexed: Mapped[bool] = mapped_column(
        Boolean, default=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    def __repr__(self) -> str:
        return (
            f"<Document id={self.id} "
            f"name={self.original_name} "
            f"chunks={self.total_chunks}>"
        )