"""
Helper script to reset database tables and seed initial Super Admin user.
"""

import asyncio
from sqlalchemy import text
from app.database.database import async_session_maker
from app.models.user import User, UserRole
from app.core.security import get_password_hash


async def reset_and_seed():
    async with async_session_maker() as session:
        # Truncate all tables
        await session.execute(
            text("TRUNCATE TABLE comments, blogs, refresh_tokens, users CASCADE;")
        )
        await session.commit()
        print("SUCCESS: Database tables truncated cleanly!")

        # Create initial Super Admin
        admin = User(
            email="admin@company.com",
            username="superadmin",
            hashed_password=get_password_hash("Admin123!"),
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
        )
        session.add(admin)
        await session.commit()
        print("SUCCESS: Initial Super Admin seeded (admin@company.com / Admin123!)")


if __name__ == "__main__":
    asyncio.run(reset_and_seed())
