#!/usr/bin/env python3
"""Business Unit: strategy & signal generation; Status: current.

Strategy Order Tracker for Per-Strategy P&L Management.

This module provides dedicated tracking of orders and positions per strategy for accurate P&L calculations.
It persists order data and calculates realized/unrealized P&L per strategy.

Key Features:
- Tag orders with strategy information during execution
- Maintain positions and average cost on a per-strategy basis
- Calculate realized P&L when positions are reduced/closed
- Calculate unrealized P&L from current market prices
- Persist order history to S3 for long-term tracking
- Support for both individual strategy and portfolio-wide P&L

Design:
- Uses existing S3 utilities for persistent storage
- Integrates with trading engine to capture order fills
- Provides P&L metrics for email reporting and dashboards
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any, cast

from the_alchemiser.application.mapping.tracking_mapping import (
    orders_to_execution_summary_dto,
    strategy_pnl_to_dict,
)
from the_alchemiser.domain.registry import StrategyType
from the_alchemiser.infrastructure.config import load_settings
from the_alchemiser.infrastructure.s3.s3_utils import get_s3_handler
from the_alchemiser.interfaces.schemas.tracking import (
    ExecutionStatus,
    StrategyExecutionSummaryDTO,
    StrategyLiteral,
    StrategyOrderDTO,
    StrategyPnLDTO,
    StrategyPositionDTO,
)
from the_alchemiser.infrastructure.errors import TradingSystemErrorHandler
from the_alchemiser.shared_kernel.errors import DataProviderError
from the_alchemiser.strategy.domain.errors import StrategyExecutionError

# TODO: Import order history and email summary types once implementation aligns
# from the_alchemiser.interfaces.schemas.execution import OrderHistoryDTO
# from the_alchemiser.interfaces.schemas.reporting import EmailSummary


@dataclass  # Note: Pydantic DTOs available in interfaces.schemas.tracking for I/O boundaries
class StrategyOrder:
    """Represents a completed order tagged with strategy information."""

    order_id: str
    strategy: str  # StrategyType.value
    symbol: str
    side: str  # 'BUY' or 'SELL'
    quantity: float
    price: float
    timestamp: str  # ISO format

    @classmethod
    def from_order_data(
        cls,
        order_id: str,
        strategy: StrategyType,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
    ) -> StrategyOrder:
        """Create StrategyOrder from order execution data."""
        return cls(
            order_id=order_id,
            strategy=strategy.value,
            symbol=symbol,
            side=side.upper(),
            quantity=float(quantity),
            price=float(price),
            timestamp=datetime.now(UTC).isoformat(),
        )


@dataclass  # Note: Pydantic DTOs available in interfaces.schemas.tracking for I/O boundaries
class StrategyPosition:
    """Represents a position held by a specific strategy."""

    strategy: str
    symbol: str
    quantity: float
    average_cost: float
    total_cost: float
    last_updated: str

    def update_with_order(self, order: StrategyOrder) -> None:
        """Update position with new order data."""
        if order.side == "BUY":
            # Add to position
            new_total_cost = self.total_cost + (order.quantity * order.price)
            new_quantity = self.quantity + order.quantity
            if new_quantity > 0:
                self.average_cost = new_total_cost / new_quantity
            self.quantity = new_quantity
            self.total_cost = new_total_cost
        elif order.side == "SELL":
            # Reduce position
            if self.quantity <= 0:
                logging.warning(
                    f"Attempted to sell {order.symbol} with no position in {order.strategy}"
                )
                return

            # Use FIFO accounting for cost basis
            self.quantity -= order.quantity
            if self.quantity <= 0:
                # Position closed
                self.quantity = 0
                self.total_cost = 0
                self.average_cost = 0
            else:
                # Reduce total cost proportionally
                self.total_cost = self.quantity * self.average_cost

        self.last_updated = order.timestamp


@dataclass  # Note: Pydantic DTOs available in interfaces.schemas.tracking for I/O boundaries
class StrategyPnL:
    """P&L metrics for a specific strategy."""

    strategy: str
    realized_pnl: float
    unrealized_pnl: float
    total_pnl: float
    positions: dict[str, float]  # symbol -> quantity
    allocation_value: float

    @property
    def total_return_pct(self) -> float:
        """Calculate total return percentage."""
        if self.allocation_value <= 0:
            return 0.0
        return (self.total_pnl / self.allocation_value) * 100


class StrategyOrderTracker:
    """Dedicated component for tracking orders and P&L by strategy."""

    def __init__(self, config: Any = None, paper_trading: bool = True) -> None:
        """Initialize tracker with S3 configuration.

        Args:
            config: Configuration object
            paper_trading: Whether this is for paper trading (separates data storage)

        """
        self.config = config or load_settings()
        self.s3_handler = get_s3_handler()
        self.paper_trading = paper_trading
        self.error_handler = TradingSystemErrorHandler()

        # Initialize S3 paths for data persistence
        self._setup_s3_paths()

        # Initialize in-memory caches
        self._orders_cache: list[StrategyOrder] = []
        self._positions_cache: dict[
            tuple[str, str], StrategyPosition
        ] = {}  # (strategy, symbol) -> position
        self._realized_pnl_cache: dict[str, float] = {}  # strategy -> realized P&L

        # Load existing data from S3
        self._load_data()

        mode_str = "paper" if paper_trading else "live"
        logging.info(
            f"StrategyOrderTracker initialized with S3 persistence ({mode_str} trading mode)"
        )

    def _setup_s3_paths(self) -> None:
        """Set up S3 paths for data persistence."""
        tracking_config = self.config.tracking if self.config else None

        if not tracking_config:
            # Fallback defaults
            bucket = "the-alchemiser-s3"
            orders_path = "strategy_orders/"
            positions_path = "strategy_positions/"
            pnl_history_path = "strategy_pnl_history/"
            self.order_history_limit = 1000
        else:
            bucket = tracking_config.s3_bucket
            orders_path = tracking_config.strategy_orders_path
            positions_path = tracking_config.strategy_positions_path
            pnl_history_path = tracking_config.strategy_pnl_history_path
            self.order_history_limit = tracking_config.order_history_limit

        # Separate by trading mode (paper/live)
        mode_prefix = "paper/" if self.paper_trading else "live/"

        self.orders_s3_path = f"s3://{bucket}/{mode_prefix}{orders_path}"
        self.positions_s3_path = f"s3://{bucket}/{mode_prefix}{positions_path}"
        self.pnl_history_s3_path = f"s3://{bucket}/{mode_prefix}{pnl_history_path}"

    def record_order(
        self,
        order_id: str,
        strategy: StrategyType,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
    ) -> None:
        """Record a completed order with strategy tagging."""
        try:
            # Create order record
            order = StrategyOrder.from_order_data(order_id, strategy, symbol, side, quantity, price)

            # Process the order
            self._process_order(order)

            logging.info(
                f"Recorded {strategy.value} order: {side} {quantity} {symbol} @ ${price:.2f}"
            )

        except (StrategyExecutionError, DataProviderError) as e:
            # Use TradingSystemErrorHandler for comprehensive error handling
            self.error_handler.handle_error(
                error=e,
                context="order_recording",
                component="StrategyOrderTracker.record_order",
                additional_data={
                    "order_id": order_id,
                    "strategy": strategy.value,
                    "symbol": symbol,
                    "side": side,
                    "quantity": quantity,
                    "price": price,
                },
            )
            logging.error(f"Error recording order {order_id}: {e}")
        except Exception as e:
            # Handle unexpected errors
            self.error_handler.handle_error(
                error=e,
                context="order_recording_unexpected",
                component="StrategyOrderTracker.record_order",
                additional_data={
                    "order_id": order_id,
                    "strategy": strategy.value,
                    "symbol": symbol,
                    "side": side,
                    "quantity": quantity,
                    "price": price,
                },
            )
            logging.error(f"Unexpected error recording order {order_id}: {e}")

    def _process_order(self, order: StrategyOrder) -> None:
        """Process a new order - update caches and persist to S3."""
        try:
            # Add to cache
            self._orders_cache.append(order)

            # Update position
            self._update_position(order)

            # Calculate realized P&L if this is a sell
            if order.side.upper() == "SELL":
                self._calculate_realized_pnl(order)

            # Persist to S3
            self._persist_order(order)
            self._persist_positions()

        except Exception as e:
            # Use error handler for processing errors
            self.error_handler.handle_error(
                error=e,
                context="order_processing",
                component="StrategyOrderTracker._process_order",
                additional_data={
                    "order_id": order.order_id,
                    "strategy": order.strategy,
                    "symbol": order.symbol,
                },
            )
            raise  # Re-raise to be handled by record_order

    def get_execution_summary_dto(
        self,
        strategy: StrategyType,
        symbol: str | None = None,
        days: int = 30,
    ) -> StrategyExecutionSummaryDTO:
        """Get execution summary as DTO for the specified strategy and symbol."""
        try:
            # Get filtered orders
            orders = self.get_order_history(strategy, symbol, days)

            if not orders:
                return StrategyExecutionSummaryDTO(
                    strategy=strategy.value,
                    symbol=symbol or "ALL",
                    total_qty=Decimal("0"),
                    avg_price=None,
                    pnl=None,
                    status=ExecutionStatus.OK,
                    details=[],
                )

            # Filter to single symbol if specified
            if symbol:
                orders = [o for o in orders if o.symbol == symbol]
                target_symbol = symbol
            else:
                # Use the most common symbol for multi-symbol summary
                symbols = [o.symbol for o in orders]
                target_symbol = max(set(symbols), key=symbols.count) if symbols else "ALL"

            # Calculate P&L for this strategy (symbol-specific breakdown can be added later)
            pnl_data = self.get_strategy_pnl(strategy)
            symbol_pnl = Decimal(str(pnl_data.total_pnl))

            # Determine execution status
            status = ExecutionStatus.OK
            if self.error_handler.has_critical_errors():
                status = ExecutionStatus.FAILED
            elif self.error_handler.has_trading_errors():
                status = ExecutionStatus.PARTIAL

            return orders_to_execution_summary_dto(
                orders=orders,
                strategy=strategy.value,
                symbol=target_symbol,
                status=status,
                pnl=symbol_pnl,
            )

        except Exception as e:
            self.error_handler.handle_error(
                error=e,
                context="execution_summary_generation",
                component="StrategyOrderTracker.get_execution_summary_dto",
                additional_data={
                    "strategy": strategy.value,
                    "symbol": symbol,
                    "days": days,
                },
            )
            # Return a failed summary on error
            return StrategyExecutionSummaryDTO(
                strategy=strategy.value,
                symbol=symbol or "ALL",
                total_qty=Decimal("0"),
                avg_price=None,
                pnl=None,
                status=ExecutionStatus.FAILED,
                details=[],
            )

    def get_strategy_pnl(
        self, strategy: StrategyType, current_prices: dict[str, float] | None = None
    ) -> StrategyPnL:
        """Calculate comprehensive P&L for a strategy."""
        strategy_str = strategy.value

        # Get positions for this strategy
        strategy_positions = {
            symbol: pos.quantity
            for (strat, symbol), pos in self._positions_cache.items()
            if strat == strategy_str and pos.quantity > 0
        }

        # Calculate unrealized P&L
        unrealized_pnl = 0.0
        allocation_value = 0.0

        if current_prices:
            for symbol, quantity in strategy_positions.items():
                if symbol in current_prices and quantity > 0:
                    position = self._positions_cache.get((strategy_str, symbol))
                    if position:
                        current_value = quantity * current_prices[symbol]
                        cost_basis = quantity * position.average_cost
                        unrealized_pnl += current_value - cost_basis
                        allocation_value += current_value

        # Get realized P&L
        realized_pnl = self._realized_pnl_cache.get(strategy_str, 0.0)

        # Calculate total P&L
        total_pnl = realized_pnl + unrealized_pnl

        return StrategyPnL(
            strategy=strategy_str,
            realized_pnl=realized_pnl,
            unrealized_pnl=unrealized_pnl,
            total_pnl=total_pnl,
            positions=strategy_positions,
            allocation_value=allocation_value,
        )

    def get_all_strategy_pnl(
        self, current_prices: dict[str, float] | None = None
    ) -> dict[StrategyType, StrategyPnL]:
        """Get P&L for all strategies."""
        result = {}
        for strategy in StrategyType:
            result[strategy] = self.get_strategy_pnl(strategy, current_prices)
        return result

    def get_order_history(
        self,
        strategy: StrategyType | None = None,
        symbol: str | None = None,
        days: int = 30,
    ) -> list[StrategyOrder]:
        """Get filtered order history."""
        # Filter by strategy
        orders = self._orders_cache
        if strategy:
            orders = [o for o in orders if o.strategy == strategy.value]

        # Filter by symbol
        if symbol:
            orders = [o for o in orders if o.symbol == symbol]

        # Filter by date (last N days)
        if days > 0:
            cutoff_date = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_date = cutoff_date - timedelta(days=days)
            cutoff_str = cutoff_date.isoformat()
            orders = [o for o in orders if o.timestamp >= cutoff_str]

        # Sort by timestamp (most recent first)
        orders.sort(key=lambda x: x.timestamp, reverse=True)
        return orders

    def archive_daily_pnl(self, current_prices: dict[str, float] | None = None) -> None:
        """Archive daily P&L snapshot for historical tracking."""
        try:
            today = datetime.now(UTC).strftime("%Y-%m-%d")

            # Get P&L for all strategies
            all_pnl = self.get_all_strategy_pnl(current_prices)

            # Create archive record with Decimal precision
            archive_data = {
                "date": today,
                "timestamp": datetime.now(UTC).isoformat(),
                "strategies": {
                    strategy.value: strategy_pnl_to_dict(pnl) for strategy, pnl in all_pnl.items()
                },
            }

            # Save to S3
            archive_path = f"{self.pnl_history_s3_path}{today}.json"
            success = self.s3_handler.write_json(archive_path, archive_data)

            if success:
                logging.info(f"Archived daily P&L snapshot for {today}")
            else:
                logging.error(f"Failed to archive daily P&L for {today}")

        except Exception as e:
            self.error_handler.handle_error(
                error=e,
                context="pnl_archive",
                component="StrategyOrderTracker.archive_daily_pnl",
                additional_data={
                    "date": today if "today" in locals() else "unknown",
                    "strategies_count": len(all_pnl) if "all_pnl" in locals() else 0,
                },
            )
            logging.error(f"Error archiving daily P&L: {e}")

    # ==================== DTO-based Methods ====================

    def add_order(self, order_dto: StrategyOrderDTO) -> None:
        """Add strategy order using DTO (new DTO-based interface)."""
        try:
            # Validate DTO (Pydantic validation happens automatically)
            validated_order = StrategyOrderDTO.model_validate(order_dto.model_dump())

            # Convert DTO to internal dataclass for existing processing logic
            strategy_order = self._dto_to_strategy_order(validated_order)

            # Process using existing logic
            self._process_order(strategy_order)

            logging.info(
                f"Added DTO order: {validated_order.strategy} {validated_order.side} "
                f"{validated_order.quantity} {validated_order.symbol} @ ${validated_order.price}"
            )
        except Exception as e:
            self.error_handler.handle_error(
                error=e,
                context="dto_order_addition",
                component="StrategyOrderTracker.add_order",
                additional_data={
                    "order_id": order_dto.order_id,
                    "strategy": order_dto.strategy,
                    "symbol": order_dto.symbol,
                },
            )
            raise

    def track_order_error(
        self,
        order_id: str,
        strategy: StrategyType,
        symbol: str,
        side: str,
        quantity: Decimal,
        error: Exception,
        order_price: Decimal | None = None,
    ) -> None:
        """Track an order error with classified error information.

        This method creates an order event with ERROR status and includes
        classified error metadata for analytics and debugging.

        Args:
            order_id: Unique order identifier
            strategy: Strategy that generated the order
            symbol: Symbol being traded
            side: Order side (buy/sell)
            quantity: Order quantity
            error: The exception that caused the error
            order_price: Order price if available

        """
        try:
            # Classify the error using the order error classification system
            from the_alchemiser.shared_kernel.value_objects.identifier import (
                Identifier,
            )
            from the_alchemiser.domain.trading.errors import classify_exception

            # Convert string order_id to Identifier for classification
            typed_order_id = None
            try:
                typed_order_id = Identifier.from_string(order_id)
            except (ValueError, TypeError):
                # If conversion fails, we'll pass None and include the raw ID in context
                pass

            classified_error = classify_exception(
                error,
                order_id=typed_order_id,
                additional_context={
                    "raw_order_id": order_id,
                    "strategy": strategy.value,
                    "symbol": symbol,
                    "side": side,
                    "quantity": str(quantity),
                    "price": str(order_price) if order_price else None,
                },
            )

            # Log the classified error for monitoring
            logging.error(
                f"Order error tracked: [{classified_error.category.value}|{classified_error.code.value}] "
                f"{classified_error.message} (Order: {order_id}, Strategy: {strategy.value})",
                extra={
                    "order_id": order_id,
                    "strategy": strategy.value,
                    "symbol": symbol,
                    "error_category": classified_error.category.value,
                    "error_code": classified_error.code.value,
                    "is_transient": classified_error.is_transient,
                    "classified_error_details": classified_error.to_dict(),
                },
            )

            # Build error order dict without float coercion (preserve precision via str)
            error_order_dict: dict[str, Any] = {
                "order_id": order_id,
                "strategy": strategy.value,
                "symbol": symbol.upper(),
                "side": side.upper(),
                "quantity": str(quantity),
                "price": str(order_price) if order_price is not None else None,
                "timestamp": datetime.now(UTC).isoformat(),
                "status": "ERROR",
                "error_message": str(error),
                "classified_error": classified_error.to_dict(),
                "error_category": classified_error.category.value,
                "error_code": classified_error.code.value,
                "is_transient": classified_error.is_transient,
            }

            # Persist the error order with classification metadata
            self._persist_error_order(error_order_dict)

        except Exception as tracking_error:
            # Handle errors in error tracking itself
            self.error_handler.handle_error(
                error=tracking_error,
                context="error_order_tracking",
                component="StrategyOrderTracker.track_order_error",
                additional_data={
                    "original_error": str(error),
                    "order_id": order_id,
                    "strategy": strategy.value,
                    "symbol": symbol,
                },
            )

    def _persist_error_order(self, error_order_dict: dict[str, Any]) -> None:
        """Persist error order with classification metadata to S3."""
        try:
            # Create a specialized error orders file
            error_orders_path = f"{self.orders_s3_path}error_orders.json"

            # Load existing error orders
            existing_errors = []
            if self.s3_handler.file_exists(error_orders_path):
                existing_data = self.s3_handler.read_json(error_orders_path)
                if existing_data is not None:
                    existing_errors = existing_data.get("error_orders", [])

            # Add new error order
            existing_errors.append(
                {
                    **error_order_dict,
                    "tracked_at": datetime.now(UTC).isoformat(),
                }
            )

            # Keep only recent error orders (last 1000)
            if len(existing_errors) > 1000:
                existing_errors = existing_errors[-1000:]

            # Save back to S3
            error_data = {
                "error_orders": existing_errors,
                "last_updated": datetime.now(UTC).isoformat(),
                "total_count": len(existing_errors),
            }

            self.s3_handler.write_json(error_orders_path, error_data)

        except Exception as e:
            logging.error(f"Failed to persist error order: {e}")

    def get_orders_for_strategy(self, strategy_name: str) -> list[StrategyOrderDTO]:
        """Get strategy orders as DTOs (new DTO-based interface)."""
        try:
            # Validate strategy name
            strategy_type = StrategyType(strategy_name)

            # Get orders using existing logic
            raw_orders = self.get_order_history(strategy=strategy_type)

            # Convert to DTOs
            return [self._strategy_order_to_dto(order) for order in raw_orders]
        except ValueError as e:
            valid_strategies = [s.value for s in StrategyType]
            raise ValueError(
                f"Invalid strategy '{strategy_name}'. Valid strategies: {valid_strategies}"
            ) from e
        except Exception as e:
            self.error_handler.handle_error(
                error=e,
                context="dto_orders_retrieval",
                component="StrategyOrderTracker.get_orders_for_strategy",
                additional_data={"strategy_name": strategy_name},
            )
            return []

    def get_positions_summary(self) -> list[StrategyPositionDTO]:
        """Get all strategy positions as DTOs (new DTO-based interface)."""
        try:
            position_dtos = []

            for (_strategy, _symbol), position in self._positions_cache.items():
                # Only include positions with non-zero quantity
                if position.quantity > 0:
                    dto = self._strategy_position_to_dto(position)
                    position_dtos.append(dto)

            # Sort by strategy, then by symbol for consistent ordering
            position_dtos.sort(key=lambda p: (p.strategy, p.symbol))
            return position_dtos
        except Exception as e:
            self.error_handler.handle_error(
                error=e,
                context="dto_positions_summary",
                component="StrategyOrderTracker.get_positions_summary",
            )
            return []

    def get_pnl_summary(
        self, strategy_name: str, current_prices: dict[str, float] | None = None
    ) -> StrategyPnLDTO:
        """Get strategy P&L as DTO (new DTO-based interface)."""
        try:
            # Validate strategy name
            strategy_type = StrategyType(strategy_name)

            # Get P&L using existing logic
            strategy_pnl = self.get_strategy_pnl(strategy_type, current_prices)

            # Convert to DTO
            return self._strategy_pnl_to_dto(strategy_pnl)
        except ValueError as e:
            valid_strategies = [s.value for s in StrategyType]
            raise ValueError(
                f"Invalid strategy '{strategy_name}'. Valid strategies: {valid_strategies}"
            ) from e
        except Exception as e:
            self.error_handler.handle_error(
                error=e,
                context="dto_pnl_summary",
                component="StrategyOrderTracker.get_pnl_summary",
                additional_data={"strategy_name": strategy_name},
            )
            # Return empty P&L on error
            return StrategyPnLDTO(
                strategy=cast(StrategyLiteral, strategy_name),
                realized_pnl=Decimal("0"),
                unrealized_pnl=Decimal("0"),
                total_pnl=Decimal("0"),
                positions={},
                allocation_value=Decimal("0"),
            )

    # ==================== DTO Conversion Methods ====================

    def _dto_to_strategy_order(self, dto: StrategyOrderDTO) -> StrategyOrder:
        """Convert StrategyOrderDTO to internal StrategyOrder dataclass."""
        return StrategyOrder(
            order_id=dto.order_id,
            strategy=dto.strategy,
            symbol=dto.symbol,
            side=dto.side.upper(),  # Convert to uppercase for internal consistency
            quantity=float(dto.quantity),
            price=float(dto.price),
            timestamp=dto.timestamp.isoformat(),
        )

    def _strategy_order_to_dto(self, order: StrategyOrder) -> StrategyOrderDTO:
        """Convert internal StrategyOrder dataclass to StrategyOrderDTO."""
        # Quantize to enforce max 6 decimal places (DTO validator requirement) and tame float artifacts
        from decimal import ROUND_HALF_UP, Decimal

        qty_dec = Decimal(str(order.quantity)).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
        price_dec = Decimal(str(order.price)).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)

        return StrategyOrderDTO.from_strategy_order_data(
            order_id=order.order_id,
            strategy=order.strategy,
            symbol=order.symbol,
            side=order.side.lower(),  # Convert to lowercase for DTO
            quantity=float(qty_dec),
            price=float(price_dec),
            timestamp=order.timestamp,
        )

    def _strategy_position_to_dto(self, position: StrategyPosition) -> StrategyPositionDTO:
        """Convert internal StrategyPosition dataclass to StrategyPositionDTO."""
        return StrategyPositionDTO.from_position_data(
            strategy=position.strategy,
            symbol=position.symbol,
            quantity=position.quantity,
            average_cost=position.average_cost,
            total_cost=position.total_cost,
            last_updated=position.last_updated,
        )

    def _strategy_pnl_to_dto(self, pnl: StrategyPnL) -> StrategyPnLDTO:
        """Convert internal StrategyPnL dataclass to StrategyPnLDTO."""
        return StrategyPnLDTO.from_pnl_data(
            strategy=pnl.strategy,
            realized_pnl=pnl.realized_pnl,
            unrealized_pnl=pnl.unrealized_pnl,
            total_pnl=pnl.total_pnl,
            positions=pnl.positions,
            allocation_value=pnl.allocation_value,
        )

    # ==================== Enhanced Persistence Methods ====================

    def _dto_to_storage(self, dto: StrategyOrderDTO) -> dict[str, Any]:
        """Convert DTO to storage format."""
        return dto.model_dump(mode="json", exclude_none=True)  # Ensures Decimal serialization

    def _storage_to_dto(self, data: dict[str, Any]) -> StrategyOrderDTO:
        """Convert storage data to DTO."""
        return StrategyOrderDTO.model_validate(data)

    def migrate_existing_tracking_data(self) -> None:
        """Migrate existing tracking data to DTO format."""
        try:
            logging.info("Starting migration of existing tracking data to DTO format...")

            # Load existing raw data
            existing_data = self._load_all_tracking_data()

            migrated_count = 0
            error_count = 0

            for strategy_name, orders in existing_data.items():
                migrated_orders = []

                for order_data in orders:
                    try:
                        # Try to create DTO from existing data
                        if self._is_dto_format(order_data):
                            # Already in DTO format
                            order_dto = StrategyOrderDTO.model_validate(order_data)
                        else:
                            # Older persisted schema - normalize/upgrade to DTO
                            upgraded_data = self._upgrade_legacy_order(order_data)
                            order_dto = StrategyOrderDTO.model_validate(upgraded_data)

                        migrated_orders.append(order_dto)
                        migrated_count += 1

                    except Exception as e:
                        # Handle malformed data
                        self._handle_migration_error(strategy_name, order_data, e)
                        error_count += 1

                # Save migrated data back (optional - for now just validate)
                # self._save_migrated_orders(strategy_name, migrated_orders)

            logging.info(
                f"Migration completed: {migrated_count} orders migrated, {error_count} errors"
            )

        except Exception as e:
            self.error_handler.handle_error(
                error=e,
                context="tracking_data_migration",
                component="StrategyOrderTracker.migrate_existing_tracking_data",
            )
            logging.error(f"Error during tracking data migration: {e}")

    def _load_all_tracking_data(self) -> dict[str, list[dict[str, Any]]]:
        """Load all existing tracking data for migration."""
        all_data: dict[str, list[dict[str, Any]]] = {}

        try:
            orders_path = f"{self.orders_s3_path}recent_orders.json"

            if self.s3_handler.file_exists(orders_path):
                data = self.s3_handler.read_json(orders_path)
                if data and "orders" in data:
                    # Group orders by strategy
                    for order in data["orders"]:
                        strategy = order.get("strategy", "UNKNOWN")
                        if strategy not in all_data:
                            all_data[strategy] = []
                        all_data[strategy].append(order)

        except Exception as e:
            logging.error(f"Error loading tracking data for migration: {e}")

        return all_data

    def _is_dto_format(self, order_data: dict[str, Any]) -> bool:
        """Check if order data is already in DTO format."""
        # Simple check - DTO format should have specific fields and types
        required_fields = {
            "order_id",
            "strategy",
            "symbol",
            "side",
            "quantity",
            "price",
            "timestamp",
        }
        return all(field in order_data for field in required_fields)

    def _upgrade_legacy_order(self, legacy_data: dict[str, Any]) -> dict[str, Any]:
        """Upgrade legacy order format to DTO format."""
        # Create a copy to avoid modifying original
        upgraded = legacy_data.copy()

        # Ensure all required fields are present with defaults
        upgraded.setdefault(
            "order_id",
            f"legacy_{legacy_data.get('symbol', 'unknown')}_{legacy_data.get('timestamp', 'unknown')}",
        )
        upgraded.setdefault("strategy", "UNKNOWN")
        upgraded.setdefault("symbol", "UNKNOWN")
        upgraded.setdefault("side", "buy")
        upgraded.setdefault("quantity", 0.0)
        upgraded.setdefault("price", 0.0)
        upgraded.setdefault("timestamp", datetime.now(UTC).isoformat())

        # Normalize side to lowercase for DTO
        if "side" in upgraded:
            upgraded["side"] = upgraded["side"].lower()

        return upgraded

    def _handle_migration_error(
        self, strategy_name: str, order_data: dict[str, Any], error: Exception
    ) -> None:
        """Handle errors during data migration."""
        self.error_handler.handle_error(
            error=error,
            context="tracking_data_migration_item",
            component="StrategyOrderTracker._handle_migration_error",
            additional_data={
                "strategy_name": strategy_name,
                "order_data_keys": list(order_data.keys()),
                "error_type": type(error).__name__,
            },
        )
        logging.warning(f"Failed to migrate order for {strategy_name}: {error}")

    def _load_order_as_dto(self, order_data: dict[str, Any]) -> StrategyOrderDTO:
        """Load order; if not in current DTO schema attempt structured normalization."""
        try:
            return StrategyOrderDTO.model_validate(order_data)
        except Exception:
            # Attempt normalization/upgrade of older schema
            upgraded_data = self._upgrade_legacy_order(order_data)
            return StrategyOrderDTO.model_validate(upgraded_data)

    # ==================== Private Methods ====================

    def _update_position(self, order: StrategyOrder) -> None:
        """Update position cache with new order."""
        key = (order.strategy, order.symbol)

        if key not in self._positions_cache:
            # Create new position
            self._positions_cache[key] = StrategyPosition(
                strategy=order.strategy,
                symbol=order.symbol,
                quantity=0.0,
                average_cost=0.0,
                total_cost=0.0,
                last_updated=order.timestamp,
            )

        # Update existing position
        self._positions_cache[key].update_with_order(order)

    def _calculate_realized_pnl(self, sell_order: StrategyOrder) -> None:
        """Calculate realized P&L from a sell order."""
        try:
            key = (sell_order.strategy, sell_order.symbol)
            position = self._positions_cache.get(key)

            if not position or position.average_cost <= 0:
                logging.warning(
                    f"No position data for realized P&L calculation: {sell_order.symbol}"
                )
                return

            # Calculate realized P&L for this sale
            cost_basis = sell_order.quantity * position.average_cost
            sale_proceeds = sell_order.quantity * sell_order.price
            realized_pnl = sale_proceeds - cost_basis

            # Add to strategy's total realized P&L
            if sell_order.strategy not in self._realized_pnl_cache:
                self._realized_pnl_cache[sell_order.strategy] = 0.0

            self._realized_pnl_cache[sell_order.strategy] += realized_pnl

            logging.info(
                f"Realized P&L for {sell_order.strategy} {sell_order.symbol}: ${realized_pnl:.2f}"
            )

        except Exception as e:
            self.error_handler.handle_error(
                error=e,
                context="realized_pnl_calculation",
                component="StrategyOrderTracker._calculate_realized_pnl",
                additional_data={
                    "strategy": sell_order.strategy,
                    "symbol": sell_order.symbol,
                    "quantity": sell_order.quantity,
                    "price": sell_order.price,
                },
            )
            logging.error(f"Error calculating realized P&L: {e}")

    def _load_data(self) -> None:
        """Load existing data from S3."""
        try:
            # Load data in this order to ensure dependencies are satisfied
            self._load_recent_orders(days=90)
            self._load_positions()
            self._load_realized_pnl()
        except Exception as e:
            # Graceful degradation for S3 connectivity issues
            if "s3" in str(e).lower() or "aws" in str(e).lower() or "credential" in str(e).lower():
                logging.warning(f"S3 tracking data unavailable, continuing with empty state: {e}")
            else:
                self.error_handler.handle_error(
                    error=e,
                    context="tracker_data_loading",
                    component="StrategyOrderTracker._load_data",
                    additional_data={
                        "load_operations": ["orders", "positions", "realized_pnl"],
                    },
                )
                logging.error(f"Error loading tracker data: {e}")

    def _load_recent_orders(self, days: int = 90) -> None:
        """Load recent orders from S3 with support for both legacy and DTO formats."""
        try:
            # For now, load from a consolidated orders file
            # In production, you might want to partition by date
            orders_path = f"{self.orders_s3_path}recent_orders.json"

            if not self.s3_handler.file_exists(orders_path):
                logging.info("No recent orders file found")
                return

            data = self.s3_handler.read_json(orders_path)
            if not data or "orders" not in data:
                logging.info("No orders data found in file")
                return

            # Process orders with backward compatibility
            for order_data in data["orders"]:
                try:
                    # Try to load as DTO first for validation, then convert to internal format
                    order_dto = self._load_order_as_dto(order_data)
                    order = self._dto_to_strategy_order(order_dto)
                    self._orders_cache.append(order)
                except Exception as e:
                    logging.warning(
                        f"Failed to load order {order_data.get('order_id', 'unknown')}: {e}"
                    )
                    # Continue with other orders

            # Filter to last N days
            self._filter_orders_by_date(days)

            logging.info(f"Loaded {len(self._orders_cache)} recent orders")
        except Exception as e:
            self.error_handler.handle_error(
                error=e,
                context="orders_loading",
                component="StrategyOrderTracker._load_recent_orders",
                additional_data={"days": days},
            )
            logging.error(f"Error loading orders: {e}")

    def _filter_orders_by_date(self, days: int) -> None:
        """Filter orders cache to only include orders from the last N days."""
        if days <= 0 or not self._orders_cache:
            return

        cutoff_date = datetime.now(UTC) - timedelta(days=days)
        cutoff_str = cutoff_date.isoformat()
        self._orders_cache = [o for o in self._orders_cache if o.timestamp >= cutoff_str]

    def _load_positions(self) -> None:
        """Load current positions from S3."""
        try:
            positions_path = f"{self.positions_s3_path}current_positions.json"

            if not self.s3_handler.file_exists(positions_path):
                logging.info("No positions file found")
                return

            data = self.s3_handler.read_json(positions_path)
            if not data or "positions" not in data:
                logging.info("No positions data found in file")
                return

            # Process positions
            for pos_data in data["positions"]:
                pos = StrategyPosition(**pos_data)
                key = (pos.strategy, pos.symbol)
                self._positions_cache[key] = pos

            logging.info(f"Loaded {len(self._positions_cache)} positions")
        except Exception as e:
            self.error_handler.handle_error(
                error=e,
                context="positions_loading",
                component="StrategyOrderTracker._load_positions",
            )
            logging.error(f"Error loading positions: {e}")

    def _load_realized_pnl(self) -> None:
        """Load realized P&L from S3."""
        try:
            pnl_path = f"{self.positions_s3_path}realized_pnl.json"

            if not self.s3_handler.file_exists(pnl_path):
                logging.info("No realized P&L file found")
                return

            data = self.s3_handler.read_json(pnl_path)
            if not data:
                logging.info("No realized P&L data found in file")
                return

            self._realized_pnl_cache = data
            logging.info(f"Loaded realized P&L for {len(data)} strategies")
        except Exception as e:
            self.error_handler.handle_error(
                error=e,
                context="realized_pnl_loading",
                component="StrategyOrderTracker._load_realized_pnl",
            )
            logging.error(f"Error loading realized P&L: {e}")

    def _persist_order(self, order: StrategyOrder) -> None:
        """Persist single order to S3."""
        try:
            orders_path = f"{self.orders_s3_path}recent_orders.json"

            # Load existing data or create new data structure
            existing_data = self.s3_handler.read_json(orders_path) or {"orders": []}

            # Add new order
            existing_data["orders"].append(asdict(order))

            # Apply history limit to prevent file size growth
            self._apply_order_history_limit(existing_data)

            # Save back to S3
            success = self.s3_handler.write_json(orders_path, existing_data)
            if not success:
                logging.warning(f"Failed to save order {order.order_id} to S3")

        except Exception as e:
            self.error_handler.handle_error(
                error=e,
                context="order_persistence",
                component="StrategyOrderTracker._persist_order",
                additional_data={
                    "order_id": order.order_id,
                    "strategy": order.strategy,
                    "symbol": order.symbol,
                },
            )
            logging.error(f"Error persisting order: {e}")

    def _apply_order_history_limit(self, data: dict[str, Any]) -> None:
        """Limit the number of orders kept in history."""
        if len(data["orders"]) > self.order_history_limit:
            data["orders"] = data["orders"][-self.order_history_limit :]

    def _persist_positions(self) -> None:
        """Persist all positions and realized P&L to S3."""
        try:
            # Save positions
            self._persist_positions_data()

            # Save realized P&L
            self._persist_realized_pnl()

        except Exception as e:
            self.error_handler.handle_error(
                error=e,
                context="positions_persistence",
                component="StrategyOrderTracker._persist_positions",
                additional_data={
                    "positions_count": len(self._positions_cache),
                },
            )
            logging.error(f"Error persisting positions: {e}")

    def _persist_positions_data(self) -> None:
        """Save positions data to S3."""
        positions_data = {
            "positions": [asdict(pos) for pos in self._positions_cache.values()],
            "last_updated": datetime.now(UTC).isoformat(),
        }

        positions_path = f"{self.positions_s3_path}current_positions.json"
        success = self.s3_handler.write_json(positions_path, positions_data)
        if not success:
            logging.warning("Failed to save positions data to S3")

    def _persist_realized_pnl(self) -> None:
        """Save realized P&L data to S3."""
        pnl_path = f"{self.positions_s3_path}realized_pnl.json"
        success = self.s3_handler.write_json(pnl_path, self._realized_pnl_cache)
        if not success:
            logging.warning("Failed to save realized P&L data to S3")

    def get_summary_for_email(
        self, current_prices: dict[str, float] | None = None
    ) -> dict[str, Any]:
        """Get summary data suitable for email reporting."""
        try:
            all_pnl = self.get_all_strategy_pnl(current_prices)

            summary: dict[str, Any] = {
                "total_portfolio_pnl": sum(pnl.total_pnl for pnl in all_pnl.values()),
                "total_realized_pnl": sum(pnl.realized_pnl for pnl in all_pnl.values()),
                "total_unrealized_pnl": sum(pnl.unrealized_pnl for pnl in all_pnl.values()),
                "strategies": {},
            }

            for strategy, pnl in all_pnl.items():
                summary["strategies"][strategy.value] = {
                    "realized_pnl": pnl.realized_pnl,
                    "unrealized_pnl": pnl.unrealized_pnl,
                    "total_pnl": pnl.total_pnl,
                    "total_return_pct": pnl.total_return_pct,
                    "allocation_value": pnl.allocation_value,
                    "position_count": len([q for q in pnl.positions.values() if q > 0]),
                }

            return summary

        except Exception as e:
            self.error_handler.handle_error(
                error=e,
                context="email_summary_generation",
                component="StrategyOrderTracker.get_summary_for_email",
            )
            logging.error(f"Error generating email summary: {e}")
            return {}


# Global instances for easy access - separate by trading mode
_strategy_tracker_paper: StrategyOrderTracker | None = None
_strategy_tracker_live: StrategyOrderTracker | None = None


def get_strategy_tracker(
    paper_trading: bool = True,
) -> StrategyOrderTracker:
    """Get or create strategy order tracker instance for specified trading mode.

    Args:
        paper_trading: Whether to get the paper trading tracker (default: True)

    Returns:
        StrategyOrderTracker: The appropriate tracker instance

    """
    global _strategy_tracker_paper, _strategy_tracker_live

    if paper_trading:
        if _strategy_tracker_paper is None:
            _strategy_tracker_paper = StrategyOrderTracker(paper_trading=True)
        return _strategy_tracker_paper
    if _strategy_tracker_live is None:
        _strategy_tracker_live = StrategyOrderTracker(paper_trading=False)
    return _strategy_tracker_live
