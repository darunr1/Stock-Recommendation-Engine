from __future__ import annotations

import os
import sys

import httpx

base = (os.environ.get("BASE_URL") or (sys.argv[1] if len(sys.argv) > 1 else "")).rstrip("/")
if not base.startswith("https://"):
    raise SystemExit("BASE_URL must be the verified HTTPS deployment")
paths = ("/", "/methodology", "/stocks/AAPL", "/api/v1/health/ready")
with httpx.Client(base_url=base, timeout=20, follow_redirects=True) as client:
    for path in paths:
        response = client.get(path)
        response.raise_for_status()
        print(f"PASS {base}{path}")
