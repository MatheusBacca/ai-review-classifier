"""Application configuration loaded from environment variables."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed settings object for the entire project."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = Field(
        alias="DATABASE_URL",
        min_length=1,
        description="Database connection URL for PostgreSQL.",
    )

    huggingface_token: str = Field(
        alias="HUGGINGFACE_TOKEN",
        min_length=1,
        description="Token da Hugging Face.",
        optional=True,
    )


settings = Settings()
