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
from typing import TYPE_CHECKING, Literal

from pydantic import ValidationError

from the_alchemiser.shared.config.config import load_settings
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.repositories.dynamodb_trade_ledger_repository import (
    DynamoDBTradeLedgerRepository,
)
from the_alchemiser.shared.schemas.trade_ledger import TradeLedger, TradeLedgerEntry

if TYPE_CHECKING:
    from the_alchemiser.execution_v2.models.execution_result import OrderResult
    from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlan
    from the_alchemiser.shared.types.market_data import QuoteModel

logger = get_logger(__name__)

__all__ = ["TradeLedgerService"]

# Import boto3 exceptions for DynamoDB error handling
from botocore.exceptions import BotoCoreError, ClientError

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

        Returns:
            TradeLedgerEntry if order was filled and recorded, None otherwise

        """
        # Validate order is recordable
        if not self._is_order_recordable(order_result, correlation_id):
            return None

        # Extract strategy attribution
        strategy_names, strategy_weights = self._extract_strategy_attribution(
            order_result.symbol, rebalance_plan
        )

        # Extract and validate quote data
        bid_at_fill, ask_at_fill = self._process_quote_data(quote_at_fill, order_result)

        # Extract order metadata
        order_type = order_result.order_type
        fill_timestamp = order_result.filled_at or order_result.timestamp

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
        )

        if not entry:
            return None

        # Store in-memory
        self._entries.append(entry)

        # Write to DynamoDB
        if self._repository:
            try:
                self._repository.put_trade(entry, self._ledger_id)
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
        self, symbol: str, rebalance_plan: RebalancePlan | None
    ) -> tuple[list[str], dict[str, Decimal] | None]:
        """Extract strategy attribution from rebalance plan metadata.

        Args:
            symbol: Trading symbol
            rebalance_plan: Optional rebalance plan with strategy metadata

        Returns:
            Tuple of (strategy_names, strategy_weights)

        """
        if not rebalance_plan or not rebalance_plan.metadata:
            return [], None

        # Check for strategy attribution in metadata
        # Format: {"strategy_attribution": {"SYMBOL": {"strategy1": 0.6, "strategy2": 0.4}}}
        strategy_attr = rebalance_plan.metadata.get("strategy_attribution", {})
        symbol_attr = strategy_attr.get(symbol, {})

        if not symbol_attr:
            return [], None

        strategy_names = list(symbol_attr.keys())
        strategy_weights = {name: Decimal(str(weight)) for name, weight in symbol_attr.items()}

        return strategy_names, strategy_weights

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
