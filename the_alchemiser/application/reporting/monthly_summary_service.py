#!/usr/bin/env python3
"""
Monthly Summary Service

This module provides functionality to generate comprehensive monthly trading summaries,
including P&L analysis, fee calculations, and performance metrics for email reporting.
"""

import logging
from datetime import datetime, timedelta
from typing import Any

from the_alchemiser.application.tracking.strategy_order_tracker import get_strategy_tracker
from the_alchemiser.services.errors.exceptions import DataProviderError
from the_alchemiser.services.repository.alpaca_manager import AlpacaManager

logger = logging.getLogger(__name__)


class MonthlySummaryService:
    """Service for generating monthly trading and performance summaries."""

    def __init__(self, api_key: str, secret_key: str, paper: bool = True):
        """
        Initialize the monthly summary service.

        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key
            paper: Whether using paper trading (default: True)
        """
        self.alpaca_manager = AlpacaManager(api_key, secret_key, paper)
        self.paper_trading = paper
        self.logger = logging.getLogger(__name__)

    def generate_monthly_summary(self, target_month: datetime | None = None) -> dict[str, Any]:
        """
        Generate comprehensive monthly trading summary.

        Args:
            target_month: Target month for summary (defaults to previous month)

        Returns:
            Dictionary containing comprehensive monthly summary data
        """
        try:
            # Default to previous month
            if target_month is None:
                today = datetime.now()
                if today.month == 1:
                    target_month = today.replace(year=today.year - 1, month=12, day=1)
                else:
                    target_month = today.replace(month=today.month - 1, day=1)

            # Calculate date range for the month
            start_date = target_month.replace(day=1)
            if start_date.month == 12:
                end_date = start_date.replace(year=start_date.year + 1, month=1, day=1) - timedelta(
                    days=1
                )
            else:
                end_date = start_date.replace(month=start_date.month + 1, day=1) - timedelta(days=1)

            self.logger.info(f"Generating monthly summary for {start_date.strftime('%B %Y')}")

            # Gather all required data
            summary = {
                "month": start_date.strftime("%B %Y"),
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "account_summary": self._get_account_summary(),
                "portfolio_performance": self._get_portfolio_performance(start_date, end_date),
                "trading_activity": self._get_trading_activity(start_date, end_date),
                "strategy_performance": self._get_strategy_performance(),
                "fees_and_costs": self._get_fees_and_costs(start_date, end_date),
                "positions_summary": self._get_positions_summary(),
                "generated_at": datetime.now().isoformat(),
            }

            self.logger.info(f"Successfully generated monthly summary for {summary['month']}")
            return summary

        except Exception as e:
            self.logger.error(f"Failed to generate monthly summary: {e}")
            raise DataProviderError(f"Monthly summary generation failed: {e}") from e

    def _get_account_summary(self) -> dict[str, Any]:
        """Get current account summary information."""
        try:
            account = self.alpaca_manager.get_account()
            if not account:
                return {}

            return {
                "portfolio_value": float(account.get("portfolio_value", 0)),
                "equity": float(account.get("equity", 0)),
                "cash": float(account.get("cash", 0)),
                "buying_power": float(account.get("buying_power", 0)),
                "day_trades_remaining": account.get("day_trades_remaining", 0),
                "status": account.get("status", "UNKNOWN"),
            }
        except Exception as e:
            self.logger.warning(f"Failed to get account summary: {e}")
            return {}

    def _get_portfolio_performance(
        self, start_date: datetime, end_date: datetime
    ) -> dict[str, Any]:
        """Get portfolio performance metrics for the month."""
        try:
            history = self.alpaca_manager.get_portfolio_history(
                start_date=start_date.isoformat(), end_date=end_date.isoformat(), timeframe="1Day"
            )

            if not history or not history.get("equity"):
                return {}

            equity_values = [float(eq) for eq in history.get("equity", [])]
            pnl_values = [float(pnl) for pnl in history.get("profit_loss", [])]

            if not equity_values:
                return {}

            # Calculate performance metrics
            start_value = equity_values[0]
            end_value = equity_values[-1]
            total_return = end_value - start_value
            total_return_pct = (total_return / start_value * 100) if start_value > 0 else 0

            # Calculate max/min values for the month
            max_value = max(equity_values)
            min_value = min(equity_values)
            max_drawdown = ((max_value - min_value) / max_value * 100) if max_value > 0 else 0

            # Sum realized P&L for the month
            total_realized_pnl = sum(pnl_values) if pnl_values else 0

            return {
                "start_value": round(start_value, 2),
                "end_value": round(end_value, 2),
                "total_return": round(total_return, 2),
                "total_return_pct": round(total_return_pct, 2),
                "max_value": round(max_value, 2),
                "min_value": round(min_value, 2),
                "max_drawdown_pct": round(max_drawdown, 2),
                "total_realized_pnl": round(total_realized_pnl, 2),
                "trading_days": len(equity_values),
            }

        except Exception as e:
            self.logger.warning(f"Failed to get portfolio performance: {e}")
            return {}

    def _get_trading_activity(self, start_date: datetime, end_date: datetime) -> dict[str, Any]:
        """Get trading activity summary for the month."""
        try:
            activities = self.alpaca_manager.get_activities(
                activity_type="FILL",
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
            )

            if not activities:
                return {"total_trades": 0, "buy_trades": 0, "sell_trades": 0}

            buy_trades = [a for a in activities if str(a.get("side", "")).upper() == "BUY"]
            sell_trades = [a for a in activities if str(a.get("side", "")).upper() == "SELL"]

            # Calculate trade volumes
            total_buy_volume = sum(
                float(a.get("qty", 0)) * float(a.get("price", 0))
                for a in buy_trades
                if a.get("qty") and a.get("price")
            )
            total_sell_volume = sum(
                float(a.get("qty", 0)) * float(a.get("price", 0))
                for a in sell_trades
                if a.get("qty") and a.get("price")
            )

            # Get unique symbols traded
            symbols_traded = set()
            for activity in activities:
                if activity.get("symbol"):
                    symbols_traded.add(activity.get("symbol"))

            return {
                "total_trades": len(activities),
                "buy_trades": len(buy_trades),
                "sell_trades": len(sell_trades),
                "total_buy_volume": round(total_buy_volume, 2),
                "total_sell_volume": round(total_sell_volume, 2),
                "symbols_traded": list(symbols_traded),
                "symbol_count": len(symbols_traded),
            }

        except Exception as e:
            self.logger.warning(f"Failed to get trading activity: {e}")
            return {"total_trades": 0, "buy_trades": 0, "sell_trades": 0}

    def _get_strategy_performance(self) -> dict[str, Any]:
        """Get strategy-specific performance metrics."""
        try:
            tracker = get_strategy_tracker(paper_trading=self.paper_trading)

            # Get current prices for P&L calculations
            positions = self.alpaca_manager.get_positions_dict()
            current_prices = {}
            if positions:
                current_prices = self.alpaca_manager.get_current_prices(list(positions.keys()))

            # Get strategy P&L summary
            all_strategy_pnl = tracker.get_all_strategy_pnl(current_prices)

            strategy_summary = {}
            total_realized = 0.0
            total_unrealized = 0.0

            for strategy_type, pnl in all_strategy_pnl.items():
                strategy_name = (
                    strategy_type.value if hasattr(strategy_type, "value") else str(strategy_type)
                )

                strategy_summary[strategy_name] = {
                    "realized_pnl": round(pnl.realized_pnl, 2),
                    "unrealized_pnl": round(pnl.unrealized_pnl, 2),
                    "total_pnl": round(pnl.total_pnl, 2),
                    "allocation_value": round(pnl.allocation_value, 2),
                    "position_count": len([q for q in pnl.positions.values() if q > 0]),
                    "total_return_pct": (
                        round(pnl.total_return_pct, 2) if hasattr(pnl, "total_return_pct") else 0.0
                    ),
                }

                total_realized += pnl.realized_pnl
                total_unrealized += pnl.unrealized_pnl

            return {
                "strategies": strategy_summary,
                "total_realized_pnl": round(total_realized, 2),
                "total_unrealized_pnl": round(total_unrealized, 2),
                "total_strategy_pnl": round(total_realized + total_unrealized, 2),
            }

        except Exception as e:
            self.logger.warning(f"Failed to get strategy performance: {e}")
            return {"strategies": {}}

    def _get_fees_and_costs(self, start_date: datetime, end_date: datetime) -> dict[str, Any]:
        """Get trading fees and costs for the month."""
        try:
            # Note: Alpaca typically doesn't charge commission fees, but we can check for other fees
            # This is a placeholder for potential fee tracking if needed
            # For now, Alpaca has zero commission trading
            # But this structure allows for future fee calculations
            return {
                "commission_fees": 0.0,
                "sec_fees": 0.0,
                "other_fees": 0.0,
                "total_fees": 0.0,
                "note": "Alpaca provides commission-free trading",
            }

        except Exception as e:
            self.logger.warning(f"Failed to get fees and costs: {e}")
            return {"total_fees": 0.0}

    def _get_positions_summary(self) -> dict[str, Any]:
        """Get current positions summary."""
        try:
            positions = self.alpaca_manager.get_positions()
            if not positions:
                return {"total_positions": 0}

            total_market_value = sum(float(getattr(pos, "market_value", 0)) for pos in positions)
            total_unrealized_pnl = sum(float(getattr(pos, "unrealized_pl", 0)) for pos in positions)

            # Get top positions by market value
            position_list = []
            for pos in positions:
                position_list.append(
                    {
                        "symbol": str(getattr(pos, "symbol", "")),
                        "qty": float(getattr(pos, "qty", 0)),
                        "market_value": float(getattr(pos, "market_value", 0)),
                        "unrealized_pl": float(getattr(pos, "unrealized_pl", 0)),
                        "current_price": float(getattr(pos, "current_price", 0)),
                    }
                )

            # Sort by market value (absolute value)
            position_list.sort(
                key=lambda x: abs(x["market_value"]) if isinstance(x["market_value"], (int, float)) else 0, 
                reverse=True
            )

            return {
                "total_positions": len(positions),
                "total_market_value": round(total_market_value, 2),
                "total_unrealized_pnl": round(total_unrealized_pnl, 2),
                "top_positions": position_list[:10],  # Top 10 positions
            }

        except Exception as e:
            self.logger.warning(f"Failed to get positions summary: {e}")
            return {"total_positions": 0}
