#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Base Account Value Logger Implementation.

This module provides the base class for account value logging implementations,
offering a simplified interface for tracking daily portfolio values.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from typing import Protocol

from ..schemas.account_value_logger import AccountValueEntry, AccountValueQuery

logger = logging.getLogger(__name__)


class AccountValueLoggerProtocol(Protocol):
    """Protocol defining the interface for account value loggers."""

    def log_account_value(self, entry: AccountValueEntry) -> None:
        """Log a single account value entry.

        Args:
            entry: Account value entry to log

        Raises:
            ValueError: If entry is invalid
            IOError: If logging operation fails

        """
        ...

    def log_account_values(self, entries: Iterable[AccountValueEntry]) -> None:
        """Log multiple account value entries.

        Args:
            entries: Iterable of account value entries to log

        Raises:
            ValueError: If any entry is invalid
            IOError: If logging operation fails

        """
        ...

    def query_account_values(self, filters: AccountValueQuery) -> Iterable[AccountValueEntry]:
        """Query account value entries based on filters.

        Args:
            filters: Query filters

        Returns:
            Iterable of matching account value entries

        Raises:
            IOError: If query operation fails

        """
        ...

    def get_latest_value(self, account_id: str) -> AccountValueEntry | None:
        """Get the latest account value entry for an account.

        Args:
            account_id: Account identifier

        Returns:
            Latest account value entry or None if not found

        Raises:
            IOError: If query operation fails

        """
        ...


class BaseAccountValueLogger:
    """Base class providing shared business logic for account value logger implementations."""

    def _matches_filters(self, entry: AccountValueEntry, filters: AccountValueQuery) -> bool:
        """Check if entry matches query filters.

        Args:
            entry: Account value entry to check
            filters: Query filters

        Returns:
            True if entry matches all filters

        """
        if filters.account_id and entry.account_id != filters.account_id:
            return False

        if filters.start_date and entry.timestamp < filters.start_date:
            return False

        return not (filters.end_date and entry.timestamp > filters.end_date)

    def _sort_entries_by_timestamp(
        self, entries: list[AccountValueEntry]
    ) -> list[AccountValueEntry]:
        """Sort entries by timestamp in ascending order.

        Args:
            entries: List of account value entries

        Returns:
            Sorted list of entries

        """
        return sorted(entries, key=lambda e: e.timestamp)
