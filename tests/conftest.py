import os

# Use an isolated SQLite DB for tests, and a fixed secret key
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["SECRET_KEY"] = "test-secret-key"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

TEST_DB_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    """Drop + recreate all tables before each test — perfect isolation."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    """Register + login a default user, return Authorization header."""
    client.post(
        "/auth/register",
        json={"email": "user@example.com", "password": "password123", "full_name": "Test"},
    )
    r = client.post(
        "/auth/login",
        data={"username": "user@example.com", "password": "password123"},
    )
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def second_user_headers(client):
    """A second user for isolation tests."""
    client.post(
        "/auth/register",
        json={"email": "other@example.com", "password": "password123"},
    )
    r = client.post(
        "/auth/login",
        data={"username": "other@example.com", "password": "password123"},
    )
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_job():
    return {
        "title": "Junior AI Engineer",
        "company": "Tech Company",
        "location": "Remote",
        "status": "saved",
        "technologies": ["Python", "FastAPI", "PyTorch"],
        "job_url": "https://example.com/job",
        "application_deadline": "2026-11-30",
    }