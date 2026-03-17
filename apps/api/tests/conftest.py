"""
Pytest fixtures shared across the entire test suite.

Design decisions:
- Each test function gets a fresh database transaction that is rolled back
  after the test, so tests are fully isolated without needing to recreate
  tables between runs.
- The AsyncClient is configured to use the same in-transaction session so
  requests made through the HTTP client see the test data.
- The test database URL is read from the DATABASE_URL environment variable
  (defaulting to the CI value) so there is no hard-coded connection string.
"""

from __future__ import annotations

import os
from typing import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# ---------------------------------------------------------------------------
# Resolve test DATABASE_URL
# ---------------------------------------------------------------------------
_raw_db_url = os.environ.get(
    "DATABASE_URL",
    "postgresql://applyflow:applyflow@localhost:5432/applyflow_test",
)

# Ensure we always use the asyncpg driver for tests.
if _raw_db_url.startswith("postgresql://"):
    TEST_DATABASE_URL = _raw_db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
elif _raw_db_url.startswith("postgres://"):
    TEST_DATABASE_URL = _raw_db_url.replace("postgres://", "postgresql+asyncpg://", 1)
else:
    TEST_DATABASE_URL = _raw_db_url

# ---------------------------------------------------------------------------
# Import application pieces after env is configured
# ---------------------------------------------------------------------------
from app.core.database import get_db  # noqa: E402
from app.models import (  # noqa: F401, E402
    agent,
    application,
    calendar,
    document,
    email,
    job,
    profile,
    resume,
    user,
)
from main import app  # noqa: E402


# ---------------------------------------------------------------------------
# Pytest configuration
# ---------------------------------------------------------------------------
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "integration: mark test as requiring a live database")


# ---------------------------------------------------------------------------
# Per-test database connection with savepoint rollback
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture()
async def db_connection() -> AsyncGenerator[AsyncConnection, None]:
    """
    Yield a fresh connection per test and wrap it in an outer transaction.

    CI runs Alembic before pytest, so the schema already exists. Creating a
    fresh engine per test avoids reusing asyncpg connections across different
    pytest-managed event loops.
    """
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.connect() as conn:
        transaction = await conn.begin()
        try:
            yield conn
        finally:
            await transaction.rollback()
    await engine.dispose()


@pytest_asyncio.fixture()
async def async_session(db_connection) -> AsyncGenerator[AsyncSession, None]:
    """Yield an AsyncSession bound to the per-test savepoint connection."""
    session_factory = async_sessionmaker(
        bind=db_connection,
        class_=AsyncSession,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
        autocommit=False,
        autoflush=False,
    )
    async with session_factory() as session:
        yield session


# ---------------------------------------------------------------------------
# HTTP test client
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture()
async def client(async_session) -> AsyncGenerator[AsyncClient, None]:
    """
    Yield an AsyncClient wired to the FastAPI app.

    The `get_db` dependency is overridden to return the per-test session so
    HTTP requests and direct ORM assertions share the same transaction.
    """

    async def _override_get_db():
        yield async_session

    app.dependency_overrides[get_db] = _override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Common data fixtures
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture()
async def test_user(async_session) -> dict:
    """
    Insert a verified, active user and return a dict with id + plain credentials.
    """
    from app.core.security import get_password_hash
    from app.models.user import User

    plain_password = "TestPass123"

    user_obj = User(
        email="test@applyflow.dev",
        hashed_password=get_password_hash(plain_password),
        full_name="Test User",
        is_active=True,
        is_verified=True,
    )
    async_session.add(user_obj)
    await async_session.commit()
    await async_session.refresh(user_obj)

    return {
        "id": str(user_obj.id),
        "email": user_obj.email,
        "password": plain_password,
        "full_name": user_obj.full_name,
    }


@pytest_asyncio.fixture()
async def auth_headers(client, test_user) -> dict:
    """Return Authorization headers for the test user."""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": test_user["email"], "password": test_user["password"]},
    )
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture()
async def test_profile(async_session, test_user) -> dict:
    """Insert a profile for the test user."""
    import uuid

    from app.models.profile import Profile, RemotePreference, SeniorityLevel

    profile_obj = Profile(
        user_id=uuid.UUID(test_user["id"]),
        target_roles=["ML Engineer", "AI Engineer"],
        preferred_locations=["San Francisco, CA", "Remote"],
        remote_preference=RemotePreference.remote,
        seniority_level=SeniorityLevel.senior,
        skills=["Python", "PyTorch", "TensorFlow", "SQL"],
        years_of_experience=5,
        preferred_salary_min=150_000,
        preferred_salary_max=250_000,
        preferred_currency="USD",
    )
    async_session.add(profile_obj)
    await async_session.commit()
    await async_session.refresh(profile_obj)

    return {"id": str(profile_obj.id), "user_id": test_user["id"]}


@pytest_asyncio.fixture()
async def test_job(async_session) -> dict:
    """Insert a single active job posting."""
    import uuid

    from app.models.job import EmploymentType, Job, JobSeniority, JobSource, JobStatus

    source = JobSource(
        name="LinkedIn (Test)",
        connector_type="linkedin",
        is_active=True,
    )
    async_session.add(source)
    await async_session.flush()

    job_obj = Job(
        source_id=source.id,
        source_job_id=f"linkedin-test-{uuid.uuid4().hex[:8]}",
        company_name="Acme AI",
        title="Senior ML Engineer",
        location="San Francisco, CA",
        is_remote=True,
        employment_type=EmploymentType.full_time,
        seniority=JobSeniority.senior,
        salary_min=180_000,
        salary_max=240_000,
        currency="USD",
        raw_description="Build and deploy large-scale ML models.",
        status=JobStatus.active,
    )
    async_session.add(job_obj)
    await async_session.commit()
    await async_session.refresh(job_obj)

    return {"id": str(job_obj.id), "title": job_obj.title, "company": job_obj.company_name}
