"""Application configuration loaded from environment variables."""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed settings object for the entire project.

    Attributes:
        database_url: Connection string used by SQLModel engine.
        huggingface_token: Optional token used to access Hugging Face services.

    Example:
        >>> settings = Settings(DATABASE_URL="sqlite:///tmp.db")
        >>> settings.database_url
        'sqlite:///tmp.db'
    """

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

    huggingface_token: Optional[str] = Field(
        alias="HUGGINGFACE_TOKEN",
        description="Token da Hugging Face.",
    )


settings = Settings()
