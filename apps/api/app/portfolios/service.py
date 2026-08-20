from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    DailyPrice,
    PaperPortfolio,
    PaperPosition,
    PaperTransaction,
    Stock,
)

CENT = Decimal("0.01")
ZERO = Decimal("0")


def money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


async def latest_price(
    session: AsyncSession, stock_id: str, execution_date: date | None = None
) -> tuple[date, Decimal]:
    query = select(DailyPrice).where(DailyPrice.stock_id == stock_id, DailyPrice.valid.is_(True))
    if execution_date:
        query = query.where(DailyPrice.trading_date <= execution_date)
    row = await session.scalar(query.order_by(DailyPrice.trading_date.desc()).limit(1))
    if not row:
        raise ValueError("No eligible close is available for this symbol")
    return row.trading_date, Decimal(row.adjusted_close)


async def execute_trade(
    session: AsyncSession,
    *,
    user_id: str,
    symbol: str,
    side: str,
    quantity: Decimal,
    execution_date: date | None,
    explicit_price: Decimal | None = None,
) -> PaperTransaction:
    if quantity <= 0:
        raise ValueError("Quantity must be greater than zero")
    stock = await session.scalar(
        select(Stock).where(Stock.symbol == symbol, Stock.active.is_(True))
    )
    if not stock:
        raise ValueError("Unknown or inactive symbol")
    portfolio = await session.scalar(
        select(PaperPortfolio).where(PaperPortfolio.user_id == user_id).with_for_update()
    )
    if not portfolio:
        raise ValueError("Paper portfolio is unavailable")
    priced_date, market_price = await latest_price(session, stock.id, execution_date)
    price = explicit_price or market_price
    if price <= 0:
        raise ValueError("Execution price must be positive")
    position = await session.scalar(
        select(PaperPosition)
        .where(PaperPosition.portfolio_id == portfolio.id, PaperPosition.stock_id == stock.id)
        .with_for_update()
    )
    realized = ZERO
    if side == "buy":
        cost = money(price * quantity)
        if cost > Decimal(portfolio.cash):
            raise ValueError("Trade exceeds available simulated cash")
        old_quantity = Decimal(position.quantity) if position else ZERO
        old_cost = Decimal(position.average_cost) * old_quantity if position else ZERO
        new_quantity = old_quantity + quantity
        average_cost = (old_cost + price * quantity) / new_quantity
        if position:
            position.quantity = new_quantity
            position.average_cost = average_cost
        else:
            position = PaperPosition(
                portfolio_id=portfolio.id,
                stock_id=stock.id,
                quantity=new_quantity,
                average_cost=average_cost,
            )
            session.add(position)
        portfolio.cash = money(Decimal(portfolio.cash) - cost)
    elif side == "sell":
        if not position or quantity > Decimal(position.quantity):
            raise ValueError("Trade exceeds the simulated position")
        proceeds = money(price * quantity)
        realized = money((price - Decimal(position.average_cost)) * quantity)
        remaining = Decimal(position.quantity) - quantity
        portfolio.cash = money(Decimal(portfolio.cash) + proceeds)
        portfolio.realized_pl = money(Decimal(portfolio.realized_pl) + realized)
        if remaining == 0:
            await session.delete(position)
        else:
            position.quantity = remaining
    else:
        raise ValueError("Side must be buy or sell")
    transaction = PaperTransaction(
        portfolio_id=portfolio.id,
        stock_id=stock.id,
        side=side,
        quantity=quantity,
        price=price,
        execution_date=priced_date,
        fees=ZERO,
        realized_pl=realized,
        created_at=datetime.now(UTC),
    )
    session.add(transaction)
    await session.flush()
    return transaction


async def portfolio_snapshot(session: AsyncSession, user_id: str) -> dict[str, object]:
    portfolio = await session.scalar(
        select(PaperPortfolio).where(PaperPortfolio.user_id == user_id)
    )
    if not portfolio:
        raise ValueError("Paper portfolio is unavailable")
    rows = (
        await session.execute(
            select(PaperPosition, Stock)
            .join(Stock, Stock.id == PaperPosition.stock_id)
            .where(PaperPosition.portfolio_id == portfolio.id)
            .order_by(Stock.symbol)
        )
    ).all()
    positions: list[dict[str, object]] = []
    market_value = ZERO
    unrealized = ZERO
    for position, stock in rows:
        priced_date, price = await latest_price(session, stock.id)
        value = money(price * Decimal(position.quantity))
        gain = money((price - Decimal(position.average_cost)) * Decimal(position.quantity))
        market_value += value
        unrealized += gain
        positions.append(
            {
                "symbol": stock.symbol,
                "company_name": stock.company_name,
                "quantity": float(position.quantity),
                "average_cost": float(position.average_cost),
                "latest_price": float(price),
                "price_date": priced_date.isoformat(),
                "market_value": float(value),
                "unrealized_pl": float(gain),
            }
        )
    total = money(Decimal(portfolio.cash) + market_value)
    start = Decimal(portfolio.starting_cash)
    transactions = (
        await session.execute(
            select(PaperTransaction, Stock)
            .join(Stock, Stock.id == PaperTransaction.stock_id)
            .where(PaperTransaction.portfolio_id == portfolio.id)
            .order_by(PaperTransaction.created_at.desc())
        )
    ).all()
    return {
        "id": portfolio.id,
        "name": portfolio.name,
        "starting_cash": float(start),
        "cash": float(portfolio.cash),
        "market_value": float(market_value),
        "total_value": float(total),
        "total_return": float(total / start - 1),
        "realized_pl": float(portfolio.realized_pl),
        "unrealized_pl": float(unrealized),
        "positions": positions,
        "transactions": [
            {
                "id": transaction.id,
                "symbol": stock.symbol,
                "side": transaction.side,
                "quantity": float(transaction.quantity),
                "price": float(transaction.price),
                "execution_date": transaction.execution_date.isoformat(),
                "realized_pl": float(transaction.realized_pl),
                "created_at": transaction.created_at.isoformat(),
            }
            for transaction, stock in transactions
        ],
        "disclosure": "Simplified simulation using selected daily closes; not live execution.",
    }


async def reset_portfolio(session: AsyncSession, user_id: str, starting_cash: Decimal) -> None:
    portfolio = await session.scalar(
        select(PaperPortfolio).where(PaperPortfolio.user_id == user_id).with_for_update()
    )
    if not portfolio:
        raise ValueError("Paper portfolio is unavailable")
    await session.execute(delete(PaperPosition).where(PaperPosition.portfolio_id == portfolio.id))
    await session.execute(
        delete(PaperTransaction).where(PaperTransaction.portfolio_id == portfolio.id)
    )
    portfolio.starting_cash = money(starting_cash)
    portfolio.cash = money(starting_cash)
    portfolio.realized_pl = ZERO
