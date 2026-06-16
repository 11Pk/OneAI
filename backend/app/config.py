"""
Application settings loaded from environment variables.
Uses pydantic-settings for easy .env file support.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """All configuration in one place."""

    # Database connection string
    database_url: str = "postgresql+asyncpg://oneai:oneai_password@localhost:5432/oneai"

    # API keys for AI providers
    openrouter_api_key: str = ""
    gemini_api_key: str = ""
    groq_api_key: str = ""

    # Default models for each provider
    openrouter_model: str = "openai/gpt-4o-mini"
    gemini_model: str = "gemini-2.0-flash"
    groq_model: str = "llama-3.3-70b-versatile"

    # Allowed frontend origins for CORS
    cors_origins: str = "http://localhost:3000"

    # Default user ID (from seed data in schema.sql)
    default_user_id: str = "00000000-0000-0000-0000-000000000001"

    class Config:
        env_file = ".env"
        extra = "ignore"


# Single shared settings instance used across the app
settings = Settings()
