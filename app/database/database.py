"""
Database setup and session management.

This module initializes the SQLAlchemy async engine, configures the async session factory,
and declares the DeclarativeBase class for all ORM models.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

# Create the async engine.
# pool_pre_ping=True ensures dead connections are transparently recycled.
engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    echo=settings.DEBUG,  # Echoes SQL queries to stdout in debug mode
    pool_pre_ping=True,
)

# Configure the session maker.
# expire_on_commit=False prevents SQLAlchemy from querying the db again
# when accessing attributes on committed model instances.
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models.
    """
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency injection function to provide an asynchronous database session.
    Ensures that sessions are properly closed after the request lifecycle.
    """
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
