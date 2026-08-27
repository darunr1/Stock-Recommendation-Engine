from __future__ import annotations

from fastapi.testclient import TestClient


def test_anonymous_browser_event_is_allow_listed(client: TestClient) -> None:
    accepted = client.post(
        "/api/v1/events",
        headers={"X-Anonymous-Id": "browser-test"},
        json={"name": "landing_viewed", "properties": {"campaign": "test"}},
    )
    assert accepted.status_code == 202
    rejected = client.post(
        "/api/v1/events",
        headers={"X-Anonymous-Id": "browser-test"},
        json={"name": "password_captured", "properties": {}},
    )
    assert rejected.status_code == 422


def test_deletion_grace_period_can_be_cancelled(client: TestClient) -> None:
    login = client.post("/api/v1/auth/demo-login", json={"role": "user"})
    assert login.status_code == 200
    scheduled = client.post(
        "/api/v1/account/delete-request",
        json={"password": "DemoResearch2026!"},
    )
    assert scheduled.status_code == 200
    assert scheduled.json() == {"scheduled": True, "grace_days": 7}
    assert client.get("/api/v1/market/summary").status_code == 403
    cancelled = client.post("/api/v1/account/delete-cancel")
    assert cancelled.status_code == 200
    assert client.get("/api/v1/market/summary").status_code == 200
