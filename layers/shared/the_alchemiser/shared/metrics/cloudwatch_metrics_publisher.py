"""Business Unit: shared | Status: current.

CloudWatch metrics publisher for strategy performance tracking.

Publishes per-strategy realized P&L metrics to CloudWatch for dashboard visualization.
"""

from __future__ import annotations

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

# CloudWatch metric names
METRIC_NAME_REALIZED_PNL = "RealizedPnL"
METRIC_NAME_CAPITAL_DEPLOYED = "CapitalDeployedPct"
METRIC_NAME_CURRENT_HOLDINGS_VALUE = "CurrentHoldingsValue"
METRIC_NAME_CURRENT_HOLDINGS = "CurrentHoldings"
METRIC_NAME_COMPLETED_TRADES = "CompletedTrades"
METRIC_NAME_WIN_RATE = "WinRate"
METRIC_NAME_AVG_PROFIT_PER_TRADE = "AvgProfitPerTrade"
METRIC_NAME_WINNING_TRADES = "WinningTrades"
METRIC_NAME_LOSING_TRADES = "LosingTrades"

# AWS exception types
AWSException = (ClientError, BotoCoreError)


class CloudWatchMetricsPublisher:
    """Publisher for strategy performance metrics to CloudWatch.

    Queries closed lots from DynamoDB, aggregates P&L by strategy, and publishes
    metrics to CloudWatch for dashboard visualization.
    """

    def __init__(
        self,
        trade_ledger_table_name: str,
        stage: str,
        region: str = "us-east-1",
    ) -> None:
        """Initialize metrics publisher.

        Args:
            trade_ledger_table_name: DynamoDB trade ledger table name
            stage: Deployment stage (dev or production)
            region: AWS region

        """
        self.region = region
        self.namespace = f"Alchemiser/{stage.title()}"
        self._cloudwatch = boto3.client("cloudwatch", region_name=region)
        self._repository = DynamoDBTradeLedgerRepository(trade_ledger_table_name)

    def publish_strategy_pnl_metrics(self, correlation_id: str) -> None:
        """Publish per-strategy realized P&L metrics to CloudWatch.

        Queries all lots with completed trades from DynamoDB, aggregates by strategy,
        and publishes cumulative realized P&L for each strategy.

        Args:
            correlation_id: Correlation ID for tracing

        """
        logger.info(
            "Publishing strategy P&L metrics to CloudWatch",
            extra={"correlation_id": correlation_id},
        )

        try:
            # Discover all strategies with completed trades (exit records)
            strategy_names = self._repository.discover_strategies_with_completed_trades()

            if not strategy_names:
                logger.info(
                    "No strategies with completed trades found",
                    extra={"correlation_id": correlation_id},
                )
                return

            # Aggregate P&L per strategy
            metric_data: list[dict[str, Any]] = []
            timestamp = datetime.now(UTC)

            for strategy_name in strategy_names:
                pnl = self._calculate_strategy_pnl(strategy_name)

                # Create metric data point
                metric_data.append(
                    {
                        "MetricName": METRIC_NAME_REALIZED_PNL,
                        "Dimensions": [
                            {"Name": "StrategyName", "Value": strategy_name},
                        ],
                        "Value": float(pnl),
                        "Unit": "None",  # Dollar amount
                        "Timestamp": timestamp,
                    }
                )

                logger.info(
                    f"Strategy {strategy_name} realized P&L: ${pnl}",
                    extra={
                        "correlation_id": correlation_id,
                        "strategy_name": strategy_name,
                        "realized_pnl": str(pnl),
                    },
                )

            # Publish metrics in batch (CloudWatch supports up to 1000 per call)
            if metric_data:
                self._cloudwatch.put_metric_data(
                    Namespace=self.namespace,
                    MetricData=metric_data,
                )

                logger.info(
                    f"Published {len(metric_data)} strategy P&L metrics to CloudWatch",
                    extra={
                        "correlation_id": correlation_id,
                        "strategy_count": len(metric_data),
                        "namespace": self.namespace,
                    },
                )

        except AWSException as e:
            logger.error(
                f"Failed to publish CloudWatch metrics: {e}",
                extra={
                    "correlation_id": correlation_id,
                    "error_type": type(e).__name__,
                },
            )
        except Exception as e:
            logger.error(
                f"Unexpected error publishing CloudWatch metrics: {e}",
                exc_info=True,
                extra={
                    "correlation_id": correlation_id,
                    "error_type": type(e).__name__,
                },
            )

    def _calculate_strategy_pnl(self, strategy_name: str) -> Decimal:
        """Calculate cumulative realized P&L for a strategy.

        Sums P&L from all exit records across all lots for the strategy.
        Each exit record represents a completed trade with its own P&L.

        Args:
            strategy_name: Strategy name

        Returns:
            Cumulative realized P&L from all completed trades

        """
        # Query ALL lots for the strategy (not just closed ones)
        all_lots = self._repository.query_all_lots_by_strategy(strategy_name)

        total_pnl = Decimal("0")
        for lot in all_lots:
            # lot.realized_pnl is a computed property that sums all exit_records
            if lot.realized_pnl is not None:
                total_pnl += lot.realized_pnl

        return total_pnl

    def publish_capital_deployed_metric(
        self, capital_deployed_pct: Decimal | None, correlation_id: str
    ) -> None:
        """Publish capital deployed percentage metric to CloudWatch.

        Args:
            capital_deployed_pct: Capital deployed as percentage (0-100), or None if unavailable
            correlation_id: Correlation ID for tracing

        """
        if capital_deployed_pct is None:
            logger.info(
                "Capital deployed percentage not available, skipping metric",
                extra={"correlation_id": correlation_id},
            )
            return

        try:
            timestamp = datetime.now(UTC)
            self._cloudwatch.put_metric_data(
                Namespace=self.namespace,
                MetricData=[
                    {
                        "MetricName": METRIC_NAME_CAPITAL_DEPLOYED,
                        "Value": float(capital_deployed_pct),
                        "Unit": "Percent",
                        "Timestamp": timestamp,
                    }
                ],
            )

            logger.info(
                f"Published capital deployed metric: {capital_deployed_pct:.2f}%",
                extra={
                    "correlation_id": correlation_id,
                    "capital_deployed_pct": str(capital_deployed_pct),
                    "namespace": self.namespace,
                },
            )

        except AWSException as e:
            logger.error(
                f"Failed to publish capital deployed metric: {e}",
                extra={
                    "correlation_id": correlation_id,
                    "error_type": type(e).__name__,
                },
            )
        except Exception as e:
            logger.error(
                f"Unexpected error publishing capital deployed metric: {e}",
                exc_info=True,
                extra={
                    "correlation_id": correlation_id,
                    "error_type": type(e).__name__,
                },
            )

    def publish_all_strategy_metrics(self, correlation_id: str) -> None:
        """Publish per-strategy performance metrics to CloudWatch.

        Fetches strategy summaries from DynamoDB and publishes metrics with
        StrategyName dimension for each strategy.

        Args:
            correlation_id: Correlation ID for tracing

        """
        try:
            summaries = self._repository.get_all_strategy_summaries()

            if not summaries:
                logger.info(
                    "No strategy summaries found, skipping per-strategy metrics",
                    extra={"correlation_id": correlation_id},
                )
                return

            timestamp = datetime.now(UTC)
            metric_data: list[dict[str, Any]] = []

            for summary in summaries:
                strategy_name = summary["strategy_name"]
                dimensions = [{"Name": "StrategyName", "Value": strategy_name}]

                # Add all metrics for this strategy
                metric_data.extend(
                    [
                        {
                            "MetricName": METRIC_NAME_CURRENT_HOLDINGS_VALUE,
                            "Value": float(summary["current_holdings_value"]),
                            "Unit": "None",
                            "Timestamp": timestamp,
                            "Dimensions": dimensions,
                        },
                        {
                            "MetricName": METRIC_NAME_CURRENT_HOLDINGS,
                            "Value": float(summary["current_holdings"]),
                            "Unit": "Count",
                            "Timestamp": timestamp,
                            "Dimensions": dimensions,
                        },
                        {
                            "MetricName": METRIC_NAME_COMPLETED_TRADES,
                            "Value": float(summary["completed_trades"]),
                            "Unit": "Count",
                            "Dimensions": dimensions,
                            "Timestamp": timestamp,
                        },
                        {
                            "MetricName": METRIC_NAME_REALIZED_PNL,
                            "Value": float(summary["total_realized_pnl"]),
                            "Unit": "None",
                            "Timestamp": timestamp,
                            "Dimensions": dimensions,
                        },
                        {
                            "MetricName": METRIC_NAME_WINNING_TRADES,
                            "Value": float(summary["winning_trades"]),
                            "Unit": "Count",
                            "Timestamp": timestamp,
                            "Dimensions": dimensions,
                        },
                        {
                            "MetricName": METRIC_NAME_LOSING_TRADES,
                            "Value": float(summary["losing_trades"]),
                            "Unit": "Count",
                            "Timestamp": timestamp,
                            "Dimensions": dimensions,
                        },
                        {
                            "MetricName": METRIC_NAME_WIN_RATE,
                            "Value": float(summary["win_rate"]),
                            "Unit": "Percent",
                            "Timestamp": timestamp,
                            "Dimensions": dimensions,
                        },
                        {
                            "MetricName": METRIC_NAME_AVG_PROFIT_PER_TRADE,
                            "Value": float(summary["avg_profit_per_trade"]),
                            "Unit": "None",
                            "Timestamp": timestamp,
                            "Dimensions": dimensions,
                        },
                    ]
                )

            # CloudWatch allows max 1000 metrics per put_metric_data call
            batch_size = 1000
            for i in range(0, len(metric_data), batch_size):
                batch = metric_data[i : i + batch_size]
                self._cloudwatch.put_metric_data(
                    Namespace=self.namespace,
                    MetricData=batch,
                )

            logger.info(
                f"Published per-strategy metrics for {len(summaries)} strategies",
                extra={
                    "correlation_id": correlation_id,
                    "strategy_count": len(summaries),
                    "metric_count": len(metric_data),
                    "namespace": self.namespace,
                },
            )

        except AWSException as e:
            logger.error(
                f"Failed to publish per-strategy metrics: {e}",
                extra={
                    "correlation_id": correlation_id,
                    "error_type": type(e).__name__,
                },
            )
        except Exception as e:
            logger.error(
                f"Unexpected error publishing per-strategy metrics: {e}",
                exc_info=True,
                extra={
                    "correlation_id": correlation_id,
                    "error_type": type(e).__name__,
                },
            )
