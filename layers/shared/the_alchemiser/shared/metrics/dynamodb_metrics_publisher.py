"""Business Unit: shared | Status: current.

DynamoDB metrics publisher for strategy performance tracking.

Writes per-strategy performance metrics to DynamoDB for dashboard consumption.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.repositories.dynamodb_trade_ledger_repository import (
    DynamoDBTradeLedgerRepository,
)

logger = get_logger(__name__)

# TTL: 90 days in seconds
_TTL_SECONDS = 90 * 24 * 60 * 60

AWSException = (ClientError, BotoCoreError)


class DynamoDBMetricsPublisher:
    """Publisher for strategy performance metrics to DynamoDB.

    Queries closed lots from TradeLedger, aggregates P&L by strategy,
    and writes snapshot items to the StrategyPerformance table.
    """

    def __init__(
        self,
        trade_ledger_table_name: str,
        strategy_performance_table_name: str,
    ) -> None:
        """Initialize with trade ledger (read) and performance (write) tables."""
        self._repository = DynamoDBTradeLedgerRepository(trade_ledger_table_name)
        dynamodb = boto3.resource("dynamodb")
        self._table = dynamodb.Table(strategy_performance_table_name)

    def write_strategy_metrics(self, correlation_id: str) -> None:
        """Write per-strategy performance snapshots to DynamoDB.

        Fetches strategy summaries from the trade ledger and writes
        one item per strategy (snapshot + LATEST pointer).

        Args:
            correlation_id: Correlation ID for tracing

        """
        try:
            summaries = self._repository.get_all_strategy_summaries()

            if not summaries:
                logger.info(
                    "No strategy summaries found, skipping metrics write",
                    extra={"correlation_id": correlation_id},
                )
                return

            timestamp = datetime.now(UTC)
            iso_ts = timestamp.isoformat()
            ttl = int(time.time()) + _TTL_SECONDS

            with self._table.batch_writer() as batch:
                for summary in summaries:
                    strategy_name = summary["strategy_name"]
                    item = self._build_item(summary, iso_ts, ttl, correlation_id)

                    # Write snapshot item
                    snapshot_item = {
                        "PK": f"STRATEGY#{strategy_name}",
                        "SK": f"SNAPSHOT#{iso_ts}",
                        **item,
                    }
                    batch.put_item(Item=snapshot_item)

                    # Write LATEST pointer (overwrites previous)
                    latest_item = {
                        "PK": "LATEST",
                        "SK": f"STRATEGY#{strategy_name}",
                        **item,
                    }
                    batch.put_item(Item=latest_item)

            logger.info(
                f"Wrote performance metrics for {len(summaries)} strategies",
                extra={
                    "correlation_id": correlation_id,
                    "strategy_count": len(summaries),
                },
            )

        except AWSException as e:
            logger.error(
                f"Failed to write strategy metrics: {e}",
                extra={
                    "correlation_id": correlation_id,
                    "error_type": type(e).__name__,
                },
            )
        except Exception as e:
            logger.error(
                f"Unexpected error writing strategy metrics: {e}",
                exc_info=True,
                extra={
                    "correlation_id": correlation_id,
                    "error_type": type(e).__name__,
                },
            )

    def write_capital_deployed_metric(
        self, capital_deployed_pct: Decimal | None, correlation_id: str
    ) -> None:
        """Write capital deployed percentage to DynamoDB.

        Args:
            capital_deployed_pct: Capital deployed as percentage (0-100)
            correlation_id: Correlation ID for tracing

        """
        if capital_deployed_pct is None:
            return

        try:
            timestamp = datetime.now(UTC)
            iso_ts = timestamp.isoformat()
            ttl = int(time.time()) + _TTL_SECONDS

            item: dict[str, str | int] = {
                "PK": "CAPITAL_DEPLOYED",
                "SK": f"SNAPSHOT#{iso_ts}",
                "capital_deployed_pct": str(capital_deployed_pct),
                "snapshot_timestamp": iso_ts,
                "correlation_id": correlation_id,
                "ExpiresAt": ttl,
            }
            self._table.put_item(Item=item)

            # LATEST pointer
            latest_item: dict[str, str | int] = {
                "PK": "LATEST",
                "SK": "CAPITAL_DEPLOYED",
                "capital_deployed_pct": str(capital_deployed_pct),
                "snapshot_timestamp": iso_ts,
                "correlation_id": correlation_id,
                "ExpiresAt": ttl,
            }
            self._table.put_item(Item=latest_item)

            logger.info(
                f"Wrote capital deployed metric: {capital_deployed_pct:.2f}%",
                extra={
                    "correlation_id": correlation_id,
                    "capital_deployed_pct": str(capital_deployed_pct),
                },
            )

        except AWSException as e:
            logger.error(
                f"Failed to write capital deployed metric: {e}",
                extra={
                    "correlation_id": correlation_id,
                    "error_type": type(e).__name__,
                },
            )

    @staticmethod
    def _build_item(
        summary: dict[str, Any],
        iso_ts: str,
        ttl: int,
        correlation_id: str,
    ) -> dict[str, Any]:
        """Build a DynamoDB item from a strategy summary."""
        return {
            "strategy_name": summary["strategy_name"],
            "snapshot_timestamp": iso_ts,
            "realized_pnl": str(summary["total_realized_pnl"]),
            "current_holdings_value": str(summary["current_holdings_value"]),
            "current_holdings": summary["current_holdings"],
            "completed_trades": summary["completed_trades"],
            "winning_trades": summary["winning_trades"],
            "losing_trades": summary["losing_trades"],
            "win_rate": str(summary["win_rate"]),
            "avg_profit_per_trade": str(summary["avg_profit_per_trade"]),
            "correlation_id": correlation_id,
            "ExpiresAt": ttl,
        }
