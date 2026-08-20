from __future__ import annotations

import os
from pathlib import Path

required = [
    ".env.example",
    "compose.yaml",
    "apps/web/vercel.json",
    "railway.toml",
    "DEPLOYMENT.md",
    "LAUNCH_CHECKLIST.md",
    "RUNBOOK.md",
    "docs/environment-variables.md",
    "docs/market-data-display.md",
]
missing = [path for path in required if not Path(path).exists()]
if missing:
    raise SystemExit(f"Missing deployment files: {', '.join(missing)}")
if os.environ.get("APP_ENV") == "production":
    mode = os.environ.get("PUBLIC_MARKET_DATA_MODE", "restricted")
    if mode == "licensed" and os.environ.get("PUBLIC_MARKET_DATA_LICENSE_ACKNOWLEDGED") != "true":
        raise SystemExit("Licensed mode requires an explicit market-data license acknowledgement")
print("Deployment configuration is structurally complete. Account-bound launch gates remain external.")
