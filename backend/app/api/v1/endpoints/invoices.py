import json
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.db.session import get_db
from app.models.invoice import Invoice
from app.schemas.invoice import InvoiceOut, WeeklySummary, InvoiceVerify
from app.services.ocr_service import extract_invoice_data
from app.utils.file_handler import validate_image, save_upload

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.post(
    "/process",
    response_model=InvoiceOut,
    summary="Upload invoice image and extract data with OCR"
)
async def process_invoice(
    file: UploadFile = File(..., description="Invoice image (JPEG/PNG/WebP)"),
    uploaded_by: str = Form(default="api", description="Who is uploading"),
    db: Session = Depends(get_db)
):
    """
    Full invoice processing pipeline:
    1. Validate the uploaded image
    2. Read image bytes into memory
    3. Send to Groq Vision for OCR extraction
    4. Save image to disk
    5. Store extracted data in PostgreSQL
    6. Return the saved invoice record
    """
    # Step 1: Read file into memory
    image_bytes = await file.read()

    # Step 2: Validate (raises HTTPException if invalid)
    validate_image(file.content_type, len(image_bytes))

    # Step 3: OCR extraction via Groq Vision
    try:
        extracted = extract_invoice_data(image_bytes, file.content_type)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"OCR failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="OCR processing failed. Please try a clearer image."
        )

    # Step 4: Save image to disk
    try:
        image_path = save_upload(image_bytes, file.content_type)
    except Exception as e:
        logger.warning(f"Could not save image: {e}")
        image_path = None  # not critical — proceed without saving

    # Step 5: Store in database
    invoice = Invoice(
        vendor=extracted.get("vendor") or "Unknown",
        amount=float(extracted.get("amount") or 0.0),
        currency=extracted.get("currency") or "BDT",
        invoice_date=extracted.get("invoice_date"),
        items=json.dumps(extracted.get("items") or []),
        raw_text=json.dumps(extracted),
        image_path=image_path,
        uploaded_by=uploaded_by,
        is_verified=False
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    logger.info(f"Invoice #{invoice.id} saved: {invoice.vendor} {invoice.amount}")
    return invoice


@router.get(
    "/weekly-summary",
    response_model=WeeklySummary,
    summary="Get this week's expense summary"
)
def get_weekly_summary(db: Session = Depends(get_db)):
    """
    Aggregates all invoices from the last 7 days.
    Returns total, count, top vendors, and day-by-day breakdown.
    """
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)

    invoices = db.scalars(
        select(Invoice)
        .where(Invoice.created_at >= week_ago)
        .order_by(Invoice.created_at.desc())
    ).all()

    if not invoices:
        return WeeklySummary(
            period_start=week_ago.date().isoformat(),
            period_end=now.date().isoformat(),
            total_expenses=0.0,
            currency="BDT",
            invoice_count=0,
            top_vendors=[],
            daily_breakdown={}
        )

    total = round(sum(i.amount for i in invoices), 2)

    # Top vendors by total spend
    vendor_totals: dict[str, float] = {}
    for inv in invoices:
        vendor_totals[inv.vendor] = vendor_totals.get(inv.vendor, 0) + inv.amount
    top_vendors = sorted(vendor_totals, key=vendor_totals.get, reverse=True)[:5]

    # Day-by-day breakdown
    daily: dict[str, float] = {}
    for inv in invoices:
        day = inv.created_at.date().isoformat()
        daily[day] = round(daily.get(day, 0) + inv.amount, 2)

    return WeeklySummary(
        period_start=week_ago.date().isoformat(),
        period_end=now.date().isoformat(),
        total_expenses=total,
        currency="BDT",
        invoice_count=len(invoices),
        top_vendors=top_vendors,
        daily_breakdown=daily
    )


@router.get(
    "/",
    response_model=list[InvoiceOut],
    summary="List all invoices"
)
def list_invoices(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Returns paginated list of all invoices, newest first."""
    return db.scalars(
        select(Invoice)
        .order_by(Invoice.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()


@router.get(
    "/{invoice_id}",
    response_model=InvoiceOut,
    summary="Get a single invoice"
)
def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    invoice = db.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@router.patch(
    "/{invoice_id}/verify",
    response_model=InvoiceOut,
    summary="Verify or correct an invoice"
)
def verify_invoice(
    invoice_id: int,
    data: InvoiceVerify,
    db: Session = Depends(get_db)
):
    """
    Human verification endpoint.
    When OCR gets something wrong, the user corrects it here.
    Only updates fields that are provided.
    """
    invoice = db.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if data.vendor is not None:
        invoice.vendor = data.vendor
    if data.amount is not None:
        invoice.amount = data.amount
    if data.invoice_date is not None:
        invoice.invoice_date = data.invoice_date

    invoice.is_verified = data.is_verified
    db.commit()
    db.refresh(invoice)
    return invoice


@router.delete(
    "/{invoice_id}",
    summary="Delete an invoice"
)
def delete_invoice(invoice_id: int, db: Session = Depends(get_db)):
    invoice = db.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    db.delete(invoice)
    db.commit()
    return {"message": f"Invoice #{invoice_id} deleted"} 