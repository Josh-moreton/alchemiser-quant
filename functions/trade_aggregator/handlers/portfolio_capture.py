"""Business Unit: trade_aggregator | Status: current.

Capture portfolio state and P&L metrics from Alpaca after trades complete.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from the_alchemiser.shared.config.container import ApplicationContainer
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.services.pnl_service import PnLService

logger = get_logger(__name__)


def capture_portfolio_state(correlation_id: str) -> tuple[Decimal | None, dict[str, Any]]:
    """Capture portfolio state from Alpaca account.

    Called once per run after all trades complete. Returns both capital deployed
    percentage and full portfolio snapshot for email notifications.

    Args:
        correlation_id: Correlation ID for tracing.

    Returns:
        Tuple of (capital_deployed_pct, portfolio_snapshot dict).

    """
    empty_snapshot: dict[str, Any] = {
        "equity": 0,
        "cash": 0,
        "gross_exposure": 0,
        "net_exposure": 0,
        "top_positions": [],
    }

    try:
        container = ApplicationContainer.create_for_notifications("production")
        alpaca_manager = container.infrastructure.alpaca_manager()
        account = alpaca_manager.get_account_object()

        if not account:
            logger.warning(
                "Failed to fetch account for portfolio state capture",
                extra={"correlation_id": correlation_id},
            )
            return None, empty_snapshot

        equity = Decimal(str(account.equity))
        cash = Decimal(str(account.cash)) if account.cash else Decimal("0")
        long_market_value = (
            Decimal(str(account.long_market_value)) if account.long_market_value else Decimal("0")
        )
        short_market_value = (
            Decimal(str(account.short_market_value)) if account.short_market_value else Decimal("0")
        )

        if equity > 0:
            gross_exposure = (long_market_value + abs(short_market_value)) / equity
            net_exposure = (long_market_value - abs(short_market_value)) / equity
            capital_deployed_pct = (long_market_value / equity) * Decimal("100")
        else:
            gross_exposure = Decimal("0")
            net_exposure = Decimal("0")
            capital_deployed_pct = None

        top_positions: list[dict[str, Any]] = []
        try:
            positions = alpaca_manager.get_positions()
            if positions and equity > 0:
                sorted_positions = sorted(
                    positions,
                    key=lambda p: abs(float(p.market_value)) if p.market_value else 0,
                    reverse=True,
                )
                for pos in sorted_positions:
                    market_value = (
                        Decimal(str(pos.market_value)) if pos.market_value else Decimal("0")
                    )
                    weight = (market_value / equity) * Decimal("100")
                    top_positions.append(
                        {
                            "symbol": pos.symbol,
                            "weight": float(weight.quantize(Decimal("0.1"))),
                            "market_value": float(market_value),
                            "qty": float(pos.qty) if pos.qty else 0,
                        }
                    )
        except Exception as pos_error:
            logger.warning(
                f"Failed to fetch positions for top positions list: {pos_error}",
                extra={"correlation_id": correlation_id},
            )

        portfolio_snapshot: dict[str, Any] = {
            "equity": float(equity),
            "cash": float(cash),
            "gross_exposure": float(gross_exposure.quantize(Decimal("0.01"))),
            "net_exposure": float(net_exposure.quantize(Decimal("0.01"))),
            "top_positions": top_positions,
        }

        logger.info(
            f"Portfolio captured: equity=${equity:,.2f}, cash=${cash:,.2f}, "
            f"gross={gross_exposure:.2f}x, positions={len(top_positions)}",
            extra={
                "correlation_id": correlation_id,
                "capital_deployed_pct": str(capital_deployed_pct)
                if capital_deployed_pct
                else "N/A",
                "equity": str(equity),
                "cash": str(cash),
            },
        )

        return (
            capital_deployed_pct.quantize(Decimal("0.01")) if capital_deployed_pct else None,
            portfolio_snapshot,
        )

    except Exception as e:
        logger.warning(
            f"Failed to capture portfolio state: {e}",
            extra={
                "correlation_id": correlation_id,
                "error_type": type(e).__name__,
            },
        )
        return None, empty_snapshot


def fetch_pnl_metrics(correlation_id: str) -> dict[str, Any]:
    """Fetch P&L metrics from Alpaca for email notifications.

    Fetches the last 3 calendar months of P&L data for display in email
    notifications. Gracefully handles errors.

    Args:
        correlation_id: Correlation ID for tracing.

    Returns:
        Dict with monthly_pnl containing a 'months' list of P&L data.

    """
    empty_pnl: dict[str, Any] = {
        "monthly_pnl": {},
        "yearly_pnl": {},
    }

    try:
        pnl_service = PnLService(correlation_id=correlation_id)

        months_data: list[dict[str, Any]] = []
        try:
            pnl_list = pnl_service.get_last_n_calendar_months_pnl(n_months=3)
            for pnl_data in pnl_list:
                months_data.append(
                    {
                        "period": pnl_data.period,
                        "start_date": pnl_data.start_date,
                        "end_date": pnl_data.end_date,
                        "total_pnl": float(pnl_data.total_pnl) if pnl_data.total_pnl else None,
                        "total_pnl_pct": (
                            float(pnl_data.total_pnl_pct) if pnl_data.total_pnl_pct else None
                        ),
                    }
                )
        except Exception as e:
            logger.warning(
                f"Failed to fetch calendar month P&L: {e}",
                extra={"correlation_id": correlation_id, "error_type": type(e).__name__},
            )

        month_summaries = [
            f"{m.get('period')}: {m.get('total_pnl_pct', 0):.2f}%"
            for m in months_data
            if m.get("total_pnl_pct") is not None
        ]
        logger.info(
            "P&L metrics fetched successfully",
            extra={
                "correlation_id": correlation_id,
                "months_count": len(months_data),
                "months_summary": ", ".join(month_summaries) if month_summaries else "N/A",
            },
        )

        return {
            "monthly_pnl": {"months": months_data},
            "yearly_pnl": {},
        }

    except Exception as e:
        logger.warning(
            f"Failed to initialize PnLService: {e}",
            extra={
                "correlation_id": correlation_id,
                "error_type": type(e).__name__,
            },
        )
        return empty_pnl
