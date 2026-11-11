"""Error responses shared by every endpoint."""

from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


async def validation_error_response(request: Request, exc: Exception) -> JSONResponse:
    """Report why a request failed validation, without repeating the rejected value.

    FastAPI's default handler includes each rejected value under `input`. That reflects
    arbitrarily large or sensitive request content back to the client, and fails outright for
    values that cannot be written as JSON: a NaN in a request body would produce a 500 while
    the 422 that rejects it is being built.
    """
    assert isinstance(exc, RequestValidationError)
    errors = [{k: v for k, v in error.items() if k != "input"} for error in exc.errors()]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"detail": jsonable_encoder(errors)},
    )
