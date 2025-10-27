"""Configuration management for Service20 FastAPI application."""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "Service20 Investment Opportunities API"
    app_version: str = "1.0.0"
    api_port: int = int(os.getenv("API_PORT", 8000))
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"

    # Database
    database_url: str = os.getenv("DATABASE_URL", "")

    # Database Connection Pool
    db_pool_min_size: int = 5
    db_pool_max_size: int = 20
    db_pool_max_queries: int = 50000
    db_pool_max_inactive_connection_lifetime: float = 300.0

    # Tracing
    arize_space_key: Optional[str] = os.getenv("ARIZE_SPACE_KEY")
    arize_api_key: Optional[str] = os.getenv("ARIZE_API_KEY")
    langfuse_public_key: Optional[str] = os.getenv("LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key: Optional[str] = os.getenv("LANGFUSE_SECRET_KEY")
    langfuse_base_url: str = os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com")

    # CORS
    cors_origins: list = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8898",
    ]

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
