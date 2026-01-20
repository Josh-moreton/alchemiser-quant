#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

P&L Analysis Service for The Alchemiser Trading System.

This service provides portfolio profit and loss analysis using the Alpaca API,
supporting weekly and monthly performance reports.
"""

from __future__ import annotations

import calendar
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from the_alchemiser.shared.brokers.alpaca_manager import (
    AlpacaManager,
    create_alpaca_manager,
)
from the_alchemiser.shared.config.secrets_adapter import get_alpaca_keys
from the_alchemiser.shared.errors.exceptions import ConfigurationError, DataProviderError
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.pnl import DailyPnLEntry, PnLData
from the_alchemiser.shared.types.money import Money

logger = get_logger(__name__)

# Constants
PERCENTAGE_MULTIPLIER: Decimal = Decimal("100")


class PnLService:
    """Service for P&L analysis and reporting.
    
    This service provides a unified interface for P&L data, using DynamoDB
    as the primary source for historical daily data (fast, consistent) and
    Alpaca as fallback for real-time or missing data.
    """

    def __init__(
        self,
        alpaca_manager: AlpacaManager | None = None,
        correlation_id: str | None = None,
        dynamodb_table_name: str | None = None,
        environment: str | None = None,
    ) -> None:
        """Initialize P&L service.

        Args:
            alpaca_manager: Alpaca manager instance. If None, creates one from config.
            correlation_id: Optional correlation ID for observability tracing.
            dynamodb_table_name: Optional DynamoDB table name for daily PnL cache.
            environment: Environment (dev/staging/prod) for DynamoDB filtering.

        Raises:
            ConfigurationError: If Alpaca API keys are not found in configuration.

        """
        self._correlation_id = correlation_id or ""
        self._dynamodb_table_name = dynamodb_table_name
        self._environment = environment or "dev"
        self._daily_pnl_service = None
        
        if alpaca_manager is None:
            api_key, secret_key, endpoint = get_alpaca_keys()
            if not api_key or not secret_key:
                raise ConfigurationError(
                    "Alpaca API keys not found in configuration",
                    config_key="ALPACA_KEY/ALPACA_SECRET",
                )

            # Determine if this is paper trading based on endpoint (normalize variants)
            paper = self._is_paper_from_endpoint(endpoint)

            self._alpaca_manager = create_alpaca_manager(
                api_key=api_key, secret_key=secret_key, paper=paper
            )
        else:
            self._alpaca_manager = alpaca_manager
        
        # Initialize DailyPnLService if table name provided
        # Lazy import to avoid circular dependency (DailyPnLService imports AlpacaManager)
        if dynamodb_table_name:
            from the_alchemiser.shared.services.daily_pnl_service import DailyPnLService
            
            self._daily_pnl_service = DailyPnLService(
                table_name=dynamodb_table_name,
                environment=self._environment,
                alpaca_manager=self._alpaca_manager,
                correlation_id=self._correlation_id,
            )

    @staticmethod
    def _is_paper_from_endpoint(ep: str | None) -> bool:
        """Determine if endpoint is for paper trading.

        Args:
            ep: Endpoint URL string or None.

        Returns:
            True if endpoint is for paper trading, False for live trading.

        """
        if not ep:
            return True
        ep_norm = ep.strip().rstrip("/").lower()
        if ep_norm.endswith("/v2"):
            ep_norm = ep_norm[:-3]
        # Explicit paper host
        if "paper-api.alpaca.markets" in ep_norm:
            return True
        # Explicit live host
        return not ("api.alpaca.markets" in ep_norm and "paper" not in ep_norm)

    def get_weekly_pnl(self, weeks_back: int = 1) -> PnLData:
        """Get P&L for the past N weeks.

        Args:
            weeks_back: Number of weeks back to analyze (default: 1 = last week)

        Returns:
            PnLData object with weekly performance

        """
        # Calculate date range for the specified week
        today = datetime.now(UTC).date()
        end_date = today - timedelta(days=(today.weekday() + 1) % 7)  # Last Sunday
        start_date = end_date - timedelta(days=7 * weeks_back - 1)

        return self._get_period_pnl(
            period=f"{weeks_back} week{'s' if weeks_back > 1 else ''}",
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )

    def get_monthly_pnl(self, months_back: int = 1) -> PnLData:
        """Get P&L for the past N months.

        Args:
            months_back: Number of months back to analyze (default: 1 = last month)

        Returns:
            PnLData object with monthly performance

        """
        # Calculate date range for the specified month
        today = datetime.now(UTC).date()

        # Go back to start of N months ago
        year = today.year
        month = today.month - months_back
        if month <= 0:
            month += 12
            year -= 1

        start_date = datetime(year, month, 1, tzinfo=UTC).date()

        # End date is last day of that month
        if month == 12:
            end_year = year + 1
            end_month = 1
        else:
            end_year = year
            end_month = month + 1
        end_date = (datetime(end_year, end_month, 1, tzinfo=UTC) - timedelta(days=1)).date()

        return self._get_period_pnl(
            period=f"{months_back} month{'s' if months_back > 1 else ''}",
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )

    def get_calendar_month_pnl(self, year: int, month: int) -> PnLData:
        """Get P&L for a specific calendar month.

        Args:
            year: The year (e.g., 2025)
            month: The month (1-12)

        Returns:
            PnLData object with the month's performance.
            Period label includes month name (e.g., "December 2025").

        Raises:
            ValueError: If month is not in range 1-12.

        """
        if not 1 <= month <= 12:
            raise ValueError(f"month must be in range 1-12; got {month}")

        # Start of the month
        start_date = datetime(year, month, 1, tzinfo=UTC).date()

        # End of the month (or today if current month)
        today = datetime.now(UTC).date()
        if year == today.year and month == today.month:
            # Current month - use today as end date (MTD)
            end_date = today
            month_name = calendar.month_name[month]
            period_label = f"{month_name} {year} (MTD)"
        else:
            # Past month - use last day of month
            if month == 12:
                end_date = (datetime(year + 1, 1, 1, tzinfo=UTC) - timedelta(days=1)).date()
            else:
                end_date = (datetime(year, month + 1, 1, tzinfo=UTC) - timedelta(days=1)).date()
            month_name = calendar.month_name[month]
            period_label = f"{month_name} {year}"

        return self._get_period_pnl(
            period=period_label,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )

    def get_last_n_calendar_months_pnl(self, n_months: int = 3) -> list[PnLData]:
        """Get P&L for the last N calendar months including current month.
        
        Uses DynamoDB as primary source for completed days if available,
        falling back to Alpaca for missing or current-month data.

        Args:
            n_months: Number of months to fetch (must be positive; default 3, including current month)

        Returns:
            List of PnLData objects, oldest first (e.g., [Nov, Dec, Jan MTD]).

        Raises:
            ValueError: If n_months is not a positive integer.

        """
        if n_months <= 0:
            raise ValueError(f"n_months must be a positive integer; got {n_months}")
        
        # Try DynamoDB first for faster, cached results
        if self._daily_pnl_service:
            try:
                return self._get_last_n_months_from_dynamodb(n_months)
            except Exception as e:
                logger.warning(
                    f"Failed to fetch P&L from DynamoDB, falling back to Alpaca: {e}",
                    extra={
                        "correlation_id": self._correlation_id,
                        "error_type": type(e).__name__,
                    },
                )
        
        # Fallback to Alpaca (original implementation)
        return self._get_last_n_months_from_alpaca(n_months)
    
    def _get_last_n_months_from_dynamodb(self, n_months: int) -> list[PnLData]:
        """Get last N months P&L from DynamoDB with daily granularity.
        
        Aggregates daily records from DynamoDB into monthly PnLData objects.
        """
        today = datetime.now(UTC).date()
        results: list[PnLData] = []
        
        for i in range(n_months - 1, -1, -1):  # Start from oldest
            # Calculate target month
            target_month = today.month - i
            target_year = today.year

            while target_month <= 0:
                target_month += 12
                target_year -= 1
            
            # Calculate date range for this month
            start_date = datetime(target_year, target_month, 1, tzinfo=UTC).date()
            
            # End date is last day of month or today if current month
            if target_year == today.year and target_month == today.month:
                end_date = today
                month_name = calendar.month_name[target_month]
                period_label = f"{month_name} {target_year} (MTD)"
            else:
                if target_month == 12:
                    end_date = (datetime(target_year + 1, 1, 1, tzinfo=UTC) - timedelta(days=1)).date()
                else:
                    end_date = (datetime(target_year, target_month + 1, 1, tzinfo=UTC) - timedelta(days=1)).date()
                month_name = calendar.month_name[target_month]
                period_label = f"{month_name} {target_year}"
            
            # Fetch daily records from DynamoDB
            try:
                daily_records = self._daily_pnl_service.get_daily_pnl_range(start_date, end_date)
                
                if not daily_records:
                    # No data in DynamoDB, add empty entry
                    results.append(PnLData(period=period_label))
                    continue
                
                # Aggregate daily records into monthly P&L
                first_record = daily_records[0]
                if first_record.date == start_date.isoformat():
                    # We have data from the requested period start; derive start-of-day equity
                    start_equity = first_record.equity - first_record.pnl_amount
                else:
                    # Data does not start at the requested month boundary; fall back to using
                    # the first available day's ending equity as the period start. This avoids
                    # incorrectly inferring true month-start equity when records are missing.
                    logger.warning(
                        "Daily P&L records do not start at requested start_date; "
                        "using first available day's ending equity as start_equity.",
                        extra={
                            "correlation_id": self._correlation_id,
                            "year": target_year,
                            "month": target_month,
                            "requested_start_date": start_date.isoformat(),
                            "actual_first_date": first_record.date,
                        },
                    )
                    start_equity = first_record.equity
                
                end_equity = daily_records[-1].equity
                
                # Sum daily P&L (already adjusted for deposits/withdrawals)
                total_pnl = sum(record.pnl_amount for record in daily_records)
                
                # Calculate percentage
                if start_equity > Decimal("0"):
                    total_pnl_pct = (total_pnl / start_equity) * Decimal("100")
                else:
                    total_pnl_pct = Decimal("0")
                
                # Convert daily records to DailyPnLEntry
                daily_data = [
                    DailyPnLEntry(
                        date=record.date,
                        equity=record.equity,
                        profit_loss=record.pnl_amount,
                        profit_loss_pct=record.pnl_percent,
                    )
                    for record in daily_records
                ]
                
                results.append(
                    PnLData(
                        period=period_label,
                        start_date=start_date.isoformat(),
                        end_date=end_date.isoformat(),
                        start_value=start_equity,
                        end_value=end_equity,
                        total_pnl=total_pnl,
                        total_pnl_pct=total_pnl_pct,
                        daily_data=daily_data,
                    )
                )
            except Exception as e:
                logger.warning(
                    f"Failed to fetch P&L from DynamoDB for {target_year}-{target_month:02d}: {e}",
                    extra={
                        "correlation_id": self._correlation_id,
                        "year": target_year,
                        "month": target_month,
                    },
                )
                # Add empty entry
                results.append(PnLData(period=period_label))
        
        return results
    
    def _get_last_n_months_from_alpaca(self, n_months: int) -> list[PnLData]:
        """Get last N months P&L from Alpaca (original implementation)."""
        today = datetime.now(UTC).date()
        results: list[PnLData] = []

        for i in range(n_months - 1, -1, -1):  # Start from oldest
            # Calculate target month
            target_month = today.month - i
            target_year = today.year

            while target_month <= 0:
                target_month += 12
                target_year -= 1

            try:
                pnl_data = self.get_calendar_month_pnl(target_year, target_month)
                results.append(pnl_data)
            except Exception as e:
                logger.warning(
                    f"Failed to fetch P&L for {target_year}-{target_month:02d}: {e}",
                    extra={
                        "correlation_id": self._correlation_id,
                        "year": target_year,
                        "month": target_month,
                    },
                )
                # Still add an empty entry so we have consistent count
                import calendar

                month_name = calendar.month_name[target_month]
                is_current = target_year == today.year and target_month == today.month
                period_label = f"{month_name} {target_year}" + (" (MTD)" if is_current else "")
                results.append(PnLData(period=period_label))

        return results

    def get_period_pnl(self, period: str) -> PnLData:
        """Get P&L using Alpaca period strings.

        Args:
            period: Alpaca period string (e.g., '1W', '1M', '3M', '1A')

        Returns:
            PnLData object with period performance

        Raises:
            DataProviderError: If Alpaca API call fails or returns invalid data.

        """
        try:
            history = self._alpaca_manager.get_portfolio_history(period=period)
            if not history:
                logger.error(
                    "Failed to get portfolio history for period",
                    period=period,
                    correlation_id=self._correlation_id,
                    module="pnl_service",
                    method="get_period_pnl",
                )
                raise DataProviderError(
                    f"Alpaca returned empty history for period {period}",
                    context={"period": period, "correlation_id": self._correlation_id},
                )

            # Debug logging to diagnose P&L calculation issues
            timestamps = history.get("timestamp", [])
            profit_loss = history.get("profit_loss", [])
            profit_loss_pct = history.get("profit_loss_pct", [])
            logger.info(
                "Portfolio history received from Alpaca",
                period=period,
                base_value=history.get("base_value"),
                data_points=len(timestamps),
                first_timestamp=timestamps[0] if timestamps else None,
                last_timestamp=timestamps[-1] if timestamps else None,
                first_profit_loss=profit_loss[0] if profit_loss else None,
                last_profit_loss=profit_loss[-1] if profit_loss else None,
                last_profit_loss_pct=profit_loss_pct[-1] if profit_loss_pct else None,
                correlation_id=self._correlation_id,
                module="pnl_service",
                method="get_period_pnl",
            )

            return self._process_history_data(history, period)

        except DataProviderError:
            # Re-raise our typed errors
            raise
        except Exception as e:
            logger.error(
                "Error getting period P&L",
                period=period,
                error=str(e),
                error_type=type(e).__name__,
                correlation_id=self._correlation_id,
                module="pnl_service",
                method="get_period_pnl",
            )
            raise DataProviderError(
                f"Failed to retrieve P&L for period {period}: {e}",
                context={
                    "period": period,
                    "error": str(e),
                    "correlation_id": self._correlation_id,
                },
            ) from e

    def _get_period_pnl(self, period: str, start_date: str, end_date: str) -> PnLData:
        """Get P&L for a specific date range.

        Uses pnl_reset='no_reset' to get CUMULATIVE P&L values from Alpaca,
        then subtracts deposits (CSD) and adds withdrawals (CSW) to calculate
        TRUE trading P&L that excludes cash movements.

        Args:
            period: Human-readable period description
            start_date: Start date in ISO format
            end_date: End date in ISO format

        Returns:
            PnLData object with performance data

        Raises:
            DataProviderError: If Alpaca API call fails or returns invalid data.

        """
        try:
            # Use pnl_reset='no_reset' to get CUMULATIVE P&L values
            # This makes profit_loss values cumulative from base_value
            history = self._alpaca_manager.get_portfolio_history(
                start_date=start_date,
                end_date=end_date,
                timeframe="1D",
                pnl_reset="no_reset",
                intraday_reporting="market_hours",
            )

            if not history:
                logger.error(
                    "Failed to get portfolio history from start_date to end_date",
                    start_date=start_date,
                    end_date=end_date,
                    period=period,
                    correlation_id=self._correlation_id,
                    module="pnl_service",
                    method="_get_period_pnl",
                )
                raise DataProviderError(
                    f"Alpaca returned empty history for date range {start_date} to {end_date}",
                    context={
                        "period": period,
                        "start_date": start_date,
                        "end_date": end_date,
                        "correlation_id": self._correlation_id,
                    },
                )

            # Fetch non-trade activities (deposits AND withdrawals) for the period
            # CSD = Cash Deposit (money IN, inflates equity, NOT trading profit)
            # CSW = Cash Withdrawal (money OUT, reduces equity, NOT trading loss)
            cash_activities = self._alpaca_manager.get_non_trade_activities(
                start_date=start_date,
                activity_types=["CSD", "CSW"],
            )

            # Calculate total deposits and withdrawals for TRUE trading P&L
            # Deposits inflate equity but are NOT trading gains - subtract
            # Withdrawals reduce equity but are NOT trading losses - add back
            net_deposits, net_withdrawals = self._calculate_cash_movements(
                cash_activities, start_date, end_date
            )

            logger.debug(
                "Fetched cash activities for P&L adjustment",
                start_date=start_date,
                end_date=end_date,
                activity_count=len(cash_activities),
                net_deposits=float(net_deposits),
                net_withdrawals=float(net_withdrawals),
                correlation_id=self._correlation_id,
                module="pnl_service",
            )

            return self._process_history_data(
                history, period, start_date, end_date, net_deposits, net_withdrawals
            )

        except DataProviderError:
            # Re-raise our typed errors
            raise
        except Exception as e:
            logger.error(
                "Error getting P&L for period",
                period=period,
                start_date=start_date,
                end_date=end_date,
                error=str(e),
                error_type=type(e).__name__,
                correlation_id=self._correlation_id,
                module="pnl_service",
                method="_get_period_pnl",
            )
            raise DataProviderError(
                f"Failed to retrieve P&L for {period} ({start_date} to {end_date}): {e}",
                context={
                    "period": period,
                    "start_date": start_date,
                    "end_date": end_date,
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
            cash_activities: List of CSD/CSW activities from Alpaca
            start_date: Period start date (YYYY-MM-DD)
            end_date: Period end date (YYYY-MM-DD)

        Returns:
            Tuple of (total_deposits, total_withdrawals).
            - Deposits (CSD): Cash IN, inflates equity, NOT trading profit - subtract from P&L
            - Withdrawals (CSW): Cash OUT, reduces equity, NOT trading loss - add back to P&L

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

            if activity_type == "CSD":  # Cash Deposit - subtract from P&L
                total_deposits += amount
            elif activity_type == "CSW":  # Cash Withdrawal - add back to P&L
                # Withdrawals are reported as negative amounts, so we take absolute value
                total_withdrawals += abs(amount)

        return total_deposits, total_withdrawals

    def _process_history_data(
        self,
        history: dict[str, list[float] | list[int]],
        period: str,
        start_date: str | None = None,
        end_date: str | None = None,
        net_deposits: Decimal | None = None,
        net_withdrawals: Decimal | None = None,
    ) -> PnLData:
        """Process portfolio history data into P&L metrics.

        Args:
            history: Portfolio history data from Alpaca with timestamp, equity, profit_loss,
                     and profit_loss_pct arrays (CUMULATIVE when pnl_reset='no_reset')
            period: Period description
            start_date: Start date string
            end_date: End date string
            net_deposits: Total deposits (CSD) in period to subtract from P&L
            net_withdrawals: Total withdrawals (CSW) in period to add back to P&L

        Returns:
            PnLData object with calculated metrics

        Raises:
            DataProviderError: If history data is invalid or missing required fields.

        """
        try:
            # Validate and extract required fields
            timestamps = history.get("timestamp", [])
            equity_values = history.get("equity", [])
            profit_loss_values = history.get("profit_loss", [])
            profit_loss_pct_values = history.get("profit_loss_pct", [])

            # Type guard: ensure all are lists
            if not isinstance(timestamps, list) or not isinstance(equity_values, list):
                raise DataProviderError(
                    "Invalid Alpaca history structure: timestamp or equity not a list",
                    context={
                        "period": period,
                        "correlation_id": self._correlation_id,
                    },
                )

            if not timestamps or not equity_values:
                logger.warning(
                    "No data found for period",
                    period=period,
                    correlation_id=self._correlation_id,
                    module="pnl_service",
                    method="_process_history_data",
                )
                return PnLData(period=period, start_date=start_date, end_date=end_date)

            # Calculate totals using CUMULATIVE P&L values and adjusting for cash movements
            start_value, end_value, total_pnl, total_pnl_pct = self._calculate_totals(
                equity_values,
                profit_loss_values,
                profit_loss_pct_values,
                net_deposits=net_deposits or Decimal("0"),
                net_withdrawals=net_withdrawals or Decimal("0"),
            )
            daily_data = self._build_daily_data(
                timestamps, equity_values, profit_loss_values, profit_loss_pct_values
            )

            return PnLData(
                period=period,
                start_date=start_date or (daily_data[0].date if daily_data else None),
                end_date=end_date or (daily_data[-1].date if daily_data else None),
                start_value=start_value,
                end_value=end_value,
                total_pnl=total_pnl,
                total_pnl_pct=total_pnl_pct,
                daily_data=daily_data,
            )

        except DataProviderError:
            # Re-raise our typed errors
            raise
        except Exception as e:
            logger.error(
                "Error processing history data",
                error=str(e),
                error_type=type(e).__name__,
                period=period,
                correlation_id=self._correlation_id,
                module="pnl_service",
                method="_process_history_data",
            )
            raise DataProviderError(
                f"Failed to process portfolio history for {period}: {e}",
                context={
                    "period": period,
                    "error": str(e),
                    "correlation_id": self._correlation_id,
                },
            ) from e

    def _calculate_totals(
        self,
        equity_values: list[float] | list[int],
        profit_loss_values: list[float] | list[int],
        profit_loss_pct_values: list[float] | list[int],
        net_deposits: Decimal = Decimal("0"),
        net_withdrawals: Decimal = Decimal("0"),
    ) -> tuple[Decimal | None, Decimal | None, Decimal | None, Decimal | None]:
        """Extract start/end equity and total P&L from Alpaca's CUMULATIVE arrays.

        With pnl_reset='no_reset', profit_loss values are CUMULATIVE from account inception.
        To get TRUE trading P&L for just this period:
        - Calculate period change: profit_loss[-1] - profit_loss[0]
        - Subtract deposits (CSD) which inflate equity without being trading gains
        - Add back withdrawals (CSW) which reduce equity without being trading losses

        Args:
            equity_values: List of equity values from Alpaca.
            profit_loss_values: CUMULATIVE P&L values from Alpaca (with pnl_reset='no_reset').
            profit_loss_pct_values: CUMULATIVE P&L percentage values from Alpaca.
            net_deposits: Total deposits (CSD) in the period to subtract from P&L.
            net_withdrawals: Total withdrawals (CSW) in the period to add back to P&L.

        Returns:
            Tuple of (start_value, end_value, total_pnl, total_pnl_pct).

        """
        if not equity_values:
            return None, None, None, None

        # Use Money for precise value handling
        start_money = Money.from_decimal(Decimal(str(equity_values[0])), "USD")
        end_money = Money.from_decimal(Decimal(str(equity_values[-1])), "USD")

        total_pnl: Decimal | None = None
        total_pnl_pct: Decimal | None = None

        # Calculate PERIOD-SPECIFIC P&L from cumulative values
        if profit_loss_values and len(profit_loss_values) > 0:
            first_pnl = (
                Decimal(str(profit_loss_values[0])) if profit_loss_values[0] else Decimal("0")
            )
            last_pnl = (
                Decimal(str(profit_loss_values[-1])) if profit_loss_values[-1] else Decimal("0")
            )
            # Period change in cumulative P&L
            period_cumulative_change = last_pnl - first_pnl
            # TRUE trading P&L = period change - deposits + withdrawals
            # Deposits inflate equity (not trading gains), withdrawals reduce equity (not losses)
            total_pnl = period_cumulative_change - net_deposits + net_withdrawals

        # Calculate percentage from TRUE P&L relative to starting equity
        if total_pnl is not None and start_money.to_decimal() > Decimal("0"):
            total_pnl_pct = (total_pnl / start_money.to_decimal()) * PERCENTAGE_MULTIPLIER

        return start_money.to_decimal(), end_money.to_decimal(), total_pnl, total_pnl_pct

    def _build_daily_data(
        self,
        timestamps: list[int] | list[float],
        equity_values: list[float] | list[int],
        profit_loss_values: list[float] | list[int],
        profit_loss_pct_values: list[float] | list[int],
    ) -> list[DailyPnLEntry]:
        """Convert raw history arrays into per-day entries.

        Notes:
        - With pnl_reset='no_reset', Alpaca's profit_loss values are CUMULATIVE.
        - profit_loss[i] = cumulative P&L from base_value up to day i.
        - To get daily P&L: profit_loss[i] - profit_loss[i-1].
        - First day uses the cumulative P&L value directly (trading activity on day 1).

        Args:
            timestamps: Unix timestamps (seconds since epoch).
            equity_values: Daily equity values.
            profit_loss_values: CUMULATIVE P&L values from Alpaca.
            profit_loss_pct_values: CUMULATIVE P&L percentage values from Alpaca.

        Returns:
            List of DailyPnLEntry objects with computed daily P&L.

        """
        daily: list[DailyPnLEntry] = []
        n = min(len(timestamps), len(equity_values))
        if n == 0:
            return daily

        for i in range(n):
            ts = timestamps[i]
            curr_equity = Decimal(str(equity_values[i]))
            date_str = datetime.fromtimestamp(ts, tz=UTC).date().isoformat()

            # Get current cumulative P&L
            curr_cumulative = (
                Decimal(str(profit_loss_values[i]))
                if (i < len(profit_loss_values) and profit_loss_values[i] is not None)
                else Decimal("0")
            )

            if i == 0:
                # First day: use the first cumulative value as-is
                # This represents actual trading P&L on day 1 of the period
                daily_pnl = curr_cumulative
                # Calculate percentage from first day P&L relative to starting equity
                if curr_equity > Decimal("0"):
                    # Use equity minus P&L as the base (what we started with)
                    base_equity = curr_equity - daily_pnl
                    if base_equity > Decimal("0"):
                        daily_pct = (daily_pnl / base_equity) * PERCENTAGE_MULTIPLIER
                    else:
                        daily_pct = Decimal("0")
                else:
                    daily_pct = Decimal("0")
            else:
                # Subsequent days: compute difference from previous day
                prev_cumulative = (
                    Decimal(str(profit_loss_values[i - 1]))
                    if ((i - 1) < len(profit_loss_values) and profit_loss_values[i - 1] is not None)
                    else Decimal("0")
                )
                daily_pnl = curr_cumulative - prev_cumulative

                # Calculate daily percentage from daily P&L and previous day's equity
                prev_equity = (
                    Decimal(str(equity_values[i - 1])) if equity_values[i - 1] else Decimal("1")
                )
                if prev_equity > Decimal("0"):
                    daily_pct = (daily_pnl / prev_equity) * PERCENTAGE_MULTIPLIER
                else:
                    daily_pct = Decimal("0")

            entry = DailyPnLEntry(
                date=date_str,
                equity=curr_equity,
                profit_loss=daily_pnl,
                profit_loss_pct=daily_pct,
            )
            daily.append(entry)

        return daily

    def format_pnl_report(self, pnl_data: PnLData, *, detailed: bool = False) -> str:
        """Format P&L data into a readable report.

        Args:
            pnl_data: P&L data to format
            detailed: Whether to include daily breakdown

        Returns:
            Formatted report string

        """
        lines = self._build_report_header(pnl_data)

        if detailed and pnl_data.daily_data:
            lines.extend(self._format_daily_breakdown(pnl_data.daily_data))

        return "\n".join(lines)

    def _build_report_header(self, pnl_data: PnLData) -> list[str]:
        """Build the header section for the P&L report."""
        lines: list[str] = []
        lines.append(f"📊 Portfolio P&L Report - {pnl_data.period.title()}")
        lines.append("=" * 50)
        if pnl_data.start_date and pnl_data.end_date:
            lines.append(f"Period: {pnl_data.start_date} to {pnl_data.end_date}")
        if pnl_data.start_value is not None:
            lines.append(f"Starting Value: ${pnl_data.start_value:,.2f}")
        if pnl_data.end_value is not None:
            lines.append(f"Ending Value: ${pnl_data.end_value:,.2f}")
        if pnl_data.total_pnl is not None:
            pnl_sign = "📈" if pnl_data.total_pnl >= 0 else "📉"
            lines.append(f"Total P&L: {pnl_sign} ${pnl_data.total_pnl:+,.2f}")
        if pnl_data.total_pnl_pct is not None:
            lines.append(f"Total P&L %: {pnl_data.total_pnl_pct:+.2f}%")
        return lines

    def _format_daily_breakdown(self, daily_data: list[DailyPnLEntry]) -> list[str]:
        """Format the daily breakdown lines for the report.

        Args:
            daily_data: List of daily P&L entries.

        Returns:
            List of formatted string lines for the report.

        """
        lines: list[str] = []
        lines.append("\nDaily Breakdown:")
        lines.append("-" * 30)
        for day_data in daily_data:
            pnl_str = f"${day_data.profit_loss:+.2f}"
            pnl_pct_str = f"({day_data.profit_loss_pct:+.2f}%)"
            lines.append(f"{day_data.date}: ${day_data.equity:,.2f} | P&L: {pnl_str} {pnl_pct_str}")
        return lines
