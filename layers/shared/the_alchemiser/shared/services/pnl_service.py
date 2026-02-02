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
from typing import Any

import requests

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
# Deposit-adjustment algorithm constants
DEPOSIT_LOOKBACK_DAYS: int = 3  # Check deposit day and up to 3 prior days
DEPOSIT_TOLERANCE: float = 0.15  # 15% tolerance for matching deposits to inflated P&L
ALPACA_LIVE_API_URL: str = "https://api.alpaca.markets/v2/account/portfolio/history"


class PnLService:
    """Service for P&L analysis and reporting.

    This service provides a unified interface for P&L data using the Alpaca API.
    """

    def __init__(
        self,
        alpaca_manager: AlpacaManager | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Initialize P&L service.

        Args:
            alpaca_manager: Alpaca manager instance. If None, creates one from config.
            correlation_id: Optional correlation ID for observability tracing.

        Raises:
            ConfigurationError: If Alpaca API keys are not found in configuration.

        """
        self._correlation_id = correlation_id or ""

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

    @staticmethod
    def _is_paper_from_endpoint(ep: str | None) -> bool:
        """Determine if endpoint is for paper trading.

        Args:
            ep: Endpoint URL string or None.

        Returns:
            True if endpoint is for paper trading, False for live trading.
            Defaults to True (paper) for safety if endpoint is unknown.

        """
        if not ep:
            return True

        ep_lower = ep.lower()

        # Check for known Alpaca production endpoint
        if "api.alpaca.markets" in ep_lower and "paper" not in ep_lower:
            return False

        # Check for known Alpaca paper endpoint
        if "paper-api.alpaca.markets" in ep_lower:
            return True

        # Default to paper trading for safety (unknown endpoints)
        return True

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

        Args:
            n_months: Number of months to fetch (must be positive; default 3, including current month)

        Returns:
            List of PnLData objects, oldest first (e.g., [Nov, Dec, Jan MTD]).

        Raises:
            ValueError: If n_months is not a positive integer.

        """
        if n_months <= 0:
            raise ValueError(f"n_months must be a positive integer; got {n_months}")

        return self._get_last_n_months_from_alpaca(n_months)

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

    # ========================================================================
    # DEPOSIT-ADJUSTED P&L METHODS
    # ========================================================================
    # These methods provide true trading P&L by detecting and subtracting
    # deposits that inflate Alpaca's raw profit_loss values on settlement days.

    def get_all_daily_records(
        self, period: str = "1A"
    ) -> tuple[list[DailyPnLEntry], dict[str, Decimal]]:
        """Get all daily P&L records with deposit adjustments.

        Uses the cashflow_types API parameter to get deposits/withdrawals aligned
        with timestamps, then applies a tolerance-matching algorithm to subtract
        deposit amounts from inflated P&L days.

        Args:
            period: Alpaca period string (1W, 1M, 3M, 1A). Default is 1A (1 year).

        Returns:
            Tuple of (daily_records, deposits_by_date):
            - daily_records: List of DailyPnLEntry with deposit-adjusted profit_loss
            - deposits_by_date: Dict mapping date strings to deposit amounts

        Raises:
            ConfigurationError: If API keys are not configured.
            DataProviderError: If Alpaca API call fails.

        """
        api_key, secret_key, _ = get_alpaca_keys()
        if not api_key or not secret_key:
            raise ConfigurationError(
                "Alpaca API keys not found in configuration",
                config_key="ALPACA_KEY/ALPACA_SECRET",
            )

        data = self._fetch_portfolio_history_with_cashflow(api_key, secret_key, period)
        return self._build_deposit_adjusted_records(data)

    def _fetch_portfolio_history_with_cashflow(
        self, api_key: str, secret_key: str, period: str = "1A"
    ) -> dict[str, Any]:
        """Fetch portfolio history WITH cashflow data in a single API call.

        Uses the cashflow_types parameter to get deposits (CSD) and withdrawals (CSW)
        aligned with the timestamp array.

        Args:
            api_key: Alpaca API key.
            secret_key: Alpaca secret key.
            period: Period string (1W, 1M, 3M, 1A).

        Returns:
            Dictionary with timestamp, equity, profit_loss, profit_loss_pct,
            base_value, and cashflow arrays.

        Raises:
            DataProviderError: If API call fails.

        """
        headers = {
            "APCA-API-KEY-ID": api_key,
            "APCA-API-SECRET-KEY": secret_key,
            "accept": "application/json",
        }
        params = {
            "period": period,
            "timeframe": "1D",
            "intraday_reporting": "market_hours",
            "pnl_reset": "per_day",
            "cashflow_types": "CSD,CSW",  # Include deposits and withdrawals
        }

        try:
            resp = requests.get(
                ALPACA_LIVE_API_URL, headers=headers, params=params, timeout=30
            )
            resp.raise_for_status()
            result: dict[str, Any] = resp.json()
            return result
        except requests.RequestException as e:
            logger.error(
                "Failed to fetch portfolio history with cashflow",
                error=str(e),
                period=period,
                correlation_id=self._correlation_id,
                module="pnl_service",
            )
            raise DataProviderError(
                f"Failed to fetch Alpaca portfolio history: {e}",
                context={"period": period, "correlation_id": self._correlation_id},
            ) from e

    def _build_deposit_adjusted_records(
        self, data: dict[str, Any]
    ) -> tuple[list[DailyPnLEntry], dict[str, Decimal]]:
        """Build daily records with deposit-adjusted P&L from unified API response.

        Key insight: Alpaca's profit_loss field gets inflated on the day a deposit
        settles. The inflated P&L appears on the day the deposit settles (typically
        the next trading day after the deposit is made, or Monday for weekend deposits).

        Algorithm:
        1. Build raw records from Alpaca data
        2. For each deposit, scan that day and prior few days to find the inflated P&L
        3. Match using 15% tolerance: find a P&L that's within 15% of the deposit amount
        4. Subtract the deposit from the matched day's raw P&L

        Args:
            data: Raw API response with timestamp, equity, profit_loss, and cashflow.

        Returns:
            Tuple of (daily_records, deposits_by_date).

        """
        timestamps = data.get("timestamp", [])
        equities = data.get("equity", [])
        profit_losses = data.get("profit_loss", [])
        cashflow = data.get("cashflow", {})

        # Extract cashflow arrays (aligned with timestamps, default to zeros)
        csd_values = cashflow.get("CSD", [0] * len(timestamps))
        csw_values = cashflow.get("CSW", [0] * len(timestamps))

        # Pad arrays if shorter than timestamps
        while len(csd_values) < len(timestamps):
            csd_values.append(0)
        while len(csw_values) < len(timestamps):
            csw_values.append(0)

        # Build list of all trading dates
        all_dates = [self._format_timestamp(ts) for ts in timestamps]

        # Build deposits_by_index from cashflow array
        deposits_by_index: dict[int, Decimal] = {}
        for i, _ in enumerate(all_dates):
            if csd_values[i] != 0:
                deposits_by_index[i] = Decimal(str(csd_values[i]))

        # Build raw P&L values indexed
        raw_pnl_values = [Decimal(str(pl)) for pl in profit_losses]

        # Track which deposit was matched to which day's adjustment
        deposit_adjustments: dict[int, Decimal] = {}

        # For each deposit, find the day with inflated P&L
        for deposit_idx, deposit_amount in deposits_by_index.items():
            best_match_idx = None
            best_match_diff = float("inf")

            # Check the deposit day and prior days
            for offset in range(DEPOSIT_LOOKBACK_DAYS + 1):
                check_idx = deposit_idx - offset
                if check_idx < 0:
                    break

                raw_pnl = raw_pnl_values[check_idx]

                # Check if this P&L is close to the deposit amount (within tolerance)
                diff = abs(float(raw_pnl) - float(deposit_amount))
                relative_diff = (
                    diff / float(deposit_amount) if deposit_amount != 0 else float("inf")
                )

                if relative_diff <= DEPOSIT_TOLERANCE and diff < best_match_diff:
                    best_match_idx = check_idx
                    best_match_diff = diff

            if best_match_idx is not None:
                # Found a match - record the adjustment for that day
                if best_match_idx in deposit_adjustments:
                    deposit_adjustments[best_match_idx] += deposit_amount
                else:
                    deposit_adjustments[best_match_idx] = deposit_amount

        # Build final records
        records: list[DailyPnLEntry] = []
        deposits_by_date: dict[str, Decimal] = {}

        for i, ts in enumerate(timestamps):
            date_str = self._format_timestamp(ts)
            equity = Decimal(str(equities[i]))
            raw_pnl = raw_pnl_values[i]
            withdrawal_today = (
                abs(Decimal(str(csw_values[i]))) if csw_values[i] else Decimal("0")
            )

            # Get deposit that was recorded on this day (for display)
            deposit_on_this_day = (
                Decimal(str(csd_values[i])) if csd_values[i] != 0 else Decimal("0")
            )
            if deposit_on_this_day != 0:
                deposits_by_date[date_str] = deposit_on_this_day

            # Adjust P&L if this day was matched to a deposit
            adjustment = deposit_adjustments.get(i, Decimal("0"))
            adjusted_pnl = raw_pnl - adjustment

            # Calculate percentage based on start-of-day equity
            start_equity = equity - adjusted_pnl
            pnl_pct = (
                (adjusted_pnl / start_equity * PERCENTAGE_MULTIPLIER)
                if start_equity != 0
                else Decimal("0")
            )

            records.append(
                DailyPnLEntry(
                    date=date_str,
                    equity=equity,
                    profit_loss=adjusted_pnl,
                    profit_loss_pct=pnl_pct,
                    deposit=deposit_on_this_day if deposit_on_this_day != 0 else None,
                    withdrawal=withdrawal_today if withdrawal_today != 0 else None,
                )
            )

        return records, deposits_by_date

    @staticmethod
    def _format_timestamp(ts: int) -> str:
        """Convert Unix timestamp to YYYY-MM-DD."""
        return datetime.fromtimestamp(ts, tz=UTC).strftime("%Y-%m-%d")

    @staticmethod
    def aggregate_by_month(
        daily_records: list[DailyPnLEntry],
    ) -> dict[str, dict[str, Decimal]]:
        """Aggregate daily records by month for summary tables.

        Args:
            daily_records: List of daily P&L entries.

        Returns:
            Dict mapping month keys (YYYY-MM) to aggregated data:
            - total_pnl: Sum of adjusted P&L for the month
            - end_equity: Last day's equity
            - total_deposits: Sum of deposits in the month

        """
        months: dict[str, dict[str, Decimal]] = {}

        for rec in daily_records:
            # Skip days with zero equity (inactive)
            if rec.equity <= 0:
                continue

            month_key = rec.date[:7]  # YYYY-MM

            if month_key not in months:
                months[month_key] = {
                    "total_pnl": Decimal("0"),
                    "end_equity": Decimal("0"),
                    "total_deposits": Decimal("0"),
                }

            months[month_key]["total_pnl"] += rec.profit_loss
            months[month_key]["end_equity"] = rec.equity
            months[month_key]["total_deposits"] += rec.deposit or Decimal("0")

        return months
