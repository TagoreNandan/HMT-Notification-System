# ruff: noqa: E402
import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Configure test environment before importing application modules.
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-key-for-pytest-only")
os.environ.setdefault("POLL_INTERVAL_SECONDS", "3600")
os.environ.setdefault("NOTIFICATION_CHANNEL", "console")
os.environ.setdefault("BASE_URL", "http://testserver")
os.environ.setdefault("MAX_PRODUCTS_PER_USER", "20")
os.environ.setdefault("SIGNUP_RATE_LIMIT", "5/hour")
os.environ.setdefault("NOTIFICATION_PREFERENCE_RATE_LIMIT", "20/hour")

from config import get_settings

get_settings.cache_clear()

from api.rate_limit import limiter
from db.models import Base
from db.session import get_db
from main import app
from scheduler import stop_scheduler


@pytest.fixture(scope="session", autouse=True)
def _shutdown_scheduler_after_session() -> Generator[None, None, None]:
    yield
    stop_scheduler()


@pytest.fixture(autouse=True)
def _disable_rate_limits_by_default() -> Generator[None, None, None]:
    limiter.enabled = False
    limiter.reset()
    yield
    limiter.enabled = False
    limiter.reset()


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def auth_headers(client: TestClient, email: str = "user@example.com", password: str = "password123") -> dict[str, str]:
    response = client.post("/auth/signup", json={"email": email, "password": password})
    assert response.status_code == 201, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
