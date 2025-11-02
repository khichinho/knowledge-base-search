from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App Info
    app_name: str = "KnowledgeBase API"
    app_version: str = "1.0.0"
    debug: bool = True

    # OpenAI
    openai_api_key: str

    # Storage
    upload_dir: str = "./uploads"
    chroma_persist_dir: str = "./chroma_db"

    # Embedding
    embedding_model: str = "all-MiniLM-L6-v2"

    # LLM
    llm_model: str = "gpt-3.5-turbo"
    max_tokens: int = 1000
    temperature: float = 0.7

    # Search
    top_k_results: int = 5
    chunk_size: int = 500
    chunk_overlap: int = 50

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()
