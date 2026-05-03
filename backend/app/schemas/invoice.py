from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class InvoiceOut(BaseModel):
    """
    What the API returns after processing an invoice.
    Always returned to the client.
    """
    model_config = {"from_attributes": True}

    id: int
    vendor: str
    amount: float
    currency: str
    invoice_date: Optional[str] = None
    items: Optional[str] = None
    uploaded_by: str
    is_verified: bool
    created_at: datetime


class WeeklySummary(BaseModel):
    """
    Aggregated weekly expense report.
    """
    period_start: str
    period_end: str
    total_expenses: float
    currency: str
    invoice_count: int
    top_vendors: list[str]
    daily_breakdown: dict[str, float]  # {"2026-04-28": 1500.0}


class InvoiceVerify(BaseModel):
    """
    Used when a human confirms or corrects OCR output.
    All fields optional — only update what changed.
    """
    vendor: Optional[str] = None
    amount: Optional[float] = None
    invoice_date: Optional[str] = None
    is_verified: bool = True