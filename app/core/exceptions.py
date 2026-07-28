"""
Global Exception Handling & Error Formatting.

Provides centralized exception handlers to format all API errors into a consistent JSON payload,
preventing internal Python stack traces from leaking to clients.
"""

import http
import logging
from typing import Any, Dict
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger("app.exceptions")


def create_error_response(
    status_code: int,
    code: str,
    message: str,
    details: Any = None,
) -> JSONResponse:
    """
    Construct a standardized JSON error response body.
    """
    payload = {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": details,
        },
    }
    return JSONResponse(status_code=status_code, content=payload)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handler for standard HTTPExceptions thrown by services or dependencies.
    """
    try:
        status_phrase = http.HTTPStatus(exc.status_code).name
    except ValueError:
        status_phrase = "HTTP_ERROR"

    return create_error_response(
        status_code=exc.status_code,
        code=status_phrase,
        message=str(exc.detail),
        details=None,
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """
    Handler for Pydantic input validation errors (422 Unprocessable Entity).
    """
    formatted_details = []
    for err in exc.errors():
        # Format field path (e.g. 'body.email' or 'query.token')
        loc = ".".join(str(item) for item in err.get("loc", []))
        formatted_details.append({
            "field": loc,
            "message": err.get("msg", "Invalid input"),
        })

    return create_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        code="VALIDATION_ERROR",
        message=f"Validation failed for {len(formatted_details)} field(s).",
        details=formatted_details,
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all handler for unhandled server exceptions (500 Internal Server Error).
    Logs full exception details internally while returning a safe message to the client.
    """
    logger.error(f"Unhandled server exception on {request.method} {request.url}: {exc}", exc_info=True)
    
    return create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected server error occurred. Please try again later.",
        details=None,
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """
    Register custom exception handlers with the FastAPI application instance.
    """
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
