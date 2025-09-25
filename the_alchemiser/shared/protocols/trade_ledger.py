#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Trade Ledger Protocol Interface for Trading System Persistence.

This module defines the protocol for trade ledger operations, allowing
different implementations (local JSONL, S3, DynamoDB) based on trading mode.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from ..schemas.trade_ledger import Lot, PerformanceSummary, TradeLedgerEntry, TradeLedgerQuery


class TradeLedger(Protocol):
    """Protocol for trade ledger persistence operations."""

    def upsert(self, entry: TradeLedgerEntry) -> None:
        """Insert or update a trade ledger entry (idempotent by unique key).

        Args:
            entry: Trade ledger entry to insert/update

        Raises:
            ValueError: If entry is invalid or conflicts with existing data
            IOError: If persistence operation fails

        """
        ...

    def upsert_many(self, entries: Iterable[TradeLedgerEntry]) -> None:
        """Insert or update multiple trade ledger entries (idempotent by unique key).

        Args:
            entries: Iterable of trade ledger entries to insert/update

        Raises:
            ValueError: If any entry is invalid or conflicts with existing data
            IOError: If persistence operation fails

        """
        ...

    def query(self, filters: TradeLedgerQuery) -> Iterable[TradeLedgerEntry]:
        """Query trade ledger entries with filtering and pagination.

        Args:
            filters: Query filters and pagination options

        Returns:
            Iterable of matching trade ledger entries

        Raises:
            ValueError: If query parameters are invalid
            IOError: If query operation fails

        """
        ...

    def get_open_lots(self, strategy: str | None = None, symbol: str | None = None) -> list[Lot]:
        """Get open lots for attribution tracking.

        Args:
            strategy: Filter by strategy name (None for all strategies)
            symbol: Filter by symbol (None for all symbols)

        Returns:
            List of open lots matching criteria

        Raises:
            ValueError: If parameters are invalid
            IOError: If query operation fails

        """
        ...

    def calculate_performance(
        self,
        strategy: str | None = None,
        symbol: str | None = None,
        current_prices: dict[str, float] | None = None,
    ) -> list[PerformanceSummary]:
        """Calculate performance summaries for strategies and symbols.

        Args:
            strategy: Filter by strategy name (None for all strategies)
            symbol: Filter by symbol (None for all symbols)
            current_prices: Current market prices for unrealized P&L calculation

        Returns:
            List of performance summaries

        Raises:
            ValueError: If parameters are invalid
            IOError: If calculation fails

        """
        ...

    def get_ledger_entries_by_order(self, order_id: str) -> list[TradeLedgerEntry]:
        """Get all ledger entries for a specific order.

        Args:
            order_id: Order identifier

        Returns:
            List of ledger entries for the order

        Raises:
            ValueError: If order_id is invalid
            IOError: If query operation fails

        """
        ...

    def verify_integrity(self) -> bool:
        """Verify ledger integrity and consistency.

        Returns:
            True if ledger is consistent, False otherwise

        Raises:
            IOError: If verification fails due to storage issues

        """
        ...
