"""
KOVIRX — Local Database Initializer.

Initializes the SQLite database kovirx.db and seeds the initial admin user.
"""

import asyncio
import os
import sys

# Add backend directory to sys.path
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_THIS_DIR, ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from database.base import Base
from sqlalchemy.ext.asyncio import create_async_engine
from backend.core.config import settings
from backend.core.security import hash_password
from database.models.user import User, UserRole


async def init_db():
    db_url = settings.database_url
    print(f"Initializing database at: {db_url}")

    engine = create_async_engine(db_url, echo=True)

    async with engine.begin() as conn:
        print("Creating all tables...")
        # Drop all first to ensure clean state
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Seed admin user
    from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
    async_session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_factory() as session:
        print("Seeding default admin user...")
        admin = User(
            email="admin@kovirx.com",
            username="admin",
            hashed_password=hash_password("admin123"),
            role=UserRole.super_admin,
            is_active=True,
        )
        session.add(admin)
        await session.commit()
        print("[SUCCESS] Database initialized successfully and admin user seeded!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(init_db())
