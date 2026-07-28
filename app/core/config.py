"""
Configuration settings for the FastAPI application.

This module uses Pydantic Settings v2 to read environment variables from a .env file,
perform validation, and compile them into a type-safe settings object used across the application.
"""

from typing import Any, Dict, Optional
from pydantic import EmailStr, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables and .env file.
    
    Defines defaults, performs validation, and formats credentials into URIs.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",  # Ignore extra fields not defined in this class
    )

    # API Configuration
    PROJECT_NAME: str = "Anonymous"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    # WebSocket configuration
    # The query parameter name used to pass the JWT access token during the
    # WebSocket handshake. Browsers cannot set custom HTTP headers on the
    # WebSocket upgrade request, so the token is passed as a query param.
    # See: app/schemas/ws.py and Task 3.1 WS auth adapter.
    WS_TOKEN_QUERY_PARAM: str = "token"

    # CORS allowed origins. Default is wildcard for local development.
    # Task 5.4 will replace ["*"] with an explicit allow-list via this field.
    ALLOWED_ORIGINS: list[str] = ["*"]

    # Cryptography & Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # PostgreSQL Database Configurations
    POSTGRES_SERVER: Optional[str] = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: Optional[str] = "postgres"
    POSTGRES_PASSWORD: Optional[str] = "postgres"
    POSTGRES_DB: Optional[str] = "fastapi_auth_db"
    
    # Environment variable alias for cloud deployment (e.g. Render, Heroku, Neon)
    DATABASE_URL: Optional[str] = None

    # Constructed dynamically or parsed from DATABASE_URL / SQLALCHEMY_DATABASE_URI
    SQLALCHEMY_DATABASE_URI: Optional[str] = None

    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info: ValidationInfo) -> Any:
        """
        Dynamically construct or normalize database connection string for asyncpg.
        Supports raw DATABASE_URL, SQLALCHEMY_DATABASE_URI, or individual POSTGRES_* fields.
        """
        raw_uri = v or info.data.get("DATABASE_URL")
        if isinstance(raw_uri, str) and raw_uri.strip():
            uri = raw_uri.strip()
            # Normalize postgresql:// or postgres:// to postgresql+asyncpg:// for SQLAlchemy 2.0
            if uri.startswith("postgresql://"):
                uri = "postgresql+asyncpg://" + uri[len("postgresql://"):]
            elif uri.startswith("postgres://"):
                uri = "postgresql+asyncpg://" + uri[len("postgres://"):]
            
            # Normalize sslmode= to ssl= for asyncpg driver compatibility
            if "sslmode=" in uri:
                uri = uri.replace("sslmode=", "ssl=")
            return uri

        user = info.data.get("POSTGRES_USER") or "postgres"
        password = info.data.get("POSTGRES_PASSWORD") or "postgres"
        server = info.data.get("POSTGRES_SERVER") or "localhost"
        port = info.data.get("POSTGRES_PORT") or 5432
        db = info.data.get("POSTGRES_DB") or "fastapi_auth_db"
        
        return f"postgresql+asyncpg://{user}:{password}@{server}:{port}/{db}"

    # SMTP (Email) Configurations
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: Optional[EmailStr] = None
    SMTP_FROM_NAME: Optional[str] = None
    EMAILS_ENABLED: bool = False

    # Resend API Configuration
    RESEND_API_KEY: Optional[str] = None

    # Frontend URL Configuration
    FRONTEND_URL: str = "http://localhost:5173"

    # Stripe Billing Configurations
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_PREMIUM_MONTHLY: str = ""


# Instantiate settings to be imported by other modules
settings = Settings()
