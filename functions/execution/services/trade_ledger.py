"""Business Unit: execution | Status: current.

Trade ledger service for recording filled orders.

This service captures trade execution details including fill price, bid/ask spreads,
quantities, and strategy attribution. It handles cases where market data may not be
fully available without blocking the recording of core trade information.

Trade ledger entries are persisted to DynamoDB for historical analysis and audit purposes.

FEATURES IMPLEMENTED:
=====================
- Quote data capture: Integrated with pricing_service when available
- Order type detection: Extracts actual order type (MARKET, LIMIT, etc.) from OrderResult
- Fill timestamp: Uses filled_at when available, falls back to order placement timestamp
- Strategy attribution: Multi-strategy aggregation support
- Validation: Zero quantity, invalid actions, price checks
- DynamoDB persistence: Single-table design with GSIs for efficient querying
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Literal

from botocore.exceptions import BotoCoreError, ClientError
from pydantic import ValidationError

from the_alchemiser.shared.config.config import load_settings
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.repositories.dynamodb_trade_ledger_repository import (
    DynamoDBTradeLedgerRepository,
)
from the_alchemiser.shared.schemas.strategy_lot import StrategyLot
from the_alchemiser.shared.schemas.trade_ledger import TradeLedger, TradeLedgerEntry
from the_alchemiser.shared.utils.order_id_utils import parse_client_order_id

if TYPE_CHECKING:
    from models.execution_result import OrderResult

    from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlan
    from the_alchemiser.shared.types.market_data import QuoteModel

logger = get_logger(__name__)

__all__ = ["TradeLedgerService"]

# DynamoDB exception types for error handling
DynamoDBException = (ClientError, BotoCoreError)


class TradeLedgerService:
    """Service for recording filled orders to trade ledger.

    Captures order execution details with strategy attribution and market data
    when available. Supports multi-strategy aggregation where multiple strategies
    suggest the same symbol.

    Persists trade ledger entries to DynamoDB for historical analysis and audit purposes.
    """

    def __init__(self) -> None:
        """Initialize the trade ledger service."""
        self._ledger_id = str(uuid.uuid4())
        self._entries: list[TradeLedgerEntry] = []  # In-memory for current run
        self._created_at = datetime.now(UTC)
        self._settings = load_settings()

        # Initialize DynamoDB repository
        table_name = self._settings.trade_ledger.table_name
        if not table_name:
            logger.warning("TRADE_LEDGER__TABLE_NAME not set - trade ledger disabled")
            self._repository = None
        else:
            self._repository = DynamoDBTradeLedgerRepository(table_name)
            logger.info("Trade ledger initialized", table=table_name)

    def record_filled_order(
        self,
        order_result: OrderResult,
        correlation_id: str,
        rebalance_plan: RebalancePlan | None = None,
        quote_at_fill: QuoteModel | None = None,
        strategy_attribution: dict[str, dict[str, float]] | None = None,
        execution_quality: dict[str, Any] | None = None,
        strategy_id: str | None = None,
    ) -> TradeLedgerEntry | None:
        """Record a filled order to the trade ledger.

        Writes to both:
        1. In-memory list (for current run queries)
        2. DynamoDB (persistent storage)

        Args:
            order_result: The order execution result
            correlation_id: Correlation ID for traceability
            rebalance_plan: Optional rebalance plan with strategy attribution metadata
            quote_at_fill: Optional market quote at time of fill
            strategy_attribution: Optional direct strategy attribution from TradeMessage
                metadata. Format: {symbol: {strategy_name: weight_float}}
            execution_quality: Optional dict with execution quality metrics:
                - expected_price: Decimal - mid price at order submission
                - slippage_bps: Decimal - slippage in basis points
                - slippage_amount: Decimal - dollar slippage
                - spread_at_order: Decimal - bid-ask spread at order time
                - execution_steps: int - walk-the-book steps used (1-4)
                - time_to_fill_ms: int - milliseconds to fill
                - quote_timestamp: datetime - when quote was captured
            strategy_id: Strategy identifier from TradeMessage. When provided,
                this is the definitive attribution source (per-strategy books).

        Returns:
            TradeLedgerEntry if order was filled and recorded, None otherwise

        """
        # Validate order is recordable
        if not self._is_order_recordable(order_result, correlation_id):
            return None

        # Extract strategy attribution
        strategy_names, strategy_weights = self._extract_strategy_attribution(
            order_result.symbol,
            rebalance_plan,
            order_result,
            strategy_attribution,
            strategy_id,
        )

        # Extract and validate quote data
        bid_at_fill, ask_at_fill = self._process_quote_data(quote_at_fill, order_result)

        # Extract order metadata
        order_type = order_result.order_type
        fill_timestamp = order_result.filled_at or order_result.timestamp

        # Extract execution quality metrics
        eq = execution_quality or {}

        # Create and record ledger entry
        entry = self._create_entry(
            order_result=order_result,
            correlation_id=correlation_id,
            bid_at_fill=bid_at_fill,
            ask_at_fill=ask_at_fill,
            fill_timestamp=fill_timestamp,
            order_type=order_type,
            strategy_names=strategy_names,
            strategy_weights=strategy_weights,
            expected_price=eq.get("expected_price"),
            slippage_bps=eq.get("slippage_bps"),
            slippage_amount=eq.get("slippage_amount"),
            spread_at_order=eq.get("spread_at_order"),
            execution_steps=eq.get("execution_steps"),
            time_to_fill_ms=eq.get("time_to_fill_ms"),
            quote_timestamp=eq.get("quote_timestamp"),
        )

        if not entry:
            return None

        # Store in-memory
        self._entries.append(entry)

        # Write to DynamoDB
        if self._repository:
            try:
                self._repository.put_trade(entry, self._ledger_id)
                # Update linked signals to EXECUTED state
                self._update_signal_lifecycle(entry, correlation_id)
                # Handle lot-based strategy P&L tracking
                self._process_strategy_lots(entry)
            except DynamoDBException as e:
                logger.error(
                    "Failed to write trade to DynamoDB - trade in memory only",
                    order_id=entry.order_id,
                    error=str(e),
                )

        return entry

    def _is_order_recordable(self, order_result: OrderResult, correlation_id: str) -> bool:
        """Check if order meets criteria for ledger recording.

        Args:
            order_result: The order execution result
            correlation_id: Correlation ID for traceability

        Returns:
            True if order should be recorded, False otherwise

        """
        # Only record successful fills
        if not order_result.success or not order_result.order_id:
            logger.debug(
                "Skipping ledger recording for unsuccessful order",
                symbol=order_result.symbol,
                success=order_result.success,
                correlation_id=correlation_id,
            )
            return False

        # Only record if we have a fill price
        if order_result.price is None or order_result.price <= 0:
            logger.debug(
                "Skipping ledger recording - no valid fill price",
                symbol=order_result.symbol,
                order_id=order_result.order_id,
                correlation_id=correlation_id,
            )
            return False

        # Only record if we have valid quantity
        if order_result.shares <= 0:
            logger.debug(
                "Skipping ledger recording - invalid quantity",
                symbol=order_result.symbol,
                order_id=order_result.order_id,
                shares=str(order_result.shares),
                correlation_id=correlation_id,
            )
            return False

        # Validate action is BUY or SELL
        if order_result.action not in ("BUY", "SELL"):
            logger.warning(
                "Invalid order action, skipping ledger recording",
                action=order_result.action,
                symbol=order_result.symbol,
                order_id=order_result.order_id,
                correlation_id=correlation_id,
            )
            return False

        return True

    def _process_quote_data(
        self, quote_at_fill: QuoteModel | None, order_result: OrderResult
    ) -> tuple[Decimal | None, Decimal | None]:
        """Extract and validate bid/ask prices from quote.

        Args:
            quote_at_fill: Optional market quote at time of fill
            order_result: The order execution result

        Returns:
            Tuple of (bid_at_fill, ask_at_fill), both may be None

        """
        bid_at_fill = None
        ask_at_fill = None

        if quote_at_fill:
            # Filter out zero or negative prices which fail validation
            if quote_at_fill.bid_price > 0:
                bid_at_fill = quote_at_fill.bid_price
            if quote_at_fill.ask_price > 0:
                ask_at_fill = quote_at_fill.ask_price

            # Log warning if quote data is invalid
            if quote_at_fill.bid_price <= 0 or quote_at_fill.ask_price <= 0:
                logger.warning(
                    "Quote data has invalid prices (≤ 0) - excluding from ledger",
                    symbol=order_result.symbol,
                    bid_price=str(quote_at_fill.bid_price),
                    ask_price=str(quote_at_fill.ask_price),
                    order_id=order_result.order_id,
                )

        return bid_at_fill, ask_at_fill

    def _create_entry(
        self,
        order_result: OrderResult,
        correlation_id: str,
        bid_at_fill: Decimal | None,
        ask_at_fill: Decimal | None,
        fill_timestamp: datetime,
        order_type: Literal["MARKET", "LIMIT", "STOP", "STOP_LIMIT"],
        strategy_names: list[str],
        strategy_weights: dict[str, Decimal] | None,
        expected_price: Decimal | None = None,
        slippage_bps: Decimal | None = None,
        slippage_amount: Decimal | None = None,
        spread_at_order: Decimal | None = None,
        execution_steps: int | None = None,
        time_to_fill_ms: int | None = None,
        quote_timestamp: datetime | None = None,
    ) -> TradeLedgerEntry | None:
        """Create TradeLedgerEntry DTO.

        Args:
            order_result: The order execution result
            correlation_id: Correlation ID for traceability
            bid_at_fill: Bid price at fill time
            ask_at_fill: Ask price at fill time
            fill_timestamp: Timestamp of the fill
            order_type: Type of order (MARKET, LIMIT, etc.)
            strategy_names: List of strategy names
            strategy_weights: Strategy weight attribution
            expected_price: Mid price at order submission (arrival price)
            slippage_bps: Slippage in basis points
            slippage_amount: Dollar slippage amount
            spread_at_order: Bid-ask spread at order submission
            execution_steps: Walk-the-book steps used (1-4)
            time_to_fill_ms: Milliseconds from submission to fill
            quote_timestamp: When the initial quote was captured

        Returns:
            TradeLedgerEntry if successful, None if validation fails

        """
        try:
            # Type assertions: validated by _is_order_recordable
            assert order_result.order_id is not None  # noqa: S101
            assert order_result.price is not None  # noqa: S101

            entry = TradeLedgerEntry(
                order_id=order_result.order_id,
                correlation_id=correlation_id,
                symbol=order_result.symbol,
                direction=order_result.action,
                filled_qty=order_result.shares,
                fill_price=order_result.price,
                bid_at_fill=bid_at_fill,
                ask_at_fill=ask_at_fill,
                expected_price=expected_price,
                slippage_bps=slippage_bps,
                slippage_amount=slippage_amount,
                spread_at_order=spread_at_order,
                execution_steps=execution_steps,
                time_to_fill_ms=time_to_fill_ms,
                quote_timestamp=quote_timestamp,
                fill_timestamp=fill_timestamp,
                order_type=order_type,
                strategy_names=strategy_names,
                strategy_weights=strategy_weights,
            )

            logger.info(
                "Trade ledger entry created",
                order_id=entry.order_id,
                symbol=entry.symbol,
                direction=entry.direction,
                strategies=strategy_names,
            )

            return entry

        except ValidationError as e:
            logger.error(
                "Failed to create trade ledger entry",
                symbol=order_result.symbol,
                error=str(e),
                validation_errors=e.errors(),
            )
            return None

    def _extract_strategy_attribution(
        self,
        symbol: str,
        rebalance_plan: RebalancePlan | None,
        order_result: OrderResult | None = None,
        direct_attribution: dict[str, dict[str, float]] | None = None,
        strategy_id: str | None = None,
    ) -> tuple[list[str], dict[str, Decimal] | None]:
        """Extract strategy attribution for a trade.

        Per-strategy books architecture: each trade belongs to exactly one
        strategy. The strategy_id from TradeMessage is the primary source.

        Fallback chain:
        1. strategy_id from TradeMessage (per-strategy books)
        2. Direct attribution dict (from TradeMessage.metadata)
        3. Client order ID parsing (safety net)

        Args:
            symbol: Trading symbol.
            rebalance_plan: Optional rebalance plan (unused in per-strategy mode).
            order_result: Optional order result with client_order_id for fallback.
            direct_attribution: Optional attribution from TradeMessage.metadata.
            strategy_id: Strategy identifier from TradeMessage.

        Returns:
            Tuple of (strategy_names, strategy_weights).

        """
        symbol_upper = symbol.strip().upper()

        # Primary: strategy_id from TradeMessage (per-strategy books)
        if strategy_id:
            logger.debug(
                "Strategy attribution from strategy_id",
                extra={
                    "symbol": symbol_upper,
                    "strategy_id": strategy_id,
                    "source": "trade_message",
                },
            )
            return [strategy_id], {strategy_id: Decimal("1.0")}

        # Fallback: direct attribution from metadata
        if direct_attribution:
            symbol_attr = direct_attribution.get(symbol_upper, {}) or direct_attribution.get(
                symbol, {}
            )
            if symbol_attr:
                strategy_names = list(symbol_attr.keys())
                strategy_weights = {
                    name: Decimal(str(weight)) for name, weight in symbol_attr.items()
                }
                logger.debug(
                    "Strategy attribution from direct attribution",
                    extra={
                        "symbol": symbol_upper,
                        "strategies": strategy_names,
                        "source": "direct_attribution",
                    },
                )
                return strategy_names, strategy_weights

        # Safety net: client_order_id parsing
        if order_result and order_result.client_order_id:
            parsed = parse_client_order_id(order_result.client_order_id)
            if parsed:
                parsed_id = parsed.get("strategy_id")
                if parsed_id and parsed_id != "unknown":
                    logger.info(
                        "Strategy attribution from client_order_id fallback",
                        extra={
                            "symbol": symbol_upper,
                            "strategy_id": parsed_id,
                            "source": "client_order_id",
                        },
                    )
                    return [parsed_id], {parsed_id: Decimal("1.0")}

        logger.debug(
            "No strategy attribution available",
            extra={"symbol": symbol_upper},
        )
        return [], None

    def get_ledger(self) -> TradeLedger:
        """Get the current trade ledger.

        Returns:
            TradeLedger with all recorded entries

        """
        return TradeLedger(
            entries=list(self._entries),
            ledger_id=self._ledger_id,
            created_at=self._created_at,
        )

    def get_entries_for_symbol(self, symbol: str) -> list[TradeLedgerEntry]:
        """Get all ledger entries for a specific symbol from current run.

        Args:
            symbol: Trading symbol

        Returns:
            List of entries for the symbol

        """
        return [entry for entry in self._entries if entry.symbol == symbol.upper()]

    def get_entries_for_strategy(self, strategy_name: str) -> list[TradeLedgerEntry]:
        """Get all ledger entries attributed to a specific strategy from current run.

        Args:
            strategy_name: Strategy name

        Returns:
            List of entries attributed to the strategy

        """
        return [entry for entry in self._entries if strategy_name in entry.strategy_names]

    @property
    def total_entries(self) -> int:
        """Get total number of entries recorded in current run."""
        return len(self._entries)

    def _update_signal_lifecycle(self, entry: TradeLedgerEntry, correlation_id: str) -> None:
        """Update signal lifecycle state to EXECUTED after trade is recorded.

        Links the trade to originating signals via correlation_id.

        Args:
            entry: Trade ledger entry that was just recorded
            correlation_id: Correlation ID linking trade to signals

        """
        if not self._repository:
            return

        try:
            # Query signals for this correlation_id
            signals = self._repository.query_signals_by_correlation(correlation_id)

            if not signals:
                logger.debug(
                    "No signals found for correlation_id - trade may not have originated from signal",
                    correlation_id=correlation_id,
                    order_id=entry.order_id,
                )
                return

            # Update signals matching this trade's symbol and action
            for signal in signals:
                # Only update signals that match this trade
                if (
                    signal.get("symbol") == entry.symbol
                    and signal.get("action") == entry.direction
                    and signal.get("lifecycle_state") == "GENERATED"
                ):
                    signal_id = signal.get("signal_id")
                    if signal_id:
                        # Atomically append this trade ID to the signal's executed_trade_ids
                        # The repository uses list_append to prevent race conditions
                        self._repository.update_signal_lifecycle(
                            signal_id, "EXECUTED", [entry.order_id]
                        )

                        logger.debug(
                            "Updated signal lifecycle to EXECUTED",
                            signal_id=signal_id,
                            order_id=entry.order_id,
                            symbol=entry.symbol,
                        )

        except Exception as e:
            # Log error but don't fail the trade recording
            logger.warning(
                f"Failed to update signal lifecycle: {e}",
                correlation_id=correlation_id,
                order_id=entry.order_id,
                error_type=type(e).__name__,
            )

    def _process_strategy_lots(self, entry: TradeLedgerEntry) -> None:
        """Process strategy lot creation (BUY) or exit matching (SELL).

        For BUY orders: Creates a new StrategyLot for each attributed strategy,
        weighted by their contribution to the trade.

        For SELL orders: Uses FIFO matching to close existing lots per strategy,
        calculating realized P&L for each closed portion.

        Args:
            entry: The trade ledger entry that was just recorded

        """
        if not self._repository:
            return

        # Skip if no strategy attribution
        if not entry.strategy_names or not entry.strategy_weights:
            logger.debug(
                "No strategy attribution for lot processing",
                order_id=entry.order_id,
                symbol=entry.symbol,
            )
            return

        try:
            if entry.direction == "BUY":
                self._create_strategy_lots(entry)
            elif entry.direction == "SELL":
                self._match_strategy_lot_exits(entry)
        except Exception as e:
            # Log error but don't fail - lot tracking is secondary to trade recording
            logger.warning(
                f"Failed to process strategy lots: {e}",
                order_id=entry.order_id,
                symbol=entry.symbol,
                direction=entry.direction,
                error_type=type(e).__name__,
            )

    def _create_strategy_lots(self, entry: TradeLedgerEntry) -> None:
        """Create StrategyLot entries for a BUY trade.

        Allocates the filled quantity proportionally across strategies
        based on their weight attribution.

        Args:
            entry: BUY trade ledger entry with strategy attribution

        """
        if not self._repository or not entry.strategy_weights:
            return

        total_qty = entry.filled_qty
        total_weight = sum(entry.strategy_weights.values())

        for strategy_name, weight in entry.strategy_weights.items():
            # Calculate proportional quantity for this strategy
            # Use fractional shares - Alpaca supports this
            strategy_qty = total_qty * (weight / total_weight)

            if strategy_qty <= 0:
                continue

            lot = StrategyLot(
                strategy_name=strategy_name,
                symbol=entry.symbol,
                entry_order_id=entry.order_id,
                entry_price=entry.fill_price,
                entry_timestamp=entry.fill_timestamp,
                entry_qty=strategy_qty,
                remaining_qty=strategy_qty,
                correlation_id=entry.correlation_id,
            )

            self._repository.put_lot(lot)

            logger.info(
                "Created strategy lot",
                lot_id=lot.lot_id,
                strategy=strategy_name,
                symbol=entry.symbol,
                qty=str(strategy_qty),
                entry_price=str(entry.fill_price),
            )

    def _match_strategy_lot_exits(self, entry: TradeLedgerEntry) -> None:
        """Match SELL trade against open lots using FIFO per strategy.

        For each strategy attributed to the SELL, finds open lots for that
        strategy+symbol and matches exits in FIFO order until the strategy's
        portion of the sale is fully matched.

        Args:
            entry: SELL trade ledger entry with strategy attribution

        """
        if not self._repository or not entry.strategy_weights:
            return

        total_qty = entry.filled_qty
        total_weight = sum(entry.strategy_weights.values())

        for strategy_name, weight in entry.strategy_weights.items():
            # Calculate how much of this sale belongs to this strategy
            strategy_sell_qty = total_qty * (weight / total_weight)

            if strategy_sell_qty <= 0:
                continue

            # Query open lots for this strategy+symbol (returns FIFO ordered)
            open_lots = self._repository.query_open_lots_by_strategy_and_symbol(
                strategy_name, entry.symbol
            )

            if not open_lots:
                logger.warning(
                    "No open lots found for SELL - may be pre-existing position",
                    strategy=strategy_name,
                    symbol=entry.symbol,
                    sell_qty=str(strategy_sell_qty),
                )
                continue

            remaining_to_exit = strategy_sell_qty

            for lot in open_lots:
                if remaining_to_exit <= 0:
                    break

                # Determine how much to exit from this lot
                exit_qty = min(remaining_to_exit, lot.remaining_qty)

                # Record the exit on the lot
                lot.record_exit(
                    exit_order_id=entry.order_id,
                    exit_price=entry.fill_price,
                    exit_timestamp=entry.fill_timestamp,
                    exit_qty=exit_qty,
                )

                # Update lot in DynamoDB
                self._repository.update_lot(lot)

                remaining_to_exit -= exit_qty

                logger.info(
                    "Matched lot exit",
                    lot_id=lot.lot_id,
                    strategy=strategy_name,
                    symbol=entry.symbol,
                    exit_qty=str(exit_qty),
                    exit_price=str(entry.fill_price),
                    realized_pnl=str(lot.realized_pnl),
                    lot_is_open=lot.is_open,
                )

            if remaining_to_exit > Decimal("0.0001"):  # Allow for tiny rounding
                logger.warning(
                    "Incomplete lot matching - sell qty exceeds tracked lots",
                    strategy=strategy_name,
                    symbol=entry.symbol,
                    unmatched_qty=str(remaining_to_exit),
                )
