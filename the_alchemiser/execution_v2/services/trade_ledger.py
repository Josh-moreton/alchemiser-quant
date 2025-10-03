"""Business Unit: execution | Status: current.

Trade ledger service for recording filled orders.

This service captures trade execution details including fill price, bid/ask spreads,
quantities, and strategy attribution. It handles cases where market data may not be
fully available without blocking the recording of core trade information.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.trade_ledger import TradeLedger, TradeLedgerEntry

if TYPE_CHECKING:
    from the_alchemiser.execution_v2.models.execution_result import OrderResult
    from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlan
    from the_alchemiser.shared.types.quote import QuoteModel

logger = get_logger(__name__)


class TradeLedgerService:
    """Service for recording filled orders to trade ledger.

    Captures order execution details with strategy attribution and market data
    when available. Supports multi-strategy aggregation where multiple strategies
    suggest the same symbol.
    """

    def __init__(self) -> None:
        """Initialize the trade ledger service."""
        self._ledger_id = str(uuid.uuid4())
        self._entries: list[TradeLedgerEntry] = []

    def record_filled_order(
        self,
        order_result: OrderResult,
        correlation_id: str,
        rebalance_plan: RebalancePlan | None = None,
        quote_at_fill: QuoteModel | None = None,
    ) -> TradeLedgerEntry | None:
        """Record a filled order to the trade ledger.

        Args:
            order_result: The order execution result
            correlation_id: Correlation ID for traceability
            rebalance_plan: Optional rebalance plan with strategy attribution metadata
            quote_at_fill: Optional market quote at time of fill

        Returns:
            TradeLedgerEntry if order was filled and recorded, None otherwise

        """
        # Only record successful fills
        if not order_result.success or not order_result.order_id:
            logger.debug(
                "Skipping ledger recording for unsuccessful order",
                symbol=order_result.symbol,
                success=order_result.success,
            )
            return None

        # Only record if we have a fill price
        if order_result.price is None or order_result.price <= 0:
            logger.debug(
                "Skipping ledger recording - no valid fill price",
                symbol=order_result.symbol,
                order_id=order_result.order_id,
            )
            return None

        # Extract strategy attribution from rebalance plan metadata
        strategy_names, strategy_weights = self._extract_strategy_attribution(
            order_result.symbol, rebalance_plan
        )

        # Extract bid/ask from quote if available
        bid_at_fill = quote_at_fill.bid if quote_at_fill else None
        ask_at_fill = quote_at_fill.ask if quote_at_fill else None

        # Determine order type from context (default to MARKET if not in plan metadata)
        order_type = self._determine_order_type(order_result.symbol, rebalance_plan)

        try:
            entry = TradeLedgerEntry(
                order_id=order_result.order_id,
                correlation_id=correlation_id,
                symbol=order_result.symbol,
                direction=order_result.action,  # Already "BUY" or "SELL"
                filled_qty=order_result.shares,
                fill_price=order_result.price,
                bid_at_fill=bid_at_fill,
                ask_at_fill=ask_at_fill,
                fill_timestamp=order_result.timestamp,
                order_type=order_type,
                strategy_names=strategy_names,
                strategy_weights=strategy_weights,
            )

            self._entries.append(entry)

            logger.info(
                "Recorded trade to ledger",
                order_id=entry.order_id,
                symbol=entry.symbol,
                direction=entry.direction,
                filled_qty=str(entry.filled_qty),
                fill_price=str(entry.fill_price),
                strategies=strategy_names,
                correlation_id=correlation_id,
            )

            return entry

        except Exception as e:
            logger.error(
                f"Failed to record trade to ledger: {e}",
                symbol=order_result.symbol,
                order_id=order_result.order_id,
                correlation_id=correlation_id,
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

    def _determine_order_type(
        self, symbol: str, rebalance_plan: RebalancePlan | None
    ) -> str:
        """Determine order type from rebalance plan metadata.

        Args:
            symbol: Trading symbol
            rebalance_plan: Optional rebalance plan with order type metadata

        Returns:
            Order type string (MARKET, LIMIT, etc.)

        """
        if not rebalance_plan or not rebalance_plan.metadata:
            return "MARKET"

        # Check for order type in metadata
        # Format: {"order_types": {"SYMBOL": "LIMIT"}}
        order_types = rebalance_plan.metadata.get("order_types", {})
        return order_types.get(symbol, "MARKET")

    def get_ledger(self) -> TradeLedger:
        """Get the current trade ledger.

        Returns:
            TradeLedger with all recorded entries

        """
        return TradeLedger(
            entries=list(self._entries),
            ledger_id=self._ledger_id,
            created_at=datetime.now(UTC),
        )

    def get_entries_for_symbol(self, symbol: str) -> list[TradeLedgerEntry]:
        """Get all ledger entries for a specific symbol.

        Args:
            symbol: Trading symbol

        Returns:
            List of entries for the symbol

        """
        return [entry for entry in self._entries if entry.symbol == symbol.upper()]

    def get_entries_for_strategy(self, strategy_name: str) -> list[TradeLedgerEntry]:
        """Get all ledger entries attributed to a specific strategy.

        Args:
            strategy_name: Strategy name

        Returns:
            List of entries attributed to the strategy

        """
        return [entry for entry in self._entries if strategy_name in entry.strategy_names]

    @property
    def total_entries(self) -> int:
        """Get total number of entries recorded."""
        return len(self._entries)
