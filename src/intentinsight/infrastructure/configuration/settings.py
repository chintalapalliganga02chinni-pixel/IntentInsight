"""Application configuration management."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Application configuration loaded from environment variables."""

    github_token: str
    github_api_url: str
    github_api_version: str
    database_url: str
    log_level: str


def load_settings() -> Settings:
    """Load and validate application settings from the environment."""
    github_token = os.getenv("GITHUB_TOKEN", "").strip()

    if not github_token:
        raise ValueError(
            "GITHUB_TOKEN is not configured. "
            "Add it to the local .env file before using GitHub services."
        )

    return Settings(
        github_token=github_token,
        github_api_url=os.getenv(
            "GITHUB_API_URL",
            "https://api.github.com",
        ),
        github_api_version=os.getenv(
            "GITHUB_API_VERSION",
            "2026-03-10",
        ),
        database_url=os.getenv(
            "DATABASE_URL",
            "sqlite:///./intentinsight.db",
        ),
        log_level=os.getenv(
            "LOG_LEVEL",
            "INFO",
        ),
    )