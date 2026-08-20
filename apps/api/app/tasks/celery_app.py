from __future__ import annotations

import asyncio

from celery import Celery

from app.api.router import process_backtest
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.demo_seed import seed_demo

settings = get_settings()
celery_app = Celery("equitylens", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    task_time_limit=1800,
    task_soft_time_limit=1500,
    beat_schedule={
        "daily-demo-sync": {"task": "equitylens.sync_demo", "schedule": 60 * 60 * 24},
        "weekly-fundamentals": {"task": "equitylens.sync_demo", "schedule": 60 * 60 * 24 * 7},
    },
)


@celery_app.task(name="equitylens.backtest")
def backtest_task(run_id: str) -> None:
    asyncio.run(process_backtest(run_id))


@celery_app.task(name="equitylens.sync_demo")
def sync_demo_task() -> dict[str, int]:
    async def run() -> dict[str, int]:
        async with SessionLocal() as session:
            return await seed_demo(session, settings)

    return asyncio.run(run())
