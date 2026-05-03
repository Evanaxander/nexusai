from fastapi import APIRouter
from datetime import datetime

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    """
    Simple health check endpoint.
    Used by Docker and monitoring tools to verify the app is alive.
    """
    return {
        "status": "ok",
        "service": "nexusai-backend",
        "timestamp": datetime.utcnow().isoformat()
    }