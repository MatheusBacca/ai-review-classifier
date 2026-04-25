"""Application configuration loaded from environment variables."""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed settings object for the entire project.

    Attributes:
        database_url: Connection string used by SQLModel engine.
        huggingface_token: Optional token used to access Hugging Face services.
        log_level: Root logger level (e.g. INFO, DEBUG).
        log_directory: Directory where rotating log files are stored.
        log_rotation_max_mb: Maximum size in MB before rotating log file.
        log_backup_count: Maximum number of rotated log files kept on disk.

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

    log_level: str = Field(
        alias="LOG_LEVEL",
        default="INFO",
        description="Application log level.",
    )

    log_directory: str = Field(
        alias="LOG_DIRECTORY",
        default="logs",
        description="Directory where application logs are written.",
    )

    log_rotation_max_mb: int = Field(
        alias="LOG_ROTATION_MAX_MB",
        default=10,
        ge=1,
        description="Maximum log file size in MB before rotation.",
    )

    log_backup_count: int = Field(
        alias="LOG_BACKUP_COUNT",
        default=10,
        ge=1,
        le=10,
        description="Maximum number of rotated log files kept.",
    )


settings = Settings()
