"""Configuration package for application settings."""

from app.config.logging import configure_logging
from app.config.settings import settings

__all__ = ["settings", "configure_logging"]
