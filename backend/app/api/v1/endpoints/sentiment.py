import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.sentiment_service import (
    classify_sentiment,
    classify_batch,
    summarize_sentiment
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sentiment", tags=["sentiment"])


class SingleRequest(BaseModel):
    text: str


class BatchRequest(BaseModel):
    texts: list[str]
    summarize: bool = True


class SentimentResult(BaseModel):
    label: str
    confidence: float
    text_preview: str


class BatchResponse(BaseModel):
    results: list[SentimentResult]
    summary: Optional[dict] = None


@router.post(
    "/classify",
    response_model=SentimentResult,
    summary="Classify sentiment of a single text"
)
def classify_single(request: SingleRequest):
    """
    Classify one piece of customer feedback.
    Returns: positive / negative / neutral with confidence score.
    """
    if not request.text.strip():
        raise HTTPException(400, "Text cannot be empty")

    try:
        result = classify_sentiment(request.text)
        return SentimentResult(**result)
    except FileNotFoundError as e:
        raise HTTPException(503, str(e))
    except Exception as e:
        logger.error(f"Sentiment classification failed: {e}", exc_info=True)
        raise HTTPException(500, f"Classification failed: {str(e)}")


@router.post(
    "/classify-batch",
    response_model=BatchResponse,
    summary="Classify sentiment of multiple texts"
)
def classify_multiple(request: BatchRequest):
    """
    Classify a batch of customer feedback texts.
    Optionally returns an aggregate summary.

    Use this for: analysing a week of customer emails,
    processing survey responses, reviewing support tickets.
    """
    if not request.texts:
        raise HTTPException(400, "texts list cannot be empty")

    if len(request.texts) > 100:
        raise HTTPException(400, "Maximum 100 texts per batch")

    try:
        results = classify_batch(request.texts)
        summary = summarize_sentiment(results) if request.summarize else None

        return BatchResponse(
            results=[SentimentResult(**r) for r in results],
            summary=summary
        )
    except FileNotFoundError as e:
        raise HTTPException(503, str(e))
    except Exception as e:
        logger.error(f"Batch classification failed: {e}", exc_info=True)
        raise HTTPException(500, f"Classification failed: {str(e)}")