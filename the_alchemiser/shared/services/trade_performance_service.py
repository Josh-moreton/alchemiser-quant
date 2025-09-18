#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Trade Performance Service for Strategy Attribution and P&L Calculation.

This module provides high-level trade performance analysis and attribution
services that consume the trade ledger and provide strategy-level insights.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from ..dto.trade_ledger_dto import Lot, PerformanceSummary, TradeLedgerQuery
from ..protocols.trade_ledger import TradeLedger

logger = logging.getLogger(__name__)


class TradePerformanceService:
    """Service for calculating trade performance and attribution across strategies."""

    def __init__(self, trade_ledger: TradeLedger) -> None:
        """Initialize the performance service.

        Args:
            trade_ledger: Trade ledger implementation to query

        """
        self.trade_ledger = trade_ledger

    def get_strategy_performance(
        self,
        strategy_name: str,
        current_prices: dict[str, float] | None = None,
    ) -> list[PerformanceSummary]:
        """Get performance summary for a specific strategy.

        Args:
            strategy_name: Strategy name to analyze
            current_prices: Current market prices for unrealized P&L calculation

        Returns:
            List of performance summaries (per symbol + total)

        """
        try:
            return self.trade_ledger.calculate_performance(
                strategy=strategy_name,
                symbol=None,
                current_prices=current_prices,
            )
        except Exception as e:
            logger.error(f"Failed to get strategy performance for {strategy_name}: {e}")
            raise

    def get_symbol_performance(
        self,
        symbol: str,
        current_prices: dict[str, float] | None = None,
    ) -> list[PerformanceSummary]:
        """Get performance summary for a specific symbol across all strategies.

        Args:
            symbol: Symbol to analyze
            current_prices: Current market prices for unrealized P&L calculation

        Returns:
            List of performance summaries per strategy for the symbol

        """
        try:
            return self.trade_ledger.calculate_performance(
                strategy=None,
                symbol=symbol,
                current_prices=current_prices,
            )
        except Exception as e:
            logger.error(f"Failed to get symbol performance for {symbol}: {e}")
            raise

    def get_all_performance(
        self,
        current_prices: dict[str, float] | None = None,
    ) -> list[PerformanceSummary]:
        """Get performance summaries for all strategies and symbols.

        Args:
            current_prices: Current market prices for unrealized P&L calculation

        Returns:
            List of all performance summaries

        """
        try:
            return self.trade_ledger.calculate_performance(
                strategy=None,
                symbol=None,
                current_prices=current_prices,
            )
        except Exception as e:
            logger.error(f"Failed to get all performance: {e}")
            raise

    def get_open_positions(self, strategy_name: str | None = None) -> list[Lot]:
        """Get open positions (lots) for attribution tracking.

        Args:
            strategy_name: Strategy name to filter by (None for all strategies)

        Returns:
            List of open lots

        """
        try:
            return self.trade_ledger.get_open_lots(strategy=strategy_name, symbol=None)
        except Exception as e:
            logger.error(f"Failed to get open positions for {strategy_name}: {e}")
            raise

    def get_realized_pnl(
        self,
        strategy_name: str | None = None,
        symbol: str | None = None,
    ) -> Decimal:
        """Get total realized P&L for strategy/symbol combination.

        Args:
            strategy_name: Strategy name to filter by (None for all strategies)
            symbol: Symbol to filter by (None for all symbols)

        Returns:
            Total realized P&L

        """
        try:
            summaries = self.trade_ledger.calculate_performance(
                strategy=strategy_name,
                symbol=symbol,
                current_prices=None,
            )

            # Find the total summary (the one without a specific symbol if filtering by strategy)
            if strategy_name and not symbol:
                # Looking for strategy total
                for summary in summaries:
                    if summary.strategy_name == strategy_name and summary.symbol is None:
                        return summary.realized_pnl
            elif symbol and not strategy_name:
                # Sum across all strategies for this symbol
                result = sum(s.realized_pnl for s in summaries if s.symbol == symbol)
                return result or Decimal("0")
            elif strategy_name and symbol:
                # Specific strategy-symbol combination
                for summary in summaries:
                    if summary.strategy_name == strategy_name and summary.symbol == symbol:
                        return summary.realized_pnl
            else:
                # Total across everything
                result = sum(
                    s.realized_pnl
                    for s in summaries
                    if s.symbol is None  # Only strategy totals to avoid double counting
                )
                return result or Decimal("0")

            return Decimal("0")

        except Exception as e:
            logger.error(f"Failed to get realized P&L: {e}")
            raise

    def get_unrealized_pnl(
        self,
        current_prices: dict[str, float],
        strategy_name: str | None = None,
        symbol: str | None = None,
    ) -> Decimal | None:
        """Get total unrealized P&L for strategy/symbol combination.

        Args:
            current_prices: Current market prices
            strategy_name: Strategy name to filter by (None for all strategies)
            symbol: Symbol to filter by (None for all symbols)

        Returns:
            Total unrealized P&L or None if prices unavailable

        """
        try:
            summaries = self.trade_ledger.calculate_performance(
                strategy=strategy_name,
                symbol=symbol,
                current_prices=current_prices,
            )

            total_unrealized = Decimal("0")
            has_unrealized = False

            if strategy_name and not symbol:
                # Looking for strategy total
                for summary in summaries:
                    if summary.strategy_name == strategy_name and summary.symbol is None:
                        return summary.unrealized_pnl
            elif symbol and not strategy_name:
                # Sum across all strategies for this symbol
                for summary in summaries:
                    if summary.symbol == symbol and summary.unrealized_pnl is not None:
                        total_unrealized += summary.unrealized_pnl
                        has_unrealized = True
            elif strategy_name and symbol:
                # Specific strategy-symbol combination
                for summary in summaries:
                    if (
                        summary.strategy_name == strategy_name
                        and summary.symbol == symbol
                        and summary.unrealized_pnl is not None
                    ):
                        return summary.unrealized_pnl
            else:
                # Total across everything
                for summary in summaries:
                    if summary.symbol is None and summary.unrealized_pnl is not None:
                        total_unrealized += summary.unrealized_pnl
                        has_unrealized = True

            return total_unrealized if has_unrealized else None

        except Exception as e:
            logger.error(f"Failed to get unrealized P&L: {e}")
            raise

    def get_attribution_report(
        self,
        symbol: str,
        current_prices: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        """Get detailed attribution report for a symbol across strategies.

        Args:
            symbol: Symbol to analyze
            current_prices: Current market prices for unrealized P&L

        Returns:
            Attribution report with strategy breakdowns

        """
        try:
            # Get all performance data for this symbol
            summaries = self.trade_ledger.calculate_performance(
                strategy=None,
                symbol=symbol,
                current_prices=current_prices,
            )

            # Get open lots for position details
            lots = self.trade_ledger.get_open_lots(strategy=None, symbol=symbol)

            # Build attribution report
            strategy_breakdown = {}
            total_realized = Decimal("0")
            total_unrealized = Decimal("0")
            total_open_quantity = Decimal("0")

            for summary in summaries:
                if summary.symbol == symbol:
                    strategy_breakdown[summary.strategy_name] = {
                        "realized_pnl": summary.realized_pnl,
                        "unrealized_pnl": summary.unrealized_pnl,
                        "open_quantity": summary.open_quantity,
                        "average_cost_basis": summary.average_cost_basis,
                        "total_fees": summary.total_fees,
                        "realized_trades": summary.realized_trades,
                    }
                    total_realized += summary.realized_pnl
                    if summary.unrealized_pnl:
                        total_unrealized += summary.unrealized_pnl
                    total_open_quantity += summary.open_quantity

            # Group lots by strategy
            lots_by_strategy: dict[str, list[dict[str, Any]]] = {}
            for lot in lots:
                if lot.symbol == symbol:
                    if lot.strategy_name not in lots_by_strategy:
                        lots_by_strategy[lot.strategy_name] = []
                    lots_by_strategy[lot.strategy_name].append(
                        {
                            "lot_id": lot.lot_id,
                            "quantity": lot.remaining_quantity,
                            "cost_basis": lot.cost_basis,
                            "opened_timestamp": lot.opened_timestamp.isoformat(),
                        }
                    )

            return {
                "symbol": symbol,
                "current_price": current_prices.get(symbol) if current_prices else None,
                "total_realized_pnl": total_realized,
                "total_unrealized_pnl": total_unrealized if total_unrealized else None,
                "total_open_quantity": total_open_quantity,
                "strategies": strategy_breakdown,
                "open_lots_by_strategy": lots_by_strategy,
            }

        except Exception as e:
            logger.error(f"Failed to get attribution report for {symbol}: {e}")
            raise

    def verify_attribution_consistency(self) -> dict[str, Any]:
        """Verify that attribution calculations are consistent and balanced.

        Returns:
            Verification report with any inconsistencies found

        """
        try:
            # Get all trade data
            all_query = TradeLedgerQuery(order_by="timestamp", ascending=True)
            all_entries = list(self.trade_ledger.query(all_query))

            # Get all performance summaries
            all_summaries = self.trade_ledger.calculate_performance()

            # Check for basic consistency
            issues = []

            # Group entries by symbol
            entries_by_symbol: dict[str, list[Any]] = {}
            for entry in all_entries:
                if entry.symbol not in entries_by_symbol:
                    entries_by_symbol[entry.symbol] = []
                entries_by_symbol[entry.symbol].append(entry)

            # For each symbol, verify quantities balance
            for symbol, entries in entries_by_symbol.items():
                buy_quantity = sum(e.quantity for e in entries if e.side.value == "BUY")
                sell_quantity = sum(e.quantity for e in entries if e.side.value == "SELL")
                net_quantity = buy_quantity - sell_quantity

                # Get total open quantity from summaries
                symbol_summaries = [s for s in all_summaries if s.symbol == symbol]
                total_open_from_summaries = sum(s.open_quantity for s in symbol_summaries)

                if abs(net_quantity - total_open_from_summaries) > Decimal("0.001"):
                    issues.append(
                        f"Symbol {symbol}: net quantity mismatch - "
                        f"calculated={net_quantity}, summaries={total_open_from_summaries}"
                    )

            return {
                "verification_passed": len(issues) == 0,
                "total_entries": len(all_entries),
                "total_summaries": len(all_summaries),
                "symbols_analyzed": len(entries_by_symbol),
                "issues": issues,
            }

        except Exception as e:
            logger.error(f"Failed to verify attribution consistency: {e}")
            raise