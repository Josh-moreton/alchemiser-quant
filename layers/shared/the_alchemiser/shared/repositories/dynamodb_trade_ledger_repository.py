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
from the_alchemiser.shared.schemas.strategy_lot import StrategyLot
from the_alchemiser.shared.schemas.trade_ledger import SignalLedgerEntry, TradeLedgerEntry

logger = get_logger(__name__)

__all__ = ["DynamoDBTradeLedgerRepository"]

# DynamoDB exception types for error handling
DynamoDBException = (ClientError, BotoCoreError)

# Entity type prefix constants
SIGNAL_PREFIX = "SIGNAL#"


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
                # Add quantity and price for FIFO P&L calculation
                "quantity": str(entry.filled_qty * weight),
                "price": str(entry.fill_price),
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
            # Use the strategy GSI and filter to only return strategy-link items
            # (EntityType == 'STRATEGY_TRADE'). Main trade items use the same
            # GSI keys but do not contain `quantity`/`price`, which breaks FIFO
            # matching. Filtering avoids returning those items.
            kwargs: dict[str, Any] = {
                "IndexName": "GSI3-StrategyIndex",
                "KeyConditionExpression": "GSI3PK = :pk AND begins_with(GSI3SK, :sk)",
                "FilterExpression": "EntityType = :etype",
                "ExpressionAttributeValues": {
                    ":pk": f"STRATEGY#{strategy_name}",
                    ":sk": "TRADE#",
                    ":etype": "STRATEGY_TRADE",
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

    def _is_valid_trade_for_fifo(self, trade: dict[str, Any]) -> bool:
        """Check if a trade has required fields for FIFO P&L calculation.

        Args:
            trade: Trade item from DynamoDB

        Returns:
            True if trade has quantity and price fields, False otherwise

        """
        return trade.get("quantity") is not None and trade.get("price") is not None

    def _match_trades_fifo(self, symbol_trades: list[dict[str, Any]]) -> Decimal:
        """Match SELL trades against BUY trades using FIFO for a single symbol.

        Args:
            symbol_trades: List of trades for a single symbol (chronologically sorted)

        Returns:
            Total realized P&L from matched buy-sell pairs for this symbol

        """
        # Separate into buy and sell queues, filtering out trades without required fields
        buy_queue: list[dict[str, Any]] = []
        sell_queue: list[dict[str, Any]] = []
        skipped_count = 0

        for trade in symbol_trades:
            # Skip trades missing quantity or price (legacy data or schema mismatch)
            if not self._is_valid_trade_for_fifo(trade):
                skipped_count += 1
                logger.warning(
                    "Skipping trade missing quantity/price for FIFO matching",
                    order_id=trade.get("order_id"),
                    symbol=trade.get("symbol"),
                    direction=trade.get("direction"),
                    has_quantity=trade.get("quantity") is not None,
                    has_price=trade.get("price") is not None,
                )
                continue

            if trade["direction"] == "BUY":
                buy_queue.append(trade)
            else:
                sell_queue.append(trade)

        if skipped_count > 0:
            logger.info(
                f"Skipped {skipped_count} trades without quantity/price data",
                symbol=symbol_trades[0].get("symbol") if symbol_trades else "unknown",
            )

        # Match sells against buys using FIFO
        realized_pnl = Decimal("0")
        buy_idx = 0
        sell_idx = 0

        while buy_idx < len(buy_queue) and sell_idx < len(sell_queue):
            buy_trade = buy_queue[buy_idx]
            sell_trade = sell_queue[sell_idx]

            # Extract quantities and prices (validated above)
            buy_qty = Decimal(buy_trade["quantity"])
            sell_qty = Decimal(sell_trade["quantity"])
            buy_price = Decimal(buy_trade["price"])
            sell_price = Decimal(sell_trade["price"])

            # Enforce 1:1 matching by quantity
            if buy_qty != sell_qty:
                # Log warning but continue with partial matching to avoid blocking reports
                logger.warning(
                    "Trade quantity mismatch in FIFO matching, using minimum quantity",
                    buy_qty=str(buy_qty),
                    sell_qty=str(sell_qty),
                    buy_order_id=buy_trade.get("order_id"),
                    sell_order_id=sell_trade.get("order_id"),
                )
                # Use smaller quantity for P&L calculation
                matched_qty = min(buy_qty, sell_qty)
                realized_pnl += (sell_price - buy_price) * matched_qty
                # Advance both indices since we can't do partial lot tracking
                buy_idx += 1
                sell_idx += 1
            else:
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

    def put_signal(
        self,
        signal: SignalLedgerEntry,
        ledger_id: str,
    ) -> None:
        """Write a strategy signal to DynamoDB.

        Writes signal item with GSI keys for efficient querying by correlation_id,
        symbol, strategy, and lifecycle state.

        Args:
            signal: Signal ledger entry
            ledger_id: Ledger identifier

        """
        timestamp_str = signal.timestamp.isoformat()

        # Main signal item
        signal_item: dict[str, Any] = {
            "PK": f"{SIGNAL_PREFIX}{signal.signal_id}",
            "SK": "METADATA",
            "EntityType": "SIGNAL",
            "signal_id": signal.signal_id,
            "correlation_id": signal.correlation_id,
            "causation_id": signal.causation_id,
            "timestamp": timestamp_str,
            "strategy_name": signal.strategy_name,
            "data_source": signal.data_source,
            "symbol": signal.symbol,
            "action": signal.action,
            "target_allocation": str(signal.target_allocation),
            "reasoning": signal.reasoning,
            "lifecycle_state": signal.lifecycle_state,
            "executed_trade_ids": signal.executed_trade_ids,
            "signal_dto": signal.signal_dto,
            "created_at": signal.created_at.isoformat(),
            "ledger_id": ledger_id,
            # GSI keys for query patterns
            "GSI1PK": f"CORR#{signal.correlation_id}",
            "GSI1SK": f"{SIGNAL_PREFIX}{timestamp_str}#{signal.signal_id}",
            "GSI2PK": f"SYMBOL#{signal.symbol}",
            "GSI2SK": f"{SIGNAL_PREFIX}{timestamp_str}#{signal.signal_id}",
            "GSI3PK": f"STRATEGY#{signal.strategy_name}",
            "GSI3SK": f"{SIGNAL_PREFIX}{timestamp_str}#{signal.signal_id}",
            "GSI4PK": f"STATE#{signal.lifecycle_state}",
            "GSI4SK": f"{SIGNAL_PREFIX}{timestamp_str}#{signal.signal_id}",
        }

        # Optional fields
        if signal.signal_strength is not None:
            signal_item["signal_strength"] = str(signal.signal_strength)
        if signal.technical_indicators:
            # Convert Decimal values to strings for DynamoDB
            indicators_serialized = {}
            for symbol_key, indicators in signal.technical_indicators.items():
                indicators_serialized[symbol_key] = {
                    k: str(v) if isinstance(v, Decimal) else v for k, v in indicators.items()
                }
            signal_item["technical_indicators"] = indicators_serialized

        # Write signal item
        self._table.put_item(Item=signal_item)

        logger.info(
            "Signal written to DynamoDB",
            signal_id=signal.signal_id,
            symbol=signal.symbol,
            strategy=signal.strategy_name,
            state=signal.lifecycle_state,
        )

    def query_signals_by_correlation(
        self, correlation_id: str, limit: int | None = None
    ) -> list[dict[str, Any]]:
        """Query signals by correlation_id using GSI1.

        Args:
            correlation_id: Correlation identifier
            limit: Max items to return

        Returns:
            List of signal items (most recent first)

        """
        try:
            kwargs: dict[str, Any] = {
                "IndexName": "GSI1-CorrelationIndex",
                "KeyConditionExpression": "GSI1PK = :pk AND begins_with(GSI1SK, :sk)",
                "ExpressionAttributeValues": {
                    ":pk": f"CORR#{correlation_id}",
                    ":sk": SIGNAL_PREFIX,
                },
                "ScanIndexForward": False,  # Most recent first
            }

            if limit:
                kwargs["Limit"] = limit

            response = self._table.query(**kwargs)
            items = response.get("Items", [])
            return [dict(item) for item in items]
        except DynamoDBException as e:
            logger.error(
                "Failed to query signals by correlation",
                correlation_id=correlation_id,
                error=str(e),
            )
            return []

    def query_signals_by_symbol(
        self, symbol: str, limit: int | None = None
    ) -> list[dict[str, Any]]:
        """Query signals by symbol using GSI2.

        Args:
            symbol: Trading symbol
            limit: Max items to return

        Returns:
            List of signal items (most recent first)

        """
        try:
            kwargs: dict[str, Any] = {
                "IndexName": "GSI2-SymbolIndex",
                "KeyConditionExpression": "GSI2PK = :pk AND begins_with(GSI2SK, :sk)",
                "ExpressionAttributeValues": {
                    ":pk": f"SYMBOL#{symbol.upper()}",
                    ":sk": SIGNAL_PREFIX,
                },
                "ScanIndexForward": False,
            }

            if limit:
                kwargs["Limit"] = limit

            response = self._table.query(**kwargs)
            items = response.get("Items", [])
            return [dict(item) for item in items]
        except DynamoDBException as e:
            logger.error("Failed to query signals by symbol", symbol=symbol, error=str(e))
            return []

    def query_signals_by_strategy(
        self, strategy_name: str, limit: int | None = None
    ) -> list[dict[str, Any]]:
        """Query signals by strategy name using GSI3.

        Args:
            strategy_name: Strategy name
            limit: Max items to return

        Returns:
            List of signal items (most recent first)

        """
        try:
            kwargs: dict[str, Any] = {
                "IndexName": "GSI3-StrategyIndex",
                "KeyConditionExpression": "GSI3PK = :pk AND begins_with(GSI3SK, :sk)",
                "ExpressionAttributeValues": {
                    ":pk": f"STRATEGY#{strategy_name}",
                    ":sk": SIGNAL_PREFIX,
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
                "Failed to query signals by strategy",
                strategy_name=strategy_name,
                error=str(e),
            )
            return []

    def query_signals_by_state(
        self, lifecycle_state: str, limit: int | None = None
    ) -> list[dict[str, Any]]:
        """Query signals by lifecycle state using GSI4.

        Args:
            lifecycle_state: Lifecycle state (GENERATED, EXECUTED, IGNORED, SUPERSEDED)
            limit: Max items to return

        Returns:
            List of signal items (most recent first)

        """
        try:
            kwargs: dict[str, Any] = {
                "IndexName": "GSI4-StateIndex",
                "KeyConditionExpression": "GSI4PK = :pk AND begins_with(GSI4SK, :sk)",
                "ExpressionAttributeValues": {
                    ":pk": f"STATE#{lifecycle_state}",
                    ":sk": SIGNAL_PREFIX,
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
                "Failed to query signals by state",
                lifecycle_state=lifecycle_state,
                error=str(e),
            )
            return []

    def update_signal_lifecycle(
        self,
        signal_id: str,
        new_state: str,
        trade_ids: list[str] | None = None,
    ) -> None:
        """Update signal lifecycle state and optionally link to executed trades.

        Uses atomic list append to prevent race conditions when multiple trades
        execute concurrently for the same signal. The list_append operation ensures
        that trade IDs are appended atomically without read-modify-write races.

        Args:
            signal_id: Signal identifier
            new_state: New lifecycle state
            trade_ids: Optional list of trade IDs to atomically append to the signal's
                      executed_trade_ids list. Each trade ID will be appended individually
                      to support concurrent updates.

        """
        try:
            update_expression = "SET lifecycle_state = :state, GSI4PK = :gsi4pk, GSI4SK = :gsi4sk"
            expression_values: dict[str, Any] = {
                ":state": new_state,
                ":gsi4pk": f"STATE#{new_state}",
            }

            # Get current item to extract timestamp for GSI4SK
            response = self._table.get_item(
                Key={"PK": f"{SIGNAL_PREFIX}{signal_id}", "SK": "METADATA"}
            )
            item = response.get("Item")
            if not item:
                logger.warning(f"Signal {signal_id} not found for lifecycle update")
                return

            timestamp_str = str(item.get("timestamp", datetime.now(UTC).isoformat()))
            expression_values[":gsi4sk"] = f"{SIGNAL_PREFIX}{timestamp_str}#{signal_id}"

            if trade_ids is not None:
                # Use SET with list_append for atomic append operation
                # This prevents race conditions when multiple trades execute concurrently
                update_expression += (
                    ", executed_trade_ids = "
                    "list_append(if_not_exists(executed_trade_ids, :empty_list), :trade_ids)"
                )
                expression_values[":trade_ids"] = trade_ids
                expression_values[":empty_list"] = []

            self._table.update_item(
                Key={"PK": f"{SIGNAL_PREFIX}{signal_id}", "SK": "METADATA"},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values,
            )

            logger.info(
                "Signal lifecycle updated",
                signal_id=signal_id,
                new_state=new_state,
                trade_count=len(trade_ids) if trade_ids else 0,
            )

        except DynamoDBException as e:
            logger.error(
                "Failed to update signal lifecycle",
                signal_id=signal_id,
                new_state=new_state,
                error=str(e),
            )

    def compute_signal_execution_rate(self, strategy_name: str) -> dict[str, Any]:
        """Compute signal execution rate for a strategy.

        Calculates the percentage of signals that resulted in trades.

        Args:
            strategy_name: Strategy name

        Returns:
            Dictionary with execution rate metrics

        """
        signals = self.query_signals_by_strategy(strategy_name)

        if not signals:
            return {
                "strategy_name": strategy_name,
                "total_signals": 0,
                "executed_signals": 0,
                "ignored_signals": 0,
                "execution_rate": Decimal("0"),
            }

        executed_count = sum(1 for s in signals if s.get("lifecycle_state") == "EXECUTED")
        ignored_count = sum(1 for s in signals if s.get("lifecycle_state") == "IGNORED")

        execution_rate = (
            Decimal(str(executed_count)) / Decimal(str(len(signals)))
            if len(signals) > 0
            else Decimal("0")
        )

        return {
            "strategy_name": strategy_name,
            "total_signals": len(signals),
            "executed_signals": executed_count,
            "ignored_signals": ignored_count,
            "execution_rate": execution_rate,
        }

    # =========================================================================
    # Strategy Lot Methods - Per-strategy position tracking for accurate P&L
    # =========================================================================

    def put_lot(self, lot: StrategyLot) -> None:
        """Write a strategy lot to DynamoDB.

        Creates the lot item with GSI keys for querying by strategy and symbol.

        Args:
            lot: StrategyLot to persist

        """
        try:
            item = lot.to_dynamodb_item()
            self._table.put_item(Item=item)

            logger.info(
                "Strategy lot written to DynamoDB",
                lot_id=lot.lot_id,
                strategy=lot.strategy_name,
                symbol=lot.symbol,
                entry_qty=str(lot.entry_qty),
            )
        except DynamoDBException as e:
            logger.error(
                "Failed to write strategy lot",
                lot_id=lot.lot_id,
                error=str(e),
            )
            raise

    def get_lot(self, lot_id: str) -> StrategyLot | None:
        """Get a strategy lot by ID.

        Args:
            lot_id: Lot identifier

        Returns:
            StrategyLot or None if not found

        """
        try:
            response = self._table.get_item(Key={"PK": f"LOT#{lot_id}", "SK": "METADATA"})
            item = response.get("Item")
            if not item:
                return None
            return StrategyLot.from_dynamodb_item(item)
        except DynamoDBException as e:
            logger.error("Failed to get lot", lot_id=lot_id, error=str(e))
            return None

    def update_lot(self, lot: StrategyLot) -> None:
        """Update an existing strategy lot in DynamoDB.

        Overwrites the lot item with the current state.

        Args:
            lot: StrategyLot with updated state

        """
        try:
            item = lot.to_dynamodb_item()
            self._table.put_item(Item=item)

            logger.debug(
                "Strategy lot updated",
                lot_id=lot.lot_id,
                remaining_qty=str(lot.remaining_qty),
                is_open=lot.is_open,
            )
        except DynamoDBException as e:
            logger.error(
                "Failed to update strategy lot",
                lot_id=lot.lot_id,
                error=str(e),
            )
            raise

    def query_open_lots_by_strategy_and_symbol(
        self, strategy_name: str, symbol: str
    ) -> list[StrategyLot]:
        """Query open lots for a strategy and symbol.

        Returns lots in FIFO order (oldest first) for exit matching.

        Args:
            strategy_name: Strategy name
            symbol: Trading symbol

        Returns:
            List of open StrategyLots in FIFO order

        """
        try:
            # Query using GSI5 (STRATEGY_LOTS#strategy -> OPEN#symbol#timestamp)
            response = self._table.query(
                IndexName="GSI5-StrategyLotsIndex",
                KeyConditionExpression="GSI5PK = :pk AND begins_with(GSI5SK, :sk)",
                ExpressionAttributeValues={
                    ":pk": f"STRATEGY_LOTS#{strategy_name}",
                    ":sk": f"OPEN#{symbol.upper()}#",
                },
                ScanIndexForward=True,  # Oldest first for FIFO
            )

            items = response.get("Items", [])
            lots = []
            for item in items:
                try:
                    lot = StrategyLot.from_dynamodb_item(item)
                    lots.append(lot)
                except Exception as e:
                    logger.warning(f"Failed to parse lot item: {e}")

            return lots
        except DynamoDBException as e:
            logger.error(
                "Failed to query open lots",
                strategy=strategy_name,
                symbol=symbol,
                error=str(e),
            )
            return []

    def query_closed_lots_by_strategy(
        self, strategy_name: str, limit: int | None = None
    ) -> list[StrategyLot]:
        """Query closed lots for a strategy.

        Returns closed lots for P&L reporting.

        Args:
            strategy_name: Strategy name
            limit: Max items to return

        Returns:
            List of closed StrategyLots (most recently closed first)

        """
        try:
            kwargs: dict[str, Any] = {
                "IndexName": "GSI5-StrategyLotsIndex",
                "KeyConditionExpression": "GSI5PK = :pk AND begins_with(GSI5SK, :sk)",
                "ExpressionAttributeValues": {
                    ":pk": f"STRATEGY_LOTS#{strategy_name}",
                    ":sk": "CLOSED#",
                },
                "ScanIndexForward": False,  # Most recent first
            }

            if limit:
                kwargs["Limit"] = limit

            response = self._table.query(**kwargs)
            items = response.get("Items", [])

            lots = []
            for item in items:
                try:
                    lot = StrategyLot.from_dynamodb_item(item)
                    lots.append(lot)
                except Exception as e:
                    logger.warning(f"Failed to parse lot item: {e}")

            return lots
        except DynamoDBException as e:
            logger.error(
                "Failed to query closed lots",
                strategy=strategy_name,
                error=str(e),
            )
            return []

    def query_all_lots_by_strategy(
        self, strategy_name: str, limit: int | None = None
    ) -> list[StrategyLot]:
        """Query all lots (open and closed) for a strategy.

        Args:
            strategy_name: Strategy name
            limit: Max items to return

        Returns:
            List of all StrategyLots for the strategy

        """
        try:
            kwargs: dict[str, Any] = {
                "IndexName": "GSI5-StrategyLotsIndex",
                "KeyConditionExpression": "GSI5PK = :pk",
                "ExpressionAttributeValues": {
                    ":pk": f"STRATEGY_LOTS#{strategy_name}",
                },
                "ScanIndexForward": False,
            }

            if limit:
                kwargs["Limit"] = limit

            response = self._table.query(**kwargs)
            items = response.get("Items", [])

            lots = []
            for item in items:
                try:
                    lot = StrategyLot.from_dynamodb_item(item)
                    lots.append(lot)
                except Exception as e:
                    logger.warning(f"Failed to parse lot item: {e}")

            return lots
        except DynamoDBException as e:
            logger.error(
                "Failed to query all lots",
                strategy=strategy_name,
                error=str(e),
            )
            return []

    def discover_strategies_with_closed_lots(self) -> list[str]:
        """Discover all strategies that have closed lots.

        Scans for unique strategy names from closed lot items.

        Returns:
            List of unique strategy names with closed lots

        """
        try:
            # Scan for all LOT# items that are closed
            response = self._table.scan(
                FilterExpression="begins_with(PK, :pk) AND is_open = :open",
                ExpressionAttributeValues={
                    ":pk": "LOT#",
                    ":open": False,
                },
                ProjectionExpression="strategy_name",
            )

            strategy_names: set[str] = set()
            for item in response.get("Items", []):
                strategy_name = item.get("strategy_name")
                if strategy_name and isinstance(strategy_name, str):
                    strategy_names.add(strategy_name)

            # Handle pagination
            while "LastEvaluatedKey" in response:
                response = self._table.scan(
                    FilterExpression="begins_with(PK, :pk) AND is_open = :open",
                    ExpressionAttributeValues={
                        ":pk": "LOT#",
                        ":open": False,
                    },
                    ProjectionExpression="strategy_name",
                    ExclusiveStartKey=response["LastEvaluatedKey"],
                )
                for item in response.get("Items", []):
                    strategy_name = item.get("strategy_name")
                    if strategy_name and isinstance(strategy_name, str):
                        strategy_names.add(strategy_name)

            return sorted(strategy_names)
        except DynamoDBException as e:
            logger.error(f"Failed to discover strategies with closed lots: {e}")
            return []

    def discover_strategies_with_completed_trades(self) -> list[str]:
        """Discover all strategies that have completed trades (exit records).

        Scans for unique strategy names from lots that have at least one exit record.
        This is the correct method for P&L reporting - a completed trade is any exit,
        regardless of whether the lot still has remaining shares.

        Returns:
            List of unique strategy names with completed trades

        """
        try:
            # Scan for all LOT# items that have exit_records
            response = self._table.scan(
                FilterExpression="begins_with(PK, :pk) AND size(exit_records) > :zero",
                ExpressionAttributeValues={
                    ":pk": "LOT#",
                    ":zero": 0,
                },
                ProjectionExpression="strategy_name",
            )

            strategy_names: set[str] = set()
            for item in response.get("Items", []):
                strategy_name = item.get("strategy_name")
                if strategy_name and isinstance(strategy_name, str):
                    strategy_names.add(strategy_name)

            # Handle pagination
            while "LastEvaluatedKey" in response:
                response = self._table.scan(
                    FilterExpression="begins_with(PK, :pk) AND size(exit_records) > :zero",
                    ExpressionAttributeValues={
                        ":pk": "LOT#",
                        ":zero": 0,
                    },
                    ProjectionExpression="strategy_name",
                    ExclusiveStartKey=response["LastEvaluatedKey"],
                )
                for item in response.get("Items", []):
                    strategy_name = item.get("strategy_name")
                    if strategy_name and isinstance(strategy_name, str):
                        strategy_names.add(strategy_name)

            return sorted(strategy_names)
        except DynamoDBException as e:
            logger.error(f"Failed to discover strategies with completed trades: {e}")
            return []

    # ========================================================================
    # Strategy Metadata Operations
    # ========================================================================

    def put_strategy_metadata(
        self,
        strategy_name: str,
        display_name: str,
        source_url: str,
        filename: str,
        assets: list[str],
        frontrunners: list[str] | None = None,
        date_updated: str | None = None,
    ) -> None:
        """Write strategy metadata to DynamoDB.

        Creates a STRATEGY_METADATA item with the strategy definition.
        This syncs the strategy ledger YAML to DynamoDB for web UI access.

        The strategy_name is the filename stem (e.g., 'rain' from 'rain.clj')
        which matches the runtime attribution used throughout the system.

        Args:
            strategy_name: Unique strategy identifier (filename stem, matches runtime)
            display_name: Human-readable name from defsymphony declaration
            source_url: Original Composer symphony URL
            filename: Local .clj filename
            assets: List of asset tickers traded by this strategy
            frontrunners: List of frontrunner tickers (used in indicators only)
            date_updated: Last update date (YYYY-MM-DD format)

        """
        now = datetime.now(UTC)

        item: dict[str, Any] = {
            "PK": f"STRATEGY#{strategy_name}",
            "SK": "METADATA",
            "EntityType": "STRATEGY_METADATA",
            "strategy_name": strategy_name,
            "display_name": display_name,
            "source_url": source_url,
            "filename": filename,
            "assets": assets,
            "frontrunners": frontrunners or [],
            "date_updated": date_updated or now.strftime("%Y-%m-%d"),
            "synced_at": now.isoformat(),
            # GSI3 allows listing all strategies
            "GSI3PK": "STRATEGIES",
            "GSI3SK": f"METADATA#{strategy_name}",
        }

        try:
            self._table.put_item(Item=item)
            logger.info(
                "Strategy metadata written to DynamoDB",
                strategy_name=strategy_name,
                display_name=display_name,
                assets_count=len(assets),
            )
        except DynamoDBException as e:
            logger.error(
                "Failed to write strategy metadata",
                strategy_name=strategy_name,
                error=str(e),
            )
            raise

    def get_strategy_metadata(self, strategy_name: str) -> dict[str, Any] | None:
        """Get strategy metadata by name.

        Args:
            strategy_name: Strategy name (filename stem)

        Returns:
            Strategy metadata dict or None if not found

        """
        try:
            response = self._table.get_item(
                Key={"PK": f"STRATEGY#{strategy_name}", "SK": "METADATA"}
            )
            item = response.get("Item")
            return dict(item) if item else None
        except DynamoDBException as e:
            logger.error(
                "Failed to get strategy metadata",
                strategy_name=strategy_name,
                error=str(e),
            )
            return None

    def list_strategy_metadata(self) -> list[dict[str, Any]]:
        """List all strategy metadata records.

        Uses GSI3 to efficiently query all STRATEGY_METADATA items.

        Returns:
            List of strategy metadata dicts

        """
        try:
            response = self._table.query(
                IndexName="GSI3-StrategyIndex",
                KeyConditionExpression="GSI3PK = :pk",
                ExpressionAttributeValues={":pk": "STRATEGIES"},
            )

            items = response.get("Items", [])

            # Handle pagination
            while "LastEvaluatedKey" in response:
                response = self._table.query(
                    IndexName="GSI3-StrategyIndex",
                    KeyConditionExpression="GSI3PK = :pk",
                    ExpressionAttributeValues={":pk": "STRATEGIES"},
                    ExclusiveStartKey=response["LastEvaluatedKey"],
                )
                items.extend(response.get("Items", []))

            return [dict(item) for item in items]
        except DynamoDBException as e:
            logger.error(f"Failed to list strategy metadata: {e}")
            return []

    def delete_strategy_metadata(self, strategy_name: str) -> bool:
        """Delete strategy metadata by name.

        Args:
            strategy_name: Strategy name (filename stem)

        Returns:
            True if deleted, False on error

        """
        try:
            self._table.delete_item(Key={"PK": f"STRATEGY#{strategy_name}", "SK": "METADATA"})
            logger.info("Strategy metadata deleted", strategy_name=strategy_name)
            return True
        except DynamoDBException as e:
            logger.error(
                "Failed to delete strategy metadata",
                strategy_name=strategy_name,
                error=str(e),
            )
            return False

    def get_strategy_summary(self, strategy_name: str) -> dict[str, Any]:
        """Get aggregated statistics for a strategy.

        Calculates comprehensive metrics from all lots for the strategy.
        Each exit_record represents a completed trade - when the strategy
        decided to close a position. Strategies are always 100% allocated,
        so every exit is a complete trade decision from the strategy's perspective.

        Args:
            strategy_name: Strategy name (filename stem)

        Returns:
            Dict with keys:
                - current_holdings: Number of lots with remaining position
                - current_holdings_value: Cost basis of remaining positions
                - completed_trades: Number of closed trades (exit records)
                - total_realized_pnl: Sum of realized P&L from all closed trades
                - winning_trades: Count of trades with positive P&L
                - losing_trades: Count of trades with negative or zero P&L
                - win_rate: Percentage of winning trades (0-100)
                - avg_profit_per_trade: Average realized P&L per closed trade

        """
        from decimal import Decimal

        lots = self.query_all_lots_by_strategy(strategy_name)

        current_holdings = 0
        current_holdings_value = Decimal("0")
        total_realized_pnl = Decimal("0")
        winning_trades = 0
        losing_trades = 0

        for lot in lots:
            # Track current holdings (lots with remaining position)
            if lot.remaining_qty > 0:
                current_holdings += 1
                current_holdings_value += lot.remaining_qty * lot.entry_price

            # Each exit_record is a completed trade - strategy closed that position
            for exit_record in lot.exit_records:
                pnl = exit_record.realized_pnl
                total_realized_pnl += pnl
                if pnl > 0:
                    winning_trades += 1
                else:
                    losing_trades += 1

        completed_trades = winning_trades + losing_trades
        win_rate = (
            (winning_trades / completed_trades * 100) if completed_trades > 0 else Decimal("0")
        )
        avg_profit = (
            (total_realized_pnl / completed_trades) if completed_trades > 0 else Decimal("0")
        )

        return {
            "strategy_name": strategy_name,
            "current_holdings": current_holdings,
            "current_holdings_value": current_holdings_value,
            "completed_trades": completed_trades,
            "total_realized_pnl": total_realized_pnl,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": Decimal(str(win_rate)),
            "avg_profit_per_trade": avg_profit,
        }

    def get_all_strategy_summaries(self) -> list[dict[str, Any]]:
        """Get aggregated statistics for all strategies.

        Returns:
            List of strategy summary dicts

        """
        # Get all registered strategies from metadata
        metadata_list = self.list_strategy_metadata()
        strategy_names: set[str] = set()
        for m in metadata_list:
            name = m.get("strategy_name")
            if name and isinstance(name, str):
                strategy_names.add(name)

        # Also include strategies with lots but no metadata (shouldn't happen, but be safe)
        strategies_with_lots: set[str] = set(self.discover_strategies_with_closed_lots())

        # Query for strategies with open lots too
        try:
            response = self._table.scan(
                FilterExpression="begins_with(PK, :pk) AND is_open = :open",
                ExpressionAttributeValues={
                    ":pk": "LOT#",
                    ":open": True,
                },
                ProjectionExpression="strategy_name",
            )
            for item in response.get("Items", []):
                name = item.get("strategy_name")
                if name and isinstance(name, str):
                    strategies_with_lots.add(name)
        except DynamoDBException:
            pass  # Best effort

        all_strategies = strategy_names | strategies_with_lots
        summaries = []

        for strategy_name in sorted(all_strategies):
            summary = self.get_strategy_summary(strategy_name)
            summaries.append(summary)

        return summaries
