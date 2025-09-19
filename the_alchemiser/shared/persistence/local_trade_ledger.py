#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Local Trade Ledger Implementation for Paper Trading Persistence.

This module provides local file-based trade ledger storage for paper trading mode,
using JSONL files with an index for idempotency and efficient querying.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Iterable
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from ..dto.trade_ledger_dto import (
    Lot,
    PerformanceSummary,
    TradeLedgerEntry,
    TradeLedgerQuery,
)
from .base_trade_ledger import BaseTradeLedger

logger = logging.getLogger(__name__)


class LocalTradeLedger(BaseTradeLedger):
    """Local file-based trade ledger implementation.

    Uses JSONL format for append-only storage with an index file for
    idempotency checks and efficient querying.
    """

    def __init__(self, base_path: str | None = None) -> None:
        """Initialize local trade ledger.

        Args:
            base_path: Base directory for ledger files (defaults to ./data/trade_ledger)

        """
        self.base_path = Path(base_path or "./data/trade_ledger")
        self.base_path.mkdir(parents=True, exist_ok=True)

        # File paths
        self.ledger_file = self.base_path / "ledger.jsonl"
        self.index_file = self.base_path / "index.json"

        # In-memory index for performance (loaded on demand)
        self._index: dict[tuple[str, str], str] | None = None
        self._index_loaded = False

    def _load_index(self) -> dict[tuple[str, str], str]:
        """Load the index from file if not already loaded.

        Returns:
            Dictionary mapping unique keys to ledger entry IDs

        """
        if self._index_loaded:
            return self._index or {}

        try:
            if self.index_file.exists():
                with self.index_file.open("r", encoding="utf-8") as f:
                    index_data = json.load(f)
                    # Convert string keys back to tuples
                    self._index = {
                        tuple(key.split("||")): value for key, value in index_data.items()
                    }
            else:
                self._index = {}
                self._save_index()
        except Exception as e:
            logger.warning(f"Failed to load index, rebuilding: {e}")
            self._index = self._rebuild_index()

        self._index_loaded = True
        return self._index

    def _save_index(self) -> None:
        """Save the index to file."""
        if self._index is None:
            return

        try:
            # Convert tuple keys to strings for JSON serialization
            index_data = {"||".join(key): value for key, value in self._index.items()}
            with self.index_file.open("w", encoding="utf-8") as f:
                json.dump(index_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save index: {e}")
            raise

    def _rebuild_index(self) -> dict[tuple[str, str], str]:
        """Rebuild index by scanning the entire ledger file.

        Returns:
            Rebuilt index dictionary

        """
        logger.info("Rebuilding trade ledger index")
        index: dict[tuple[str, str], str] = {}

        if not self.ledger_file.exists():
            return index

        try:
            with self.ledger_file.open("r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        data = json.loads(line.strip())
                        if "order_id" in data and "ledger_id" in data:
                            fill_id = data.get("fill_id") or data["ledger_id"]
                            unique_key = (data["order_id"], fill_id)
                            index[unique_key] = data["ledger_id"]
                    except json.JSONDecodeError as e:
                        logger.warning(f"Invalid JSON on line {line_num}: {e}")
                    except KeyError as e:
                        logger.warning(f"Missing required field on line {line_num}: {e}")

            logger.info(f"Rebuilt index with {len(index)} entries")
            self._save_index()
        except Exception as e:
            logger.error(f"Failed to rebuild index: {e}")
            raise

        return index

    def upsert(self, entry: TradeLedgerEntry) -> None:
        """Insert or update a trade ledger entry (idempotent by unique key).

        Args:
            entry: Trade ledger entry to insert/update

        Raises:
            ValueError: If entry is invalid
            IOError: If persistence operation fails

        """
        try:
            index = self._load_index()
            unique_key = entry.get_unique_key()

            # Check if entry already exists
            if unique_key in index:
                existing_id = index[unique_key]
                if existing_id == entry.ledger_id:
                    logger.debug(f"Entry {entry.ledger_id} already exists, skipping")
                    return
                logger.warning(
                    f"Duplicate key {unique_key} with different ledger_id: "
                    f"existing={existing_id}, new={entry.ledger_id}"
                )
                return

            # Append to ledger file
            serialized = self._serialize_entry(entry)
            with self.ledger_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(serialized) + "\n")

            # Update index
            index[unique_key] = entry.ledger_id
            self._save_index()

            logger.debug(f"Added ledger entry {entry.ledger_id} for {entry.symbol}")

        except Exception as e:
            logger.error(f"Failed to upsert trade ledger entry: {e}")
            raise

    def upsert_many(self, entries: Iterable[TradeLedgerEntry]) -> None:
        """Insert or update multiple trade ledger entries (idempotent by unique key).

        Args:
            entries: Iterable of trade ledger entries to insert/update

        Raises:
            ValueError: If any entry is invalid
            IOError: If persistence operation fails

        """
        entries_list = list(entries)
        if not entries_list:
            return

        try:
            index = self._load_index()
            new_entries = []

            # Filter out existing entries
            for entry in entries_list:
                unique_key = entry.get_unique_key()
                if unique_key in index:
                    existing_id = index[unique_key]
                    if existing_id == entry.ledger_id:
                        continue
                    logger.warning(
                        f"Duplicate key {unique_key} with different ledger_id: "
                        f"existing={existing_id}, new={entry.ledger_id}"
                    )
                    continue
                new_entries.append(entry)

            if not new_entries:
                logger.debug("All entries already exist, skipping batch upsert")
                return

            # Append new entries to ledger file
            with self.ledger_file.open("a", encoding="utf-8") as f:
                for entry in new_entries:
                    serialized = self._serialize_entry(entry)
                    f.write(json.dumps(serialized) + "\n")
                    index[entry.get_unique_key()] = entry.ledger_id

            # Save updated index
            self._save_index()

            logger.info(f"Added {len(new_entries)} new ledger entries")

        except Exception as e:
            logger.error(f"Failed to upsert multiple trade ledger entries: {e}")
            raise

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
        try:
            if not self.ledger_file.exists():
                return []

            entries: list[TradeLedgerEntry] = []
            with self.ledger_file.open("r", encoding="utf-8") as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        entry = self._deserialize_entry(data)

                        if self._matches_filters(entry, filters):
                            entries.append(entry)
                    except (json.JSONDecodeError, ValueError) as e:
                        logger.warning(f"Skipping invalid ledger entry: {e}")

            # Sort results
            entries.sort(
                key=lambda e: getattr(e, filters.order_by),
                reverse=not filters.ascending,
            )

            # Apply pagination
            start = filters.offset or 0
            end = start + (filters.limit or len(entries))
            return entries[start:end]

        except Exception as e:
            logger.error(f"Failed to query trade ledger: {e}")
            raise

    def get_open_lots(self, strategy: str | None = None, symbol: str | None = None) -> list[Lot]:
        """Get open lots for attribution tracking.

        This is a simplified implementation that calculates lots on-the-fly.
        For production, consider caching or maintaining a separate lots index.

        Args:
            strategy: Filter by strategy name (None for all strategies)
            symbol: Filter by symbol (None for all symbols)

        Returns:
            List of open lots matching criteria

        """
        try:
            # Query all entries for the given filters
            query_filters = TradeLedgerQuery(
                strategy_name=strategy,
                symbol=symbol,
                order_by="timestamp",
                ascending=True,
            )

            entries = list(self.query(query_filters))
            return self._calculate_lots_from_entries(entries)

        except Exception as e:
            logger.error(f"Failed to get open lots: {e}")
            raise

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

        """
        try:
            # Query all entries for the given filters
            query_filters = TradeLedgerQuery(
                strategy_name=strategy,
                symbol=symbol,
                order_by="timestamp",
                ascending=True,
            )

            entries = list(self.query(query_filters))
            return self._calculate_performance_from_entries(entries, current_prices or {})

        except Exception as e:
            logger.error(f"Failed to calculate performance: {e}")
            raise

    def get_ledger_entries_by_order(self, order_id: str) -> list[TradeLedgerEntry]:
        """Get all ledger entries for a specific order.

        Args:
            order_id: Order identifier

        Returns:
            List of ledger entries for the order

        """
        try:
            entries: list[TradeLedgerEntry] = []
            if not self.ledger_file.exists():
                return entries

            with self.ledger_file.open("r", encoding="utf-8") as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        if data.get("order_id") == order_id:
                            entry = self._deserialize_entry(data)
                            entries.append(entry)
                    except (json.JSONDecodeError, ValueError) as e:
                        logger.warning(f"Skipping invalid ledger entry: {e}")

            return sorted(entries, key=lambda e: e.timestamp)

        except Exception as e:
            logger.error(f"Failed to get ledger entries by order: {e}")
            raise

    def verify_integrity(self) -> bool:
        """Verify ledger integrity and consistency.

        Returns:
            True if ledger is consistent, False otherwise

        """
        try:
            # Check file existence
            if not self.ledger_file.exists():
                return True  # Empty ledger is valid

            # Verify each entry can be parsed
            line_count = 0
            with self.ledger_file.open("r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        data = json.loads(line.strip())
                        self._deserialize_entry(data)
                        line_count += 1
                    except Exception as e:
                        logger.error(f"Integrity check failed on line {line_num}: {e}")
                        return False

            # Verify index consistency
            index = self._load_index()
            if len(index) != line_count:
                logger.warning(
                    f"Index size mismatch: index={len(index)}, file_lines={line_count}"
                )
                # Rebuild index
                self._index = self._rebuild_index()

            logger.info(f"Ledger integrity verified: {line_count} entries")
            return True

        except Exception as e:
            logger.error(f"Integrity verification failed: {e}")
            return False

    def _serialize_entry(self, entry: TradeLedgerEntry) -> dict[str, Any]:
        """Serialize trade ledger entry to dictionary.

        Args:
            entry: Trade ledger entry to serialize

        Returns:
            Serialized dictionary

        """
        data = entry.model_dump()

        # Convert datetime to ISO string
        if isinstance(data["timestamp"], datetime):
            data["timestamp"] = data["timestamp"].isoformat()

        # Convert Decimal fields to strings
        decimal_fields = ["quantity", "price", "fees"]
        for field in decimal_fields:
            if data.get(field) is not None:
                data[field] = str(data[field])

        return data

    def _deserialize_entry(self, data: dict[str, Any]) -> TradeLedgerEntry:
        """Deserialize dictionary to trade ledger entry.

        Args:
            data: Serialized data dictionary

        Returns:
            Trade ledger entry

        """
        # Convert timestamp back to datetime
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])

        # Convert string decimal fields back to Decimal
        decimal_fields = ["quantity", "price", "fees"]
        for field in decimal_fields:
            if data.get(field) is not None and isinstance(data[field], str):
                data[field] = Decimal(data[field])

        return TradeLedgerEntry(**data)