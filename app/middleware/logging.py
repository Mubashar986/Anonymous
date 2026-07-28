"""
Custom ASGI Middleware for request execution timing and logging.
"""

import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class ProcessTimeMiddleware(BaseHTTPMiddleware):
    """
    Middleware that calculates total HTTP request execution duration in milliseconds
    and appends an 'X-Process-Time' header to the outgoing HTTP response.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()
        
        response: Response = await call_next(request)
        
        process_time = time.perf_counter() - start_time
        # Convert seconds to milliseconds
        process_time_ms = f"{process_time * 1000:.2f}ms"
        
        response.headers["X-Process-Time"] = process_time_ms
        return response
