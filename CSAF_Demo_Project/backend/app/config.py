"""Application settings loaded from environment variables.

Business rules (budget, quantity, checkout confirmation) are stored per agent
in the database. This module only holds process-level configuration such as
the database URL and optional Gemini credentials.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration. Secrets never belong in source files."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    agent_provider: str = "mock"
    database_url: str = "sqlite:///./nozama.db"

    @property
    def gemini_configured(self) -> bool:
        return bool(self.gemini_api_key.strip())

    @property
    def effective_provider(self) -> str:
        """Gemini is opt-in and requires a key. Missing keys stay in mock mode."""
        requested = (self.agent_provider or "mock").strip().lower()
        if requested == "gemini" and not self.gemini_configured:
            return "mock"
        if requested not in {"mock", "gemini"}:
            return "mock"
        return requested


@lru_cache
def get_settings() -> Settings:
    return Settings()
