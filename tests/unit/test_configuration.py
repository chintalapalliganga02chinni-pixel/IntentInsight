"""Tests for application configuration."""

from intentinsight.infrastructure.configuration.settings import Settings


def test_settings_can_be_created() -> None:
    """Verify that the Settings model can be instantiated."""
    settings = Settings(
        github_token="test-token",
        github_api_url="https://api.github.com",
        github_api_version="2026-03-10",
        database_url="sqlite:///./test.db",
        log_level="INFO",
    )

    assert settings.github_token == "test-token"
    assert settings.github_api_url == "https://api.github.com"
    assert settings.log_level == "INFO"