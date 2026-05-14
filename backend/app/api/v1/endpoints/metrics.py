import logging
from fastapi import APIRouter
from app.core.observability import metrics

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get(
    "/",
    summary="Get agent performance metrics"
)
def get_metrics():
    """
    Returns aggregated metrics for all agent runs:
    - Total runs
    - Success rate
    - Average response time
    - Agent usage breakdown
    - Last 10 runs with details

    This is your observability dashboard endpoint.
    In Week 6 the React frontend will visualize this data.
    """
    return metrics.get_stats()


@router.get(
    "/health-score",
    summary="Get system health score"
)
def get_health_score():
    """
    Simple health score based on recent performance.
    Returns a score from 0-100 and status label.
    """
    stats = metrics.get_stats()

    if stats["total_runs"] == 0:
        return {
            "score": 100,
            "status": "idle",
            "message": "No runs recorded yet"
        }

    # Score based on success rate and speed
    success_score = stats["success_rate"] * 70  # 70% weight
    speed_score = max(
        0,
        30 - (stats["avg_duration_seconds"] * 3)
    )  # 30% weight — penalize if avg > 10s

    score = round(success_score + speed_score)

    if score >= 80:
        status = "healthy"
    elif score >= 60:
        status = "degraded"
    else:
        status = "unhealthy"

    return {
        "score": min(score, 100),
        "status": status,
        "success_rate": stats["success_rate"],
        "avg_duration_seconds": stats["avg_duration_seconds"],
        "total_runs": stats["total_runs"]
    }