from __future__ import annotations

import argparse
import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import func, select

from app.core.config import get_settings
from app.db.models import BacktestRun, Recommendation, Stock, User
from app.db.session import SessionLocal, create_schema
from app.services.demo_seed import seed_demo
from app.services.email import email_provider


async def seed_command(reset: bool) -> None:
    await create_schema()
    async with SessionLocal() as session:
        counts = await seed_demo(session, get_settings(), reset=reset)
    print(json.dumps(counts, indent=2))


async def email_preview_command() -> None:
    provider = email_provider(get_settings())
    message_id = await provider.send(
        to="preview@equitylens.local",
        subject="EquityLens email preview",
        text="Your score changed because the factor inputs changed.\n\n"
        "For education and research only. Not investment advice.",
        kind="preview",
    )
    print(f"Captured preview: {message_id}")


async def evidence_command() -> None:
    async with SessionLocal() as session:
        stock_count = await session.scalar(select(func.count()).select_from(Stock)) or 0
        snapshot_count = await session.scalar(select(func.count()).select_from(Recommendation)) or 0
        backtest_count = (
            await session.scalar(
                select(func.count())
                .select_from(BacktestRun)
                .where(BacktestRun.status == "completed")
            )
            or 0
        )
        registered = (
            await session.scalar(
                select(func.count())
                .select_from(User)
                .where(User.is_demo.is_(False), User.role != "admin")
            )
            or 0
        )
        verified = (
            await session.scalar(
                select(func.count())
                .select_from(User)
                .where(
                    User.is_demo.is_(False),
                    User.role != "admin",
                    User.email_verified_at.is_not(None),
                )
            )
            or 0
        )
        activated = (
            await session.scalar(
                select(func.count())
                .select_from(User)
                .where(
                    User.is_demo.is_(False), User.role != "admin", User.activated_at.is_not(None)
                )
            )
            or 0
        )
    content = f"""# EquityLens resume evidence

Generated: {datetime.now(UTC).isoformat()}

| Claim | Value | Source |
|---|---:|---|
| Production URL | Not yet deployed | Owner-authorized post-deploy smoke |
| Last production smoke | Not yet measured | Post-deploy workflow |
| Registered users | {registered} | Aggregate; demo/admin excluded |
| Verified users | {verified} | Aggregate; demo/admin excluded |
| Activated users | {activated} | Server-verified aggregate; demo/admin excluded |
| DAU / WAU | Not yet measured | Production event aggregates |
| Current universe | {stock_count} symbols | `stocks` table |
| Recommendation snapshots | {snapshot_count} | `recommendations` table |
| Completed backtests | {backtest_count} | `backtest_runs` table |
| API p95 | Not yet measured | Production request-duration window |
| CI run | Not yet measured | GitHub Actions |
| Uptime | Not yet measured | External uptime monitor |

Unknown production claims remain explicitly unmeasured. Demo data is never represented as market performance.
"""
    Path("RESUME_EVIDENCE.md").write_text(content, encoding="utf-8")
    print("Updated RESUME_EVIDENCE.md")


def main() -> None:
    parser = argparse.ArgumentParser(description="EquityLens administration CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    seed_parser = subparsers.add_parser("seed")
    seed_parser.add_argument("--reset", action="store_true")
    subparsers.add_parser("email-preview")
    subparsers.add_parser("evidence")
    args = parser.parse_args()
    if args.command == "seed":
        asyncio.run(seed_command(args.reset))
    elif args.command == "email-preview":
        asyncio.run(email_preview_command())
    elif args.command == "evidence":
        asyncio.run(evidence_command())


if __name__ == "__main__":
    main()
