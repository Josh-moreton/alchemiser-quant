#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Local Account Value Logger Implementation for Daily Portfolio Value Persistence.

This module provides local file-based account value logging using JSONL files
for tracking daily portfolio values over time for performance analysis.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from collections.abc import Iterable
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from ..schemas.account_value_logger import AccountValueEntry, AccountValueQuery
from .base_account_value_logger import BaseAccountValueLogger

logger = logging.getLogger(__name__)


class LocalAccountValueLogger(BaseAccountValueLogger):
    """Local file-based account value logger implementation.

    Uses JSONL format for append-only storage with daily account values.
    Supports environment variable configuration for storage path.
    """

    def __init__(self, base_path: str | None = None) -> None:
        """Initialize local account value logger.

        Args:
            base_path: Base directory for value log files (defaults to ./data/account_values)

        """
        # Prefer explicit override via environment, then Lambda /tmp, then local path
        env_base = os.getenv("ACCOUNT_VALUE_LOGGER_BASE_PATH")
        if base_path:
            resolved_base = base_path
        elif env_base:
            resolved_base = env_base
        elif os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
            resolved_base = str(Path(tempfile.gettempdir()) / "alchemiser" / "account_values")
        else:
            resolved_base = "./data/account_values"

        self.base_path = Path(resolved_base)
        self.base_path.mkdir(parents=True, exist_ok=True)

        # File paths
        self.values_file = self.base_path / "account_values.jsonl"

    def log_account_value(self, entry: AccountValueEntry) -> None:
        """Log a single account value entry (idempotent by date).

        Args:
            entry: Account value entry to log

        Raises:
            ValueError: If entry is invalid
            IOError: If persistence operation fails

        """
        try:
            # Check if entry for this date already exists
            date_key = entry.get_date_key()
            existing_entries = list(self._load_entries_for_date(date_key))

            # If entry for this date exists, update it; otherwise append
            if existing_entries:
                self._update_entry_for_date(date_key, entry)
                logger.debug(f"Updated account value entry for {date_key}")
            else:
                self._append_entry(entry)
                logger.debug(f"Added new account value entry for {date_key}")

        except Exception as e:
            logger.error(f"Failed to log account value entry: {e}")
            raise

    def log_account_values(self, entries: Iterable[AccountValueEntry]) -> None:
        """Log multiple account value entries.

        Args:
            entries: Iterable of account value entries to log

        Raises:
            ValueError: If any entry is invalid
            IOError: If persistence operation fails

        """
        entries_list = list(entries)
        if not entries_list:
            return

        try:
            for entry in entries_list:
                self.log_account_value(entry)

            logger.info(f"Logged {len(entries_list)} account value entries")

        except Exception as e:
            logger.error(f"Failed to log multiple account value entries: {e}")
            raise

    def query_account_values(self, filters: AccountValueQuery) -> Iterable[AccountValueEntry]:
        """Query account value entries based on filters.

        Args:
            filters: Query filters

        Returns:
            Iterable of matching account value entries

        Raises:
            IOError: If query operation fails

        """
        try:
            matching_entries: list[AccountValueEntry] = []

            if not self.values_file.exists():
                return matching_entries

            with self.values_file.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        data = json.loads(line)
                        entry = self._deserialize_entry(data)

                        if self._matches_filters(entry, filters):
                            matching_entries.append(entry)
                    except (json.JSONDecodeError, ValueError) as e:
                        logger.warning(f"Skipping invalid entry: {e}")
                        continue

            return self._sort_entries_by_timestamp(matching_entries)

        except Exception as e:
            logger.error(f"Failed to query account value entries: {e}")
            raise

    def get_latest_value(self, account_id: str) -> AccountValueEntry | None:
        """Get the latest account value entry for an account.

        Args:
            account_id: Account identifier

        Returns:
            Latest account value entry or None if not found

        Raises:
            IOError: If query operation fails

        """
        try:
            filters = AccountValueQuery(account_id=account_id)
            entries = list(self.query_account_values(filters))

            if not entries:
                return None

            # Entries are already sorted by timestamp
            return entries[-1]

        except Exception as e:
            logger.error(f"Failed to get latest account value: {e}")
            raise

    def _load_entries_for_date(self, date_key: str) -> Iterable[AccountValueEntry]:
        """Load entries for a specific date.

        Args:
            date_key: Date key in YYYY-MM-DD format

        Returns:
            Iterable of entries for that date

        """
        if not self.values_file.exists():
            return []

        matching_entries: list[AccountValueEntry] = []
        with self.values_file.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    entry = self._deserialize_entry(data)

                    if entry.get_date_key() == date_key:
                        matching_entries.append(entry)
                except (json.JSONDecodeError, ValueError):
                    continue

        return matching_entries

    def _update_entry_for_date(self, date_key: str, new_entry: AccountValueEntry) -> None:
        """Update entry for a specific date by rewriting the file.

        Args:
            date_key: Date key in YYYY-MM-DD format
            new_entry: New entry to replace existing entry for this date

        """
        if not self.values_file.exists():
            self._append_entry(new_entry)
            return

        # Read all entries
        all_entries = []
        with self.values_file.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    entry = self._deserialize_entry(data)

                    # Replace entry if date matches, otherwise keep existing
                    if entry.get_date_key() == date_key:
                        all_entries.append(new_entry)
                    else:
                        all_entries.append(entry)
                except (json.JSONDecodeError, ValueError):
                    continue

        # Rewrite file with updated entries
        with self.values_file.open("w", encoding="utf-8") as f:
            for entry in all_entries:
                serialized = self._serialize_entry(entry)
                f.write(json.dumps(serialized) + "\n")

    def _append_entry(self, entry: AccountValueEntry) -> None:
        """Append entry to file.

        Args:
            entry: Entry to append

        """
        serialized = self._serialize_entry(entry)
        with self.values_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(serialized) + "\n")

    def _serialize_entry(self, entry: AccountValueEntry) -> dict[str, Any]:
        """Serialize account value entry to dictionary.

        Args:
            entry: Account value entry to serialize

        Returns:
            Serialized dictionary

        """
        data = entry.model_dump()

        # Convert datetime to ISO string
        if isinstance(data["timestamp"], datetime):
            data["timestamp"] = data["timestamp"].isoformat()

        # Convert Decimal fields to strings
        decimal_fields = ["portfolio_value", "cash", "equity"]
        for field in decimal_fields:
            if data.get(field) is not None:
                data[field] = str(data[field])

        return data

    def _deserialize_entry(self, data: dict[str, Any]) -> AccountValueEntry:
        """Deserialize dictionary to account value entry.

        Args:
            data: Serialized data

        Returns:
            Account value entry

        Raises:
            ValueError: If data is invalid

        """
        # Convert string timestamp back to datetime
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])

        # Convert string Decimal fields back to Decimal
        decimal_fields = ["portfolio_value", "cash", "equity"]
        for field in decimal_fields:
            if data.get(field) is not None and isinstance(data[field], str):
                data[field] = Decimal(data[field])

        return AccountValueEntry(**data)
