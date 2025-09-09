#!/usr/bin/env python3
"""Business Unit: order execution/placement; Status: current.

Smart Execution Engine with Professional Order Strategy.

This module provides sophisticated order execution using the Better Orders strategy:
- Aggressive marketable limits (ask+1¢ for buys, bid-1¢ for sells)
- Market timing logic for 9:30-9:35 ET execution
- Fast 2-3 second timeouts with re-pegging
- Designed for leveraged ETFs and high-volume trading
- Market order fallback for execution certainty

Refactored to use composition instead of thin proxy methods.
Focuses on execution strategy logic while delegating order placement to specialized components.
"""

from __future__ import annotations

import logging
import time
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Protocol

from the_alchemiser.execution.config.execution_config import (
    ExecutionConfig,
    get_execution_config,
)
from the_alchemiser.execution.core.execution_schemas import WebSocketResultDTO
from the_alchemiser.execution.core.executor import (
    CanonicalOrderExecutor,
)
from the_alchemiser.execution.orders.order_types import (
    OrderType as DomainOrderType,
)
from the_alchemiser.execution.orders.order_types import Side as DomainSide
from the_alchemiser.execution.orders.schemas import OrderRequest
from the_alchemiser.shared.types.broker_enums import BrokerOrderSide
from the_alchemiser.shared.types.money import Money
from the_alchemiser.shared.types.quantity import (
    Quantity as DomainQuantity,
)
from the_alchemiser.shared.types.time_in_force import (
    TimeInForce as DomainTimeInForce,
)
from the_alchemiser.shared.value_objects.symbol import Symbol as DomainSymbol

if TYPE_CHECKING:
    pass
from the_alchemiser.shared.types.exceptions import (
    BuyingPowerError,
    DataProviderError,
    OrderExecutionError,
    OrderPlacementError,
    SpreadAnalysisError,
    TradingClientError,
)


class OrderExecutor(Protocol):
    """Protocol for minimal dependencies required by SmartExecution.

    Legacy direct order placement methods removed; SmartExecution now builds
    canonical OrderRequest objects internally and uses CanonicalOrderExecutor.
    """

    def place_smart_sell_order(self, symbol: str, qty: float) -> str | None: ...
    def liquidate_position(self, symbol: str) -> str | None: ...
    def get_current_positions(self) -> dict[str, float]: ...
    def wait_for_order_completion(
        self, order_ids: list[str], max_wait_seconds: int = 30
    ) -> WebSocketResultDTO: ...

    @property
    def trading_client(self) -> Any: ...  # noqa: ANN401  # External SDK trading client for backward compatibility

    @property
    def data_provider(self) -> DataProvider: ...


class DataProvider(Protocol):
    """Protocol for data provider components."""

    def get_current_price(self, symbol: str) -> float | None:
        """Get current price for a symbol."""
        ...

    def get_latest_quote(
        self, symbol: str
    ) -> tuple[float, float] | None:  # Phase 5: precise tuple typing for bid/ask
        """Get latest quote for a symbol."""
        ...


def is_market_open(trading_client: Any) -> bool:  # noqa: ANN401  # External SDK trading client object
    """Check if the market is currently open."""
    try:
        clock = trading_client.get_clock()
        return getattr(clock, "is_open", False)
    except TradingClientError:
        # If we can't get market status, assume closed for safety
        return False
    except Exception:
        # For any unexpected errors, assume market is closed for safety
        return False


