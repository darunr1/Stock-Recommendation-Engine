from __future__ import annotations

import os

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./var/equitylens-test.db")
os.environ.setdefault("EMAIL_CAPTURE_DIR", "captured-emails-test")
os.environ.setdefault("DEMO_TASKS_EAGER", "true")
