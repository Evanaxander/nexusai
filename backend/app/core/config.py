from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str
    groq_api_key: str
    secret_key: str
    upload_dir: str = "../uploads"
    max_upload_size_mb: int = 10
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    sentiment_model_path: str = "../models/sentiment"  # ← add this

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()