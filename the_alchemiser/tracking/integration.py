#!/usr/bin/env python3
"""
Trading Engine Integration for Strategy Order Tracker

This module provides integration between the trading engine and strategy order tracker
to automatically capture and track orders by strategy for P&L calculations.

Key Features:
- Automatic order tracking when orders are executed
- Strategy context preservation through the execution chain
- Integration with existing TradingEngine and SmartExecution
- Minimal changes to existing code patterns
"""

import logging
from contextlib import contextmanager
from typing import Any

from the_alchemiser.core.trading.strategy_manager import StrategyType
from the_alchemiser.tracking.strategy_order_tracker import get_strategy_tracker

# TODO: Add these imports once data structures match:
# from ..core.types import StrategyPnLSummary, OrderDetails, AlpacaOrderProtocol


class StrategyExecutionContext:
    """Context manager to track which strategy is currently executing orders."""

    _current_strategy: StrategyType | None = None
    _order_tracker = None

    @classmethod
    def set_current_strategy(cls, strategy: StrategyType) -> None:
        """Set the currently executing strategy."""
        cls._current_strategy = strategy
        if cls._order_tracker is None:
            cls._order_tracker = get_strategy_tracker()

    @classmethod
    def get_current_strategy(cls) -> StrategyType | None:
        """Get the currently executing strategy."""
        return cls._current_strategy

    @classmethod
    def clear_current_strategy(cls) -> None:
        """Clear the current strategy context."""
        cls._current_strategy = None

    @classmethod
    def record_order_if_active(
        cls, order_id: str, symbol: str, side: str, quantity: float, price: float
    ) -> None:
        """Record an order if there's an active strategy context."""
        if cls._current_strategy and cls._order_tracker and order_id:
            try:
                cls._order_tracker.record_order(
                    order_id=order_id,
                    strategy=cls._current_strategy,
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                    price=price,
                )
                logging.info(
                    f"Tracked {cls._current_strategy.value} order: {side} {quantity} {symbol} @ ${price:.2f}"
                )
            except Exception as e:
                logging.error(f"Failed to track order {order_id}: {e}")


@contextmanager
def strategy_execution_context(
    strategy: StrategyType,
) -> Any:  # TODO: Phase 15 - Added return type for context manager
    """Context manager for strategy execution tracking."""
    StrategyExecutionContext.set_current_strategy(strategy)
    try:
        yield
    finally:
        StrategyExecutionContext.clear_current_strategy()


def track_order_execution(
    order_id: str, symbol: str, side: str, quantity: float, price: float
) -> None:
    """Track an order execution in the current strategy context."""
    StrategyExecutionContext.record_order_if_active(order_id, symbol, side, quantity, price)


def get_current_strategy_context() -> StrategyType | None:
    """Get the current strategy context for debugging/logging."""
    return StrategyExecutionContext.get_current_strategy()


# Integration helper functions for existing code


def create_strategy_aware_order_callback(original_order_function):
    """Decorator to make order functions strategy-aware."""

    def wrapper(*args, **kwargs):
        # Execute original order function
        result = original_order_function(*args, **kwargs)

        # If we got an order ID back and have strategy context, track it
        if result and isinstance(result, str):  # Order ID
            # Extract order details from args/kwargs
            # This would need to be customized based on the specific function signature
            # For now, just log that we have an order to track
            current_strategy = StrategyExecutionContext.get_current_strategy()
            if current_strategy:
                logging.debug(f"Order {result} executed in {current_strategy.value} context")

        return result

    return wrapper


class StrategyTrackingMixin:
    """Mixin class to add strategy tracking to trading components."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._strategy_tracker = get_strategy_tracker()

    def track_filled_order(
        self, order_id: str, symbol: str, side: str, quantity: float, price: float
    ) -> None:
        """Track a filled order with strategy context."""
        current_strategy = StrategyExecutionContext.get_current_strategy()
        if current_strategy:
            self._strategy_tracker.record_order(
                order_id=order_id,
                strategy=current_strategy,
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
            )

    def get_strategy_pnl_summary(
        self, current_prices: dict[str, float] | None = None
    ) -> dict[str, Any]:  # TODO: Change to StrategyPnLSummary once data structure matches
        """Get P&L summary for all strategies."""
        return self._strategy_tracker.get_summary_for_email(current_prices)


# Helper function to extract order details from Alpaca order objects
def extract_order_details_from_alpaca_order(
    order: Any,  # TODO: Phase 15 - Use AlpacaOrderProtocol when ready
) -> dict[str, Any]:  # TODO: Phase 15 - Return OrderDetails when structure matches
    """Extract order details from Alpaca order object for tracking."""
    try:
        # Handle both order response objects and order status objects
        order_id = str(getattr(order, "id", "unknown"))
        symbol = str(getattr(order, "symbol", ""))
        side = str(getattr(order, "side", "")).upper()

        # Get quantity - could be qty or filled_qty
        quantity = float(getattr(order, "filled_qty", 0) or getattr(order, "qty", 0) or 0)

        # Get price - could be filled_avg_price, limit_price, or market price
        price = float(
            getattr(order, "filled_avg_price", 0)
            or getattr(order, "limit_price", 0)
            or getattr(order, "price", 0)
            or 0
        )

        return {
            "order_id": order_id,
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": price,
        }
    except Exception as e:
        logging.error(f"Error extracting order details: {e}")
        return {}


def track_alpaca_order_if_filled(
    order: Any,
) -> None:  # TODO: Phase 15 - Use AlpacaOrderProtocol when ready
    """Track an Alpaca order if it's filled and we have strategy context."""
    try:
        # Check if order is filled
        status = str(getattr(order, "status", "")).lower()
        if "filled" not in status:
            return

        # Extract order details
        details = extract_order_details_from_alpaca_order(order)
        if not details or not details.get("order_id") or details.get("quantity", 0) <= 0:
            return

        # Track the order
        track_order_execution(
            order_id=details["order_id"],
            symbol=details["symbol"],
            side=details["side"],
            quantity=details["quantity"],
            price=details["price"],
        )

    except Exception as e:
        logging.error(f"Error tracking Alpaca order: {e}")


# Configuration helper
def configure_strategy_tracking_integration(
    trading_engine: Any,
) -> None:  # TODO: Phase 15 - Use TradingEngine type when ready
    """Configure strategy tracking integration with existing trading engine."""
    try:
        # Add tracking mixin to trading engine if it doesn't already have it
        if not hasattr(trading_engine, "_strategy_tracker"):
            trading_engine._strategy_tracker = get_strategy_tracker()
            trading_engine.get_strategy_pnl_summary = (
                lambda prices=None: trading_engine._strategy_tracker.get_summary_for_email(prices)
            )

            logging.info("Strategy tracking integration configured for trading engine")

    except Exception as e:
        logging.error(f"Error configuring strategy tracking integration: {e}")


# Export key functions for easy importing
__all__ = [
    "StrategyExecutionContext",
    "strategy_execution_context",
    "track_order_execution",
    "get_current_strategy_context",
    "StrategyTrackingMixin",
    "track_alpaca_order_if_filled",
    "configure_strategy_tracking_integration",
]
