from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache


_BACKEND_DIR = Path(__file__).resolve().parents[2]
_REPO_ROOT = _BACKEND_DIR.parent


class Settings(BaseSettings):
    database_url: str
    groq_api_key: str
    secret_key: str
    upload_dir: str = str(_REPO_ROOT / "uploads")
    max_upload_size_mb: int = 10
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    sentiment_model_path: str = str(_REPO_ROOT / "models" / "sentiment")

    # LangSmith
    langsmith_api_key: str = ""
    langsmith_project: str = "nexusai"
    langchain_tracing_v2: str = "true"
    langchain_endpoint: str = "https://api.smith.langchain.com"

    class Config:
        env_file = _BACKEND_DIR / ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()