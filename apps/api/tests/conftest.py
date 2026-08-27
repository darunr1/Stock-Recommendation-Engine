from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./var/equitylens-test.db")
os.environ.setdefault("EMAIL_CAPTURE_DIR", "captured-emails-test")
os.environ.setdefault("DEMO_TASKS_EAGER", "true")


@pytest.fixture(scope="session")
def api_client() -> Iterator[TestClient]:
    from app.main import app

    with TestClient(app) as client:
        yield client


@pytest.fixture
def client(api_client: TestClient) -> Iterator[TestClient]:
    api_client.cookies.clear()
    yield api_client
    api_client.cookies.clear()
