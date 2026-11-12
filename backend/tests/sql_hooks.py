"""Test helper: observe the SQL an engine sends, and optionally make one statement fail."""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from sqlalchemy import event
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine


class InjectedFailure(Exception):
    """Raised in place of sending a statement, to simulate a failure at that exact point."""


@contextmanager
def watch_statements(engine: AsyncEngine, *, fail_on: str | None = None) -> Iterator[list[str]]:
    """Yield a list that fills with each SQL statement as it is sent.

    With `fail_on`, the first statement starting with that text is not sent; InjectedFailure is
    raised instead. Statements before it have really reached the database inside the open
    transaction, which is the situation a crash or a lost connection leaves behind.
    """
    sent: list[str] = []

    def before_cursor_execute(
        conn: Connection,
        cursor: Any,
        statement: str,
        parameters: Any,
        context: Any,
        executemany: bool,
    ) -> None:
        if fail_on is not None and statement.startswith(fail_on):
            raise InjectedFailure(statement)
        sent.append(statement)

    # SQLAlchemy events attach to the synchronous engine that the async engine wraps.
    event.listen(engine.sync_engine, "before_cursor_execute", before_cursor_execute)
    try:
        yield sent
    finally:
        event.remove(engine.sync_engine, "before_cursor_execute", before_cursor_execute)
