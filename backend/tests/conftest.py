"""Shared fixtures. Tests run against a real PostgreSQL database (ADR-0005)."""

import asyncio
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import make_url, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings, get_settings
from app.core.db import create_engine, create_sessionmaker
from app.main import create_app
from app.models import Base

BACKEND_DIR = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    settings = get_settings()
    return Settings(database_url=settings.test_database_url)


@pytest.fixture(scope="session")
def alembic_config(test_settings: Settings) -> Config:
    config = Config(BACKEND_DIR / "alembic.ini")
    # configparser treats % as interpolation, so escape it (passwords may contain %).
    config.set_main_option("sqlalchemy.url", test_settings.database_url.replace("%", "%%"))
    return config


async def _create_database_if_missing(database_url: str) -> None:
    url = make_url(database_url)
    # CREATE DATABASE cannot run inside a transaction, hence AUTOCOMMIT on the maintenance DB.
    admin = create_async_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    try:
        async with admin.connect() as conn:
            exists = await conn.scalar(
                text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": url.database}
            )
            if not exists:
                quoted = conn.dialect.identifier_preparer.quote(str(url.database))
                await conn.execute(text(f"CREATE DATABASE {quoted}"))
    finally:
        await admin.dispose()


@pytest.fixture(scope="session", autouse=True)
def migrated_database(test_settings: Settings, alembic_config: Config) -> None:
    """Create the test database and bring it to the latest migration, once per test session."""
    asyncio.run(_create_database_if_missing(test_settings.database_url))
    command.upgrade(alembic_config, "head")


@pytest.fixture
async def engine(test_settings: Settings) -> AsyncIterator[AsyncEngine]:
    engine = create_engine(test_settings.database_url)
    # Truncate before (not after) each test so a crashed earlier run cannot leak state in.
    # Real commits rather than rollback-per-test: later concurrency tests need data that is
    # visible across connections.
    tables = ", ".join(table.name for table in Base.metadata.sorted_tables)
    async with engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
    yield engine
    await engine.dispose()


@pytest.fixture
def sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return create_sessionmaker(engine)


@pytest.fixture
async def session(
    sessionmaker: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    async with sessionmaker() as session:
        yield session


@pytest.fixture
async def client(engine: AsyncEngine, test_settings: Settings) -> AsyncIterator[AsyncClient]:
    # Depends on `engine` so tables are truncated first. ASGITransport does not run the app's
    # lifespan, so enter it explicitly: the app opens and closes its own pool, as in production.
    app = create_app(test_settings)
    async with (
        app.router.lifespan_context(app),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client,
    ):
        yield client
