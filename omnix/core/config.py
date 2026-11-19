"""
Configuration management for OMNIX Agent using Pydantic Settings.
Reads environment variables safely without hardcoding secrets.
"""

from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable fallback and validation."""

    # Application
    app_name: str = "OMNIX Agent"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True

    # Server Ports & Hosts
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    streamlit_port: int = 8501

    # Security & Keys
    secret_key: str = "dev-insecure-secret-key-change-in-production"
    groq_api_key: Optional[str] = None
    llm_model: str = "llama-3.3-70b-versatile"
    llm_temperature: float = 0.1

    # Database
    database_url: str = "sqlite:///./omnix.db"

    # Vector Storage / RAG
    chroma_persist_directory: str = "./chroma_db"
    embedding_model_name: str = "all-MiniLM-L6-v2"

    # Business Rules Defaults
    default_currency: str = "INR"
    max_auto_approval_limit: float = 75000.00
    high_value_threshold: float = 400000.00

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """Return a cached singleton instance of application settings."""
    return Settings()
