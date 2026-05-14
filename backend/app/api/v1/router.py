from fastapi import APIRouter
from app.api.v1.endpoints import (
    health, invoices, documents, agent, sentiment, metrics
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health.router)
api_router.include_router(invoices.router)
api_router.include_router(documents.router)
api_router.include_router(agent.router)
api_router.include_router(sentiment.router)
api_router.include_router(metrics.router)