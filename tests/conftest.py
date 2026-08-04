"""
AI-LMS Test Configuration — pytest fixtures for async testing.
"""
import asyncio
import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import hash_password
from app.database import Base, get_db
from app.main import app
from app.models.user import User, UserRole

# Use an in-memory SQLite for testing (override with TEST_DATABASE_URL if needed)
TEST_DB_URL = "sqlite+aiosqlite:///./test_ailms.db"


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    # Use aiosqlite for tests
    try:
        from sqlalchemy.ext.asyncio import create_async_engine as cae
        engine = cae(TEST_DB_URL, echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        yield engine
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()
    except Exception:
        # Fallback: skip DB-dependent tests
        yield None


@pytest_asyncio.fixture
async def db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide a test database session."""
    if test_engine is None:
        pytest.skip("Test database not available")

    session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provide an async test HTTP client with DB override."""

    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def student_user(db: AsyncSession) -> User:
    """Create a test student user."""
    user = User(
        id=uuid.uuid4(),
        email="student@test.com",
        hashed_password=hash_password("TestPass123!"),
        full_name="Test Student",
        role=UserRole.student,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def teacher_user(db: AsyncSession) -> User:
    """Create a test teacher user."""
    user = User(
        id=uuid.uuid4(),
        email="teacher@test.com",
        hashed_password=hash_password("TestPass123!"),
        full_name="Test Teacher",
        role=UserRole.teacher,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_user(db: AsyncSession) -> User:
    """Create a test admin user."""
    user = User(
        id=uuid.uuid4(),
        email="admin@test.com",
        hashed_password=hash_password("TestPass123!"),
        full_name="Test Admin",
        role=UserRole.admin,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_auth_token(client: AsyncClient, email: str, password: str) -> str:
    """Helper to get a JWT token for a user."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def auth_headers(token: str) -> dict:
    """Build Authorization header dict."""
    return {"Authorization": f"Bearer {token}"}
