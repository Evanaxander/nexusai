from datetime import datetime
from sqlalchemy import Integer, String, Float, Text, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class Invoice(Base):
    """
    Stores every invoice/receipt processed by the OCR system.
    
    Fields explained:
    - vendor: company or shop name from the receipt
    - amount: total amount as float (e.g. 1250.50)
    - currency: BDT by default, USD/EUR if detected
    - invoice_date: date shown on the invoice (string, not Date type
      because invoice dates come in many formats)
    - items: JSON string list of line items ["Rice 5kg - 450 BDT"]
    - raw_text: full OCR extraction result for debugging
    - image_path: where the image file is saved on disk
    - uploaded_by: who sent this (whatsapp number, user ID, etc.)
    - is_verified: False by default, True when human confirms it
    - created_at: when we received it
    """
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, autoincrement=True
    )
    vendor: Mapped[str] = mapped_column(
        String(200), nullable=False, default="Unknown"
    )
    amount: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    currency: Mapped[str] = mapped_column(
        String(10), nullable=False, default="BDT"
    )
    invoice_date: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )
    items: Mapped[str | None] = mapped_column(
        Text, nullable=True  # stored as JSON string
    )
    raw_text: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    image_path: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )
    uploaded_by: Mapped[str] = mapped_column(
        String(100), nullable=False, default="api"
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<Invoice id={self.id} vendor={self.vendor} amount={self.amount}>"