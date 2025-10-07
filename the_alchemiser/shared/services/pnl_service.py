#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

P&L Analysis Service for The Alchemiser Trading System.

This service provides portfolio profit and loss analysis using the Alpaca API,
supporting weekly and monthly performance reports.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from the_alchemiser.shared.brokers.alpaca_manager import (
    AlpacaManager,
    create_alpaca_manager,
)
from the_alchemiser.shared.config.secrets_adapter import get_alpaca_keys
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.pnl import PnLData
from the_alchemiser.shared.types.money import Money

logger = get_logger(__name__)

# Constants
PERCENTAGE_MULTIPLIER = Decimal("100")


## Schema moved to shared/schemas/pnl.py per typing policy


class PnLService:
    """Service for P&L analysis and reporting."""

    def __init__(self, alpaca_manager: AlpacaManager | None = None) -> None:
        """Initialize P&L service.

        Args:
            alpaca_manager: Alpaca manager instance. If None, creates one from config.

        """
        if alpaca_manager is None:
            api_key, secret_key, endpoint = get_alpaca_keys()
            if not api_key or not secret_key:
                raise ValueError("Alpaca API keys not found in configuration")

            # Determine if this is paper trading based on endpoint (normalize variants)
            def _is_paper_from_endpoint(ep: str | None) -> bool:
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

            paper = _is_paper_from_endpoint(endpoint)

            self._alpaca_manager = create_alpaca_manager(
                api_key=api_key, secret_key=secret_key, paper=paper
            )
        else:
            self._alpaca_manager = alpaca_manager

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

    def get_period_pnl(self, period: str) -> PnLData:
        """Get P&L using Alpaca period strings.

        Args:
            period: Alpaca period string (e.g., '1W', '1M', '3M', '1A')

        Returns:
            PnLData object with period performance

        """
        try:
            history = self._alpaca_manager.get_portfolio_history(period=period)
            if not history:
                logger.error("Failed to get portfolio history for period", period=period)
                return PnLData(period=period, start_date="", end_date="")

            return self._process_history_data(history, period)

        except Exception as e:
            logger.error("Error getting period P&L for", period=period, error=str(e))
            return PnLData(period=period, start_date="", end_date="")

    def _get_period_pnl(self, period: str, start_date: str, end_date: str) -> PnLData:
        """Get P&L for a specific date range.

        Args:
            period: Human-readable period description
            start_date: Start date in ISO format
            end_date: End date in ISO format

        Returns:
            PnLData object with performance data

        """
        try:
            history = self._alpaca_manager.get_portfolio_history(
                start_date=start_date, end_date=end_date, timeframe="1D"
            )

            if not history:
                logger.error(
                    "Failed to get portfolio history for to",
                    start_date=start_date,
                    end_date=end_date,
                )
                return PnLData(period=period, start_date=start_date, end_date=end_date)

            return self._process_history_data(history, period, start_date, end_date)

        except Exception as e:
            logger.error("Error getting P&L for", period=period, error=str(e))
            return PnLData(period=period, start_date=start_date, end_date=end_date)

    def _process_history_data(
        self,
        history: dict[str, Any],
        period: str,
        start_date: str = "",
        end_date: str = "",
    ) -> PnLData:
        """Process portfolio history data into P&L metrics.

        Args:
            history: Portfolio history data from Alpaca
            period: Period description
            start_date: Start date string
            end_date: End date string

        Returns:
            PnLData object with calculated metrics

        """
        try:
            timestamps = history.get("timestamp", [])
            equity_values = history.get("equity", [])
            profit_loss = history.get("profit_loss", [])
            profit_loss_pct = history.get("profit_loss_pct", [])

            if not timestamps or not equity_values:
                logger.warning("No data found for period", period=period)
                return PnLData(period=period, start_date=start_date, end_date=end_date)

            start_value, end_value, total_pnl, total_pnl_pct = self._calculate_totals(equity_values)
            daily_data = self._build_daily_data(
                timestamps, equity_values, profit_loss, profit_loss_pct
            )

            return PnLData(
                period=period,
                start_date=start_date or (daily_data[0]["date"] if daily_data else ""),
                end_date=end_date or (daily_data[-1]["date"] if daily_data else ""),
                start_value=start_value,
                end_value=end_value,
                total_pnl=total_pnl,
                total_pnl_pct=total_pnl_pct,
                daily_data=daily_data,
            )

        except Exception as e:
            logger.error("Error processing history data", error=str(e))
            return PnLData(period=period, start_date=start_date, end_date=end_date)

    def _calculate_totals(
        self, equity_values: list[Any]
    ) -> tuple[Decimal | None, Decimal | None, Decimal | None, Decimal | None]:
        """Calculate start/end values and total P&L metrics from equity series.

        Returns:
            Tuple of (start_value, end_value, total_pnl, total_pnl_pct).

        """
        if not equity_values:
            return None, None, None, None

        # Use Money for precise P&L calculations
        start_money = Money.from_decimal(Decimal(str(equity_values[0])), "USD")
        end_money = Money.from_decimal(Decimal(str(equity_values[-1])), "USD")

        total_pnl: Decimal | None = None
        total_pnl_pct: Decimal | None = None

        # Calculate total P&L using Money for currency-aware arithmetic
        if end_money >= start_money:
            total_pnl_money = end_money.subtract(start_money)
            total_pnl = total_pnl_money.to_decimal()
        else:
            # When end < start (loss), compute as -(start - end)
            total_pnl_money = start_money.subtract(end_money)
            total_pnl = -total_pnl_money.to_decimal()

        # Calculate percentage with Money precision
        if not start_money.is_zero():
            total_pnl_pct = (total_pnl / start_money.to_decimal()) * PERCENTAGE_MULTIPLIER

        return start_money.to_decimal(), end_money.to_decimal(), total_pnl, total_pnl_pct

    def _build_daily_data(
        self,
        timestamps: list[Any],
        equity_values: list[Any],
        profit_loss: list[Any],
        profit_loss_pct: list[Any],
    ) -> list[dict[str, Any]]:
        """Convert raw history arrays into per-day dictionaries.

        Notes:
        - Compute DAILY changes directly from the equity series to avoid ambiguity,
          as some providers return profit_loss/profit_loss_pct cumulative to base value.
        - Daily P&L = equity[i] - equity[i-1] (0 for first day)
        - Daily %   = (Daily P&L / equity[i-1]) * 100 (0 for first day or if prior is 0)
        - Keep keys as 'profit_loss' and 'profit_loss_pct' for backward-compatible formatting.
        - Uses Money for precise daily P&L calculations.

        """
        daily: list[dict[str, Any]] = []
        eq_len = len(equity_values)
        ts_len = len(timestamps)
        n = min(eq_len, ts_len)
        if n == 0:
            return daily

        prev_money: Money | None = None
        for i in range(n):
            ts = timestamps[i]
            curr_money = Money.from_decimal(Decimal(str(equity_values[i])), "USD")
            date_str = datetime.fromtimestamp(ts, tz=UTC).date().isoformat()

            if prev_money is None:
                daily_pnl = Decimal("0")
                daily_pct = Decimal("0")
            else:
                # Use Money for precise daily P&L calculation
                if curr_money >= prev_money:
                    daily_pnl_money = curr_money.subtract(prev_money)
                    daily_pnl = daily_pnl_money.to_decimal()
                else:
                    # Loss: compute as -(prev - curr)
                    daily_pnl_money = prev_money.subtract(curr_money)
                    daily_pnl = -daily_pnl_money.to_decimal()

                if not prev_money.is_zero():
                    daily_pct = (daily_pnl / prev_money.to_decimal()) * PERCENTAGE_MULTIPLIER
                else:
                    daily_pct = Decimal("0")

            entry: dict[str, Any] = {
                "date": date_str,
                "equity": curr_money.to_decimal(),
                "profit_loss": daily_pnl,
                "profit_loss_pct": daily_pct,
            }
            daily.append(entry)
            prev_money = curr_money

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

    def _format_daily_breakdown(self, daily_data: list[dict[str, Any]]) -> list[str]:
        """Format the daily breakdown lines for the report."""
        lines: list[str] = []
        lines.append("\nDaily Breakdown:")
        lines.append("-" * 30)
        for day_data in daily_data:
            date_str = day_data["date"]
            equity = day_data["equity"]
            pnl = day_data.get("profit_loss")
            pnl_pct = day_data.get("profit_loss_pct")
            pnl_str = f"${pnl:+.2f}" if pnl is not None else "N/A"
            pnl_pct_str = f"({pnl_pct:+.2f}%)" if pnl_pct is not None else ""
            lines.append(f"{date_str}: ${equity:,.2f} | P&L: {pnl_str} {pnl_pct_str}")
        return lines
