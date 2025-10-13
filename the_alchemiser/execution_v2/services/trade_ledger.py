"""Business Unit: execution | Status: current.

Trade ledger service for recording filled orders.

This service captures trade execution details including fill price, bid/ask spreads,
quantities, and strategy attribution. It handles cases where market data may not be
fully available without blocking the recording of core trade information.

Trade ledger entries are persisted to S3 for historical analysis and audit purposes.

FEATURES IMPLEMENTED:
=====================
- Quote data capture: Integrated with pricing_service when available
- Order type detection: Extracts actual order type (MARKET, LIMIT, etc.) from OrderResult
- Fill timestamp: Uses filled_at when available, falls back to order placement timestamp
- Strategy attribution: Multi-strategy aggregation support
- Validation: Zero quantity, invalid actions, price checks
- S3 persistence: Automatic ledger archival with graceful degradation
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from the_alchemiser.shared.config.config import load_settings
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.trade_ledger import TradeLedger, TradeLedgerEntry

if TYPE_CHECKING:
    from the_alchemiser.execution_v2.models.execution_result import OrderResult
    from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlan
    from the_alchemiser.shared.types.market_data import QuoteModel

logger = get_logger(__name__)


class TradeLedgerService:
    """Service for recording filled orders to trade ledger.

    Captures order execution details with strategy attribution and market data
    when available. Supports multi-strategy aggregation where multiple strategies
    suggest the same symbol.

    Persists trade ledger entries to S3 for historical analysis and audit purposes.
    """

    def __init__(self) -> None:
        """Initialize the trade ledger service."""
        self._ledger_id = str(uuid.uuid4())
        self._entries: list[TradeLedgerEntry] = []
        self._settings = load_settings()
        self._s3_client: object | None = None  # Lazy initialization, type: boto3 client or None
        self._s3_init_failed: bool = False  # Track S3 initialization failures

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

        # Only record if we have valid quantity
        if order_result.shares <= 0:
            logger.debug(
                "Skipping ledger recording - invalid quantity",
                symbol=order_result.symbol,
                order_id=order_result.order_id,
                shares=str(order_result.shares),
            )
            return None

        # Extract strategy attribution from rebalance plan metadata
        strategy_names, strategy_weights = self._extract_strategy_attribution(
            order_result.symbol, rebalance_plan
        )

        # Extract bid/ask from quote if available and valid (> 0)
        # Filter out zero or negative prices which fail validation
        bid_at_fill = None
        ask_at_fill = None
        if quote_at_fill:
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

        # Extract order type from OrderResult
        order_type = order_result.order_type

        # Use filled_at timestamp if available, otherwise fall back to order timestamp
        fill_timestamp = order_result.filled_at or order_result.timestamp

        # Validate action is BUY or SELL
        if order_result.action not in ("BUY", "SELL"):
            logger.warning(
                f"Invalid order action: {order_result.action}, skipping ledger recording",
                symbol=order_result.symbol,
                order_id=order_result.order_id,
            )
            return None

        try:
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

    def _get_s3_client(self) -> object | None:
        """Get or create S3 client (lazy initialization).

        Returns:
            boto3 S3 client instance or None if initialization failed

        """
        if self._s3_client is None and not self._s3_init_failed:
            try:
                import boto3

                self._s3_client = boto3.client("s3")
            except Exception as e:
                logger.error(f"Failed to initialize S3 client: {e}")
                self._s3_init_failed = True
        return self._s3_client

    def persist_to_s3(self, correlation_id: str | None = None) -> bool:
        """Persist the trade ledger to S3.

        Note: Returns True when there are no entries to persist (nothing to do).
        This is considered a success case as there's no error condition.

        Args:
            correlation_id: Optional correlation ID for the execution run

        Returns:
            True if persistence was successful or there were no entries to persist,
            False if an error occurred during persistence

        """
        if not self._settings.trade_ledger.enabled:
            logger.debug("Trade ledger S3 persistence is disabled")
            return False

        if not self._settings.trade_ledger.bucket_name:
            logger.warning("Trade ledger bucket name not configured, skipping S3 persistence")
            return False

        if not self._entries:
            logger.debug("No trade ledger entries to persist")
            return True

        s3_client = self._get_s3_client()
        if s3_client is None:
            logger.error("S3 client not available, cannot persist trade ledger")
            return False

        try:
            # Create ledger with all entries
            ledger = self.get_ledger()

            # Generate S3 key with timestamp and correlation ID
            timestamp = datetime.now(UTC).strftime("%Y/%m/%d/%H%M%S")
            correlation_suffix = f"-{correlation_id}" if correlation_id else ""
            s3_key = f"trade-ledgers/{timestamp}-{self._ledger_id}{correlation_suffix}.json"

            # Convert ledger to JSON (handle Decimal serialization)
            ledger_data = json.loads(
                ledger.model_dump_json()
            )  # Pydantic handles Decimal -> str conversion

            # Upload to S3
            s3_client.put_object(  # type: ignore[attr-defined]  # boto3 client duck-typing
                Bucket=self._settings.trade_ledger.bucket_name,
                Key=s3_key,
                Body=json.dumps(ledger_data, indent=2),
                ContentType="application/json",
            )

            logger.info(
                "Trade ledger persisted to S3",
                bucket=self._settings.trade_ledger.bucket_name,
                key=s3_key,
                entries=ledger.total_entries,
                ledger_id=self._ledger_id,
            )
            return True

        except Exception as e:
            logger.error(
                f"Failed to persist trade ledger to S3: {e}",
                ledger_id=self._ledger_id,
                entries=len(self._entries),
            )
            return False
