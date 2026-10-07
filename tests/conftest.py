import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.config import Settings
from app.core.security import create_access_token, get_password_hash
from app.db.database import Base, get_db
from app.db.models import User


@pytest.fixture(scope="session")
def test_settings():
    return Settings(
        DATABASE_URL="sqlite+aiosqlite:///./test_auth.db",
        TEST_DATABASE_URL="sqlite+aiosqlite:///./test_auth.db",
        JWT_SECRET_KEY="test-secret-key-for-testing-only-32chars",
        JWT_ALGORITHM="HS256",
        ACCESS_TOKEN_EXPIRE_MINUTES=60,
        CORS_ORIGINS=["http://localhost:3000", "http://10.0.2.2:8000"],
        APP_NAME="Test Auth API",
        APP_VERSION="1.0.0",
        DEBUG=True,
    )


@pytest_asyncio.fixture(scope="function")
async def test_engine(test_settings):
    engine = create_async_engine(
        test_settings.TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_session(test_engine):
    async_session = async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)
    async with async_session() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(test_engine):
    async_session = async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)

    async def override_get_db():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def test_user(test_session):
    user = User(
        name="Test User",
        email="test@example.com",
        password_hash=get_password_hash("Password123!"),
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def auth_token(test_user):
    return create_access_token(subject=str(test_user.id))


@pytest_asyncio.fixture(scope="function")
async def expired_token(test_user):
    from datetime import timedelta
    return create_access_token(subject=str(test_user.id), expires_delta=timedelta(seconds=-1))