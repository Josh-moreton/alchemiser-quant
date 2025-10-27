"""Business Unit: shared | Status: current.

DynamoDB repository for trade ledger.

Implements single-table design with global secondary indexes for efficient
querying by correlation_id, symbol, and strategy name.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from botocore.exceptions import BotoCoreError, ClientError

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.trade_ledger import TradeLedgerEntry

logger = get_logger(__name__)

__all__ = ["DynamoDBTradeLedgerRepository"]

# DynamoDB exception types for error handling
DynamoDBException = (ClientError, BotoCoreError)


class DynamoDBTradeLedgerRepository:
    """Repository for trade ledger using DynamoDB single-table design.

    Table structure:
    - Main table: PK (partition key), SK (sort key)
    - GSI1: Query by correlation_id + timestamp
    - GSI2: Query by symbol + timestamp
    - GSI3: Query by strategy + timestamp

    Entity types:
    - TRADE: Main trade record
    - STRATEGY_TRADE: Strategy attribution link
    """

    def __init__(self, table_name: str) -> None:
        """Initialize repository.

        Args:
            table_name: DynamoDB table name

        """
        import boto3

        self._dynamodb = boto3.resource("dynamodb")
        self._table = self._dynamodb.Table(table_name)
        logger.debug("Initialized DynamoDB trade ledger repository", table=table_name)

    def put_trade(self, entry: TradeLedgerEntry, ledger_id: str) -> None:
        """Write a trade entry to DynamoDB.

        Writes:
        1. Main trade item (PK=TRADE#{order_id}, SK=METADATA)
        2. Strategy link items for each strategy (PK=STRATEGY#{name}, SK=TRADE#{timestamp}#{order_id})

        Args:
            entry: Trade ledger entry
            ledger_id: Ledger identifier

        """
        timestamp_str = entry.fill_timestamp.isoformat()

        # Main trade item
        trade_item: dict[str, Any] = {
            "PK": f"TRADE#{entry.order_id}",
            "SK": "METADATA",
            "EntityType": "TRADE",
            "order_id": entry.order_id,
            "correlation_id": entry.correlation_id,
            "ledger_id": ledger_id,
            "symbol": entry.symbol,
            "direction": entry.direction,
            "filled_qty": str(entry.filled_qty),
            "fill_price": str(entry.fill_price),
            "fill_timestamp": timestamp_str,
            "order_type": entry.order_type,
            "strategy_names": entry.strategy_names if entry.strategy_names else [],
            "created_at": datetime.now(UTC).isoformat(),
            # GSI keys for access patterns
            "GSI1PK": f"CORR#{entry.correlation_id}",
            "GSI1SK": f"TRADE#{timestamp_str}#{entry.order_id}",
            "GSI2PK": f"SYMBOL#{entry.symbol}",
            "GSI2SK": f"TRADE#{timestamp_str}#{entry.order_id}",
        }

        # Optional fields
        if entry.bid_at_fill:
            trade_item["bid_at_fill"] = str(entry.bid_at_fill)
        if entry.ask_at_fill:
            trade_item["ask_at_fill"] = str(entry.ask_at_fill)
        if entry.strategy_weights:
            # Store as dict[str, str] for DynamoDB
            trade_item["strategy_weights"] = {k: str(v) for k, v in entry.strategy_weights.items()}

        # Write main trade item
        self._table.put_item(Item=trade_item)

        # Write strategy link items
        if entry.strategy_names:
            self._write_strategy_links(entry, timestamp_str)

        logger.info(
            "Trade written to DynamoDB",
            order_id=entry.order_id,
            symbol=entry.symbol,
            strategies=entry.strategy_names,
        )

    def _write_strategy_links(self, entry: TradeLedgerEntry, timestamp_str: str) -> None:
        """Write strategy-trade link items for multi-strategy attribution.

        Args:
            entry: Trade ledger entry
            timestamp_str: ISO formatted timestamp

        """
        trade_value = entry.filled_qty * entry.fill_price

        for strategy_name in entry.strategy_names:
            weight = (
                entry.strategy_weights.get(strategy_name, Decimal("1.0"))
                if entry.strategy_weights
                else Decimal("1.0")
            )
            strategy_trade_value = trade_value * weight

            strategy_item = {
                "PK": f"STRATEGY#{strategy_name}",
                "SK": f"TRADE#{timestamp_str}#{entry.order_id}",
                "EntityType": "STRATEGY_TRADE",
                "strategy_name": strategy_name,
                "order_id": entry.order_id,
                "symbol": entry.symbol,
                "direction": entry.direction,
                "weight": str(weight),
                "strategy_trade_value": str(strategy_trade_value),
                "fill_timestamp": timestamp_str,
                "created_at": datetime.now(UTC).isoformat(),
                # GSI3 for strategy queries
                "GSI3PK": f"STRATEGY#{strategy_name}",
                "GSI3SK": f"TRADE#{timestamp_str}#{entry.order_id}",
            }

            self._table.put_item(Item=strategy_item)

    def get_trade(self, order_id: str) -> dict[str, Any] | None:
        """Get a trade by order_id.

        Args:
            order_id: Order identifier

        Returns:
            Trade item dict or None

        """
        try:
            response = self._table.get_item(Key={"PK": f"TRADE#{order_id}", "SK": "METADATA"})
            item = response.get("Item")
            return dict(item) if item else None
        except DynamoDBException as e:
            logger.error("Failed to get trade", order_id=order_id, error=str(e))
            return None

    def query_trades_by_correlation(
        self, correlation_id: str, limit: int | None = None
    ) -> list[dict[str, Any]]:
        """Query trades by correlation_id using GSI1.

        Args:
            correlation_id: Correlation identifier
            limit: Max items to return

        Returns:
            List of trade items (most recent first)

        """
        try:
            kwargs: dict[str, Any] = {
                "IndexName": "GSI1-CorrelationIndex",
                "KeyConditionExpression": "GSI1PK = :pk",
                "ExpressionAttributeValues": {":pk": f"CORR#{correlation_id}"},
                "ScanIndexForward": False,  # Most recent first
            }

            if limit:
                kwargs["Limit"] = limit

            response = self._table.query(**kwargs)
            items = response.get("Items", [])
            return [dict(item) for item in items]
        except DynamoDBException as e:
            logger.error(
                "Failed to query trades by correlation",
                correlation_id=correlation_id,
                error=str(e),
            )
            return []

    def query_trades_by_symbol(self, symbol: str, limit: int | None = None) -> list[dict[str, Any]]:
        """Query trades by symbol using GSI2.

        Args:
            symbol: Trading symbol
            limit: Max items to return

        Returns:
            List of trade items (most recent first)

        """
        try:
            kwargs: dict[str, Any] = {
                "IndexName": "GSI2-SymbolIndex",
                "KeyConditionExpression": "GSI2PK = :pk",
                "ExpressionAttributeValues": {":pk": f"SYMBOL#{symbol.upper()}"},
                "ScanIndexForward": False,
            }

            if limit:
                kwargs["Limit"] = limit

            response = self._table.query(**kwargs)
            items = response.get("Items", [])
            return [dict(item) for item in items]
        except DynamoDBException as e:
            logger.error("Failed to query trades by symbol", symbol=symbol, error=str(e))
            return []

    def query_trades_by_strategy(
        self, strategy_name: str, limit: int | None = None
    ) -> list[dict[str, Any]]:
        """Query strategy-trade links by strategy name.

        Args:
            strategy_name: Strategy name
            limit: Max items to return

        Returns:
            List of strategy-trade link items (most recent first)

        """
        try:
            kwargs: dict[str, Any] = {
                "KeyConditionExpression": "PK = :pk AND begins_with(SK, :sk)",
                "ExpressionAttributeValues": {
                    ":pk": f"STRATEGY#{strategy_name}",
                    ":sk": "TRADE#",
                },
                "ScanIndexForward": False,
            }

            if limit:
                kwargs["Limit"] = limit

            response = self._table.query(**kwargs)
            items = response.get("Items", [])
            return [dict(item) for item in items]
        except DynamoDBException as e:
            logger.error(
                "Failed to query trades by strategy",
                strategy_name=strategy_name,
                error=str(e),
            )
            return []

    def _group_trades_by_symbol(
        self, items: list[dict[str, Any]]
    ) -> dict[str, list[dict[str, Any]]]:
        """Group trades by symbol for per-symbol FIFO matching.

        Args:
            items: List of sorted strategy-trade items

        Returns:
            Dictionary mapping symbol to list of trades for that symbol

        """
        trades_by_symbol: dict[str, list[dict[str, Any]]] = {}
        for item in items:
            symbol = item["symbol"]
            if symbol not in trades_by_symbol:
                trades_by_symbol[symbol] = []
            trades_by_symbol[symbol].append(item)
        return trades_by_symbol

    def _match_trades_fifo(self, symbol_trades: list[dict[str, Any]]) -> Decimal:
        """Match SELL trades against BUY trades using FIFO for a single symbol.

        Args:
            symbol_trades: List of trades for a single symbol (chronologically sorted)

        Returns:
            Total realized P&L from matched buy-sell pairs for this symbol

        """
        # Separate into buy and sell queues
        buy_queue: list[dict[str, Any]] = []
        sell_queue: list[dict[str, Any]] = []

        for trade in symbol_trades:
            if trade["direction"] == "BUY":
                buy_queue.append(trade)
            else:
                sell_queue.append(trade)

        # Match sells against buys using FIFO
        realized_pnl = Decimal("0")
        buy_idx = 0
        sell_idx = 0

        while buy_idx < len(buy_queue) and sell_idx < len(sell_queue):
            buy_trade = buy_queue[buy_idx]
            sell_trade = sell_queue[sell_idx]

            # Extract and validate quantities and prices
            buy_qty_raw = buy_trade.get("quantity")
            sell_qty_raw = sell_trade.get("quantity")
            buy_price_raw = buy_trade.get("price")
            sell_price_raw = sell_trade.get("price")

            if buy_qty_raw is None or sell_qty_raw is None:
                raise ValueError(
                    f"Missing quantity in trade data: buy={buy_qty_raw}, sell={sell_qty_raw}"
                )
            if buy_price_raw is None or sell_price_raw is None:
                raise ValueError(
                    f"Missing price in trade data: buy={buy_price_raw}, sell={sell_price_raw}"
                )

            buy_qty = Decimal(buy_qty_raw)
            sell_qty = Decimal(sell_qty_raw)
            buy_price = Decimal(buy_price_raw)
            sell_price = Decimal(sell_price_raw)

            # Enforce 1:1 matching by quantity
            if buy_qty != sell_qty:
                raise ValueError(
                    f"Trade quantity mismatch in FIFO matching: buy_qty={buy_qty}, sell_qty={sell_qty}. "
                    "Trades must be matched 1:1 by quantity. Ensure input data is pre-aggregated or weighted appropriately."
                )

            realized_pnl += (sell_price - buy_price) * buy_qty
            buy_idx += 1
            sell_idx += 1

        return realized_pnl

    def _calculate_realized_pnl_fifo(self, items: list[dict[str, Any]]) -> Decimal:
        """Calculate realized P&L using FIFO (First-In-First-Out) matching.

        Matches SELL trades against BUY trades chronologically to compute
        realized gains/losses. This implementation operates on weighted
        strategy trade values.

        Assumptions:
        - Each trade in the list represents a complete position entry/exit
        - Trades are matched 1:1 (one sell matched to one buy)
        - strategy_trade_value already accounts for weighted quantities
        - Partial fills are not tracked; each trade is treated as atomic

        Note: A more sophisticated implementation could track quantities and
        handle partial position closes, but this simplified approach is
        appropriate for strategy-level P&L tracking where weighted values
        are already computed.

        Args:
            items: List of strategy-trade items with direction, value, and timestamp

        Returns:
            Total realized P&L from matched buy-sell pairs

        """
        # Sort items by timestamp to ensure chronological FIFO matching.
        # ISO 8601 format strings (e.g., '2025-01-15T14:30:00Z') sort correctly
        # lexicographically, ensuring proper chronological order.
        sorted_items = sorted(items, key=lambda x: x["fill_timestamp"])

        # Group trades by symbol for per-symbol FIFO matching
        trades_by_symbol = self._group_trades_by_symbol(sorted_items)

        # Process each symbol independently and sum realized P&L
        total_realized_pnl = Decimal("0")
        for symbol_trades in trades_by_symbol.values():
            total_realized_pnl += self._match_trades_fifo(symbol_trades)

        return total_realized_pnl

    def compute_strategy_performance(self, strategy_name: str) -> dict[str, Any]:
        """Compute performance metrics for a strategy.

        Queries all strategy-trade links and aggregates in-memory.
        Calculates realized P&L using FIFO matched-pair logic.

        Args:
            strategy_name: Strategy name

        Returns:
            Performance metrics dict

        """
        items = self.query_trades_by_strategy(strategy_name)

        if not items:
            return {
                "strategy_name": strategy_name,
                "total_trades": 0,
                "buy_trades": 0,
                "sell_trades": 0,
                "total_buy_value": Decimal("0"),
                "total_sell_value": Decimal("0"),
                "gross_pnl": Decimal("0"),
                "realized_pnl": Decimal("0"),
                "symbols_traded": [],
                "first_trade_at": None,
                "last_trade_at": None,
            }

        buy_count = 0
        sell_count = 0
        buy_value = Decimal("0")
        sell_value = Decimal("0")
        symbols = set()
        timestamps = []

        for item in items:
            direction = item["direction"]
            value = Decimal(item["strategy_trade_value"])
            symbols.add(item["symbol"])
            timestamps.append(item["fill_timestamp"])

            if direction == "BUY":
                buy_count += 1
                buy_value += value
            else:
                sell_count += 1
                sell_value += value

        # Calculate realized P&L using FIFO matched-pair logic
        realized_pnl = self._calculate_realized_pnl_fifo(items)

        return {
            "strategy_name": strategy_name,
            "total_trades": len(items),
            "buy_trades": buy_count,
            "sell_trades": sell_count,
            "total_buy_value": buy_value,
            "total_sell_value": sell_value,
            "gross_pnl": sell_value - buy_value,
            "realized_pnl": realized_pnl,
            "symbols_traded": sorted(symbols),
            "first_trade_at": min(timestamps) if timestamps else None,
            "last_trade_at": max(timestamps) if timestamps else None,
        }
