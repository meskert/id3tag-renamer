"""Configuration management for ID3Tag-Renamer web application."""
import os
import secrets
from pathlib import Path


class Config:
    """Application configuration from environment variables."""

    def __init__(self):
        """Initialize configuration from environment variables."""
        # Authentication
        self.WEB_USERNAME = os.getenv("WEB_USERNAME")
        self.WEB_PASSWORD = os.getenv("WEB_PASSWORD")
        self.WEB_SESSION_SECRET = os.getenv("WEB_SESSION_SECRET", secrets.token_hex(32))
        self.WEB_REQUIRES_AUTH = bool(self.WEB_USERNAME and self.WEB_PASSWORD)

        # Session settings
        self.SESSION_MAX_AGE = int(os.getenv("WEB_SESSION_MAX_AGE", "1800"))  # 30 minutes

        # Music directory
        self.DEFAULT_MUSIC_DIR = os.getenv("MUSIC_DIR", "/music")

        # Server settings
        self.HOST = os.getenv("HOST", "0.0.0.0")
        self.PORT = int(os.getenv("PORT", "8000"))

        # Template directory
        self.TEMPLATE_DIR = Path(__file__).parent / "templates"
        self.STATIC_DIR = Path(__file__).parent / "static"


config = Config()
