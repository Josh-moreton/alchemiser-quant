#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

P&L Analysis Service for The Alchemiser Trading System.

This service provides portfolio profit and loss analysis using the Alpaca API,
supporting weekly and monthly performance reports.
"""

from __future__ import annotations

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
    """Service for P&L analysis and reporting."""

    def __init__(
        self, alpaca_manager: AlpacaManager | None = None, correlation_id: str | None = None
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

        """
        import calendar

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
            n_months: Number of months to fetch (default 3, including current month)

        Returns:
            List of PnLData objects, oldest first (e.g., [Nov, Dec, Jan MTD]).

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
                is_current = (target_year == today.year and target_month == today.month)
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
            history = self._alpaca_manager.get_portfolio_history(
                start_date=start_date, end_date=end_date, timeframe="1D"
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

            return self._process_history_data(history, period, start_date, end_date)

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

    def _process_history_data(
        self,
        history: dict[str, list[float] | list[int]],
        period: str,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> PnLData:
        """Process portfolio history data into P&L metrics.

        Args:
            history: Portfolio history data from Alpaca with timestamp, equity, profit_loss,
                     and profit_loss_pct arrays
            period: Period description
            start_date: Start date string
            end_date: End date string

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

            # Use Alpaca's provided P&L values directly
            start_value, end_value, total_pnl, total_pnl_pct = self._calculate_totals(
                equity_values, profit_loss_values, profit_loss_pct_values
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
    ) -> tuple[Decimal | None, Decimal | None, Decimal | None, Decimal | None]:
        """Extract start/end equity and total P&L from Alpaca's provided arrays.

        Per Alpaca API documentation (pnl_reset option):
        - For 1D resolution, profit_loss values are DAILY changes (not cumulative)
        - profit_loss[0] includes gains from account inception to start of period
        - To get period P&L: sum(profit_loss[1:]) - skip first day's inherited gains

        Args:
            equity_values: List of equity values from Alpaca (floats or ints).
            profit_loss_values: List of daily P&L values from Alpaca.
            profit_loss_pct_values: List of daily P&L percentage values from Alpaca.

        Returns:
            Tuple of (start_value, end_value, total_pnl, total_pnl_pct).

        """
        if not equity_values:
            return None, None, None, None

        # Use Money for precise value handling
        start_money = Money.from_decimal(Decimal(str(equity_values[0])), "USD")
        end_money = Money.from_decimal(Decimal(str(equity_values[-1])), "USD")

        # Calculate period P&L from daily values
        # profit_loss[0] contains gains from account inception to period start (exclude it)
        # profit_loss[1:] contains actual daily P&L during the period
        total_pnl: Decimal | None = None
        total_pnl_pct: Decimal | None = None

        if profit_loss_values and len(profit_loss_values) > 1:
            # Sum daily P&L values, skipping first day (has prior-period gains)
            period_pnl = sum(
                Decimal(str(pnl)) for pnl in profit_loss_values[1:] if pnl is not None
            )
            total_pnl = period_pnl
        elif profit_loss_values and len(profit_loss_values) == 1:
            # Only one data point - use it (though it includes prior gains)
            total_pnl = Decimal(str(profit_loss_values[0])) if profit_loss_values[0] else None

        if profit_loss_pct_values and len(profit_loss_pct_values) > 1:
            # Sum daily percentage changes, skipping first day
            # Alpaca returns as decimal (e.g., 0.05 for 5%)
            period_pct = sum(
                Decimal(str(pct)) for pct in profit_loss_pct_values[1:] if pct is not None
            )
            total_pnl_pct = period_pct * PERCENTAGE_MULTIPLIER
        elif profit_loss_pct_values and len(profit_loss_pct_values) == 1:
            pct = profit_loss_pct_values[0]
            total_pnl_pct = Decimal(str(pct)) * PERCENTAGE_MULTIPLIER if pct else None

        return start_money.to_decimal(), end_money.to_decimal(), total_pnl, total_pnl_pct

    def _build_daily_data(
        self,
        timestamps: list[int] | list[float],
        equity_values: list[float] | list[int],
        profit_loss_values: list[float] | list[int],
        profit_loss_pct_values: list[float] | list[int],
    ) -> list[DailyPnLEntry]:
        """Convert raw history arrays into per-day entries using Alpaca's P&L data.

        Notes:
        - Alpaca's profit_loss and profit_loss_pct values are DAILY changes.
        - profit_loss[0] includes gains from account inception (prior to period).
        - We use the raw daily values directly for display.

        Args:
            timestamps: Unix timestamps (seconds since epoch).
            equity_values: Daily equity values.
            profit_loss_values: Daily P&L values from Alpaca.
            profit_loss_pct_values: Daily P&L percentage values from Alpaca.

        Returns:
            List of DailyPnLEntry objects.

        """
        daily: list[DailyPnLEntry] = []
        n = min(len(timestamps), len(equity_values))
        if n == 0:
            return daily

        for i in range(n):
            ts = timestamps[i]
            curr_equity = Decimal(str(equity_values[i]))
            date_str = datetime.fromtimestamp(ts, tz=UTC).date().isoformat()

            # Get daily P&L directly from Alpaca (already daily values)
            if i < len(profit_loss_values) and profit_loss_values[i] is not None:
                daily_pnl = Decimal(str(profit_loss_values[i]))
            else:
                daily_pnl = Decimal("0")

            # Get daily percentage directly from Alpaca (already daily values)
            # Alpaca returns as decimal (e.g., 0.05 for 5%), convert to percentage
            if i < len(profit_loss_pct_values) and profit_loss_pct_values[i] is not None:
                daily_pct = Decimal(str(profit_loss_pct_values[i])) * PERCENTAGE_MULTIPLIER
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
