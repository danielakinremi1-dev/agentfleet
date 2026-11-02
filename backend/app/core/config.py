from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# The .env file lives at the repository root so Docker Compose and the backend share one file.
REPO_ROOT_ENV = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    """Application configuration, read from environment variables (then the repo-root .env)."""

    model_config = SettingsConfigDict(env_file=REPO_ROOT_ENV, extra="ignore")

    database_url: str = "postgresql+asyncpg://agentfleet:agentfleet@localhost:5433/agentfleet"
    test_database_url: str = (
        "postgresql+asyncpg://agentfleet:agentfleet@localhost:5433/agentfleet_test"
    )
    # Echo SQL statements to the log; useful when learning or debugging queries.
    database_echo: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
