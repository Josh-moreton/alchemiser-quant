"""Business Unit: scripts | Status: current.

Build daily returns series from DynamoDB strategy lot data.

Queries TradeLedgerTable for closed StrategyLots and reconstructs
equity curves to produce daily returns suitable for QuantStats analysis.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

import boto3
import pandas as pd
from botocore.exceptions import BotoCoreError, ClientError

if TYPE_CHECKING:
    from mypy_boto3_dynamodb.service_resource import Table

logger = logging.getLogger(__name__)

DynamoDBException = (ClientError, BotoCoreError)


class ReturnsBuilder:
    """Builds daily returns series from DynamoDB trade lot data.

    Queries closed StrategyLots from DynamoDB, reconstructs equity curves
    from realized P&L, and converts to daily returns series for QuantStats.
    """

    def __init__(self, table_name: str, initial_capital: Decimal = Decimal("100000")) -> None:
        """Initialize the returns builder.

        Args:
            table_name: DynamoDB TradeLedger table name
            initial_capital: Starting capital for equity curve reconstruction

        """
        self._dynamodb = boto3.resource("dynamodb")
        self._table: Table = self._dynamodb.Table(table_name)
        self._initial_capital = initial_capital
        logger.info(f"ReturnsBuilder initialized with table: {table_name}")

    def discover_strategies(self) -> list[str]:
        """Discover all strategies that have closed lots.

        Returns:
            Sorted list of unique strategy names with closed lots

        """
        try:
            strategy_names: set[str] = set()

            # Scan for closed LOT# items
            kwargs = {
                "FilterExpression": "begins_with(PK, :pk) AND is_open = :open",
                "ExpressionAttributeValues": {
                    ":pk": "LOT#",
                    ":open": False,
                },
                "ProjectionExpression": "strategy_name",
            }

            response = self._table.scan(**kwargs)
            for item in response.get("Items", []):
                name = item.get("strategy_name")
                if name:
                    strategy_names.add(str(name))

            # Handle pagination
            while "LastEvaluatedKey" in response:
                kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]
                response = self._table.scan(**kwargs)
                for item in response.get("Items", []):
                    name = item.get("strategy_name")
                    if name:
                        strategy_names.add(str(name))

            strategies = sorted(strategy_names)
            logger.info(f"Discovered {len(strategies)} strategies with closed lots")
            return strategies

        except DynamoDBException as e:
            logger.error(f"Failed to discover strategies: {e}")
            return []

    def query_closed_lots(
        self,
        strategy_name: str,
        days_lookback: int | None = None,
    ) -> list[dict]:
        """Query closed lots for a strategy.

        Args:
            strategy_name: Strategy name to query
            days_lookback: Optional limit to N days of history

        Returns:
            List of closed lot items from DynamoDB

        """
        try:
            kwargs = {
                "IndexName": "GSI5-StrategyLotsIndex",
                "KeyConditionExpression": "GSI5PK = :pk AND begins_with(GSI5SK, :sk)",
                "ExpressionAttributeValues": {
                    ":pk": f"STRATEGY_LOTS#{strategy_name}",
                    ":sk": "CLOSED#",
                },
                "ScanIndexForward": True,  # Chronological order
            }

            items: list[dict] = []
            response = self._table.query(**kwargs)
            items.extend(response.get("Items", []))

            # Handle pagination
            while "LastEvaluatedKey" in response:
                kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]
                response = self._table.query(**kwargs)
                items.extend(response.get("Items", []))

            # Filter by lookback if specified
            if days_lookback and items:
                cutoff = datetime.now(UTC) - timedelta(days=days_lookback)
                items = [
                    item
                    for item in items
                    if self._parse_timestamp(item.get("fully_closed_at")) >= cutoff
                ]

            logger.info(f"Found {len(items)} closed lots for strategy {strategy_name}")
            return items

        except DynamoDBException as e:
            logger.error(f"Failed to query closed lots for {strategy_name}: {e}")
            return []

    def _parse_timestamp(self, ts_str: str | None) -> datetime:
        """Parse ISO timestamp string to datetime.

        Args:
            ts_str: ISO format timestamp string

        Returns:
            Timezone-aware datetime (defaults to epoch if parse fails)

        """
        if not ts_str:
            return datetime(1970, 1, 1, tzinfo=UTC)
        try:
            dt = datetime.fromisoformat(ts_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
            return dt
        except (ValueError, TypeError):
            return datetime(1970, 1, 1, tzinfo=UTC)

    def build_equity_curve(
        self,
        lots: list[dict],
        initial_capital: Decimal | None = None,
    ) -> pd.Series:
        """Reconstruct daily equity curve from closed lot data.

        Args:
            lots: List of closed lot items from DynamoDB
            initial_capital: Starting capital (defaults to instance value)

        Returns:
            Series of daily portfolio values indexed by date

        """
        if not lots:
            return pd.Series(dtype=float)

        capital = initial_capital or self._initial_capital

        # Extract daily P&L from closed lots
        daily_pnl: dict[datetime, Decimal] = {}

        for lot in lots:
            closed_at_str = lot.get("fully_closed_at")
            if not closed_at_str:
                continue

            closed_at = self._parse_timestamp(closed_at_str)
            # Normalize to date (remove time component)
            exit_date = closed_at.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)

            # Get realized P&L from lot
            pnl = Decimal(lot.get("realized_pnl", "0"))

            if exit_date in daily_pnl:
                daily_pnl[exit_date] += pnl
            else:
                daily_pnl[exit_date] = pnl

        if not daily_pnl:
            return pd.Series(dtype=float)

        # Convert to series and build cumulative equity
        pnl_series = pd.Series(daily_pnl).sort_index()
        cumulative_pnl = pnl_series.cumsum()
        equity = float(capital) + cumulative_pnl.astype(float)

        # Fill gaps with previous value (for days without trades)
        if len(equity) > 1:
            date_range = pd.date_range(start=equity.index.min(), end=equity.index.max(), freq="D")
            equity = equity.reindex(date_range, method="ffill")

        equity.name = "portfolio_value"
        return equity

    def build_returns_series(
        self,
        strategy_name: str,
        days_lookback: int | None = None,
    ) -> pd.Series:
        """Build daily returns series for a strategy.

        Args:
            strategy_name: Strategy name to build returns for
            days_lookback: Optional limit to N days of history

        Returns:
            Series of daily percentage returns (decimals, e.g., 0.01 = 1%)

        """
        lots = self.query_closed_lots(strategy_name, days_lookback)
        equity = self.build_equity_curve(lots)

        if equity.empty or len(equity) < 2:
            logger.warning(f"Insufficient data for strategy {strategy_name}")
            return pd.Series(dtype=float)

        # Convert equity to returns
        returns = equity.pct_change().dropna()

        # QuantStats expects timezone-naive index
        if returns.index.tz is not None:
            returns.index = returns.index.tz_localize(None)

        returns.name = strategy_name
        logger.info(f"Built returns series for {strategy_name}: {len(returns)} data points")
        return returns

    def build_portfolio_returns(
        self,
        days_lookback: int | None = None,
        strategies: list[str] | None = None,
    ) -> pd.Series:
        """Build combined portfolio returns across all strategies.

        Aggregates P&L from all strategies into a single portfolio equity curve.

        Args:
            days_lookback: Optional limit to N days of history
            strategies: Optional list of strategies (discovers all if None)

        Returns:
            Series of daily portfolio returns

        """
        if strategies is None:
            strategies = self.discover_strategies()

        if not strategies:
            logger.warning("No strategies found for portfolio returns")
            return pd.Series(dtype=float)

        # Aggregate all lots from all strategies
        all_lots: list[dict] = []
        for strategy_name in strategies:
            lots = self.query_closed_lots(strategy_name, days_lookback)
            all_lots.extend(lots)

        if not all_lots:
            logger.warning("No closed lots found across all strategies")
            return pd.Series(dtype=float)

        # Build combined equity curve
        equity = self.build_equity_curve(all_lots)

        if equity.empty or len(equity) < 2:
            logger.warning("Insufficient data for portfolio returns")
            return pd.Series(dtype=float)

        # Convert to returns
        returns = equity.pct_change().dropna()

        # QuantStats expects timezone-naive index
        if returns.index.tz is not None:
            returns.index = returns.index.tz_localize(None)

        returns.name = "portfolio"
        logger.info(f"Built portfolio returns: {len(returns)} data points from {len(strategies)} strategies")
        return returns

    def get_strategy_summary(self, strategy_name: str) -> dict:
        """Get summary statistics for a strategy.

        Args:
            strategy_name: Strategy name

        Returns:
            Dict with summary metrics

        """
        lots = self.query_closed_lots(strategy_name)

        if not lots:
            return {
                "strategy_name": strategy_name,
                "total_lots": 0,
                "total_realized_pnl": Decimal("0"),
                "first_trade_date": None,
                "last_trade_date": None,
            }

        total_pnl = sum(Decimal(lot.get("realized_pnl", "0")) for lot in lots)
        timestamps = [
            self._parse_timestamp(lot.get("fully_closed_at"))
            for lot in lots
            if lot.get("fully_closed_at")
        ]

        return {
            "strategy_name": strategy_name,
            "total_lots": len(lots),
            "total_realized_pnl": total_pnl,
            "first_trade_date": min(timestamps).isoformat() if timestamps else None,
            "last_trade_date": max(timestamps).isoformat() if timestamps else None,
        }
