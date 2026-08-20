from __future__ import annotations

import os

import httpx

base = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
with httpx.Client(base_url=base, timeout=10) as client:
    for path in ("/api/v1/health/live", "/api/v1/health/ready", "/api/v1/public/market-preview", "/api/v1/public/stocks/AAPL"):
        response = client.get(path)
        response.raise_for_status()
        print(f"PASS {path} ({response.elapsed.total_seconds() * 1000:.1f} ms)")
