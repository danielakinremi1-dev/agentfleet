from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.api.errors import validation_error_response
from app.api.router import api_router
from app.core.config import Settings, get_settings
from app.core.db import create_engine, create_sessionmaker


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the app. Tests pass their own Settings to point at the test database."""
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        # One connection pool per process, created at startup and closed at shutdown.
        engine = create_engine(settings.database_url, echo=settings.database_echo)
        app.state.sessionmaker = create_sessionmaker(engine)
        yield
        await engine.dispose()

    app = FastAPI(title="AgentFleet", version="0.1.0", lifespan=lifespan)
    app.include_router(api_router)
    app.add_exception_handler(RequestValidationError, validation_error_response)
    return app


app = create_app()
