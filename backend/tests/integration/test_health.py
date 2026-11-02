from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.main import create_app


async def test_liveness(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_readiness_when_database_is_up(client: AsyncClient) -> None:
    response = await client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


async def test_readiness_reports_unreachable_database() -> None:
    # Port 1 refuses connections immediately: simulates the database being down.
    app = create_app(Settings(database_url="postgresql+asyncpg://u:p@127.0.0.1:1/none"))
    async with (
        app.router.lifespan_context(app),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client,
    ):
        response = await client.get("/health/ready")
        assert (await client.get("/health")).status_code == 200

    assert response.status_code == 503
    # Connection details must not leak into the response.
    assert "127.0.0.1" not in response.text