class SmartExecution:
    """Professional execution engine using Better Orders strategy.

    Execution responsibilities only; order placement delegated to injected executor.
    """

    def __init__(
        self,
        order_executor: OrderExecutor,
        data_provider: DataProvider,
        ignore_market_hours: bool = False,
        account_info_provider: Any = None,  # noqa: ANN401  # External provider with dynamic interface
        enable_market_order_fallback: bool = False,  # Feature flag for market order fallback
        execution_config: (ExecutionConfig | None) = None,  # Phase 2: Adaptive configuration
        # Phase 5: Lifecycle tracking removed - delegated to canonical executor
    ) -> None:
        """Initialize with dependency injection for execution and data access."""
        self._order_executor = order_executor
        self._data_provider = data_provider
        self._trading_client = getattr(order_executor, "trading_client", None)
        self._account_info_provider = account_info_provider
        self.ignore_market_hours = ignore_market_hours
        self.enable_market_order_fallback = enable_market_order_fallback
        self.execution_config = (
            execution_config or get_execution_config()
        )  # Phase 2: Use global config if not provided

        self.logger = logging.getLogger(__name__)

    # Canonical order submission helpers replacing legacy market/limit methods
    def _submit_canonical_market_order(
        self,
        symbol: str,
        side: BrokerOrderSide,
        qty: float | None = None,
        notional: float | None = None,
    ) -> str | None:
        """Submit a market order through the CanonicalOrderExecutor.

        Quantity takes precedence; notional converted using current price. Returns order id or None.
        """
        try:
            if qty is None:
                if notional is None:
                    self.logger.error(
                        "market_order_missing_qty_and_notional",
                        extra={"symbol": symbol},
                    )
                    return None
                price = None
                try:
                    price = self._data_provider.get_current_price(symbol)
                except Exception as e:
                    self.logger.warning(
                        "price_lookup_failed_for_notional_conversion",
                        extra={"symbol": symbol, "error": str(e)},
                    )
                if not price or price <= 0:
                    self.logger.warning(
                        "price_unavailable_cannot_convert_notional",
                        extra={"symbol": symbol, "notional": notional},
                    )
                    return None
                qty = float(notional / price)
            if qty <= 0:
                self.logger.warning(
                    "non_positive_quantity_aborting_market_order",
                    extra={"symbol": symbol, "qty": qty},
                )
                return None

            # Use order executor directly (now AlpacaManager after Phase 3 consolidation)
            from the_alchemiser.shared.brokers import AlpacaManager

            if not isinstance(self._order_executor, AlpacaManager):
                raise ValueError("Order executor must be AlpacaManager for canonical executor")

            side_value = "buy" if side.value.lower() == "buy" else "sell"
            # Type assertion is safe since we control the values above
            side_literal = side_value if side_value in ("buy", "sell") else "buy"
            order_request = OrderRequest(
                symbol=DomainSymbol(symbol),
                side=DomainSide(side_literal),  # type: ignore[arg-type]
                quantity=DomainQuantity(Decimal(str(qty))),
                order_type=DomainOrderType("market"),
                time_in_force=DomainTimeInForce("day"),
            )
            executor = CanonicalOrderExecutor(self._order_executor)
            result = executor.execute(order_request)
            if result.success:
                return result.order_id
            self.logger.error(
                "canonical_market_order_failed",
                extra={"symbol": symbol, "error": result.error},
            )
            return None
        except Exception as e:
            self.logger.error(
                "canonical_market_order_exception",
                extra={"symbol": symbol, "error": str(e)},
            )
            return None

    def _submit_canonical_limit_order(
        self,
        symbol: str,
        side: BrokerOrderSide,
        qty: float,
        limit_price: float,
    ) -> str | None:
        """Submit a limit order through the CanonicalOrderExecutor."""
        try:
            if qty <= 0 or limit_price <= 0:
                self.logger.warning(
                    "invalid_limit_order_params",
                    extra={"symbol": symbol, "qty": qty, "limit_price": limit_price},
                )
                return None

            side_value = "buy" if side.value.lower() == "buy" else "sell"
            # Type assertion is safe since we control the values above
            side_literal = side_value if side_value in ("buy", "sell") else "buy"
            order_request = OrderRequest(
                symbol=DomainSymbol(symbol),
                side=DomainSide(side_literal),  # type: ignore[arg-type]
                quantity=DomainQuantity(Decimal(str(qty))),
                order_type=DomainOrderType("limit"),
                time_in_force=DomainTimeInForce("day"),
                limit_price=Money(amount=Decimal(str(limit_price)), currency="USD"),
            )

            # Use order executor directly (now AlpacaManager after Phase 3 consolidation)
            from the_alchemiser.shared.brokers import AlpacaManager

            if not isinstance(self._order_executor, AlpacaManager):
                raise ValueError("Order executor must be AlpacaManager for canonical executor")

            executor = CanonicalOrderExecutor(self._order_executor)
            result = executor.execute(order_request)
            if result.success:
                return result.order_id
            self.logger.error(
                "canonical_limit_order_failed",
                extra={"symbol": symbol, "error": result.error},
            )
            return None
        except Exception as e:
            self.logger.error(
                "canonical_limit_order_exception",
                extra={"symbol": symbol, "error": str(e)},
            )
            return None

    def execute_safe_sell(self, symbol: str, target_qty: float) -> str | None:
        """Execute a safe sell using the configured order executor.

        Focuses on safe selling logic while delegating actual order placement.
        """
        return self._order_executor.place_smart_sell_order(symbol, target_qty)

    def execute_liquidation(self, symbol: str) -> str | None:
        """Execute full position liquidation using the configured order executor."""
        return self._order_executor.liquidate_position(symbol)

    def place_order(
        self,
        symbol: str,
        qty: float,
        side: BrokerOrderSide,
        max_retries: int = 3,
        poll_timeout: int = 30,
        poll_interval: float = 2.0,
        slippage_bps: float | None = None,
        notional: float | None = None,
        max_slippage_bps: float | None = None,
    ) -> str | None:
        """Place order using professional Better Orders execution strategy.

        Consolidated execution pathway: delegates to CanonicalOrderExecutor via
        _submit_canonical_market_order() and AggressiveLimitStrategy execution.

        Implements the 5-step execution ladder:
        1. Market timing assessment (9:30-9:35 ET logic)
        2. Aggressive marketable limit (ask+1¢ for buys, bid-1¢ for sells)
        3. Re-peg sequence (max 2 attempts, 2-3s timeouts)
        4. Market order fallback for execution certainty

        Args:
            symbol: Stock symbol
            qty: Quantity to trade (shares)
            side: OrderSide.BUY or OrderSide.SELL
            notional: For BUY orders, dollar amount instead of shares
            max_slippage_bps: Maximum slippage tolerance in basis points

        Returns:
            Order ID if successful, None otherwise

        """
        try:
            # Step 1: Handle notional orders and validate parameters
            validated_qty = self._handle_notional_order_conversion(symbol, qty, side, notional)

            # Step 2: Market timing and spread assessment
            return self._execute_order_with_timing_strategy(symbol, validated_qty, side)

        except (BuyingPowerError, SpreadAnalysisError) as e:
            # These errors should not fallback to market orders
            self._log_non_fallback_error(symbol, e)
            raise e
        except (OrderExecutionError, DataProviderError, Exception) as e:
            # These errors may fallback to market orders based on feature flag
            return self._handle_execution_error_with_fallback(symbol, validated_qty, side, e)

    def _handle_notional_order_conversion(
        self, symbol: str, qty: float, side: BrokerOrderSide, notional: float | None
    ) -> float:
        """Convert notional orders to quantity and validate buying power."""
        if side != BrokerOrderSide.BUY or notional is None:
            return qty

        try:
            current_price = self._data_provider.get_current_price(symbol)
            if not current_price or current_price <= 0:
                self.logger.warning(
                    "invalid_price_using_market_order",
                    extra={"symbol": symbol, "side": side.value, "notional": notional},
                )
                raise DataProviderError(f"Invalid price for {symbol}: {current_price}")

            validated_qty = self._calculate_quantity_from_notional(
                symbol, notional, current_price, side
            )

            if validated_qty <= 0:
                self.logger.warning(
                    "quantity_too_small_using_market_order",
                    extra={
                        "symbol": symbol,
                        "side": side.value,
                        "calculated_qty": validated_qty,
                        "notional": notional,
                    },
                )
                raise DataProviderError(
                    f"Calculated quantity too small for {symbol}: {validated_qty}"
                )

            return validated_qty

        except DataProviderError:
            self.logger.warning(
                "price_unavailable_using_market_order",
                extra={"symbol": symbol, "side": side.value, "quantity": qty},
            )
            raise DataProviderError(f"Price unavailable for {symbol}")

    def _calculate_quantity_from_notional(
        self, symbol: str, notional: float, current_price: float, side: BrokerOrderSide
    ) -> float:
        """Calculate quantity from notional amount with buying power validation."""
        raw_qty = notional / current_price
        rounded_qty = int(raw_qty * 1e6) / 1e6  # Round down to 6 decimals

        # Check buying power if available
        if self._account_info_provider and side == BrokerOrderSide.BUY:
            try:
                account_info = self._account_info_provider.get_account_info()
                available_cash = float(account_info.get("cash", 0))
                order_value = rounded_qty * current_price

                if order_value > available_cash:
                    rounded_qty = self._adjust_quantity_for_buying_power(
                        symbol, rounded_qty, current_price, available_cash, order_value
                    )
            except Exception as e:
                self.logger.warning(f"Could not check buying power: {e}")

        return rounded_qty * 0.99  # Scale to 99% to avoid buying power issues

    def _adjust_quantity_for_buying_power(
        self,
        symbol: str,
        original_qty: float,
        current_price: float,
        available_cash: float,
        order_value: float,
    ) -> float:
        """Adjust quantity to fit available buying power."""
        max_affordable_qty = (available_cash * 0.95) / current_price
        if max_affordable_qty > 0:
            self.logger.info(
                "order_scaled_to_available_cash",
                extra={
                    "symbol": symbol,
                    "original_qty": original_qty,
                    "scaled_qty": max_affordable_qty,
                    "available_cash": available_cash,
                },
            )
            return max_affordable_qty
        self.logger.error(
            "insufficient_buying_power_order_rejected",
            extra={
                "symbol": symbol,
                "requested_value": order_value,
                "available_cash": available_cash,
            },
        )
        raise BuyingPowerError(
            f"Insufficient buying power for {symbol} order: ${order_value:.2f} required, ${available_cash:.2f} available",
            symbol=symbol,
            required_amount=order_value,
            available_amount=available_cash,
        )

    def _execute_order_with_timing_strategy(
        self, symbol: str, qty: float, side: BrokerOrderSide
    ) -> str | None:
        """Execute order with market timing and spread assessment."""
        from the_alchemiser.execution.pricing.spread_assessment import SpreadAssessment
        from the_alchemiser.execution.timing.market_timing_utils import MarketOpenTimingEngine

        timing_engine = MarketOpenTimingEngine()
        spread_assessor = SpreadAssessment(self._data_provider)

        strategy = timing_engine.get_execution_strategy()
        self.logger.info(
            "execution_strategy_selected",
            extra={
                "symbol": symbol,
                "side": side.value,
                "quantity": qty,
                "strategy": getattr(strategy, "value", str(strategy)),
            },
        )

        # Get quote and assess spread
        bid, ask, spread_analysis = self._get_quote_and_assess_spread(
            symbol, side, qty, spread_assessor
        )

        # Wait for spread normalization if needed
        if not timing_engine.should_execute_immediately(spread_analysis.spread_cents, strategy):
            bid, ask, spread_analysis = self._wait_for_spread_normalization(
                symbol, side, qty, timing_engine, spread_assessor, strategy, spread_analysis
            )

        # Execute aggressive limit sequence
        return self._execute_aggressive_limit_sequence(symbol, qty, side, bid, ask, strategy)

    def _get_quote_and_assess_spread(
        self, symbol: str, side: BrokerOrderSide, qty: float, spread_assessor
    ) -> tuple[float, float, Any]:
        """Get current quote and assess spread quality."""
        quote = self._order_executor.data_provider.get_latest_quote(symbol)
        if not quote or len(quote) < 2:
            self.logger.warning(
                "no_valid_quote_using_market_order",
                extra={"symbol": symbol, "side": side.value, "quantity": qty},
            )
            raise DataProviderError(f"No valid quote available for {symbol}")

        bid, ask = float(quote[0]), float(quote[1])

        if bid <= 0 or ask <= 0:
            self.logger.warning(
                "invalid_quote_using_market_order",
                extra={"symbol": symbol, "side": side.value, "quantity": qty},
            )
            raise DataProviderError(f"Invalid quote for {symbol}: bid={bid}, ask={ask}")

        spread_analysis = spread_assessor.analyze_current_spread(symbol, bid, ask)
        self.logger.debug(
            "spread_assessed",
            extra={
                "symbol": symbol,
                "spread_cents": spread_analysis.spread_cents,
                "spread_quality": spread_analysis.spread_quality.value,
            },
        )

        return bid, ask, spread_analysis

    def _wait_for_spread_normalization(
        self,
        symbol: str,
        side: BrokerOrderSide,
        qty: float,
        timing_engine,
        spread_assessor,
        strategy,
        spread_analysis,
    ) -> tuple[float, float, Any]:
        """Wait for spread to normalize and reassess."""
        wait_time = timing_engine.get_wait_time_seconds(strategy, spread_analysis.spread_cents)
        self.logger.info(
            "waiting_for_spread_normalization",
            extra={
                "symbol": symbol,
                "wait_seconds": wait_time,
                "spread_cents": spread_analysis.spread_cents,
            },
        )
        time.sleep(wait_time)

        # Re-assess after waiting
        quote = self._order_executor.data_provider.get_latest_quote(symbol)
        if not quote or len(quote) < 2:
            self.logger.warning(
                "no_valid_quote_after_wait_using_market_order",
                extra={"symbol": symbol, "side": side.value, "quantity": qty},
            )
            raise DataProviderError(f"No valid quote available for {symbol} after waiting")

        bid, ask = float(quote[0]), float(quote[1])
        spread_analysis = spread_assessor.analyze_current_spread(symbol, bid, ask)
        self.logger.debug(
            "spread_reassessed",
            extra={"symbol": symbol, "updated_spread_cents": spread_analysis.spread_cents},
        )

        return bid, ask, spread_analysis

    def _log_non_fallback_error(self, symbol: str, error: Exception) -> None:
        """Log errors that should not fallback to market orders."""
        if isinstance(error, BuyingPowerError):
            self.logger.error(
                "buying_power_error",
                extra={
                    "symbol": symbol,
                    "error": str(error),
                    "phase": "better_orders_main",
                    "required_amount": getattr(error, "required_amount", None),
                    "available_amount": getattr(error, "available_amount", None),
                    "shortfall": getattr(error, "shortfall", None),
                },
            )
            self.logger.error(
                "insufficient_buying_power_no_fallback",
                extra={"symbol": symbol, "error": str(error)},
            )
        elif isinstance(error, SpreadAnalysisError):
            self.logger.error(
                "spread_analysis_error",
                extra={
                    "symbol": symbol,
                    "error": str(error),
                    "phase": "better_orders_main",
                    "bid": getattr(error, "bid", None),
                    "ask": getattr(error, "ask", None),
                    "spread_cents": getattr(error, "spread_cents", None),
                },
            )
            self.logger.error(
                "spread_analysis_failed_no_fallback", extra={"symbol": symbol, "error": str(error)}
            )

    def _handle_execution_error_with_fallback(
        self, symbol: str, qty: float, side: BrokerOrderSide, error: Exception
    ) -> str | None:
        """Handle execution errors with optional market order fallback."""
        if isinstance(error, OrderExecutionError):
            return self._handle_order_execution_error(symbol, qty, side, error)
        if isinstance(error, DataProviderError):
            return self._handle_data_provider_error(symbol, qty, side, error)
        return self._handle_unclassified_error(symbol, qty, side, error)

    def _handle_order_execution_error(
        self, symbol: str, qty: float, side: BrokerOrderSide, error: OrderExecutionError
    ) -> str | None:
        """Handle order execution errors with fallback logic."""
        self.logger.error(
            "order_execution_error",
            extra={
                "symbol": symbol,
                "error": str(error),
                "error_type": type(error).__name__,
                "phase": "better_orders_main",
            },
        )

        if self.enable_market_order_fallback:
            self.logger.info(
                "market_order_fallback_triggered",
                extra={
                    "symbol": symbol,
                    "reason": "order_execution_error",
                    "original_error": str(error),
                },
            )
            return self._submit_canonical_market_order(symbol, side, qty=qty)

        self.logger.error(
            "order_execution_failed_fallback_disabled",
            extra={"symbol": symbol, "error": str(error), "fallback_enabled": False},
        )
        raise error

    def _handle_data_provider_error(
        self, symbol: str, qty: float, side: BrokerOrderSide, error: DataProviderError
    ) -> str | None:
        """Handle data provider errors with fallback logic."""
        self.logger.error(
            "data_provider_error",
            extra={
                "symbol": symbol,
                "error": str(error),
                "phase": "better_orders_main",
            },
        )

        if self.enable_market_order_fallback:
            self.logger.info(
                "market_order_fallback_triggered",
                extra={
                    "symbol": symbol,
                    "reason": "data_provider_error",
                    "original_error": str(error),
                },
            )
            return self._submit_canonical_market_order(symbol, side, qty=qty)

        self.logger.error(
            "data_provider_error_fallback_disabled",
            extra={"symbol": symbol, "error": str(error), "fallback_enabled": False},
        )
        raise error

    def _handle_unclassified_error(
        self, symbol: str, qty: float, side: BrokerOrderSide, error: Exception
    ) -> str | None:
        """Handle unclassified errors with classification and fallback logic."""
        error_message = str(error).lower()

        if "order" in error_message and ("failed" in error_message or "reject" in error_message):
            placement_error = OrderPlacementError(
                f"Order placement failed: {error!s}",
                symbol=symbol,
                reason="unknown_placement_failure",
            )
            self.logger.error(
                "classified_order_placement_error",
                extra={
                    "symbol": symbol,
                    "original_error": str(error),
                    "phase": "better_orders_main",
                },
            )

            if self.enable_market_order_fallback:
                self.logger.info(
                    "market_order_fallback_triggered",
                    extra={
                        "symbol": symbol,
                        "reason": "order_placement_failed",
                        "original_error": str(error),
                    },
                )
                return self._submit_canonical_market_order(symbol, side, qty=qty)

            self.logger.error(
                "order_placement_failed_fallback_disabled",
                extra={"symbol": symbol, "error": str(error), "fallback_enabled": False},
            )
            raise placement_error

        # Unknown error - log and decide based on feature flag
        self.logger.error(
            "unclassified_execution_error",
            extra={
                "symbol": symbol,
                "error": str(error),
                "error_type": type(error).__name__,
                "phase": "better_orders_main",
            },
        )

        if self.enable_market_order_fallback:
            self.logger.warning(
                "market_order_fallback_triggered",
                extra={
                    "symbol": symbol,
                    "reason": "unclassified_error",
                    "original_error": str(error),
                },
            )
            return self._submit_canonical_market_order(symbol, side, qty=qty)

        self.logger.error(
            "unexpected_error_fallback_disabled",
            extra={"symbol": symbol, "error": str(error), "fallback_enabled": False},
        )
        raise OrderExecutionError(f"Unclassified execution error: {error!s}", symbol=symbol)

    def wait_for_settlement(
        self,
        sell_orders: list[dict[str, Any]],
        max_wait_time: int = 60,
        poll_interval: float = 2.0,
    ) -> bool:
        """Wait for order settlement using WebSocket-based tracking.

        Uses the OrderCompletionMonitor for real-time WebSocket settlement detection.
        No legacy polling fallbacks - WebSocket streaming only.

        Args:
            sell_orders: List of order dictionaries to monitor
            max_wait_time: Maximum time to wait in seconds
            poll_interval: Polling interval (currently unused in polling implementation)

        Returns:
            bool: True if all orders settle successfully, False if any fail or timeout

        Note:
            Returns False instead of silently succeeding when one or more orders fail
            to reach a terminal state (filled / canceled / rejected / expired) within
            the allowed window. This explicit failure propagation prevents masking
            real settlement issues and aligns with the no-legacy-fallback policy.

        """
        if not sell_orders:
            return True

        # Extract and validate order IDs
        order_ids = self._extract_valid_order_ids(sell_orders)
        if not order_ids:
            logging.warning("No valid order IDs found in settlement data")
            return False

        # Check which orders are already completed
        already_completed, remaining_order_ids = self._check_pre_completion_status(order_ids)

        # If all orders are already completed, no need to wait
        if not remaining_order_ids:
            logging.info(
                f"🎯 All {len(order_ids)} orders already settled, skipping settlement monitoring"
            )
            return True

        # Monitor remaining orders for completion
        completion_statuses = self._monitor_remaining_orders(
            remaining_order_ids, max_wait_time, already_completed
        )

        # Evaluate overall settlement success
        return self._evaluate_settlement_success(order_ids, completion_statuses)

    def _extract_valid_order_ids(self, sell_orders: list[dict[str, Any]]) -> list[str]:
        """Extract valid order IDs from order dictionaries."""
        order_ids: list[str] = []
        for order in sell_orders:
            # Try both 'id' and 'order_id' keys for compatibility
            order_id = order.get("id") or order.get("order_id")
            if order_id is not None and isinstance(order_id, str):
                order_ids.append(order_id)
        return order_ids

    def _check_pre_completion_status(
        self, order_ids: list[str]
    ) -> tuple[dict[str, str], list[str]]:
        """Check which orders are already completed before monitoring."""
        already_completed = {}
        remaining_order_ids = []

        for order_id in order_ids:
            try:
                status = self._get_order_status(order_id)
                if status in ["filled", "canceled", "rejected", "expired"]:
                    logging.info(f"✅ Order {order_id} already settled with status: {status}")
                    already_completed[order_id] = status
                else:
                    remaining_order_ids.append(order_id)
            except Exception as e:
                logging.warning(f"❌ Error checking order {order_id} pre-settlement status: {e}")
                remaining_order_ids.append(order_id)  # Include it in monitoring if we can't check

        logging.info(
            f"📊 Settlement check: {len(already_completed)} already completed, "
            f"{len(remaining_order_ids)} need monitoring"
        )

        return already_completed, remaining_order_ids

    def _get_order_status(self, order_id: str) -> str:
        """Get the current status of an order."""
        order_obj: Any = self._order_executor.trading_client.get_order_by_id(order_id)
        status = str(getattr(order_obj, "status", "unknown")).lower()
        return status.split(".")[-1] if "orderstatus." in status else status

    def _monitor_remaining_orders(
        self, remaining_order_ids: list[str], max_wait_time: int, already_completed: dict[str, str]
    ) -> dict[str, str]:
        """Monitor remaining orders for completion and return all completion statuses."""
        # Wait for order settlement
        completion_result = self._order_executor.wait_for_order_completion(
            remaining_order_ids, max_wait_time
        )

        # Extract completed order IDs from typed WebSocketResultDTO
        websocket_completed_orders = completion_result.orders_completed

        # For the orders that completed via WebSocket, we need to check their final status
        completion_statuses = {}
        for order_id in websocket_completed_orders:
            if order_id in remaining_order_ids:
                # Assume filled for orders that completed (this could be enhanced to check actual status)
                completion_statuses[order_id] = "filled"

        # For any remaining orders that didn't complete, mark as timeout
        for order_id in remaining_order_ids:
            if order_id not in completion_statuses:
                completion_statuses[order_id] = "timeout"

        # Combine pre-completed orders with newly completed ones
        all_completion_statuses = {**already_completed, **completion_statuses}

        # Log the completion statuses for debugging
        logging.info(f"Order completion statuses: {all_completion_statuses}")

        return all_completion_statuses

    def _evaluate_settlement_success(
        self, order_ids: list[str], all_completion_statuses: dict[str, str]
    ) -> bool:
        """Evaluate whether all orders settled successfully."""
        # Consider orders settled if they're filled, canceled, or rejected
        # Handle both enum values and string representations
        settled_statuses = {
            "filled",
            "canceled",
            "rejected",
            "expired",
            "OrderStatus.FILLED",
            "OrderStatus.CANCELED",
            "OrderStatus.REJECTED",
            "OrderStatus.EXPIRED",
        }

        settled_count = sum(
            1
            for status in all_completion_statuses.values()
            if status in settled_statuses or str(status).lower() in settled_statuses
        )

        success = settled_count == len(order_ids)
        if not success:
            logging.warning(f"Only {settled_count}/{len(order_ids)} orders settled")

        return success

    def calculate_dynamic_limit_price(
        self,
        side: BrokerOrderSide,
        bid: float,
        ask: float,
        step: int = 1,
        tick_size: float = 0.01,
        max_steps: int = 5,
    ) -> float:
        """Calculate a dynamic limit price based on the bid-ask spread and step.

        Test expects:
        - BUY: bid=99.0, ask=101.0, step=1, tick_size=0.2, max_steps=3 -> 100.2
        - SELL: bid=99.0, ask=101.0, step=2, tick_size=0.5, max_steps=3 -> 99.0

        Args:
            side: BrokerOrderSide.BUY or BrokerOrderSide.SELL
            bid: Current bid price
            ask: Current ask price
            step: Step number (1-based)
            tick_size: Minimum price increment
            max_steps: Maximum number of steps

        Returns:
            Calculated limit price

        """
        mid_price = (bid + ask) / 2.0

        if side == BrokerOrderSide.BUY:
            # For buy orders, step toward ask from mid
            price = mid_price + (step * tick_size)
        else:
            # For sell orders, step toward bid from mid
            price = mid_price - (step * tick_size)

        # Round to nearest tick
        return round(price / tick_size) * tick_size

    def _execute_aggressive_limit_sequence(
        self,
        symbol: str,
        qty: float,
        side: BrokerOrderSide,
        bid: float,
        ask: float,
        strategy: Any,  # noqa: ANN401  # Strategy execution context with dynamic configuration
    ) -> str | None:
        """Execute the aggressive marketable limit sequence with adaptive re-pegging.

        Phase 2 Enhancement:
        - Delegates to AggressiveLimitStrategy for all pricing and timing logic
        - Maintains orchestration shell only
        - Preserves existing error handling and lifecycle management
        """
        from decimal import Decimal

        from the_alchemiser.execution.config.execution_config import (
            create_strategy_config,
        )
        from the_alchemiser.execution.strategies import (
            AggressiveLimitStrategy,
            ExecutionContextAdapter,
        )

        strategy_config = create_strategy_config()
        aggressive_strategy = AggressiveLimitStrategy(
            config=strategy_config,
            enable_market_order_fallback=self.enable_market_order_fallback,
            # Phase 5: Lifecycle tracking removed - handled by canonical executor path
            lifecycle_manager=None,
            lifecycle_dispatcher=None,
            strategy_name="AggressiveLimitStrategy",
        )
        context = ExecutionContextAdapter(self._order_executor)
        bid_decimal = Decimal(str(bid))
        ask_decimal = Decimal(str(ask))
        try:
            return aggressive_strategy.execute(
                context=context,
                symbol=symbol,
                qty=qty,
                side=side,
                bid=bid_decimal,
                ask=ask_decimal,
            )
        except Exception as e:
            self.logger.error(
                "aggressive_limit_strategy_execution_failed",
                extra={
                    "symbol": symbol,
                    "side": side.value,
                    "quantity": qty,
                    "strategy_name": "AggressiveLimitStrategy",
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )
            raise

    def get_order_by_id(self, order_id: str) -> Any:  # noqa: ANN401  # External SDK order object
        """Get order details by order ID from the trading client."""
        try:
            return self._order_executor.trading_client.get_order_by_id(order_id)
        except Exception as e:
            logging.warning(f"Could not retrieve order {order_id}: {e}")
            return None
