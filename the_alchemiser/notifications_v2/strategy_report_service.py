"""Business Unit: notifications | Status: current.

Strategy performance report service for generating CSV reports.

Generates per-strategy performance CSV reports, uploads to S3, and returns
presigned URLs for inclusion in trading notification emails.

REPORT TYPES:
=============
1. Strategy Summary Report: High-level per-strategy performance metrics
2. Closed Trades Report: Detailed per-trade P&L with FIFO lot matching

The closed trades report provides exact per-strategy attribution including:
- Entry/exit prices and timestamps
- Quantity traded (supports fractional shares)
- Realized P&L per trade
- Hold duration
"""

from __future__ import annotations

import csv
import io
import os
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.repositories.dynamodb_trade_ledger_repository import (
    DynamoDBTradeLedgerRepository,
)
from the_alchemiser.shared.schemas.strategy_lot import StrategyLotSummary

logger = get_logger(__name__)

__all__ = [
    "StrategyPerformanceReportService",
    "generate_closed_trades_report_url",
    "generate_performance_report_url",
]

# AWS exception types
AWSException = (ClientError, BotoCoreError)

# Presigned URL expiry (7 days in seconds)
PRESIGNED_URL_EXPIRY_SECONDS = 7 * 24 * 60 * 60


class StrategyPerformanceReportService:
    """Service for generating strategy performance CSV reports.

    Queries DynamoDB for all strategy performance data, generates a consolidated
    CSV report, uploads to S3, and returns a time-limited presigned URL.
    """

    def __init__(
        self,
        table_name: str | None = None,
        bucket_name: str | None = None,
        region: str | None = None,
    ) -> None:
        """Initialize report service.

        Args:
            table_name: DynamoDB table name (falls back to env var)
            bucket_name: S3 bucket name (falls back to env var)
            region: AWS region

        """
        self.table_name = table_name or os.environ.get("TRADE_LEDGER__TABLE_NAME")
        self.bucket_name = bucket_name or os.environ.get("PERFORMANCE_REPORTS_BUCKET")
        self.region = region or os.environ.get("AWS_REGION", "us-east-1")

        self._s3_client = boto3.client("s3", region_name=self.region)
        self._repository: DynamoDBTradeLedgerRepository | None = None

        if self.table_name:
            self._repository = DynamoDBTradeLedgerRepository(self.table_name)
        else:
            logger.warning("TRADE_LEDGER__TABLE_NAME not set - report service disabled")

    def generate_report_url(
        self,
        correlation_id: str,
        strategy_names: list[str] | None = None,
    ) -> str | None:
        """Generate performance report and return presigned URL.

        Creates a CSV with all-time per-strategy performance metrics:
        - strategy_name
        - total_trades
        - buy_trades / sell_trades
        - total_buy_value / total_sell_value
        - gross_pnl
        - realized_pnl (FIFO matched)
        - symbols_traded
        - first_trade_at / last_trade_at
        - report_generated_at

        Args:
            correlation_id: Correlation ID for tracing and filename
            strategy_names: Optional list of strategy names to include.
                           If None, discovers strategies from DynamoDB.

        Returns:
            Presigned URL valid for 7 days, or None if generation fails

        """
        if not self._repository or not self.bucket_name:
            logger.warning(
                "Report service not fully configured",
                extra={
                    "has_repository": self._repository is not None,
                    "has_bucket": self.bucket_name is not None,
                    "correlation_id": correlation_id,
                },
            )
            return None

        try:
            # Discover strategies if not provided
            if strategy_names is None:
                strategy_names = self._discover_strategies()

            if not strategy_names:
                logger.info(
                    "No strategies found for performance report",
                    extra={"correlation_id": correlation_id},
                )
                return None

            # Generate CSV content
            csv_content = self._generate_csv(strategy_names, correlation_id)

            # Upload to S3
            object_key = self._upload_to_s3(csv_content, correlation_id)

            # Generate presigned URL
            presigned_url = self._generate_presigned_url(object_key)

            logger.info(
                "Performance report generated successfully",
                extra={
                    "correlation_id": correlation_id,
                    "strategy_count": len(strategy_names),
                    "object_key": object_key,
                },
            )

            return presigned_url

        except AWSException as e:
            logger.error(
                f"Failed to generate performance report: {e}",
                extra={
                    "correlation_id": correlation_id,
                    "error_type": type(e).__name__,
                },
            )
            return None
        except Exception as e:
            logger.error(
                f"Unexpected error generating performance report: {e}",
                exc_info=True,
                extra={
                    "correlation_id": correlation_id,
                    "error_type": type(e).__name__,
                },
            )
            return None

    def _discover_strategies(self) -> list[str]:
        """Discover all unique strategy names from DynamoDB.

        Scans for STRATEGY# partition keys to find all strategies with trades.

        Returns:
            List of unique strategy names

        """
        if not self._repository:
            return []

        try:
            # Query a sample of strategy-trade items to discover strategy names
            # We use a scan with filter since we don't have a GSI for listing all strategies
            table = self._repository._table
            response = table.scan(
                FilterExpression="begins_with(PK, :pk)",
                ExpressionAttributeValues={":pk": "STRATEGY#"},
                ProjectionExpression="PK",
            )

            # Extract unique strategy names from PK values
            strategy_names: set[str] = set()
            for item in response.get("Items", []):
                pk = item.get("PK", "")
                if pk.startswith("STRATEGY#"):
                    strategy_name = pk.replace("STRATEGY#", "")
                    strategy_names.add(strategy_name)

            # Handle pagination if needed
            while "LastEvaluatedKey" in response:
                response = table.scan(
                    FilterExpression="begins_with(PK, :pk)",
                    ExpressionAttributeValues={":pk": "STRATEGY#"},
                    ProjectionExpression="PK",
                    ExclusiveStartKey=response["LastEvaluatedKey"],
                )
                for item in response.get("Items", []):
                    pk = item.get("PK", "")
                    if pk.startswith("STRATEGY#"):
                        strategy_name = pk.replace("STRATEGY#", "")
                        strategy_names.add(strategy_name)

            return sorted(strategy_names)

        except AWSException as e:
            logger.error(f"Failed to discover strategies: {e}")
            return []

    def _generate_csv(self, strategy_names: list[str], correlation_id: str) -> str:
        """Generate CSV content with per-strategy performance metrics.

        Args:
            strategy_names: List of strategy names to include
            correlation_id: Correlation ID for the report

        Returns:
            CSV content as string

        """
        report_timestamp = datetime.now(UTC).isoformat()

        # CSV columns
        fieldnames = [
            "strategy_name",
            "total_trades",
            "buy_trades",
            "sell_trades",
            "total_buy_value",
            "total_sell_value",
            "gross_pnl",
            "realized_pnl",
            "symbols_traded",
            "first_trade_at",
            "last_trade_at",
            "report_generated_at",
            "correlation_id",
        ]

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for strategy_name in strategy_names:
            performance = self._get_strategy_performance(strategy_name)

            row = {
                "strategy_name": strategy_name,
                "total_trades": performance.get("total_trades", 0),
                "buy_trades": performance.get("buy_trades", 0),
                "sell_trades": performance.get("sell_trades", 0),
                "total_buy_value": self._format_decimal(performance.get("total_buy_value")),
                "total_sell_value": self._format_decimal(performance.get("total_sell_value")),
                "gross_pnl": self._format_decimal(performance.get("gross_pnl")),
                "realized_pnl": self._format_decimal(performance.get("realized_pnl")),
                "symbols_traded": ";".join(performance.get("symbols_traded", [])),
                "first_trade_at": performance.get("first_trade_at") or "",
                "last_trade_at": performance.get("last_trade_at") or "",
                "report_generated_at": report_timestamp,
                "correlation_id": correlation_id,
            }
            writer.writerow(row)

        return output.getvalue()

    def _generate_closed_trades_csv(self, correlation_id: str) -> str:
        """Generate detailed CSV with all closed trades from lot tracking.

        Each row represents a fully closed lot, including:
        - Strategy and symbol
        - Entry and exit prices/timestamps
        - Quantity traded
        - Realized P&L (absolute and percentage)
        - Hold duration

        Args:
            correlation_id: Correlation ID for the report

        Returns:
            CSV content as string

        """
        report_timestamp = datetime.now(UTC).isoformat()

        # Detailed trade columns matching StrategyLotSummary fields
        fieldnames = [
            "strategy_name",
            "symbol",
            "lot_id",
            "correlation_id",
            "entry_timestamp",
            "exit_timestamp",
            "hold_duration_seconds",
            "hold_duration_hours",
            "entry_price",
            "avg_exit_price",
            "entry_qty",
            "entry_cost_basis",
            "exit_value",
            "realized_pnl",
            "pnl_percent",
            "report_generated_at",
        ]

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        if not self._repository:
            return output.getvalue()

        # Discover all strategies with closed lots
        strategy_names = self._repository.discover_strategies_with_closed_lots()

        for strategy_name in strategy_names:
            # Get closed lots only for this strategy
            closed_lots = self._repository.query_closed_lots_by_strategy(strategy_name)

            for lot in closed_lots:
                # Skip if somehow still open
                if lot.is_open or lot.fully_closed_at is None:
                    continue

                try:
                    # Use the from_lot factory method for proper summarization
                    summary = StrategyLotSummary.from_lot(lot)

                    # Calculate hold duration in hours for convenience
                    hold_hours = Decimal(str(summary.hold_duration_seconds)) / Decimal("3600")

                    row = {
                        "strategy_name": summary.strategy_name,
                        "symbol": summary.symbol,
                        "lot_id": summary.lot_id,
                        "correlation_id": summary.correlation_id,
                        "entry_timestamp": summary.entry_timestamp.isoformat(),
                        "exit_timestamp": summary.exit_timestamp.isoformat(),
                        "hold_duration_seconds": summary.hold_duration_seconds,
                        "hold_duration_hours": self._format_decimal(hold_hours),
                        "entry_price": self._format_decimal(summary.entry_price),
                        "avg_exit_price": self._format_decimal(summary.avg_exit_price),
                        "entry_qty": self._format_decimal(summary.entry_qty),
                        "entry_cost_basis": self._format_decimal(summary.entry_cost_basis),
                        "exit_value": self._format_decimal(summary.exit_value),
                        "realized_pnl": self._format_decimal(summary.realized_pnl),
                        "pnl_percent": self._format_decimal(summary.pnl_percent),
                        "report_generated_at": report_timestamp,
                    }
                    writer.writerow(row)

                except ValueError as e:
                    logger.warning(
                        f"Failed to create lot summary: {e}",
                        lot_id=lot.lot_id,
                        strategy=strategy_name,
                    )
                    continue

        return output.getvalue()

    def generate_closed_trades_report_url(self, correlation_id: str) -> str | None:
        """Generate detailed closed trades report and return presigned URL.

        Creates a CSV with per-trade details:
        - strategy_name, symbol
        - entry_price, exit_price
        - qty, realized_pnl, pnl_percent
        - entry_timestamp, exit_timestamp, hold_duration_hours

        Args:
            correlation_id: Correlation ID for tracing and filename

        Returns:
            Presigned URL valid for 7 days, or None if generation fails

        """
        if not self._repository or not self.bucket_name:
            logger.warning(
                "Report service not fully configured",
                extra={
                    "has_repository": self._repository is not None,
                    "has_bucket": self.bucket_name is not None,
                    "correlation_id": correlation_id,
                },
            )
            return None

        try:
            # Generate CSV content
            csv_content = self._generate_closed_trades_csv(correlation_id)

            # Check if we have any data
            lines = csv_content.strip().split("\n")
            if len(lines) <= 1:  # Only header
                logger.info(
                    "No closed trades found for report",
                    extra={"correlation_id": correlation_id},
                )
                return None

            # Upload to S3
            timestamp = datetime.now(UTC).strftime("%Y-%m-%d_%H-%M-%S")
            object_key = f"reports/{timestamp}_{correlation_id[:8]}_closed_trades.csv"

            self._s3_client.put_object(
                Bucket=self.bucket_name,
                Key=object_key,
                Body=csv_content.encode("utf-8"),
                ContentType="text/csv",
                ContentDisposition=f'attachment; filename="closed_trades_{timestamp}.csv"',
            )

            # Generate presigned URL
            presigned_url = self._generate_presigned_url(object_key)

            logger.info(
                "Closed trades report generated successfully",
                extra={
                    "correlation_id": correlation_id,
                    "object_key": object_key,
                    "trade_count": len(lines) - 1,
                },
            )

            return presigned_url

        except AWSException as e:
            logger.error(
                f"Failed to generate closed trades report: {e}",
                extra={
                    "correlation_id": correlation_id,
                    "error_type": type(e).__name__,
                },
            )
            return None
        except Exception as e:
            logger.error(
                f"Unexpected error generating closed trades report: {e}",
                exc_info=True,
                extra={
                    "correlation_id": correlation_id,
                    "error_type": type(e).__name__,
                },
            )
            return None

    def _get_strategy_performance(self, strategy_name: str) -> dict[str, Any]:
        """Get performance metrics for a single strategy.

        Args:
            strategy_name: Strategy name

        Returns:
            Performance metrics dictionary

        """
        if not self._repository:
            return {}

        return self._repository.compute_strategy_performance(strategy_name)

    def _format_decimal(self, value: Decimal | None) -> str:
        """Format Decimal value for CSV output.

        Args:
            value: Decimal value or None

        Returns:
            Formatted string with 2 decimal places, or "0.00" if None

        """
        if value is None:
            return "0.00"
        return f"{value:.2f}"

    def _upload_to_s3(self, csv_content: str, correlation_id: str) -> str:
        """Upload CSV content to S3.

        Args:
            csv_content: CSV string content
            correlation_id: Correlation ID for filename

        Returns:
            S3 object key

        """
        timestamp = datetime.now(UTC).strftime("%Y-%m-%d_%H-%M-%S")
        object_key = f"reports/{timestamp}_{correlation_id[:8]}_strategy_performance.csv"

        self._s3_client.put_object(
            Bucket=self.bucket_name,
            Key=object_key,
            Body=csv_content.encode("utf-8"),
            ContentType="text/csv",
            ContentDisposition=f'attachment; filename="strategy_performance_{timestamp}.csv"',
        )

        logger.debug(
            "CSV uploaded to S3",
            extra={
                "bucket": self.bucket_name,
                "key": object_key,
                "size_bytes": len(csv_content),
            },
        )

        return object_key

    def _generate_presigned_url(self, object_key: str) -> str:
        """Generate presigned URL for S3 object.

        Args:
            object_key: S3 object key

        Returns:
            Presigned URL valid for 7 days

        """
        presigned_url: str = self._s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket_name, "Key": object_key},
            ExpiresIn=PRESIGNED_URL_EXPIRY_SECONDS,
        )

        return presigned_url


# Module-level singleton
_report_service: StrategyPerformanceReportService | None = None


def get_report_service() -> StrategyPerformanceReportService:
    """Get or create the global report service instance.

    Returns:
        Singleton StrategyPerformanceReportService instance

    """
    global _report_service
    if _report_service is None:
        _report_service = StrategyPerformanceReportService()
    return _report_service


def generate_performance_report_url(
    correlation_id: str,
    strategy_names: list[str] | None = None,
) -> str | None:
    """Generate performance report URL (convenience function).

    Args:
        correlation_id: Correlation ID for tracing
        strategy_names: Optional list of strategies to include

    Returns:
        Presigned URL or None if generation fails

    """
    return get_report_service().generate_report_url(
        correlation_id=correlation_id,
        strategy_names=strategy_names,
    )


def generate_closed_trades_report_url(correlation_id: str) -> str | None:
    """Generate closed trades report URL (convenience function).

    Args:
        correlation_id: Correlation ID for tracing

    Returns:
        Presigned URL or None if generation fails

    """
    return get_report_service().generate_closed_trades_report_url(
        correlation_id=correlation_id,
    )
