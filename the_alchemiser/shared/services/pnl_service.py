#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

P&L Analysis Service for The Alchemiser Trading System.

This service provides portfolio profit and loss analysis using the Alpaca API,
supporting weekly and monthly performance reports.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
from the_alchemiser.shared.config.config import load_settings

logger = logging.getLogger(__name__)


class PnLData:
    """Container for P&L analysis data."""
    
    def __init__(
        self,
        period: str,
        start_date: str,
        end_date: str,
        start_value: Decimal | None = None,
        end_value: Decimal | None = None,
        total_pnl: Decimal | None = None,
        total_pnl_pct: Decimal | None = None,
        daily_data: list[dict[str, Any]] | None = None,
    ) -> None:
        self.period = period
        self.start_date = start_date
        self.end_date = end_date
        self.start_value = start_value
        self.end_value = end_value
        self.total_pnl = total_pnl
        self.total_pnl_pct = total_pnl_pct
        self.daily_data = daily_data or []


class PnLService:
    """Service for P&L analysis and reporting."""

    def __init__(self, alpaca_manager: AlpacaManager | None = None) -> None:
        """Initialize P&L service.
        
        Args:
            alpaca_manager: Alpaca manager instance. If None, creates one from config.
        """
        if alpaca_manager is None:
            from the_alchemiser.shared.brokers.alpaca_manager import create_alpaca_manager
            from the_alchemiser.shared.config.secrets_adapter import get_alpaca_keys
            
            api_key, secret_key, endpoint = get_alpaca_keys()
            if not api_key or not secret_key:
                raise ValueError("Alpaca API keys not found in configuration")
            
            # Determine if this is paper trading based on endpoint
            paper = endpoint != "https://api.alpaca.markets" if endpoint else True
            
            self._alpaca_manager = create_alpaca_manager(
                api_key=api_key,
                secret_key=secret_key,
                paper=paper
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
        today = datetime.now().date()
        end_date = today - timedelta(days=(today.weekday() + 1) % 7)  # Last Sunday
        start_date = end_date - timedelta(days=7 * weeks_back - 1)
        
        return self._get_period_pnl(
            period=f"{weeks_back} week{'s' if weeks_back > 1 else ''}",
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat()
        )

    def get_monthly_pnl(self, months_back: int = 1) -> PnLData:
        """Get P&L for the past N months.
        
        Args:
            months_back: Number of months back to analyze (default: 1 = last month)
            
        Returns:
            PnLData object with monthly performance
        """
        # Calculate date range for the specified month
        today = datetime.now().date()
        
        # Go back to start of N months ago
        year = today.year
        month = today.month - months_back
        if month <= 0:
            month += 12
            year -= 1
            
        start_date = datetime(year, month, 1).date()
        
        # End date is last day of that month
        if month == 12:
            end_year = year + 1
            end_month = 1
        else:
            end_year = year
            end_month = month + 1
        end_date = (datetime(end_year, end_month, 1) - timedelta(days=1)).date()
        
        return self._get_period_pnl(
            period=f"{months_back} month{'s' if months_back > 1 else ''}",
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat()
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
                logger.error(f"Failed to get portfolio history for period {period}")
                return PnLData(period=period, start_date="", end_date="")

            return self._process_history_data(history, period)
            
        except Exception as e:
            logger.error(f"Error getting period P&L for {period}: {e}")
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
                start_date=start_date,
                end_date=end_date,
                timeframe="1Day"
            )
            
            if not history:
                logger.error(f"Failed to get portfolio history for {start_date} to {end_date}")
                return PnLData(period=period, start_date=start_date, end_date=end_date)

            return self._process_history_data(history, period, start_date, end_date)
            
        except Exception as e:
            logger.error(f"Error getting P&L for {period}: {e}")
            return PnLData(period=period, start_date=start_date, end_date=end_date)

    def _process_history_data(
        self, 
        history: dict[str, Any], 
        period: str,
        start_date: str = "",
        end_date: str = ""
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
                logger.warning(f"No data found for period {period}")
                return PnLData(period=period, start_date=start_date, end_date=end_date)

            # Calculate metrics
            start_value = Decimal(str(equity_values[0])) if equity_values else None
            end_value = Decimal(str(equity_values[-1])) if equity_values else None
            
            total_pnl = None
            total_pnl_pct = None
            
            if start_value and end_value:
                total_pnl = end_value - start_value
                if start_value > 0:
                    total_pnl_pct = (total_pnl / start_value) * Decimal('100')

            # Build daily data
            daily_data = []
            for i, timestamp in enumerate(timestamps):
                if i < len(equity_values):
                    daily_data.append({
                        "date": datetime.fromtimestamp(timestamp).date().isoformat(),
                        "equity": Decimal(str(equity_values[i])),
                        "profit_loss": Decimal(str(profit_loss[i])) if i < len(profit_loss) else None,
                        "profit_loss_pct": Decimal(str(profit_loss_pct[i])) if i < len(profit_loss_pct) else None,
                    })

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
            logger.error(f"Error processing history data: {e}")
            return PnLData(period=period, start_date=start_date, end_date=end_date)

    def format_pnl_report(self, pnl_data: PnLData, detailed: bool = False) -> str:
        """Format P&L data into a readable report.
        
        Args:
            pnl_data: P&L data to format
            detailed: Whether to include daily breakdown
            
        Returns:
            Formatted report string
        """
        lines = []
        lines.append(f"📊 Portfolio P&L Report - {pnl_data.period.title()}")
        lines.append("=" * 50)
        
        if pnl_data.start_date and pnl_data.end_date:
            lines.append(f"Period: {pnl_data.start_date} to {pnl_data.end_date}")
        
        if pnl_data.start_value is not None:
            lines.append(f"Starting Value: ${pnl_data.start_value:,.2f}")
        
        if pnl_data.end_value is not None:
            lines.append(f"Ending Value: ${pnl_data.end_value:,.2f}")
        
        if pnl_data.total_pnl is not None:
            pnl_sign = "📈" if pnl_data.total_pnl is not None and pnl_data.total_pnl >= 0 else "📉"
            lines.append(f"Total P&L: {pnl_sign} ${pnl_data.total_pnl:+,.2f}")
        
        if pnl_data.total_pnl_pct is not None:
            lines.append(f"Total P&L %: {pnl_data.total_pnl_pct:+.2f}%")
        
        if detailed and pnl_data.daily_data:
            lines.append("\nDaily Breakdown:")
            lines.append("-" * 30)
            for day_data in pnl_data.daily_data:
                date_str = day_data["date"]
                equity = day_data["equity"]
                pnl = day_data.get("profit_loss")
                pnl_pct = day_data.get("profit_loss_pct")
                
                pnl_str = f"${pnl:+.2f}" if pnl is not None else "N/A"
                pnl_pct_str = f"({pnl_pct:+.2f}%)" if pnl_pct is not None else ""
                
                lines.append(f"{date_str}: ${equity:,.2f} | P&L: {pnl_str} {pnl_pct_str}")
        
        return "\n".join(lines)