import os
import logging
import time
import functools
from datetime import datetime
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def setup_langsmith() -> bool:
    """
    Configure LangSmith tracing via environment variables.
    LangChain/LangGraph automatically detects these and sends
    traces to LangSmith without any code changes needed.

    Returns True if LangSmith is configured, False if skipped.
    """
    if not settings.langsmith_api_key:
        logger.warning(
            "LANGSMITH_API_KEY not set — tracing disabled"
        )
        return False

    # LangChain reads these env vars automatically
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_ENDPOINT"] = settings.langchain_endpoint
    os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project

    logger.info(
        f"LangSmith tracing enabled — "
        f"project: {settings.langsmith_project}"
    )
    return True


def track_llm_call(operation_name: str):
    """
    Decorator that logs every LLM call with:
    - Operation name
    - Execution time
    - Success or failure
    - Timestamp

    Use this on any function that calls an LLM directly
    (Groq, OCR, etc.) so you have local logs even without
    LangSmith configured.

    Usage:
        @track_llm_call("invoice_ocr")
        def extract_invoice_data(...):
            ...
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            timestamp = datetime.utcnow().isoformat()

            logger.info(
                f"[LLM CALL] operation={operation_name} "
                f"started_at={timestamp}"
            )

            try:
                result = func(*args, **kwargs)
                elapsed = round(time.time() - start_time, 3)

                logger.info(
                    f"[LLM CALL] operation={operation_name} "
                    f"status=success "
                    f"duration={elapsed}s"
                )
                return result

            except Exception as e:
                elapsed = round(time.time() - start_time, 3)

                logger.error(
                    f"[LLM CALL] operation={operation_name} "
                    f"status=failed "
                    f"duration={elapsed}s "
                    f"error={str(e)}"
                )
                raise

        return wrapper
    return decorator


class MetricsCollector:
    """
    In-memory metrics store for the evaluation dashboard.
    Tracks every agent run with timing and routing data.

    In production this would write to PostgreSQL or Redis.
    For Week 5 we keep it in memory — simple and effective
    for demonstrating the observability concept.
    """

    def __init__(self):
        self.runs: list[dict] = []

    def record_run(
        self,
        user_message: str,
        agents_used: dict,
        duration_seconds: float,
        success: bool,
        final_answer_length: int
    ):
        self.runs.append({
            "timestamp": datetime.utcnow().isoformat(),
            "user_message_preview": user_message[:80],
            "agents_used": agents_used,
            "duration_seconds": round(duration_seconds, 3),
            "success": success,
            "answer_length": final_answer_length
        })

        # Keep only last 100 runs in memory
        if len(self.runs) > 100:
            self.runs = self.runs[-100:]

    def get_stats(self) -> dict:
        if not self.runs:
            return {
                "total_runs": 0,
                "success_rate": 0.0,
                "avg_duration_seconds": 0.0,
                "agent_usage": {},
                "recent_runs": []
            }

        total = len(self.runs)
        successful = sum(1 for r in self.runs if r["success"])

        avg_duration = round(
            sum(r["duration_seconds"] for r in self.runs) / total, 3
        )

        # Count how often each agent was used
        agent_usage = {
            "invoice": 0,
            "document": 0,
            "sentiment": 0
        }
        for run in self.runs:
            for agent, used in run.get("agents_used", {}).items():
                if used and agent in agent_usage:
                    agent_usage[agent] += 1

        return {
            "total_runs": total,
            "success_rate": round(successful / total, 3),
            "avg_duration_seconds": avg_duration,
            "agent_usage": agent_usage,
            "recent_runs": self.runs[-10:]  # last 10
        }


# Global singleton — shared across all requests
metrics = MetricsCollector()