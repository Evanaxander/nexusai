import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.models  # noqa: F401
from app.db.base import Base
from app.db.session import engine
from app.api.v1.router import api_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting NexusAI backend...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified/created")
    logger.info("NexusAI ready at http://localhost:8000/docs")
    yield
    # Shutdown (runs when server stops)
    logger.info("NexusAI shutting down...")


app = FastAPI(
    title="NexusAI",
    description="Multi-Modal Business Intelligence Platform",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)