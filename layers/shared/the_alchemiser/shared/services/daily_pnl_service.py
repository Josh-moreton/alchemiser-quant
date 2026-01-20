#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Daily P&L tracking service with DynamoDB persistence.

This service provides the canonical interface for daily P&L tracking,
managing DynamoDB reads/writes and serving as the single source of truth
for historical performance data.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any

import boto3
from botocore.exceptions import ClientError

from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
from the_alchemiser.shared.errors.exceptions import (
    ConfigurationError,
    DataProviderError,
    StorageError,
)
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.daily_pnl import DailyPnLRecord

logger = get_logger(__name__)

# Constants
PERCENTAGE_MULTIPLIER: Decimal = Decimal("100")


class DailyPnLService:
    """Service for capturing and retrieving daily P&L from DynamoDB.

    This service is the canonical source for historical daily P&L data.
    It captures daily snapshots from Alpaca and stores them in DynamoDB,
    providing fast, consistent access to performance history.

    Attributes:
        table_name: DynamoDB table name for daily PnL records.
        environment: Environment string (dev/staging/prod).
        alpaca_manager: Optional Alpaca manager for capturing new data.

    """

    def __init__(
        self,
        table_name: str,
        environment: str,
        alpaca_manager: AlpacaManager | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Initialize DailyPnLService.

        Args:
            table_name: DynamoDB table name.
            environment: Environment (dev/staging/prod).
            alpaca_manager: Optional Alpaca manager instance.
            correlation_id: Optional correlation ID for tracing.

        Raises:
            ConfigurationError: If table_name or environment is missing.

        """
        if not table_name:
            raise ConfigurationError(
                "DynamoDB table name is required", config_key="DAILY_PNL_TABLE_NAME"
            )
        if not environment:
            raise ConfigurationError("Environment is required", config_key="ENVIRONMENT")

        self.table_name = table_name
        self.environment = environment
        self._alpaca_manager = alpaca_manager
        self._correlation_id = correlation_id or ""
        self._dynamodb = boto3.resource("dynamodb")
        self._table = self._dynamodb.Table(table_name)

    def capture_daily_pnl(self, target_date: date) -> DailyPnLRecord:
        """Capture daily P&L for a specific date and store in DynamoDB.

        Fetches equity, P&L, and cash movements from Alpaca for the target date,
        calculates adjusted P&L (minus deposits, plus withdrawals), and stores
        the record in DynamoDB.

        Args:
            target_date: Date to capture P&L for (typically yesterday).

        Returns:
            DailyPnLRecord stored in DynamoDB.

        Raises:
            ConfigurationError: If Alpaca manager is not configured.
            DataProviderError: If Alpaca API fails.
            StorageError: If DynamoDB write fails.

        """
        if not self._alpaca_manager:
            raise ConfigurationError(
                "Alpaca manager required for capturing PnL", config_key="alpaca_manager"
            )

        logger.info(
            f"Capturing daily PnL for {target_date}",
            extra={"date": target_date.isoformat(), "correlation_id": self._correlation_id},
        )

        try:
            # Fetch equity at end of target date using portfolio history
            date_str = target_date.isoformat()
            history = self._alpaca_manager.get_portfolio_history(
                start_date=date_str,
                end_date=date_str,
                timeframe="1D",
                pnl_reset="no_reset",
                intraday_reporting="market_hours",
            )

            if not history or not history.get("equity"):
                raise DataProviderError(
                    f"No equity data available for {date_str}",
                    context={"date": date_str, "correlation_id": self._correlation_id},
                )

            equity_values = history["equity"]
            profit_loss_values = history.get("profit_loss", [])

            # Get end-of-day equity
            end_equity = Decimal(str(equity_values[-1]))

            # Fetch deposits and withdrawals for the day
            cash_activities = self._alpaca_manager.get_non_trade_activities(
                start_date=date_str,
                activity_types=["CSD", "CSW"],
            )

            deposits, withdrawals = self._calculate_cash_movements(
                cash_activities, date_str, date_str
            )

            # Calculate daily P&L adjusted for cash movements
            # If we have profit_loss data, use it; otherwise estimate from equity change
            if profit_loss_values and len(profit_loss_values) > 0:
                # Get the change in cumulative P&L for this day
                if len(profit_loss_values) > 1:
                    pnl_raw = Decimal(str(profit_loss_values[-1])) - Decimal(
                        str(profit_loss_values[0])
                    )
                else:
                    pnl_raw = Decimal(str(profit_loss_values[0]))

                # Adjust for cash movements
                pnl_adjusted = pnl_raw - deposits + withdrawals
            else:
                # Fallback: estimate from equity change (less precise)
                # Get previous day's equity
                prev_date = target_date - timedelta(days=1)
                prev_record = self.get_daily_pnl(prev_date)
                if prev_record:
                    prev_equity = prev_record.equity
                    # equity_change includes both trading gains and cash movements
                    # Subtract deposits and add withdrawals to isolate trading performance
                    pnl_adjusted = (end_equity - prev_equity) - deposits + withdrawals
                else:
                    # No previous data, can't calculate daily P&L reliably
                    pnl_adjusted = Decimal("0")

            # Calculate percentage
            start_equity = end_equity - pnl_adjusted
            if start_equity > Decimal("0"):
                pnl_percent = (pnl_adjusted / start_equity) * PERCENTAGE_MULTIPLIER
            else:
                pnl_percent = Decimal("0")

            # Create record
            record = DailyPnLRecord(
                date=date_str,
                equity=end_equity,
                pnl_amount=pnl_adjusted,
                pnl_percent=pnl_percent,
                deposits=deposits,
                withdrawals=withdrawals,
                timestamp=datetime.now(UTC).isoformat(),
                environment=self.environment,
            )

            # Store in DynamoDB
            self._put_record(record)

            logger.info(
                f"Successfully captured daily PnL for {date_str}",
                extra={
                    "date": date_str,
                    "equity": float(end_equity),
                    "pnl_amount": float(pnl_adjusted),
                    "pnl_percent": float(pnl_percent),
                    "correlation_id": self._correlation_id,
                },
            )

            return record

        except DataProviderError:
            raise
        except Exception as e:
            logger.error(
                f"Failed to capture daily PnL for {target_date}: {e}",
                extra={
                    "date": target_date.isoformat(),
                    "error_type": type(e).__name__,
                    "correlation_id": self._correlation_id,
                },
            )
            raise DataProviderError(
                f"Failed to capture daily PnL for {target_date}: {e}",
                context={
                    "date": target_date.isoformat(),
                    "error": str(e),
                    "correlation_id": self._correlation_id,
                },
            ) from e

    def get_daily_pnl(self, target_date: date) -> DailyPnLRecord | None:
        """Retrieve daily P&L record for a specific date from DynamoDB.

        Args:
            target_date: Date to retrieve.

        Returns:
            DailyPnLRecord if found, None otherwise.

        Raises:
            StorageError: If DynamoDB read fails.

        """
        date_str = target_date.isoformat()
        try:
            response = self._table.get_item(Key={"date": date_str})
            if "Item" not in response:
                return None

            item = response["Item"]
            return DailyPnLRecord(
                date=item["date"],
                equity=Decimal(str(item["equity"])),
                pnl_amount=Decimal(str(item["pnl_amount"])),
                pnl_percent=Decimal(str(item["pnl_percent"])),
                deposits=Decimal(str(item.get("deposits", "0"))),
                withdrawals=Decimal(str(item.get("withdrawals", "0"))),
                timestamp=item["timestamp"],
                environment=item["environment"],
                schema_version=item.get("schema_version", "1.0"),
            )
        except ClientError as e:
            logger.error(
                f"Failed to retrieve daily PnL for {date_str}: {e}",
                extra={
                    "date": date_str,
                    "error_code": e.response.get("Error", {}).get("Code"),
                    "correlation_id": self._correlation_id,
                },
            )
            raise StorageError(
                f"Failed to retrieve daily PnL for {date_str}",
                context={"date": date_str, "error": str(e), "correlation_id": self._correlation_id},
            ) from e

    def get_daily_pnl_range(
        self, start_date: date, end_date: date
    ) -> list[DailyPnLRecord]:
        """Retrieve daily P&L records for a date range from DynamoDB.

        Note: This method uses DynamoDB Scan with pagination. For large date ranges
        (e.g., multiple years), this will scan the entire table and filter results,
        which can be expensive in terms of RCUs and latency. Consider using narrow
        date ranges where possible.

        Args:
            start_date: Start date (inclusive).
            end_date: End date (inclusive).

        Returns:
            List of DailyPnLRecord objects, sorted by date ascending.

        Raises:
            StorageError: If DynamoDB scan fails.

        """
        try:
            start_str = start_date.isoformat()
            end_str = end_date.isoformat()

            # Paginate through all results
            items: list[dict[str, Any]] = []
            last_evaluated_key: dict[str, Any] | None = None

            while True:
                scan_kwargs = {
                    "FilterExpression": "#d >= :start_date AND #d <= :end_date AND #env = :environment",
                    "ExpressionAttributeNames": {"#d": "date", "#env": "environment"},
                    "ExpressionAttributeValues": {
                        ":start_date": start_str,
                        ":end_date": end_str,
                        ":environment": self.environment,
                    },
                }
                if last_evaluated_key:
                    scan_kwargs["ExclusiveStartKey"] = last_evaluated_key

                response = self._table.scan(**scan_kwargs)
                items.extend(response.get("Items", []))
                last_evaluated_key = response.get("LastEvaluatedKey")
                if not last_evaluated_key:
                    break

            records: list[DailyPnLRecord] = []
            for item in items:
                records.append(
                    DailyPnLRecord(
                        date=item["date"],
                        equity=Decimal(str(item["equity"])),
                        pnl_amount=Decimal(str(item["pnl_amount"])),
                        pnl_percent=Decimal(str(item["pnl_percent"])),
                        deposits=Decimal(str(item.get("deposits", "0"))),
                        withdrawals=Decimal(str(item.get("withdrawals", "0"))),
                        timestamp=item["timestamp"],
                        environment=item["environment"],
                        schema_version=item.get("schema_version", "1.0"),
                    )
                )

            # Sort by date
            records.sort(key=lambda r: r.date)

            logger.info(
                f"Retrieved {len(records)} daily PnL records",
                extra={
                    "start_date": start_str,
                    "end_date": end_str,
                    "count": len(records),
                    "correlation_id": self._correlation_id,
                },
            )

            return records

        except ClientError as e:
            logger.error(
                f"Failed to retrieve daily PnL range: {e}",
                extra={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "error_code": e.response.get("Error", {}).get("Code"),
                    "correlation_id": self._correlation_id,
                },
            )
            raise StorageError(
                f"Failed to retrieve daily PnL range",
                context={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "error": str(e),
                    "correlation_id": self._correlation_id,
                },
            ) from e

    def _put_record(self, record: DailyPnLRecord) -> None:
        """Store a daily PnL record in DynamoDB.

        Args:
            record: DailyPnLRecord to store.

        Raises:
            StorageError: If DynamoDB write fails.

        """
        try:
            item = {
                "date": record.date,
                "equity": str(record.equity),
                "pnl_amount": str(record.pnl_amount),
                "pnl_percent": str(record.pnl_percent),
                "deposits": str(record.deposits),
                "withdrawals": str(record.withdrawals),
                "timestamp": record.timestamp,
                "environment": record.environment,
                "schema_version": record.schema_version,
            }
            self._table.put_item(Item=item)
        except ClientError as e:
            logger.error(
                f"Failed to store daily PnL record: {e}",
                extra={
                    "date": record.date,
                    "error_code": e.response.get("Error", {}).get("Code"),
                    "correlation_id": self._correlation_id,
                },
            )
            raise StorageError(
                f"Failed to store daily PnL record for {record.date}",
                context={
                    "date": record.date,
                    "error": str(e),
                    "correlation_id": self._correlation_id,
                },
            ) from e

    def _calculate_cash_movements(
        self,
        cash_activities: list[dict[str, str]],
        start_date: str,
        end_date: str,
    ) -> tuple[Decimal, Decimal]:
        """Calculate total deposits (CSD) and withdrawals (CSW) within the date range.

        Args:
            cash_activities: List of CSD/CSW activities from Alpaca.
            start_date: Period start date (YYYY-MM-DD).
            end_date: Period end date (YYYY-MM-DD).

        Returns:
            Tuple of (total_deposits, total_withdrawals).

        """
        total_deposits = Decimal("0")
        total_withdrawals = Decimal("0")

        for activity in cash_activities:
            activity_date = activity.get("date", "")[:10]  # YYYY-MM-DD
            activity_type = activity.get("activity_type", "")
            amount_str = activity.get("net_amount", "0")

            # Filter to activities within the period
            if activity_date < start_date or activity_date > end_date:
                continue

            try:
                amount = Decimal(str(amount_str))
            except (ValueError, ArithmeticError):
                continue

            if activity_type == "CSD":  # Cash Deposit
                total_deposits += amount
            elif activity_type == "CSW":  # Cash Withdrawal
                total_withdrawals += abs(amount)

        return total_deposits, total_withdrawals
