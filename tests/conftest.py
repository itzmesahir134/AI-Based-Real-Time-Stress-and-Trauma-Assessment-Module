import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from services.api.db import Base, get_db
from services.api.main import app

# In-memory SQLite async engine for ultra-fast, isolated testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Creates a fresh in-memory database and session for each test."""
    test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_maker() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def async_client(db_session: AsyncSession):
    """Test HTTP client with overridden DB dependency."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
    app.dependency_overrides.clear()

@pytest_asyncio.fixture(scope="function")
async def auth_client(async_client: AsyncClient):
    """Test HTTP client with auth token set."""
    res = await async_client.post(
        "/api/v1/auth/token",
        data={"username": "responder", "password": "saathi-resp-2026"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    token = res.json()["access_token"]
    async_client.headers["Authorization"] = f"Bearer {token}"
    return async_client
