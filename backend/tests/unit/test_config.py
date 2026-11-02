import pytest

from app.core.config import Settings


def test_environment_overrides_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@db.example:5432/other")
    assert Settings().database_url.endswith("db.example:5432/other")
