from __future__ import annotations

import re
import uuid
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def test_public_shape_demo_auth_watchlist_backtest_and_portfolio() -> None:
    with TestClient(app) as client:
        public = client.get("/api/v1/public/stocks/AAPL")
        assert public.status_code == 200
        payload = public.json()
        assert payload["demo"] is True
        assert "raw_features" not in payload
        assert "confidence_help" in payload

        login = client.post("/api/v1/auth/demo-login", json={"role": "user"})
        assert login.status_code == 200
        assert client.get("/api/v1/market/summary").status_code == 200
        assert (
            client.post("/api/v1/watchlist/items", json={"symbol": "AAPL", "note": ""}).status_code
            == 200
        )
        watchlist = client.get("/api/v1/watchlist").json()
        assert any(item["symbol"] == "AAPL" for item in watchlist["items"])

        trade = client.post(
            "/api/v1/paper/transactions",
            json={"symbol": "AAPL", "side": "buy", "quantity": 2},
        )
        assert trade.status_code == 200
        assert trade.json()["positions"][0]["quantity"] >= 2
        oversell = client.post(
            "/api/v1/paper/transactions",
            json={"symbol": "AAPL", "side": "sell", "quantity": 1_000_000},
        )
        assert oversell.status_code == 422

        backtest = client.post(
            "/api/v1/backtests",
            json={"start_date": "2022-01-03", "end_date": "2026-07-31"},
        )
        assert backtest.status_code == 202
        detail = client.get(f"/api/v1/backtests/{backtest.json()['id']}").json()
        assert detail["status"] == "completed"
        assert detail["result"]["metrics"]["modeled_costs"] > 0


def test_registration_verification_is_single_use_and_forgot_is_generic() -> None:
    email = f"test-{uuid.uuid4().hex[:8]}@example.com"
    capture = Path("captured-emails-test")
    before = set(capture.glob("*.json")) if capture.exists() else set()
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "LongResearchPassword!2026"},
        )
        assert response.status_code == 201
        after = set(capture.glob("*.json"))
        created = list(after - before)
        assert created
        text = created[-1].read_text(encoding="utf-8")
        token_match = re.search(r"token=([^\\n]+)", text)
        assert token_match
        token = token_match.group(1)
        assert client.post("/api/v1/auth/verify-email", json={"token": token}).status_code == 200
        assert client.post("/api/v1/auth/verify-email", json={"token": token}).status_code == 400
        known = client.post("/api/v1/auth/forgot-password", json={"email": email})
        unknown = client.post(
            "/api/v1/auth/forgot-password", json={"email": f"none-{uuid.uuid4().hex}@example.com"}
        )
        assert known.status_code == unknown.status_code == 200
        assert known.json() == unknown.json()


def test_normal_user_cannot_trigger_admin_job() -> None:
    with TestClient(app) as client:
        client.post("/api/v1/auth/demo-login", json={"role": "user"})
        response = client.post("/api/v1/admin/jobs/scoring")
        assert response.status_code == 403
