# ADR-0004: Database sessions and transaction boundaries

Status: accepted

## Context
The API uses async SQLAlchemy. A unit of work must be atomic, and architecture principle 5 requires state
changes to be persisted before they are reported to clients. FastAPI's dependency teardown (code after
`yield`) has changed timing relative to sending the response across versions, so it is not a safe place to
commit.

## Decision
1. **One engine (connection pool) per process**, created in the FastAPI lifespan and disposed at shutdown,
   stored on `app.state`. `create_app(settings)` builds it, so tests construct an app pointed at the test
   database without global state.
2. **One `AsyncSession` per request** from the `get_session` dependency. Exiting the session closes it,
   rolling back anything uncommitted and returning the connection to the pool.
3. **Services own the commit.** A service function performs its writes and calls `await session.commit()`
   before returning; routes return a response only after that. Services contain no FastAPI code, so workers
   can reuse them.
4. **`expire_on_commit=False`.** Committed objects keep their loaded values. In async code, attribute access
   cannot trigger implicit I/O, so the default (expire, then reload on access) would fail when a response is
   serialized after commit.
5. **Uniqueness is enforced by the database.** Creating a template uses
   `INSERT ... ON CONFLICT DO NOTHING RETURNING`. A conflict returns no row, which the service maps to a
   domain error (`409` at the API). There is no read-then-insert check, so concurrent requests cannot both
   succeed, and the transaction is not aborted by an error.

## Alternatives considered
- **Commit in the session dependency:** less code per service, but the commit may run after the response is
  sent, so a client could see success for a write that then fails.
- **`session.begin()` context in every route:** explicit, but puts transaction control in the HTTP layer,
  which workers do not have.
- **Catching `IntegrityError` on insert:** works, but aborts the transaction and requires inspecting
  driver-specific error details to identify the constraint.

## Consequences
- Every write path must commit explicitly; a forgotten commit silently loses the write (tests read back
  through a separate session to catch this).
- Relationship loading must be explicit (`selectinload` etc.) because async sessions cannot lazy-load.
