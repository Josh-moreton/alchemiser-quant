#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Daily P&L tracking service with DynamoDB persistence.

This service provides the canonical interface for daily P&L tracking,
managing DynamoDB reads/writes and serving as the single source of truth
for historical performance data.

Settlement Logic (T+1):
- Deposits settle T+1 (next trading day after they're made)
- A deposit on Friday settles Monday; weekend deposits settle Monday
- True trading P&L = equity_change - deposits_settled_today
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

        Uses a single Alpaca API call with cashflow_types to get portfolio history
        AND deposit/withdrawal data together. Applies T+1 settlement logic:
        - Deposits made on day D settle on the next trading day
        - True trading P&L = equity_change - deposits_settled_today

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
            date_str = target_date.isoformat()

            # Fetch portfolio history WITH cashflow data in a single API call
            # Use 7-day lookback to capture previous trading day and weekend deposits
            lookback_start = (target_date - timedelta(days=7)).isoformat()
            history = self._alpaca_manager.get_portfolio_history_with_cashflow(
                start_date=lookback_start,
                end_date=date_str,
                timeframe="1D",
                pnl_reset="per_day",
                intraday_reporting="market_hours",
                cashflow_types="CSD,CSW",
            )

            if not history or not history.get("equity") or not history.get("timestamp"):
                raise DataProviderError(
                    f"No equity data available for {date_str}",
                    context={"date": date_str, "correlation_id": self._correlation_id},
                )

            timestamps = history["timestamp"]
            equity_values = history["equity"]
            profit_loss_values = history.get("profit_loss", [])
            cashflow = history.get("cashflow", {})

            # Extract cashflow arrays (aligned with timestamps)
            csd_values = cashflow.get("CSD", [0] * len(timestamps))
            csw_values = cashflow.get("CSW", [0] * len(timestamps))

            # Build list of trading days and deposits_by_date from cashflow
            all_trading_days: list[str] = []
            deposits_by_date: dict[str, Decimal] = {}

            for i, ts in enumerate(timestamps):
                day_str = datetime.fromtimestamp(ts, tz=UTC).strftime("%Y-%m-%d")
                all_trading_days.append(day_str)
                # Record deposit amount for this day (from cashflow array)
                if i < len(csd_values) and csd_values[i] != 0:
                    deposits_by_date[day_str] = Decimal(str(csd_values[i]))

            # Find target date's index in the history
            if date_str not in all_trading_days:
                raise DataProviderError(
                    f"Target date {date_str} not in portfolio history (may not be a trading day)",
                    context={"date": date_str, "trading_days": all_trading_days[-5:]},
                )

            target_idx = all_trading_days.index(date_str)
            end_equity = Decimal(str(equity_values[target_idx]))
            raw_pnl = (
                Decimal(str(profit_loss_values[target_idx])) if profit_loss_values else Decimal("0")
            )

            # Get previous trading day's equity for equity_change calculation
            if target_idx > 0:
                prev_trading_day = all_trading_days[target_idx - 1]
                prev_equity = Decimal(str(equity_values[target_idx - 1]))
            else:
                prev_trading_day = None
                prev_equity = end_equity  # First day, no change

            equity_change = end_equity - prev_equity

            # Normalize cashflow arrays to match trading days length to ensure safe indexing
            trading_days_len = len(all_trading_days)
            if len(csd_values) < trading_days_len:
                csd_values = list(csd_values) + [0.0] * (trading_days_len - len(csd_values))
            if len(csw_values) < trading_days_len:
                csw_values = list(csw_values) + [0.0] * (trading_days_len - len(csw_values))

            # Get deposits/withdrawals for today directly from normalized cashflow arrays
            deposits_made_today = Decimal(str(csd_values[target_idx]))
            withdrawals_today = abs(Decimal(str(csw_values[target_idx])))

            # Calculate deposits that settled today using T+1 logic
            # Deposits made on prev_trading_day (or weekend days before today) settle today
            deposits_settled_today = Decimal("0")
            if prev_trading_day:
                settlement_dates = self._get_deposit_dates_for_settlement(
                    prev_trading_day, date_str, set(all_trading_days)
                )
                for d in settlement_dates:
                    if d in deposits_by_date:
                        deposits_settled_today += deposits_by_date[d]

            # True trading P&L = equity_change - deposits_settled
            pnl_adjusted = equity_change - deposits_settled_today

            # Calculate percentage based on start-of-day equity
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
                raw_pnl=raw_pnl,
                deposits_settled=deposits_settled_today,
                deposits=deposits_made_today,
                withdrawals=withdrawals_today,
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
                    "equity_change": float(equity_change),
                    "deposits_settled": float(deposits_settled_today),
                    "raw_pnl": float(raw_pnl),
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

    def _process_cash_activities(
        self, cash_activities: list[dict[str, Any]], date_str: str
    ) -> tuple[dict[str, Decimal], Decimal, Decimal]:
        """Process cash activities and return deposits/withdrawals summary.

        Args:
            cash_activities: List of activity records from Alpaca.
            date_str: Target date (YYYY-MM-DD).

        Returns:
            Tuple of (deposits_by_date, total_withdrawals, deposits_made_today).

        """
        deposits_by_date: dict[str, Decimal] = {}
        total_withdrawals = Decimal("0")
        deposits_made_today = Decimal("0")

        for activity in cash_activities:
            activity_date = activity.get("date", "")[:10]
            activity_type = activity.get("activity_type", "")
            try:
                amount = Decimal(str(activity.get("net_amount", "0")))
            except (ValueError, ArithmeticError):
                continue

            if activity_type == "CSD":
                deposits_by_date[activity_date] = (
                    deposits_by_date.get(activity_date, Decimal("0")) + amount
                )
                if activity_date == date_str:
                    deposits_made_today = amount
            elif activity_type == "CSW" and activity_date == date_str:
                total_withdrawals += abs(amount)

        return deposits_by_date, total_withdrawals, deposits_made_today

    def _get_deposit_dates_for_settlement(
        self, prev_trading_day: str, today: str, all_trading_days: set[str]
    ) -> list[str]:
        """Get calendar dates where deposits would settle on 'today'.

        Deposits settle T+1 (next trading day after they're made):
        - Deposit on trading day P settles on next trading day after P
        - Deposit on non-trading day (weekend/holiday) settles on next trading day

        For trading day D with previous trading day P:
        - Include deposits made on P (they settle on D)
        - Include deposits made on non-trading days between P and D

        Args:
            prev_trading_day: Previous trading day (YYYY-MM-DD).
            today: Current trading day (YYYY-MM-DD).
            all_trading_days: Set of all known trading days.

        Returns:
            List of dates whose deposits settle on 'today'.

        """
        start = date.fromisoformat(prev_trading_day)
        end = date.fromisoformat(today)
        dates: list[str] = []

        # Start from day AFTER prev_trading_day
        current = start + timedelta(days=1)
        while current < end:  # exclusive of today
            day_str = current.strftime("%Y-%m-%d")
            # Non-trading days: deposits settle on next trading day (today)
            if day_str not in all_trading_days:
                dates.append(day_str)
            current += timedelta(days=1)

        # Include prev_trading_day - deposits on P settle on D
        # (This is always true for consecutive trading days)
        if (end - start).days == 1:
            # Consecutive calendar days = consecutive trading days
            dates.insert(0, prev_trading_day)
        elif not dates:
            # No non-trading days between them, so P's deposits settle on D
            dates.append(prev_trading_day)
        else:
            # There are gaps (weekends/holidays), P's deposits still settle on D
            dates.insert(0, prev_trading_day)

        return dates

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
                date=str(item["date"]),
                equity=Decimal(str(item["equity"])),
                pnl_amount=Decimal(str(item["pnl_amount"])),
                pnl_percent=Decimal(str(item["pnl_percent"])),
                raw_pnl=Decimal(str(item.get("raw_pnl", "0"))),
                deposits_settled=Decimal(str(item.get("deposits_settled", "0"))),
                deposits=Decimal(str(item.get("deposits", "0"))),
                withdrawals=Decimal(str(item.get("withdrawals", "0"))),
                timestamp=str(item["timestamp"]),
                environment=str(item["environment"]),
                schema_version=str(item.get("schema_version", "1.0")),
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

    def get_daily_pnl_range(self, start_date: date, end_date: date) -> list[DailyPnLRecord]:
        """Retrieve daily P&L records for a date range from DynamoDB.

        Note: This method uses DynamoDB Scan with pagination and FilterExpression.
        For large date ranges (e.g., multiple years), this will scan the entire
        table and filter results, which can be expensive in terms of RCUs and latency.
        Consider using narrow date ranges where possible. For future optimization,
        consider adding a GSI with environment as partition key and date as sort key
        for more efficient Query operations.

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

            # Use pagination to handle tables larger than 1MB
            items: list[dict[str, Any]] = []
            last_evaluated_key: dict[str, Any] | None = None

            while True:
                scan_kwargs: dict[str, Any] = {
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
                        date=str(item["date"]),
                        equity=Decimal(str(item["equity"])),
                        pnl_amount=Decimal(str(item["pnl_amount"])),
                        pnl_percent=Decimal(str(item["pnl_percent"])),
                        raw_pnl=Decimal(str(item.get("raw_pnl", "0"))),
                        deposits_settled=Decimal(str(item.get("deposits_settled", "0"))),
                        deposits=Decimal(str(item.get("deposits", "0"))),
                        withdrawals=Decimal(str(item.get("withdrawals", "0"))),
                        timestamp=str(item["timestamp"]),
                        environment=str(item["environment"]),
                        schema_version=str(item.get("schema_version", "1.0")),
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
                "Failed to retrieve daily PnL range",
                context={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "error": str(e),
                    "correlation_id": self._correlation_id,
                },
            ) from e

    def get_weekly_aggregate(self, week_start: date) -> dict[str, Any]:
        """Get aggregated P&L for a specific week (Monday to Sunday).

        Args:
            week_start: The Monday of the week to aggregate.

        Returns:
            Dict with aggregated metrics:
            - start_date, end_date
            - start_equity, end_equity
            - total_pnl, total_pnl_percent
            - trading_days (count)
            - daily_records (list)

        """
        # Ensure week_start is a Monday
        if week_start.weekday() != 0:
            # Adjust to previous Monday
            week_start = week_start - timedelta(days=week_start.weekday())

        week_end = week_start + timedelta(days=6)  # Sunday

        records = self.get_daily_pnl_range(week_start, week_end)

        return self._aggregate_records(records, week_start, week_end, "week")

    def get_monthly_aggregate(self, year: int, month: int) -> dict[str, Any]:
        """Get aggregated P&L for a specific calendar month.

        Args:
            year: Year (e.g., 2026).
            month: Month (1-12).

        Returns:
            Dict with aggregated metrics:
            - start_date, end_date
            - start_equity, end_equity
            - total_pnl, total_pnl_percent
            - trading_days (count)
            - daily_records (list)

        """
        # Calculate month boundaries
        start_date = date(year, month, 1)

        # End date is last day of month
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)

        records = self.get_daily_pnl_range(start_date, end_date)

        return self._aggregate_records(records, start_date, end_date, "month")

    def _aggregate_records(
        self,
        records: list[DailyPnLRecord],
        start_date: date,
        end_date: date,
        period_type: str,
    ) -> dict[str, Any]:
        """Aggregate daily records into period summary.

        Args:
            records: List of daily PnL records.
            start_date: Period start date.
            end_date: Period end date.
            period_type: "week" or "month" for logging.

        Returns:
            Aggregated metrics dict.

        """
        if not records:
            logger.info(
                f"No records found for {period_type} {start_date} to {end_date}",
                extra={"correlation_id": self._correlation_id},
            )
            return {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "start_equity": None,
                "end_equity": None,
                "total_pnl": Decimal("0"),
                "total_pnl_percent": Decimal("0"),
                "trading_days": 0,
                "daily_records": [],
            }

        # First record's starting equity = equity - pnl_amount
        start_equity = records[0].equity - records[0].pnl_amount
        end_equity = records[-1].equity

        # Sum daily P&L (already deposit-adjusted)
        total_pnl = sum(r.pnl_amount for r in records)

        # Calculate percentage based on start equity
        if start_equity > Decimal("0"):
            total_pnl_percent = (total_pnl / start_equity) * PERCENTAGE_MULTIPLIER
        else:
            total_pnl_percent = Decimal("0")

        logger.info(
            f"Aggregated {period_type} P&L: {start_date} to {end_date}",
            extra={
                "trading_days": len(records),
                "total_pnl": float(total_pnl),
                "total_pnl_percent": float(total_pnl_percent),
                "correlation_id": self._correlation_id,
            },
        )

        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "start_equity": start_equity,
            "end_equity": end_equity,
            "total_pnl": total_pnl,
            "total_pnl_percent": total_pnl_percent,
            "trading_days": len(records),
            "daily_records": records,
        }

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
                "raw_pnl": str(record.raw_pnl),
                "deposits_settled": str(record.deposits_settled),
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
