"""
Pytest configuration and test fixtures.

Uses a SEPARATE test database to prevent tests from destroying development data.
Uses NullPool to prevent connection reuse across pytest-asyncio event loops.
"""

import asyncio
from typing import AsyncGenerator
import asyncpg
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.database.database import Base, get_db
import app.models  # Ensure all ORM models are registered in Base.metadata
from app.main import app


TEST_DB_NAME = f"{settings.POSTGRES_DB}_test"
TEST_DATABASE_URI = (
    f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
    f"@{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{TEST_DB_NAME}"
)


async def create_test_database():
    sys_conn = await asyncpg.connect(
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        host=settings.POSTGRES_SERVER,
        port=settings.POSTGRES_PORT,
        database="postgres",
    )
    try:
        db_exists = await sys_conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", TEST_DB_NAME
        )
        if not db_exists:
            await sys_conn.execute(f'CREATE DATABASE "{TEST_DB_NAME}"')
    finally:
        await sys_conn.close()


asyncio.run(create_test_database())

test_engine = create_async_engine(
    TEST_DATABASE_URI,
    echo=False,
    poolclass=NullPool,
)

TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(autouse=True)
def reset_connection_manager():
    from app.core.connection_manager import connection_manager
    connection_manager.active_connections.clear()
    yield
    connection_manager.active_connections.clear()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()

    async with test_engine.begin() as conn:
        await conn.execute(
            text(
                "TRUNCATE TABLE user_permission_overrides, permission_audit_logs, "
                "room_messages, room_members, room_requests, rooms, comments, blogs, "
                "subscriptions, refresh_tokens, messages, conversation_participants, "
                "conversations, follows, users RESTART IDENTITY CASCADE;"
            )
        )




@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

    app.dependency_overrides.clear()
