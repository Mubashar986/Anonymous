"""
FastAPI Main Application Entry Point.

Configures CORS middleware, custom timing middleware, mounts API routers,
and registers global exception handlers.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core.config import settings
from app.core.exceptions import setup_exception_handlers
from app.middleware import ProcessTimeMiddleware

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    description="Production-grade authentication API built with FastAPI, PostgreSQL, SQLAlchemy 2.0, and JWT.",
    version="1.0.0",
)

# Set up CORS middleware to allow cross-origin requests from frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom execution timing middleware
app.add_middleware(ProcessTimeMiddleware)

# Register global exception handlers for standardized error responses
setup_exception_handlers(app)

# Mount API v1 router
app.include_router(api_router, prefix=settings.API_V1_STR)


from typing import Dict

@app.get("/health", tags=["Health Check"])
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint for monitoring and uptime load balancers.
    """
    return {
        "status": "online",
        "project": settings.PROJECT_NAME,
        "api_version": settings.API_V1_STR,
    }
