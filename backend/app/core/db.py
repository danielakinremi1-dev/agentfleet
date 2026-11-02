from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def create_engine(database_url: str, *, echo: bool = False) -> AsyncEngine:
    # pool_pre_ping checks a pooled connection is alive before use, so a database restart
    # surfaces as a reconnect rather than an error on the next request.
    return create_async_engine(database_url, echo=echo, pool_pre_ping=True)


def create_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    # expire_on_commit=False: after commit, keep loaded attribute values instead of reloading
    # them on next access. Implicit reloads are not allowed in async code (they would need
    # hidden I/O), so objects returned from a service stay usable after it commits.
    return async_sessionmaker(engine, expire_on_commit=False)
