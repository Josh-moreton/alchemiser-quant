#!/usr/bin/env python3
"""
Strategy Order Tracker for Per-Strategy P&L Management

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

import logging
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from the_alchemiser.domain.strategies.strategy_manager import StrategyType
from the_alchemiser.infrastructure.config import load_settings
from the_alchemiser.infrastructure.s3.s3_utils import get_s3_handler
from the_alchemiser.services.exceptions import DataProviderError, StrategyExecutionError

# TODO: Add these imports once data structures match:
# from ..core.types import OrderHistoryData, EmailSummary


@dataclass  # TODO(PYDANTIC-MIGRATION): Evaluate if StrategyOrder should become Pydantic (timestamp auto & side enum) or remain simple; currently used as persistence record.
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
    ) -> "StrategyOrder":
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


@dataclass  # TODO(PYDANTIC-MIGRATION): StrategyPosition may benefit from Pydantic for invariants (quantity>=0 when closed) and computed fields.
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


@dataclass  # TODO(PYDANTIC-MIGRATION): StrategyPnL could remain dataclass or move to Pydantic for serialization consistency; low priority.
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

        # Initialize S3 paths for data persistence
        self._setup_s3_paths()

        # Initialize in-memory caches
        self._orders_cache: list[StrategyOrder] = []
        self._positions_cache: dict[tuple[str, str], StrategyPosition] = (
            {}
        )  # (strategy, symbol) -> position
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

        except StrategyExecutionError as e:
            from ..core.logging.logging_utils import get_logger, log_error_with_context

            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                e,
                "order_recording",
                function="record_order",
                order_id=order_id,
                strategy=strategy.value,
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                error_type=type(e).__name__,
            )
            logging.error(f"Strategy execution error recording order {order_id}: {e}")
        except DataProviderError as e:
            from ..core.logging.logging_utils import get_logger, log_error_with_context

            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                e,
                "order_recording",
                function="record_order",
                order_id=order_id,
                strategy=strategy.value,
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                error_type="unexpected_error",
                original_error=type(e).__name__,
            )
            logging.error(f"Unexpected error recording order {order_id}: {e}")

    def _process_order(self, order: StrategyOrder) -> None:
        """Process a new order - update caches and persist to S3."""
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
        self, strategy: StrategyType | None = None, symbol: str | None = None, days: int = 30
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

            # Create archive record
            archive_data = {
                "date": today,
                "timestamp": datetime.now(UTC).isoformat(),
                "strategies": {strategy.value: asdict(pnl) for strategy, pnl in all_pnl.items()},
            }

            # Save to S3
            archive_path = f"{self.pnl_history_s3_path}{today}.json"
            success = self.s3_handler.write_json(archive_path, archive_data)

            if success:
                logging.info(f"Archived daily P&L snapshot for {today}")
            else:
                logging.error(f"Failed to archive daily P&L for {today}")

        except DataProviderError as e:
            from ..core.logging.logging_utils import get_logger, log_error_with_context

            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                e,
                "pnl_archive_data_error",
                function="archive_daily_pnl",
                date=today,
                strategies_count=len(all_pnl) if "all_pnl" in locals() else 0,
                error_type=type(e).__name__,
            )
            logging.error(f"Data provider error archiving daily P&L: {e}")
        except StrategyExecutionError as e:
            from ..core.logging.logging_utils import get_logger, log_error_with_context

            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                e,
                "pnl_archive_error",
                function="archive_daily_pnl",
                date=today if "today" in locals() else "unknown",
                error_type="unexpected_error",
                original_error=type(e).__name__,
            )
            logging.error(f"Unexpected error archiving daily P&L: {e}")

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

        except StrategyExecutionError as e:
            from ..core.logging.logging_utils import get_logger, log_error_with_context

            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                e,
                "realized_pnl_calculation",
                function="_calculate_realized_pnl",
                strategy=sell_order.strategy,
                symbol=sell_order.symbol,
                quantity=sell_order.quantity,
                price=sell_order.price,
                error_type=type(e).__name__,
            )
            logging.error(f"Strategy execution error calculating realized P&L: {e}")
        except DataProviderError as e:
            from ..core.logging.logging_utils import get_logger, log_error_with_context

            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                e,
                "realized_pnl_calculation",
                function="_calculate_realized_pnl",
                strategy=sell_order.strategy,
                symbol=sell_order.symbol,
                quantity=sell_order.quantity,
                price=sell_order.price,
                error_type="unexpected_error",
                original_error=type(e).__name__,
            )
            logging.error(f"Unexpected error calculating realized P&L: {e}")

    def _load_data(self) -> None:
        """Load existing data from S3."""
        try:
            # Load data in this order to ensure dependencies are satisfied
            self._load_recent_orders(days=90)
            self._load_positions()
            self._load_realized_pnl()
        except DataProviderError as e:
            from ..core.logging.logging_utils import get_logger, log_error_with_context

            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                e,
                "tracker_data_loading",
                function="_load_data",
                load_operations=["orders", "positions", "realized_pnl"],
                error_type=type(e).__name__,
            )
            logging.error(f"Data provider error loading tracker data: {e}")
        except StrategyExecutionError as e:
            from ..core.logging.logging_utils import get_logger, log_error_with_context

            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                e,
                "tracker_data_loading",
                function="_load_data",
                load_operations=["orders", "positions", "realized_pnl"],
                error_type="unexpected_error",
                original_error=type(e).__name__,
            )
            logging.error(f"Unexpected error loading tracker data: {e}")

    def _load_recent_orders(self, days: int = 90) -> None:
        """Load recent orders from S3."""
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

            # Process orders
            for order_data in data["orders"]:
                order = StrategyOrder(**order_data)
                self._orders_cache.append(order)

            # Filter to last N days
            self._filter_orders_by_date(days)

            logging.info(f"Loaded {len(self._orders_cache)} recent orders")
        except DataProviderError as e:
            from ..core.logging.logging_utils import get_logger, log_error_with_context

            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                e,
                "orders_loading",
                function="_load_recent_orders",
                days=days,
                error_type=type(e).__name__,
            )
            logging.error(f"Data provider error loading orders: {e}")

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
        except DataProviderError as e:
            from ..core.logging.logging_utils import get_logger, log_error_with_context

            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                e,
                "positions_loading",
                function="_load_positions",
                error_type=type(e).__name__,
            )
            logging.error(f"Data provider error loading positions: {e}")

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
        except DataProviderError as e:
            from ..core.logging.logging_utils import get_logger, log_error_with_context

            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                e,
                "realized_pnl_loading",
                function="_load_realized_pnl",
                error_type=type(e).__name__,
            )
            logging.error(f"Data provider error loading realized P&L: {e}")

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

        except DataProviderError as e:
            from ..core.logging.logging_utils import get_logger, log_error_with_context

            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                e,
                "order_persistence",
                function="_persist_order",
                order_id=order.order_id,
                strategy=order.strategy,
                symbol=order.symbol,
                error_type=type(e).__name__,
            )
            logging.error(f"Data provider error persisting order: {e}")

    def _apply_order_history_limit(
        self, data: dict[str, Any]
    ) -> None:  # TODO: Change to OrderHistoryData once data structure matches
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

        except DataProviderError as e:
            from ..core.logging.logging_utils import get_logger, log_error_with_context

            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                e,
                "positions_persistence",
                function="_persist_positions",
                positions_count=len(self._positions_cache),
                error_type=type(e).__name__,
            )
            logging.error(f"Data provider error persisting positions: {e}")

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
    ) -> dict[str, Any]:  # TODO: Change to EmailSummary once data structure matches
        """Get summary data suitable for email reporting."""
        try:
            all_pnl = self.get_all_strategy_pnl(current_prices)

            summary: dict[str, Any] = {  # TODO: Change to EmailSummary once data structure matches
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

        except StrategyExecutionError as e:
            from ..core.logging.logging_utils import get_logger, log_error_with_context

            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                e,
                "email_summary_generation",
                function="get_summary_for_email",
                error_type=type(e).__name__,
            )
            logging.error(f"Strategy execution error generating email summary: {e}")
            return {}


# Global instances for easy access - separate by trading mode
_strategy_tracker_paper = None
_strategy_tracker_live = None


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
    else:
        if _strategy_tracker_live is None:
            _strategy_tracker_live = StrategyOrderTracker(paper_trading=False)
        return _strategy_tracker_live
