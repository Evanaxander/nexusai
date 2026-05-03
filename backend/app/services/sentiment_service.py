import logging
from pathlib import Path
from transformers import pipeline, Pipeline
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Singleton — loaded once, reused on every request
# Loading the model takes ~2 seconds
# We never want that delay on every API call
_sentiment_pipeline: Pipeline | None = None


def get_sentiment_pipeline() -> Pipeline:
    global _sentiment_pipeline

    if _sentiment_pipeline is None:
        model_path = Path(settings.sentiment_model_path)

        if not model_path.exists():
            raise FileNotFoundError(
                f"Sentiment model not found at {model_path}."
            )

        logger.info(f"Loading sentiment model from {model_path}")

        from peft import AutoPeftModelForSequenceClassification
        from transformers import AutoTokenizer, DistilBertTokenizerFast

        # Load tokenizer
        loaded_tokenizer = AutoTokenizer.from_pretrained(
            str(model_path),
            model_max_length=128
        )
        # DistilBERT doesn't use token_type_ids in newer versions
        loaded_tokenizer.model_input_names = ["input_ids", "attention_mask"]

        # Load LoRA adapter model
        loaded_model = AutoPeftModelForSequenceClassification.from_pretrained(
            str(model_path),
            num_labels=3,
            id2label={0: "negative", 1: "positive", 2: "neutral"},
            label2id={"negative": 0, "positive": 1, "neutral": 2},
            ignore_mismatched_sizes=True
        )

        _sentiment_pipeline = pipeline(
            "text-classification",
            model=loaded_model,
            tokenizer=loaded_tokenizer,
            device=-1,
            truncation=True,
            max_length=128
        )

        logger.info("Sentiment model loaded successfully")

    return _sentiment_pipeline


def classify_sentiment(text: str) -> dict:
    """
    Classify a single text as positive, negative, or neutral.

    Returns:
        {
            "label": "positive",
            "confidence": 0.94,
            "text_preview": "first 80 chars..."
        }
    """
    classifier = get_sentiment_pipeline()
    result = classifier(text[:512])[0]  # truncate very long inputs

    return {
        "label": result["label"],
        "confidence": round(result["score"], 4),
        "text_preview": text[:80] + "..." if len(text) > 80 else text
    }


def classify_batch(texts: list[str]) -> list[dict]:
    """
    Classify multiple texts at once.
    Batch processing is faster than one-by-one calls.

    Returns list of results in same order as input.
    """
    if not texts:
        return []

    classifier = get_sentiment_pipeline()

    # Truncate each text before sending to model
    truncated = [t[:512] for t in texts]
    results = classifier(truncated)

    return [
        {
            "label": r["label"],
            "confidence": round(r["score"], 4),
            "text_preview": t[:80] + "..." if len(t) > 80 else t
        }
        for r, t in zip(results, texts)
    ]


def summarize_sentiment(results: list[dict]) -> dict:
    """
    Aggregate multiple sentiment results into a summary.
    Used by the Sentiment Agent to report on a batch of feedback.

    Returns:
        {
            "total": 10,
            "positive": 6,
            "negative": 3,
            "neutral": 1,
            "dominant": "positive",
            "average_confidence": 0.87,
            "alert": True/False  ← True if >40% negative
        }
    """
    if not results:
        return {
            "total": 0,
            "positive": 0,
            "negative": 0,
            "neutral": 0,
            "dominant": "unknown",
            "average_confidence": 0.0,
            "alert": False
        }

    counts = {"positive": 0, "negative": 0, "neutral": 0}
    for r in results:
        label = r["label"].lower()
        if label in counts:
            counts[label] += 1

    total = len(results)
    dominant = max(counts, key=counts.get)
    avg_confidence = round(
        sum(r["confidence"] for r in results) / total, 4
    )

    # Alert if more than 40% of feedback is negative
    negative_ratio = counts["negative"] / total
    alert = negative_ratio > 0.4

    return {
        "total": total,
        **counts,
        "dominant": dominant,
        "average_confidence": avg_confidence,
        "alert": alert,
        "negative_ratio": round(negative_ratio, 3)
    }