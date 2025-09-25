#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Base Trade Ledger Implementation with Shared Business Logic.

This module provides the shared calculation and filtering logic used by both
local and S3 trade ledger implementations to avoid code duplication.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import UTC, datetime
from decimal import Decimal

from ..schemas.trade_ledger import (
    Lot,
    PerformanceSummary,
    TradeLedgerEntry,
    TradeLedgerQuery,
    TradeSide,
)

logger = logging.getLogger(__name__)


class BaseTradeLedger:
    """Base class providing shared business logic for trade ledger implementations."""

    def _matches_filters(self, entry: TradeLedgerEntry, filters: TradeLedgerQuery) -> bool:
        """Check if entry matches query filters.

        Args:
            entry: Trade ledger entry to check
            filters: Query filters

        Returns:
            True if entry matches all filters

        """
        if filters.strategy_name and entry.strategy_name != filters.strategy_name:
            return False

        if filters.symbol and entry.symbol != filters.symbol:
            return False

        if filters.asset_type and entry.asset_type != filters.asset_type:
            return False

        if filters.side and entry.side != filters.side:
            return False

        if filters.account_id and entry.account_id != filters.account_id:
            return False

        if filters.start_date and entry.timestamp < filters.start_date:
            return False

        return not (filters.end_date and entry.timestamp > filters.end_date)

    def _calculate_lots_from_entries(self, entries: list[TradeLedgerEntry]) -> list[Lot]:
        """Calculate open lots from trade ledger entries using FIFO matching.

        Args:
            entries: List of trade ledger entries (should be sorted by timestamp)

        Returns:
            List of open lots

        """
        # Group entries by strategy and symbol
        positions: dict[tuple[str, str], list[TradeLedgerEntry]] = defaultdict(list)
        for entry in entries:
            key = (entry.strategy_name, entry.symbol)
            positions[key].append(entry)

        lots = []
        for (strategy_name, symbol), position_entries in positions.items():
            # Separate buys and sells
            buys = [e for e in position_entries if e.side == TradeSide.BUY]
            sells = [e for e in position_entries if e.side == TradeSide.SELL]

            # Track remaining quantities for FIFO matching
            buy_queue = [(buy.quantity, buy.price, buy.timestamp, buy.ledger_id) for buy in buys]
            total_sold = sum(sell.quantity for sell in sells)

            # Match sells against buys (FIFO)
            remaining_to_sell = total_sold
            open_lots = []

            for buy_qty, buy_price, buy_time, buy_id in buy_queue:
                if remaining_to_sell >= buy_qty:
                    # This buy is fully matched
                    remaining_to_sell -= buy_qty
                elif remaining_to_sell > 0:
                    # This buy is partially matched
                    remaining_qty = buy_qty - remaining_to_sell
                    remaining_to_sell = Decimal("0")
                    open_lots.append((remaining_qty, buy_price, buy_time, [buy_id]))
                else:
                    # This buy is unmatched
                    open_lots.append((buy_qty, buy_price, buy_time, [buy_id]))

            # Create Lot DTOs for remaining open positions
            for i, (qty, price, timestamp, ledger_ids) in enumerate(open_lots):
                lot = Lot(
                    lot_id=f"{strategy_name}_{symbol}_{i}_{timestamp.isoformat()}",
                    strategy_name=strategy_name,
                    symbol=symbol,
                    quantity=qty,
                    cost_basis=price,
                    opened_timestamp=timestamp,
                    opening_ledger_ids=ledger_ids,
                    remaining_quantity=qty,
                )
                lots.append(lot)

        return lots

    def _calculate_performance_from_entries(
        self, entries: list[TradeLedgerEntry], current_prices: dict[str, float]
    ) -> list[PerformanceSummary]:
        """Calculate performance summaries from trade ledger entries.

        Args:
            entries: List of trade ledger entries
            current_prices: Current market prices for unrealized P&L

        Returns:
            List of performance summaries

        """
        # Group entries by strategy and symbol for detailed analysis
        grouped: dict[tuple[str, str], list[TradeLedgerEntry]] = defaultdict(list)
        strategy_totals: dict[str, list[TradeLedgerEntry]] = defaultdict(list)

        for entry in entries:
            key = (entry.strategy_name, entry.symbol)
            grouped[key].append(entry)
            strategy_totals[entry.strategy_name].append(entry)

        summaries = []

        # Calculate per-strategy, per-symbol summaries
        for (strategy_name, symbol), symbol_entries in grouped.items():
            summary = self._calculate_single_performance(
                strategy_name, symbol, symbol_entries, current_prices
            )
            summaries.append(summary)

        # Calculate per-strategy totals (across all symbols)
        for strategy_name, strategy_entries in strategy_totals.items():
            summary = self._calculate_single_performance(
                strategy_name, None, strategy_entries, current_prices
            )
            summaries.append(summary)

        return summaries

    def _calculate_basic_trade_metrics(
        self, entries: list[TradeLedgerEntry]
    ) -> tuple[Decimal, Decimal, Decimal, Decimal, Decimal, int]:
        """Calculate basic trading metrics from entries.

        Args:
            entries: Trade ledger entries

        Returns:
            Tuple of (total_buy_quantity, total_sell_quantity, total_fees,
                     total_buy_value, total_sell_value, realized_trades)

        """
        buys = [e for e in entries if e.side == TradeSide.BUY]
        sells = [e for e in entries if e.side == TradeSide.SELL]

        total_buy_quantity = sum(buy.quantity for buy in buys) or Decimal("0")
        total_sell_quantity = sum(sell.quantity for sell in sells) or Decimal("0")
        total_fees = sum(entry.fees for entry in entries) or Decimal("0")

        total_buy_value = sum(buy.quantity * buy.price for buy in buys) or Decimal("0")
        total_sell_value = sum(sell.quantity * sell.price for sell in sells) or Decimal("0")
        realized_trades = len(sells)

        return (
            total_buy_quantity,
            total_sell_quantity,
            total_fees,
            total_buy_value,
            total_sell_value,
            realized_trades,
        )

    def _calculate_symbol_performance_metrics(
        self,
        symbol: str,
        entries: list[TradeLedgerEntry],
        current_prices: dict[str, float],
    ) -> tuple[Decimal, Decimal | None, Decimal | None, int]:
        """Calculate performance metrics for a single symbol.

        Args:
            symbol: Symbol to analyze
            entries: Trade ledger entries
            current_prices: Current market prices

        Returns:
            Tuple of (open_quantity, avg_cost, unrealized_pnl, open_lots_count)

        """
        lots = self._calculate_lots_from_entries(entries)
        symbol_lots = [lot for lot in lots if lot.symbol == symbol]

        open_quantity = sum(lot.remaining_quantity for lot in symbol_lots) or Decimal("0")
        avg_cost: Decimal | None = None

        if open_quantity > 0:
            total_cost = sum(lot.remaining_quantity * lot.cost_basis for lot in symbol_lots)
            avg_cost = total_cost / open_quantity

        # Calculate unrealized P&L
        current_price = current_prices.get(symbol)
        unrealized_pnl = None
        if current_price and open_quantity > 0 and avg_cost:
            unrealized_pnl = open_quantity * (Decimal(str(current_price)) - avg_cost)

        return open_quantity, avg_cost, unrealized_pnl, len(symbol_lots)

    def _calculate_strategy_performance_metrics(
        self, entries: list[TradeLedgerEntry], current_prices: dict[str, float]
    ) -> tuple[Decimal, Decimal | None, Decimal | None, int]:
        """Calculate performance metrics for strategy totals across all symbols.

        Args:
            entries: Trade ledger entries
            current_prices: Current market prices

        Returns:
            Tuple of (open_quantity, avg_cost, unrealized_pnl, open_lots_count)

        """
        all_lots = self._calculate_lots_from_entries(entries)
        open_quantity = sum(lot.remaining_quantity for lot in all_lots) or Decimal("0")
        avg_cost = None  # Can't meaningfully average across different symbols

        # Calculate total unrealized P&L across all symbols
        total_unrealized = Decimal("0")
        for lot in all_lots:
            current_price = current_prices.get(lot.symbol)
            if current_price and lot.remaining_quantity > 0:
                lot_unrealized = lot.remaining_quantity * (
                    Decimal(str(current_price)) - lot.cost_basis
                )
                total_unrealized += lot_unrealized

        # Return None if no unrealized P&L
        unrealized_pnl: Decimal | None = total_unrealized if total_unrealized != 0 else None

        return open_quantity, avg_cost, unrealized_pnl, len(all_lots)

    def _calculate_single_performance(
        self,
        strategy_name: str,
        symbol: str | None,
        entries: list[TradeLedgerEntry],
        current_prices: dict[str, float],
    ) -> PerformanceSummary:
        """Calculate performance summary for a single strategy/symbol combination.

        Args:
            strategy_name: Strategy name
            symbol: Symbol (None for strategy total)
            entries: Trade ledger entries for this combination
            current_prices: Current market prices

        Returns:
            Performance summary

        """
        # Calculate basic trading metrics
        (
            total_buy_quantity,
            total_sell_quantity,
            total_fees,
            total_buy_value,
            total_sell_value,
            realized_trades,
        ) = self._calculate_basic_trade_metrics(entries)

        # Calculate realized P&L (simplified - should use proper FIFO matching)
        realized_pnl = total_sell_value - total_buy_value

        # Calculate position metrics based on scope (symbol vs strategy)
        if symbol:
            open_quantity, avg_cost, unrealized_pnl, open_lots_count = (
                self._calculate_symbol_performance_metrics(symbol, entries, current_prices)
            )
        else:
            open_quantity, avg_cost, unrealized_pnl, open_lots_count = (
                self._calculate_strategy_performance_metrics(entries, current_prices)
            )

        return PerformanceSummary(
            strategy_name=strategy_name,
            symbol=symbol,
            calculation_timestamp=datetime.now(UTC).replace(microsecond=0),
            realized_pnl=realized_pnl,
            realized_trades=realized_trades,
            open_quantity=open_quantity,
            open_lots_count=open_lots_count,
            average_cost_basis=avg_cost,
            current_price=(
                Decimal(str(current_prices[symbol]))
                if symbol and symbol in current_prices
                else None
            ),
            unrealized_pnl=unrealized_pnl,
            total_buy_quantity=total_buy_quantity,
            total_sell_quantity=total_sell_quantity,
            total_fees=total_fees,
        )
