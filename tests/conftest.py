import asyncio
import os
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Override database URL to use a test database before any other imports
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///test.db"

from backend.core.security import hash_password
from database.base import Base
from database.session import get_db
from backend.main import app
from database.models.user import User, UserRole

# Define test async engine
test_engine = create_async_engine(
    os.environ["DATABASE_URL"],
    echo=False,
)

test_async_session_factory = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def event_loop():
    """Create session-wide event loop."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    """Drop and recreate all tables in the test database on session start/end."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()
    if os.path.exists("test.db"):
        try:
            os.remove("test.db")
        except Exception:
            pass


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional DB session for individual tests."""
    async with test_async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest_asyncio.fixture(autouse=True)
async def override_db_dependency(db: AsyncSession):
    """Override get_db route dependency with the test session."""
    app.dependency_overrides[get_db] = lambda: db
    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Provide an HTTPX AsyncClient for requesting endpoints."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


from sqlalchemy import select


@pytest_asyncio.fixture
async def test_user(db: AsyncSession) -> User:
    """Create a standard analyst test user if they do not exist."""
    result = await db.execute(select(User).where(User.email == "test_analyst@kovirx.com"))
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    user = User(
        email="test_analyst@kovirx.com",
        username="test_analyst",
        hashed_password=hash_password("TestPass123!"),
        role=UserRole.security_analyst,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_admin(db: AsyncSession) -> User:
    """Create a super admin test user if they do not exist."""
    result = await db.execute(select(User).where(User.email == "test_admin@kovirx.com"))
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    user = User(
        email="test_admin@kovirx.com",
        username="test_admin",
        hashed_password=hash_password("TestPass123!"),
        role=UserRole.super_admin,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, test_user: User) -> dict[str, str]:
    """Authenticate the test analyst user and return Bearer auth header."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "TestPass123!"},
    )
    data = response.json()
    token = data["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def admin_auth_headers(client: AsyncClient, test_admin: User) -> dict[str, str]:
    """Authenticate the test admin user and return Bearer auth header."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": test_admin.email, "password": "TestPass123!"},
    )
    data = response.json()
    token = data["access_token"]
    return {"Authorization": f"Bearer {token}"}
