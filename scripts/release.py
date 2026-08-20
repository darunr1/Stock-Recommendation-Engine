from __future__ import annotations

import asyncio
import os
import subprocess
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


async def main() -> None:
    database_url = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./var/equitylens.db")
    engine = create_async_engine(database_url)
    async with engine.connect() as connection:
        if database_url.startswith("postgresql"):
            await connection.execute(text("SELECT pg_advisory_lock(19082026)"))
        try:
            subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True)
        finally:
            if database_url.startswith("postgresql"):
                await connection.execute(text("SELECT pg_advisory_unlock(19082026)"))
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
