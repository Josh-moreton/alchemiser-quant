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

# CloudWatch configuration
NAMESPACE = "Alchemiser/Production"
METRIC_NAME_REALIZED_PNL = "RealizedPnL"

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
        region: str = "us-east-1",
    ) -> None:
        """Initialize metrics publisher.

        Args:
            trade_ledger_table_name: DynamoDB trade ledger table name
            region: AWS region

        """
        self.region = region
        self._cloudwatch = boto3.client("cloudwatch", region_name=region)
        self._repository = DynamoDBTradeLedgerRepository(trade_ledger_table_name)

    def publish_strategy_pnl_metrics(self, correlation_id: str) -> None:
        """Publish per-strategy realized P&L metrics to CloudWatch.

        Queries all closed lots from DynamoDB, aggregates by strategy, and publishes
        cumulative realized P&L for each strategy.

        Args:
            correlation_id: Correlation ID for tracing

        """
        logger.info(
            "Publishing strategy P&L metrics to CloudWatch",
            extra={"correlation_id": correlation_id},
        )

        try:
            # Discover all strategies with closed lots
            strategy_names = self._repository.discover_strategies_with_closed_lots()

            if not strategy_names:
                logger.info(
                    "No strategies with closed lots found",
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
                    Namespace=NAMESPACE,
                    MetricData=metric_data,
                )

                logger.info(
                    f"Published {len(metric_data)} strategy P&L metrics to CloudWatch",
                    extra={
                        "correlation_id": correlation_id,
                        "strategy_count": len(metric_data),
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

        Args:
            strategy_name: Strategy name

        Returns:
            Cumulative realized P&L

        """
        closed_lots = self._repository.query_closed_lots_by_strategy(strategy_name)

        total_pnl = Decimal("0")
        for lot in closed_lots:
            if lot.realized_pnl is not None:
                total_pnl += lot.realized_pnl

        return total_pnl
