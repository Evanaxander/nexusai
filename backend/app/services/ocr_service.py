import json
import base64
import logging
from groq import Groq
from app.core.config import get_settings

from app.core.observability import track_llm_call  # ← add import

logger = logging.getLogger(__name__)
settings = get_settings()


# The exact prompt sent to Groq Vision.
# Specific, structured, with examples — this is prompt engineering.
OCR_PROMPT = """You are a precise invoice data extraction system.
Extract information from this invoice/receipt image and return ONLY
valid JSON with exactly these fields:

{
    "vendor": "exact company or shop name as shown",
    "amount": 0.00,
    "currency": "BDT",
    "invoice_date": "YYYY-MM-DD",
    "items": ["item name - quantity - price", "..."],
    "confidence": "high"
}

Rules:
- amount must be a number, not a string
- currency: use "BDT" for Bangladeshi Taka, otherwise use ISO code
- invoice_date: convert to YYYY-MM-DD format. If only month/year visible, use first of month
- items: list each line item. Max 10 items.
- confidence: "high" if all fields clear, "medium" if some unclear, "low" if image is poor
- If any field is truly not visible, use null (not "null" string)
- Return ONLY the JSON object. No explanation. No markdown. No code blocks."""


def _encode_image(image_bytes: bytes, content_type: str) -> str:
    """Convert image bytes to base64 data URL for Groq API."""
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:{content_type};base64,{b64}"


def _clean_json_response(raw: str) -> str:
    """
    Clean Groq's response in case it wrapped JSON in markdown.
    Sometimes models return ```json {...} ``` even when told not to.
    """
    raw = raw.strip()
    if raw.startswith("```"):
        # Remove opening ```json or ```
        lines = raw.split("\n")
        lines = lines[1:]  # remove first line
        # Remove closing ```
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        raw = "\n".join(lines)
    return raw.strip()


@track_llm_call("invoice_ocr")
def extract_invoice_data(image_bytes: bytes, content_type: str) -> dict:
    """
    Main OCR function. Sends image to Groq Vision,
    parses the structured response, returns a clean dict.
    
    Args:
        image_bytes: raw image file bytes
        content_type: MIME type e.g. "image/jpeg"
    
    Returns:
        dict with keys: vendor, amount, currency,
        invoice_date, items, confidence
    
    Raises:
        ValueError: if Groq returns unparseable response
        Exception: if Groq API call fails
    """
    client = Groq(api_key=settings.groq_api_key)
    image_data_url = _encode_image(image_bytes, content_type)

    logger.info(f"Sending image to Groq Vision ({len(image_bytes)} bytes)")

    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": image_data_url}
                    },
                    {
                        "type": "text",
                        "text": OCR_PROMPT
                    }
                ]
            }
        ],
        max_tokens=800,
        temperature=0.1  # low temperature = more consistent, less creative
    )

    raw_content = response.choices[0].message.content
    logger.info(f"Groq raw response: {raw_content[:200]}...")

    cleaned = _clean_json_response(raw_content)

    try:
        extracted = json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Groq response: {cleaned}")
        raise ValueError(f"Groq returned invalid JSON: {e}")

    # Normalize the data — handle edge cases
    # Sometimes models return amount as string "1,250.00"
    if isinstance(extracted.get("amount"), str):
        # Remove commas, currency symbols, spaces
        amount_str = extracted["amount"].replace(",", "").replace(
            "৳", "").replace("TK", "").replace("Tk", "").strip()
        try:
            extracted["amount"] = float(amount_str)
        except ValueError:
            extracted["amount"] = 0.0

    # Ensure items is always a list
    if extracted.get("items") and not isinstance(extracted["items"], list):
        extracted["items"] = [str(extracted["items"])]

    logger.info(
        f"Extracted: vendor={extracted.get('vendor')}, "
        f"amount={extracted.get('amount')}, "
        f"confidence={extracted.get('confidence')}"
    )

    return extracted


