"""Business Unit: shared | Status: current.

Sharpe ratio calculator for strategy performance evaluation.

Calculates annualized Sharpe ratios from per-strategy trade history.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.repositories.dynamodb_trade_ledger_repository import (
    DynamoDBTradeLedgerRepository,
)

logger = get_logger(__name__)

# Risk-free rate assumption (US 10-year Treasury, ~4.5% as of 2025)
RISK_FREE_RATE = Decimal("0.045")

# Trading days per year for annualization
TRADING_DAYS_PER_YEAR = Decimal("252")


class SharpeCalculator:
    """Calculator for strategy Sharpe ratios.

    Uses per-strategy closed lot P&L data to compute daily returns
    and calculate annualized Sharpe ratio.
    """

    def __init__(self, repository: DynamoDBTradeLedgerRepository, lookback_days: int = 90):
        """Initialize Sharpe calculator.

        Args:
            repository: Trade ledger repository for querying P&L data
            lookback_days: Number of days to look back for P&L history

        """
        self.repository = repository
        self.lookback_days = lookback_days
        self.cutoff_date = datetime.now(UTC) - timedelta(days=lookback_days)

    def calculate_all_strategy_sharpes(self, correlation_id: str) -> dict[str, Decimal]:
        """Calculate Sharpe ratios for all strategies with sufficient history.

        Args:
            correlation_id: Correlation ID for tracing

        Returns:
            Dict mapping strategy name to annualized Sharpe ratio

        """
        logger.info(
            f"Calculating Sharpe ratios for all strategies (lookback: {self.lookback_days} days)",
            extra={"correlation_id": correlation_id},
        )

        # Discover all strategies with closed lots
        strategy_names = self.repository.discover_strategies_with_closed_lots()

        if not strategy_names:
            logger.warning(
                "No strategies found with closed lots",
                extra={"correlation_id": correlation_id},
            )
            return {}

        sharpe_ratios = {}

        for strategy_name in strategy_names:
            try:
                sharpe = self.calculate_strategy_sharpe(strategy_name, correlation_id)
                if sharpe is not None:
                    sharpe_ratios[strategy_name] = sharpe
            except Exception as e:
                logger.error(
                    f"Failed to calculate Sharpe for {strategy_name}: {e}",
                    exc_info=True,
                    extra={"correlation_id": correlation_id, "strategy_name": strategy_name},
                )

        logger.info(
            f"Calculated Sharpe ratios for {len(sharpe_ratios)} strategies",
            extra={
                "correlation_id": correlation_id,
                "strategies": list(sharpe_ratios.keys()),
            },
        )

        return sharpe_ratios

    def calculate_strategy_sharpe(self, strategy_name: str, correlation_id: str) -> Decimal | None:
        """Calculate annualized Sharpe ratio for a single strategy.

        Sharpe Ratio = (Annualized Return - Risk Free Rate) / Annualized Volatility

        Args:
            strategy_name: Strategy name
            correlation_id: Correlation ID for tracing

        Returns:
            Annualized Sharpe ratio, or None if insufficient data

        """
        # Query closed lots for this strategy
        closed_lots = self.repository.query_closed_lots_by_strategy(strategy_name)

        # Filter to lookback period
        recent_lots = [
            lot
            for lot in closed_lots
            if lot.close_timestamp and lot.close_timestamp >= self.cutoff_date
        ]

        if len(recent_lots) < 5:
            logger.info(
                f"Insufficient trade history for {strategy_name} "
                f"({len(recent_lots)} lots in {self.lookback_days} days)",
                extra={"correlation_id": correlation_id, "strategy_name": strategy_name},
            )
            return None

        # Calculate daily returns from P&L
        daily_returns = self._calculate_daily_returns(recent_lots, correlation_id)

        if len(daily_returns) < 5:
            logger.info(
                f"Insufficient daily returns for {strategy_name} ({len(daily_returns)} days)",
                extra={"correlation_id": correlation_id, "strategy_name": strategy_name},
            )
            return None

        # Calculate annualized return and volatility
        mean_return = sum(daily_returns) / len(daily_returns)
        annualized_return = mean_return * TRADING_DAYS_PER_YEAR

        # Calculate standard deviation of daily returns
        variance = sum((r - mean_return) ** 2 for r in daily_returns) / len(daily_returns)
        daily_volatility = variance.sqrt() if variance > 0 else Decimal("0")
        annualized_volatility = daily_volatility * TRADING_DAYS_PER_YEAR.sqrt()

        # Compute Sharpe ratio
        if annualized_volatility == Decimal("0"):
            logger.warning(
                f"Zero volatility for {strategy_name} - cannot compute Sharpe",
                extra={"correlation_id": correlation_id, "strategy_name": strategy_name},
            )
            return None

        sharpe_ratio = (annualized_return - RISK_FREE_RATE) / annualized_volatility

        logger.info(
            f"Sharpe ratio for {strategy_name}: {sharpe_ratio:.3f} "
            f"(return={annualized_return:.2%}, vol={annualized_volatility:.2%})",
            extra={
                "correlation_id": correlation_id,
                "strategy_name": strategy_name,
                "sharpe_ratio": str(sharpe_ratio),
                "annualized_return": str(annualized_return),
                "annualized_volatility": str(annualized_volatility),
                "trade_count": len(recent_lots),
            },
        )

        return sharpe_ratio

    def _calculate_daily_returns(
        self, closed_lots: list[Any], correlation_id: str
    ) -> list[Decimal]:
        """Calculate daily returns from closed lots.

        Groups lots by close date and sums P&L for each day.

        Args:
            closed_lots: List of StrategyLot objects with realized_pnl
            correlation_id: Correlation ID for tracing

        Returns:
            List of daily returns (as percentage of average position value)

        """
        # Group lots by close date
        daily_pnl: dict[str, Decimal] = {}

        for lot in closed_lots:
            if lot.close_timestamp and lot.realized_pnl is not None:
                date_key = lot.close_timestamp.date().isoformat()
                daily_pnl[date_key] = daily_pnl.get(date_key, Decimal("0")) + lot.realized_pnl

        # Calculate average position value for normalization
        # Use average of entry values across all lots
        avg_position_value = Decimal("0")
        if closed_lots:
            total_value = sum(
                lot.quantity * lot.entry_price
                for lot in closed_lots
                if lot.quantity and lot.entry_price
            )
            avg_position_value = total_value / len(closed_lots)

        if avg_position_value == Decimal("0"):
            logger.warning(
                "Cannot calculate returns - zero position value",
                extra={"correlation_id": correlation_id},
            )
            return []

        # Convert daily P&L to daily returns (as percentage)
        daily_returns = [pnl / avg_position_value for pnl in daily_pnl.values()]

        logger.debug(
            f"Calculated {len(daily_returns)} daily returns from {len(closed_lots)} lots",
            extra={"correlation_id": correlation_id, "avg_position_value": str(avg_position_value)},
        )

        return daily_returns
