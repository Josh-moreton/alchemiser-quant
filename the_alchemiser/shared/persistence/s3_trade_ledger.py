#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

S3 Trade Ledger Implementation for Live Trading Persistence.

This module provides S3-based trade ledger storage for live trading mode,
using partitioned JSONL files by date with S3 objects for indexing and
efficient querying.
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from collections.abc import Iterable
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from ..dto.trade_ledger_dto import (
    Lot,
    PerformanceSummary,
    TradeLedgerEntry,
    TradeLedgerQuery,
    TradeSide,
)

logger = logging.getLogger(__name__)


class S3TradeLedger:
    """S3-based trade ledger implementation.

    Uses partitioned JSONL files by date (s3://bucket/trade_ledger/YYYY/MM/DD/account.jsonl)
    with S3 objects for indexing and idempotency checks.
    """

    def __init__(self, bucket: str, account_id: str | None = None) -> None:
        """Initialize S3 trade ledger.

        Args:
            bucket: S3 bucket name for ledger storage
            account_id: Account identifier for partitioning (defaults to 'default')

        """
        import boto3

        self.s3 = boto3.client("s3")
        self.bucket = bucket
        self.account_id = account_id or "default"

        # Key prefixes
        self.ledger_prefix = "trade_ledger"
        self.index_prefix = "trade_ledger_index"

        # In-memory index cache (loaded on demand)
        self._index_cache: dict[tuple[str, str], str] | None = None
        self._index_cache_date: str | None = None

    def _get_ledger_key(self, timestamp: datetime) -> str:
        """Get S3 key for ledger file based on timestamp.

        Args:
            timestamp: Timestamp to generate key for

        Returns:
            S3 key for the ledger file

        """
        date_str = timestamp.strftime("%Y/%m/%d")
        return f"{self.ledger_prefix}/{date_str}/{self.account_id}.jsonl"

    def _get_index_key(self, date_str: str) -> str:
        """Get S3 key for index file based on date.

        Args:
            date_str: Date string in YYYY/MM/DD format

        Returns:
            S3 key for the index file

        """
        return f"{self.index_prefix}/{date_str}/{self.account_id}.json"

    def _load_index_for_date(self, date_str: str) -> dict[tuple[str, str], str]:
        """Load index for a specific date.

        Args:
            date_str: Date string in YYYY/MM/DD format

        Returns:
            Dictionary mapping unique keys to ledger entry IDs

        """
        if self._index_cache_date == date_str and self._index_cache is not None:
            return self._index_cache

        try:
            index_key = self._get_index_key(date_str)
            response = self.s3.get_object(Bucket=self.bucket, Key=index_key)
            index_data = json.loads(response["Body"].read().decode("utf-8"))

            # Convert string keys back to tuples
            index = {tuple(key.split("||")): value for key, value in index_data.items()}

            # Cache the loaded index
            self._index_cache = index
            self._index_cache_date = date_str

            return index

        except self.s3.exceptions.NoSuchKey:
            # Index doesn't exist yet
            empty_index: dict[tuple[str, str], str] = {}
            self._index_cache = empty_index
            self._index_cache_date = date_str
            return empty_index
        except Exception as e:
            logger.warning(f"Failed to load index for {date_str}, rebuilding: {e}")
            return self._rebuild_index_for_date(date_str)

    def _save_index_for_date(self, date_str: str, index: dict[tuple[str, str], str]) -> None:
        """Save index for a specific date.

        Args:
            date_str: Date string in YYYY/MM/DD format
            index: Index dictionary to save

        """
        try:
            # Convert tuple keys to strings for JSON serialization
            index_data = {"||".join(key): value for key, value in index.items()}
            index_json = json.dumps(index_data, indent=2)

            index_key = self._get_index_key(date_str)
            self.s3.put_object(
                Bucket=self.bucket,
                Key=index_key,
                Body=index_json.encode("utf-8"),
                ContentType="application/json",
            )

            # Update cache
            self._index_cache = index
            self._index_cache_date = date_str

        except Exception as e:
            logger.error(f"Failed to save index for {date_str}: {e}")
            raise

    def _rebuild_index_for_date(self, date_str: str) -> dict[tuple[str, str], str]:
        """Rebuild index for a specific date by scanning the ledger file.

        Args:
            date_str: Date string in YYYY/MM/DD format

        Returns:
            Rebuilt index dictionary

        """
        logger.info(f"Rebuilding trade ledger index for {date_str}")
        index: dict[tuple[str, str], str] = {}

        try:
            ledger_key = f"{self.ledger_prefix}/{date_str}/{self.account_id}.jsonl"
            response = self.s3.get_object(Bucket=self.bucket, Key=ledger_key)
            content = response["Body"].read().decode("utf-8")

            for line_num, line in enumerate(content.strip().split("\n"), 1):
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    if "order_id" in data and "ledger_id" in data:
                        fill_id = data.get("fill_id") or data["ledger_id"]
                        unique_key = (data["order_id"], fill_id)
                        index[unique_key] = data["ledger_id"]
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON on line {line_num}: {e}")
                except KeyError as e:
                    logger.warning(f"Missing required field on line {line_num}: {e}")

            logger.info(f"Rebuilt index for {date_str} with {len(index)} entries")
            self._save_index_for_date(date_str, index)

        except self.s3.exceptions.NoSuchKey:
            # Ledger file doesn't exist yet, empty index is correct
            logger.info(f"No ledger file found for {date_str}, using empty index")
        except Exception as e:
            logger.error(f"Failed to rebuild index for {date_str}: {e}")
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
            date_str = entry.timestamp.strftime("%Y/%m/%d")
            index = self._load_index_for_date(date_str)
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
            ledger_key = self._get_ledger_key(entry.timestamp)

            # Get existing content if file exists
            existing_content = ""
            try:
                response = self.s3.get_object(Bucket=self.bucket, Key=ledger_key)
                existing_content = response["Body"].read().decode("utf-8")
            except self.s3.exceptions.NoSuchKey:
                pass

            # Append new entry
            new_content = existing_content + json.dumps(serialized) + "\n"

            # Write back to S3
            self.s3.put_object(
                Bucket=self.bucket,
                Key=ledger_key,
                Body=new_content.encode("utf-8"),
                ContentType="application/x-jsonlines",
            )

            # Update index
            index[unique_key] = entry.ledger_id
            self._save_index_for_date(date_str, index)

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

        # Group entries by date for efficient processing
        entries_by_date: dict[str, list[TradeLedgerEntry]] = defaultdict(list)
        for entry in entries_list:
            date_str = entry.timestamp.strftime("%Y/%m/%d")
            entries_by_date[date_str].append(entry)

        # Process each date separately
        for date_str, date_entries in entries_by_date.items():
            try:
                index = self._load_index_for_date(date_str)
                new_entries = []

                # Filter out existing entries
                for entry in date_entries:
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
                    continue

                # Get existing content for this date
                ledger_key = f"{self.ledger_prefix}/{date_str}/{self.account_id}.jsonl"
                existing_content = ""
                try:
                    response = self.s3.get_object(Bucket=self.bucket, Key=ledger_key)
                    existing_content = response["Body"].read().decode("utf-8")
                except self.s3.exceptions.NoSuchKey:
                    pass

                # Append new entries
                new_lines = []
                for entry in new_entries:
                    serialized = self._serialize_entry(entry)
                    new_lines.append(json.dumps(serialized))
                    index[entry.get_unique_key()] = entry.ledger_id

                new_content = existing_content + "\n".join(new_lines) + "\n"

                # Write back to S3
                self.s3.put_object(
                    Bucket=self.bucket,
                    Key=ledger_key,
                    Body=new_content.encode("utf-8"),
                    ContentType="application/x-jsonlines",
                )

                # Save updated index
                self._save_index_for_date(date_str, index)

                logger.info(f"Added {len(new_entries)} new ledger entries for {date_str}")

            except Exception as e:
                logger.error(f"Failed to upsert entries for {date_str}: {e}")
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
            # Determine date range to scan
            start_date = filters.start_date or datetime(2020, 1, 1, tzinfo=UTC)
            end_date = filters.end_date or datetime.now(UTC)

            entries = []

            # Scan each date in the range
            current_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            while current_date <= end_date:
                date_str = current_date.strftime("%Y/%m/%d")
                date_entries = self._query_date(date_str, filters)
                entries.extend(date_entries)

                # Move to next day
                current_date = current_date.replace(day=current_date.day + 1)

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

    def _query_date(self, date_str: str, filters: TradeLedgerQuery) -> list[TradeLedgerEntry]:
        """Query entries for a specific date.

        Args:
            date_str: Date string in YYYY/MM/DD format
            filters: Query filters

        Returns:
            List of matching entries for the date

        """
        try:
            ledger_key = f"{self.ledger_prefix}/{date_str}/{self.account_id}.jsonl"
            response = self.s3.get_object(Bucket=self.bucket, Key=ledger_key)
            content = response["Body"].read().decode("utf-8")

            entries = []
            for line in content.strip().split("\n"):
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    entry = self._deserialize_entry(data)

                    if self._matches_filters(entry, filters):
                        entries.append(entry)
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Skipping invalid ledger entry: {e}")

            return entries

        except self.s3.exceptions.NoSuchKey:
            # No ledger file for this date
            return []
        except Exception as e:
            logger.error(f"Failed to query date {date_str}: {e}")
            raise

    def get_open_lots(self, strategy: str | None = None, symbol: str | None = None) -> list[Lot]:
        """Get open lots for attribution tracking.

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
            # For efficiency, we'd ideally have an order index, but for now scan recent dates
            entries = []
            end_date = datetime.now(UTC)
            start_date = end_date.replace(day=end_date.day - 30)  # Last 30 days

            current_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            while current_date <= end_date:
                date_str = current_date.strftime("%Y/%m/%d")
                date_entries = self._get_entries_by_order_for_date(date_str, order_id)
                entries.extend(date_entries)

                # Move to next day
                current_date = current_date.replace(day=current_date.day + 1)

            return sorted(entries, key=lambda e: e.timestamp)

        except Exception as e:
            logger.error(f"Failed to get ledger entries by order: {e}")
            raise

    def _get_entries_by_order_for_date(
        self, date_str: str, order_id: str
    ) -> list[TradeLedgerEntry]:
        """Get entries for a specific order and date.

        Args:
            date_str: Date string in YYYY/MM/DD format
            order_id: Order identifier

        Returns:
            List of matching entries

        """
        try:
            ledger_key = f"{self.ledger_prefix}/{date_str}/{self.account_id}.jsonl"
            response = self.s3.get_object(Bucket=self.bucket, Key=ledger_key)
            content = response["Body"].read().decode("utf-8")

            entries = []
            for line in content.strip().split("\n"):
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    if data.get("order_id") == order_id:
                        entry = self._deserialize_entry(data)
                        entries.append(entry)
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Skipping invalid ledger entry: {e}")

            return entries

        except self.s3.exceptions.NoSuchKey:
            return []
        except Exception as e:
            logger.error(f"Failed to get entries by order for {date_str}: {e}")
            raise

    def verify_integrity(self) -> bool:
        """Verify ledger integrity and consistency.

        Returns:
            True if ledger is consistent, False otherwise

        """
        try:
            # This is a simplified integrity check - in production would be more comprehensive
            logger.info("Starting S3 trade ledger integrity verification")

            # List all ledger files
            ledger_prefix = f"{self.ledger_prefix}/"
            response = self.s3.list_objects_v2(Bucket=self.bucket, Prefix=ledger_prefix)

            if "Contents" not in response:
                logger.info("No ledger files found, integrity check passed")
                return True

            total_entries = 0
            for obj in response["Contents"]:
                if obj["Key"].endswith(".jsonl"):
                    try:
                        # Verify each file can be parsed
                        obj_response = self.s3.get_object(Bucket=self.bucket, Key=obj["Key"])
                        content = obj_response["Body"].read().decode("utf-8")

                        file_entries = 0
                        for line in content.strip().split("\n"):
                            if line.strip():
                                json.loads(line)  # Verify JSON is valid
                                file_entries += 1

                        total_entries += file_entries
                        logger.debug(f"Verified {file_entries} entries in {obj['Key']}")

                    except Exception as e:
                        logger.error(f"Integrity check failed for {obj['Key']}: {e}")
                        return False

            logger.info(f"S3 ledger integrity verified: {total_entries} total entries")
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
        if symbol:
            # Single symbol analysis
            lots = self._calculate_lots_from_entries(entries)
            symbol_lots = [lot for lot in lots if lot.symbol == symbol]

            # Calculate open position metrics
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

        else:
            # Strategy total across all symbols
            all_lots = self._calculate_lots_from_entries(entries)
            open_quantity = sum(lot.remaining_quantity for lot in all_lots) or Decimal("0")
            avg_cost = None  # Can't meaningfully average across different symbols

            # Calculate total unrealized P&L across all symbols
            unrealized_pnl = Decimal("0")
            for lot in all_lots:
                current_price = current_prices.get(lot.symbol)
                if current_price and lot.remaining_quantity > 0:
                    lot_unrealized = lot.remaining_quantity * (
                        Decimal(str(current_price)) - lot.cost_basis
                    )
                    unrealized_pnl += lot_unrealized

            if unrealized_pnl == 0:
                unrealized_pnl = None

        # Calculate basic metrics
        buys = [e for e in entries if e.side == TradeSide.BUY]
        sells = [e for e in entries if e.side == TradeSide.SELL]

        total_buy_quantity = sum(buy.quantity for buy in buys) or Decimal("0")
        total_sell_quantity = sum(sell.quantity for sell in sells) or Decimal("0")
        total_fees = sum(entry.fees for entry in entries) or Decimal("0")

        # Calculate realized P&L (simplified - should use proper FIFO matching)
        total_buy_value = sum(buy.quantity * buy.price for buy in buys) or Decimal("0")
        total_sell_value = sum(sell.quantity * sell.price for sell in sells) or Decimal("0")
        realized_pnl = total_sell_value - total_buy_value

        # Count realized trades (simplified - number of sells)
        realized_trades = len(sells)

        return PerformanceSummary(
            strategy_name=strategy_name,
            symbol=symbol,
            calculation_timestamp=datetime.now(UTC).replace(microsecond=0),
            realized_pnl=realized_pnl,
            realized_trades=realized_trades,
            open_quantity=open_quantity,
            open_lots_count=len(all_lots) if symbol is None else len(symbol_lots),
            average_cost_basis=avg_cost,
            current_price=Decimal(str(current_prices[symbol])) if symbol and symbol in current_prices else None,
            unrealized_pnl=unrealized_pnl,
            total_buy_quantity=total_buy_quantity,
            total_sell_quantity=total_sell_quantity,
            total_fees=total_fees,
        )