#!/usr/bin/env python3
"""
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

import logging
import time
from typing import TYPE_CHECKING, Any, Protocol

from alpaca.trading.enums import OrderSide

from the_alchemiser.infrastructure.config.execution_config import (
    ExecutionConfig,
    get_execution_config,
)
from the_alchemiser.interfaces.schemas.execution import WebSocketResultDTO

if TYPE_CHECKING:
    from the_alchemiser.application.trading.lifecycle import (
        LifecycleEventDispatcher,
        OrderLifecycleManager,
    )
    from the_alchemiser.domain.trading.lifecycle import (
        LifecycleEventType,
        OrderLifecycleState,
    )
from the_alchemiser.services.errors.exceptions import (
    BuyingPowerError,
    DataProviderError,
    OrderExecutionError,
    OrderPlacementError,
    OrderTimeoutError,
    SpreadAnalysisError,
    TradingClientError,
)


class OrderExecutor(Protocol):
    """Protocol for order execution components."""

    def place_market_order(
        self,
        symbol: str,
        side: OrderSide,
        qty: float | None = None,
        notional: float | None = None,
    ) -> str | None:
        """Place a market order."""
        ...

    def place_smart_sell_order(self, symbol: str, qty: float) -> str | None:
        """Place a smart sell order."""
        ...

    def liquidate_position(self, symbol: str) -> str | None:
        """Liquidate a position."""
        ...

    def get_current_positions(self) -> dict[str, float]:
        """Get current positions."""
        ...

    def place_limit_order(
        self, symbol: str, qty: float, side: OrderSide, limit_price: float
    ) -> str | None:
        """Place a limit order."""
        ...

    def wait_for_order_completion(
        self, order_ids: list[str], max_wait_seconds: int = 30
    ) -> WebSocketResultDTO:
        """Wait for order completion."""
        ...

    @property
    def trading_client(self) -> Any:  # Backward compatibility
        """Access to trading client for market hours and order queries."""
        ...

    @property
    def data_provider(self) -> "DataProvider":
        """Access to data provider for quotes and prices."""
        ...


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


def is_market_open(trading_client: Any) -> bool:
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
        order_executor: "OrderExecutor",
        data_provider: "DataProvider",
        ignore_market_hours: bool = False,
        config: Any = None,
        account_info_provider: Any = None,
        enable_market_order_fallback: bool = False,  # Feature flag for market order fallback
        execution_config: ExecutionConfig | None = None,  # Phase 2: Adaptive configuration
        lifecycle_manager: "OrderLifecycleManager | None" = None,  # Phase 3: Lifecycle tracking
        lifecycle_dispatcher: "LifecycleEventDispatcher | None" = None,  # Phase 3: Event dispatch
    ) -> None:
        """Initialize with dependency injection for execution and data access."""
        self.config = config or {}
        self._order_executor = order_executor
        self._data_provider = data_provider
        self._trading_client = getattr(order_executor, "trading_client", None)
        self._account_info_provider = account_info_provider
        self.ignore_market_hours = ignore_market_hours
        self.enable_market_order_fallback = enable_market_order_fallback
        self.execution_config = (
            execution_config or get_execution_config()
        )  # Phase 2: Use global config if not provided

        # Phase 3: Lifecycle management integration
        from the_alchemiser.application.trading.lifecycle import (
            LifecycleEventDispatcher,
            LoggingObserver,
            MetricsObserver,
            OrderLifecycleManager,
        )

        self.lifecycle_manager = lifecycle_manager or OrderLifecycleManager()

        # Initialize dispatcher with observers if not provided
        if lifecycle_dispatcher is None:
            self.lifecycle_dispatcher = LifecycleEventDispatcher()
            # Add standard observers for logging and metrics
            self.lifecycle_dispatcher.register(LoggingObserver())
            self.lifecycle_dispatcher.register(MetricsObserver())
        else:
            self.lifecycle_dispatcher = lifecycle_dispatcher

        self.logger = logging.getLogger(__name__)

    def _track_order_lifecycle(
        self,
        order_id: str,
        target_state: "OrderLifecycleState",
        event_type: "LifecycleEventType | None" = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Track order lifecycle state transitions and dispatch events.

        Phase 3: Integration helper to update lifecycle state and emit events
        for comprehensive order tracking throughout the execution pipeline.
        """
        try:
            from the_alchemiser.domain.trading.lifecycle import (
                LifecycleEventType,
                OrderLifecycleState,
            )
            from the_alchemiser.domain.trading.value_objects.order_id import OrderId

            # Default event type based on target state
            if event_type is None:
                if target_state == OrderLifecycleState.SUBMITTED:
                    event_type = LifecycleEventType.STATE_CHANGED
                elif target_state == OrderLifecycleState.FILLED:
                    event_type = LifecycleEventType.STATE_CHANGED
                elif target_state == OrderLifecycleState.PARTIALLY_FILLED:
                    event_type = LifecycleEventType.PARTIAL_FILL
                elif target_state == OrderLifecycleState.CANCELLED:
                    event_type = LifecycleEventType.CANCEL_CONFIRMED
                elif target_state == OrderLifecycleState.REJECTED:
                    event_type = LifecycleEventType.REJECTED
                elif target_state == OrderLifecycleState.EXPIRED:
                    event_type = LifecycleEventType.EXPIRED
                elif target_state == OrderLifecycleState.ERROR:
                    event_type = LifecycleEventType.ERROR
                else:
                    event_type = LifecycleEventType.STATE_CHANGED

            # Advance lifecycle state and get event
            typed_order_id = OrderId.from_string(order_id)
            lifecycle_event = self.lifecycle_manager.advance(
                typed_order_id,
                target_state,
                event_type=event_type,
                metadata=metadata,
                dispatcher=self.lifecycle_dispatcher,
            )

            # Dispatch event to observers
            self.lifecycle_dispatcher.dispatch(lifecycle_event)

        except Exception as e:
            # Don't let lifecycle tracking failures break order execution
            self.logger.warning(
                "lifecycle_tracking_error",
                extra={
                    "order_id": order_id,
                    "target_state": str(target_state),
                    "error": str(e),
                },
            )

    def _get_order_lifecycle_state(self, order_id: str) -> "OrderLifecycleState | None":
        """Get current lifecycle state for an order."""
        try:
            from the_alchemiser.domain.trading.value_objects.order_id import OrderId

            typed_order_id = OrderId.from_string(order_id)
            return self.lifecycle_manager.get_state(typed_order_id)
        except Exception as e:
            self.logger.warning(
                "lifecycle_state_query_error",
                extra={
                    "order_id": order_id,
                    "error": str(e),
                },
            )
            return None

    def execute_safe_sell(self, symbol: str, target_qty: float) -> str | None:
        """
        Execute a safe sell using the configured order executor.

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
        side: OrderSide,
        max_retries: int = 3,
        poll_timeout: int = 30,
        poll_interval: float = 2.0,
        slippage_bps: float | None = None,
        notional: float | None = None,
        max_slippage_bps: float | None = None,
    ) -> str | None:
        # TODO: Phase 1 consolidation - merge with place_market_order/place_limit_order
        # to create unified order placement interface
        """
        Place order using professional Better Orders execution strategy.

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
        from rich.console import Console

        from the_alchemiser.application.execution.spread_assessment import (
            SpreadAssessment,
        )
        from the_alchemiser.domain.math.market_timing_utils import (
            MarketOpenTimingEngine,
        )

        console = Console()
        timing_engine = MarketOpenTimingEngine()
        spread_assessor = SpreadAssessment(self._data_provider)

        # Handle notional orders for BUY by converting to quantity
        if side == OrderSide.BUY and notional is not None:
            try:
                current_price = self._data_provider.get_current_price(symbol)
                if current_price and current_price > 0:
                    # Calculate max quantity we can afford, round down, scale to 99%
                    raw_qty = notional / current_price
                    rounded_qty = int(raw_qty * 1e6) / 1e6  # Round down to 6 decimals

                    # Check buying power if we have account info provider
                    if self._account_info_provider and side.lower() == "buy":
                        try:
                            account_info = self._account_info_provider.get_account_info()
                            available_cash = float(account_info.get("cash", 0))
                            order_value = rounded_qty * current_price

                            if order_value > available_cash:
                                # Scale down to available cash with safety margin
                                max_affordable_qty = (available_cash * 0.95) / current_price
                                if max_affordable_qty > 0:
                                    rounded_qty = max_affordable_qty
                                    self.logger.info(
                                        "order_scaled_to_available_cash",
                                        extra={
                                            "symbol": symbol,
                                            "original_qty": qty,
                                            "scaled_qty": rounded_qty,
                                            "available_cash": available_cash,
                                        },
                                    )
                                else:
                                    self.logger.error(
                                        "insufficient_buying_power_order_rejected",
                                        extra={
                                            "symbol": symbol,
                                            "side": side.value,
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
                        except Exception as e:
                            self.logger.warning(f"Could not check buying power: {e}")

                    qty = rounded_qty * 0.99  # Scale to 99% to avoid buying power issues
                else:
                    self.logger.warning(
                        "invalid_price_using_market_order",
                        extra={
                            "symbol": symbol,
                            "side": side.value,
                            "notional": notional,
                        },
                    )
                    return self._order_executor.place_market_order(symbol, side, notional=notional)

                if qty <= 0:
                    self.logger.warning(
                        "quantity_too_small_using_market_order",
                        extra={
                            "symbol": symbol,
                            "side": side.value,
                            "calculated_qty": qty,
                            "notional": notional,
                        },
                    )
                    return self._order_executor.place_market_order(symbol, side, notional=notional)

            except DataProviderError:
                self.logger.warning(
                    "price_unavailable_using_market_order",
                    extra={
                        "symbol": symbol,
                        "side": side.value,
                        "quantity": qty,
                    },
                )
                return self._order_executor.place_market_order(symbol, side, notional=notional)

        # Step 1: Market timing and spread assessment
        strategy = timing_engine.get_execution_strategy()
        self.logger.info(
            "execution_strategy_selected",
            extra={
                "symbol": symbol,
                "side": side.value,
                "quantity": qty,
                "strategy": strategy.value,
            },
        )
        self.logger.info(
            "execution_strategy_selected",
            extra={
                "strategy": getattr(strategy, "value", str(strategy)),
                "symbol": symbol,
            },
        )

        # Get current bid/ask
        try:
            quote = self._order_executor.data_provider.get_latest_quote(symbol)
            if not quote or len(quote) < 2:
                self.logger.warning(
                    "no_valid_quote_using_market_order",
                    extra={
                        "symbol": symbol,
                        "side": side.value,
                        "quantity": qty,
                    },
                )
                return self._order_executor.place_market_order(symbol, side, qty=qty)
            bid, ask = float(quote[0]), float(quote[1])

            # Check if quote is invalid (fallback zeros)
            if bid <= 0 or ask <= 0:
                self.logger.warning(
                    "invalid_quote_using_market_order",
                    extra={
                        "symbol": symbol,
                        "side": side.value,
                        "quantity": qty,
                    },
                )
                return self._order_executor.place_market_order(symbol, side, qty=qty)
            spread_analysis = spread_assessor.analyze_current_spread(symbol, bid, ask)

            self.logger.debug(
                "spread_assessed",
                extra={
                    "symbol": symbol,
                    "spread_cents": spread_analysis.spread_cents,
                    "spread_quality": spread_analysis.spread_quality.value,
                },
            )

            # Check if we should wait for spreads to normalize
            if not timing_engine.should_execute_immediately(spread_analysis.spread_cents, strategy):
                wait_time = timing_engine.get_wait_time_seconds(
                    strategy, spread_analysis.spread_cents
                )
                self.logger.info(
                    "waiting_for_spread_normalization",
                    extra={
                        "symbol": symbol,
                        "wait_seconds": wait_time,
                        "spread_cents": spread_analysis.spread_cents,
                    },
                )
                time.sleep(wait_time)

                # Re-get quote after waiting
                quote = self._order_executor.data_provider.get_latest_quote(symbol)
                if not quote or len(quote) < 2:
                    self.logger.warning(
                        "no_valid_quote_after_wait_using_market_order",
                        extra={
                            "symbol": symbol,
                            "side": side.value,
                            "quantity": qty,
                        },
                    )
                    return self._order_executor.place_market_order(symbol, side, qty=qty)
                bid, ask = float(quote[0]), float(quote[1])
                spread_analysis = spread_assessor.analyze_current_spread(symbol, bid, ask)
                self.logger.debug(
                    "spread_reassessed",
                    extra={
                        "symbol": symbol,
                        "updated_spread_cents": spread_analysis.spread_cents,
                    },
                )

            # Step 2 & 3: Aggressive Marketable Limit with Re-pegging
            return self._execute_aggressive_limit_sequence(
                symbol, qty, side, bid, ask, strategy, console
            )

        except OrderExecutionError as e:
            self.logger.error(
                "order_execution_error",
                extra={
                    "symbol": symbol,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "phase": "better_orders_main",
                },
            )
            # Feature flag controlled market order fallback
            if self.enable_market_order_fallback:
                self.logger.info(
                    "market_order_fallback_triggered",
                    extra={
                        "symbol": symbol,
                        "reason": "order_execution_error",
                        "original_error": str(e),
                    },
                )
                return self._order_executor.place_market_order(symbol, side, qty=qty)
            else:
                self.logger.error(
                    "order_execution_failed_fallback_disabled",
                    extra={
                        "symbol": symbol,
                        "error": str(e),
                        "fallback_enabled": False,
                    },
                )
                raise e
        except SpreadAnalysisError as e:
            self.logger.error(
                "spread_analysis_error",
                extra={
                    "symbol": symbol,
                    "error": str(e),
                    "phase": "better_orders_main",
                    "bid": getattr(e, "bid", None),
                    "ask": getattr(e, "ask", None),
                    "spread_cents": getattr(e, "spread_cents", None),
                },
            )
            # Spread analysis failure - no fallback as pricing data is unreliable
            self.logger.error(
                "spread_analysis_failed_no_fallback",
                extra={
                    "symbol": symbol,
                    "error": str(e),
                },
            )
            raise e
        except DataProviderError as e:
            self.logger.error(
                "data_provider_error",
                extra={
                    "symbol": symbol,
                    "error": str(e),
                    "phase": "better_orders_main",
                },
            )
            # Feature flag controlled market order fallback
            if self.enable_market_order_fallback:
                self.logger.info(
                    "market_order_fallback_triggered",
                    extra={
                        "symbol": symbol,
                        "reason": "data_provider_error",
                        "original_error": str(e),
                    },
                )
                return self._order_executor.place_market_order(symbol, side, qty=qty)
            else:
                self.logger.error(
                    "data_provider_error_fallback_disabled",
                    extra={
                        "symbol": symbol,
                        "error": str(e),
                        "fallback_enabled": False,
                    },
                )
                raise e
        except BuyingPowerError as e:
            self.logger.error(
                "buying_power_error",
                extra={
                    "symbol": symbol,
                    "error": str(e),
                    "phase": "better_orders_main",
                    "required_amount": getattr(e, "required_amount", None),
                    "available_amount": getattr(e, "available_amount", None),
                    "shortfall": getattr(e, "shortfall", None),
                },
            )
            # Buying power errors should never fallback to market orders
            self.logger.error(
                "insufficient_buying_power_no_fallback",
                extra={
                    "symbol": symbol,
                    "error": str(e),
                },
            )
            raise e
        except Exception as e:
            # Classify unknown errors more specifically
            error_message = str(e).lower()

            if "buying power" in error_message or "insufficient funds" in error_message:
                buying_power_error = BuyingPowerError(
                    f"Classified buying power error: {str(e)}",
                    symbol=symbol,
                )
                self.logger.error(
                    "classified_buying_power_error",
                    extra={
                        "symbol": symbol,
                        "original_error": str(e),
                        "phase": "better_orders_main",
                    },
                )
                console.print("[red]Insufficient buying power detected[/red]")
                raise buying_power_error
            elif "order" in error_message and (
                "failed" in error_message or "reject" in error_message
            ):
                placement_error = OrderPlacementError(
                    f"Order placement failed: {str(e)}",
                    symbol=symbol,
                    reason="unknown_placement_failure",
                )
                self.logger.error(
                    "classified_order_placement_error",
                    extra={
                        "symbol": symbol,
                        "original_error": str(e),
                        "phase": "better_orders_main",
                    },
                )
                if self.enable_market_order_fallback:
                    console.print(
                        "[yellow]Order placement failed, falling back to market order[/yellow]"
                    )
                    return self._order_executor.place_market_order(symbol, side, qty=qty)
                else:
                    console.print("[red]Order placement failed, market fallback disabled[/red]")
                    raise placement_error
            else:
                # Unknown error - log and decide based on feature flag
                self.logger.error(
                    "unclassified_execution_error",
                    extra={
                        "symbol": symbol,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "phase": "better_orders_main",
                    },
                )
                if self.enable_market_order_fallback:
                    console.print("[yellow]Unexpected error, falling back to market order[/yellow]")
                    self.logger.warning(
                        "market_order_fallback_triggered",
                        extra={
                            "symbol": symbol,
                            "reason": "unclassified_error",
                            "original_error": str(e),
                        },
                    )
                    return self._order_executor.place_market_order(symbol, side, qty=qty)
                else:
                    console.print("[red]Unexpected error, market fallback disabled[/red]")
                    raise OrderExecutionError(
                        f"Unclassified execution error: {str(e)}",
                        symbol=symbol,
                    )

    def wait_for_settlement(
        self,
        sell_orders: list[dict[str, Any]],
        max_wait_time: int = 60,
        poll_interval: float = 2.0,
    ) -> bool:
        """
        Wait for order settlement using WebSocket-based tracking.

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

        # TODO: Replace with proper OrderSettlementTracker implementation
        # Current implementation uses polling-based settlement detection

        # Extract only valid string order IDs
        order_ids: list[str] = []
        for order in sell_orders:
            # Try both 'id' and 'order_id' keys for compatibility
            order_id = order.get("id") or order.get("order_id")
            if order_id is not None and isinstance(order_id, str):
                order_ids.append(order_id)

        # If we had orders but no valid order IDs, that's a failure
        if not order_ids:
            logging.warning("No valid order IDs found in settlement data")
            return False

        # Quick pre-check: see if orders are already filled before starting websocket monitoring
        already_completed = {}
        remaining_order_ids = []

        for order_id in order_ids:
            try:
                order_obj: Any = self._order_executor.trading_client.get_order_by_id(
                    order_id
                )  # TODO: Phase 5 - Migrate to AlpacaOrderObject
                status = str(getattr(order_obj, "status", "unknown")).lower()
                if "orderstatus." in status:
                    actual_status = status.split(".")[-1]
                else:
                    actual_status = status

                if actual_status in ["filled", "canceled", "rejected", "expired"]:
                    logging.info(
                        f"✅ Order {order_id} already settled with status: {actual_status}"
                    )
                    already_completed[order_id] = actual_status
                else:
                    remaining_order_ids.append(order_id)
            except (AttributeError, ValueError) as e:
                logging.warning(f"❌ Error parsing order {order_id} status data: {e}")
                remaining_order_ids.append(order_id)  # Include it in monitoring if we can't check
            except TradingClientError as e:
                logging.warning(f"❌ Trading client error checking order {order_id} status: {e}")
                remaining_order_ids.append(order_id)  # Include it in monitoring if we can't check
            except Exception as e:
                logging.warning(
                    f"❌ Unexpected error checking order {order_id} pre-settlement status: {e}"
                )
                remaining_order_ids.append(order_id)  # Include it in monitoring if we can't check

        # If all orders are already completed, no need to wait
        if not remaining_order_ids:
            logging.info(
                f"🎯 All {len(order_ids)} orders already settled, skipping settlement monitoring"
            )
            return True

        # Only monitor orders that aren't already completed
        logging.info(
            f"📊 Settlement check: {len(already_completed)} already completed, {len(remaining_order_ids)} need monitoring"
        )

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

        # Consider orders settled if they're filled, canceled, or rejected
        # Handle both enum values and string representations
        settled_count = sum(
            1
            for status in all_completion_statuses.values()
            if status in ["filled", "canceled", "rejected", "expired"]
            or str(status).lower() in ["filled", "canceled", "rejected", "expired"]
            or status
            in [
                "OrderStatus.FILLED",
                "OrderStatus.CANCELED",
                "OrderStatus.REJECTED",
                "OrderStatus.EXPIRED",
            ]
        )

        success = settled_count == len(order_ids)
        if success:
            pass  # All orders settled successfully
        else:
            logging.warning(f"Only {settled_count}/{len(order_ids)} orders settled")

        return success

    def calculate_dynamic_limit_price(
        self,
        side: OrderSide,
        bid: float,
        ask: float,
        step: int = 1,
        tick_size: float = 0.01,
        max_steps: int = 5,
    ) -> float:
        """
        Calculate a dynamic limit price based on the bid-ask spread and step.

        Test expects:
        - BUY: bid=99.0, ask=101.0, step=1, tick_size=0.2, max_steps=3 -> 100.2
        - SELL: bid=99.0, ask=101.0, step=2, tick_size=0.5, max_steps=3 -> 99.0

        Args:
            side: OrderSide.BUY or OrderSide.SELL
            bid: Current bid price
            ask: Current ask price
            step: Step number (1-based)
            tick_size: Minimum price increment
            max_steps: Maximum number of steps

        Returns:
            Calculated limit price
        """
        mid_price = (bid + ask) / 2.0

        if side == OrderSide.BUY:
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
        side: OrderSide,
        bid: float,
        ask: float,
        strategy: Any,
        console: Any,
    ) -> str | None:
        """
        Execute the aggressive marketable limit sequence with adaptive re-pegging.

        Phase 2 Enhancement:
        - Uses ExecutionConfig for adaptive timeout and price calculation
        - Monitors spread volatility to pause re-pegging if needed
        - Applies exponential backoff and progressive price improvement
        - Respects minimum re-peg intervals to avoid excessive API calls
        """
        from the_alchemiser.domain.math.market_timing_utils import ExecutionStrategy

        # Determine base timeout based on strategy and ETF speed
        if strategy == ExecutionStrategy.WAIT_FOR_SPREADS:
            base_timeout_seconds = 2.0  # Fast execution at market open
        else:
            base_timeout_seconds = self.execution_config.aggressive_timeout_seconds

        max_repegs = self.execution_config.max_repegs
        original_spread_cents = (ask - bid) * 100  # Convert to cents
        last_attempt_time = 0.0

        self.logger.info(
            "aggressive_limit_sequence_started",
            extra={
                "symbol": symbol,
                "side": side.value,
                "quantity": qty,
                "initial_bid": bid,
                "initial_ask": ask,
                "original_spread_cents": original_spread_cents,
                "max_repegs": max_repegs,
                "adaptive_enabled": self.execution_config.enable_adaptive_repegging,
            },
        )

        for attempt in range(max_repegs + 1):
            # Phase 2: Adaptive timeout with exponential backoff
            timeout_seconds = self.execution_config.get_adaptive_timeout(
                attempt, base_timeout_seconds
            )

            # Phase 2: Adaptive limit price calculation
            if self.execution_config.enable_adaptive_repegging:
                limit_price = self.execution_config.calculate_adaptive_limit_price(
                    side.value, bid, ask, attempt
                )
            else:
                # Legacy pricing logic
                if side == OrderSide.BUY:
                    limit_price = ask + 0.01
                else:
                    limit_price = bid - 0.01

            # Determine direction for display
            if side == OrderSide.BUY:
                direction = f"${limit_price - ask:.3f} above ask" if limit_price > ask else "at ask"
            else:
                direction = f"${bid - limit_price:.3f} below bid" if limit_price < bid else "at bid"

            attempt_label = "Initial order" if attempt == 0 else f"Re-peg #{attempt}"
            console.print(
                f"[cyan]{attempt_label}: {side.value} {symbol} @ ${limit_price:.2f} ({direction})[/cyan]"
            )

            # Phase 2: Respect minimum re-peg interval
            if attempt > 0 and self.execution_config.enable_adaptive_repegging:
                current_time = time.time()
                time_since_last = current_time - last_attempt_time
                min_interval = self.execution_config.min_repeg_interval_seconds

                if time_since_last < min_interval:
                    sleep_time = min_interval - time_since_last
                    self.logger.debug(
                        "repeg_interval_throttle",
                        extra={
                            "symbol": symbol,
                            "sleep_time": sleep_time,
                            "attempt": attempt,
                        },
                    )
                    time.sleep(sleep_time)

            last_attempt_time = time.time()

            # Place aggressive marketable limit
            order_id = self._order_executor.place_limit_order(symbol, qty, side, limit_price)
            if not order_id:
                error_msg = f"Limit order placement returned None ID: {symbol} {side.value} {qty}@{limit_price}"
                self.logger.error(
                    "order_placement_none_id",
                    extra={
                        "symbol": symbol,
                        "side": side.value,
                        "quantity": qty,
                        "limit_price": limit_price,
                        "attempt": attempt,
                    },
                )
                console.print("[red]Failed to place limit order - no order ID returned[/red]")
                # Don't continue the loop - this is a serious placement failure
                raise OrderPlacementError(
                    error_msg,
                    symbol=symbol,
                    order_type="limit",
                    quantity=qty,
                    price=limit_price,
                    reason="none_order_id_returned",
                )

            # Phase 3: Track order submission in lifecycle
            from the_alchemiser.domain.trading.lifecycle import OrderLifecycleState

            self._track_order_lifecycle(
                order_id,
                OrderLifecycleState.SUBMITTED,
                metadata={
                    "symbol": symbol,
                    "side": side.value,
                    "quantity": qty,
                    "limit_price": limit_price,
                    "attempt": attempt,
                    "timeout_seconds": timeout_seconds,
                    "execution_strategy": "aggressive_limit",
                },
            )

            # Wait for fill with adaptive timeout
            try:
                order_result = self._order_executor.wait_for_order_completion(
                    [order_id], max_wait_seconds=int(timeout_seconds)
                )
            except Exception as e:
                self.logger.error(
                    "order_completion_wait_error",
                    extra={
                        "symbol": symbol,
                        "order_id": order_id,
                        "timeout_seconds": timeout_seconds,
                        "attempt": attempt,
                        "error": str(e),
                    },
                )
                # Continue to next attempt rather than immediately failing
                if attempt < max_repegs:
                    console.print("[yellow]Order completion wait failed, will retry[/yellow]")
                    continue
                else:
                    raise OrderTimeoutError(
                        f"Failed to wait for order completion on final attempt: {str(e)}",
                        symbol=symbol,
                        order_id=order_id,
                        timeout_seconds=timeout_seconds,
                        attempt_number=attempt + 1,
                    )

            # Check if the order completed successfully
            order_completed = order_id in order_result.orders_completed
            if order_completed and order_result.status == "completed":
                # Phase 3: Track successful order completion in lifecycle
                self._track_order_lifecycle(
                    order_id,
                    OrderLifecycleState.FILLED,
                    metadata={
                        "symbol": symbol,
                        "execution_price": limit_price,
                        "attempt": attempt,
                        "timeout_used": timeout_seconds,
                        "completion_method": "aggressive_limit",
                    },
                )

                console.print(
                    f"[green]✅ {side.value} {symbol} filled @ ${limit_price:.2f} ({attempt_label})[/green]"
                )
                self.logger.info(
                    "aggressive_limit_filled",
                    extra={
                        "symbol": symbol,
                        "order_id": order_id,
                        "limit_price": limit_price,
                        "attempt": attempt,
                        "timeout_used": timeout_seconds,
                    },
                )
                return order_id
            else:
                # Phase 3: Track timeout/partial state if applicable
                # Note: In a real system, we'd need to query order status to determine if it's partial, cancelled, etc.
                current_lifecycle_state = self._get_order_lifecycle_state(order_id)
                if current_lifecycle_state == OrderLifecycleState.SUBMITTED:
                    # Order still in submitted state - this is a timeout
                    from the_alchemiser.domain.trading.lifecycle import LifecycleEventType

                    self._track_order_lifecycle(
                        order_id,
                        OrderLifecycleState.SUBMITTED,  # Stay in same state but emit timeout event
                        event_type=LifecycleEventType.TIMEOUT,
                        metadata={
                            "symbol": symbol,
                            "timeout_seconds": timeout_seconds,
                            "attempt": attempt,
                            "reason": "order_completion_timeout",
                        },
                    )

            # Order not filled - prepare for re-peg if attempts remain
            if attempt < max_repegs:
                console.print(
                    f"[yellow]{attempt_label} not filled, analyzing for re-peg...[/yellow]"
                )

                # Get fresh quote for re-peg pricing and volatility analysis
                try:
                    fresh_quote = self._order_executor.data_provider.get_latest_quote(symbol)
                    if not fresh_quote or len(fresh_quote) < 2:
                        raise SpreadAnalysisError(
                            f"Invalid fresh quote for re-peg: {fresh_quote}",
                            symbol=symbol,
                        )
                    bid, ask = float(fresh_quote[0]), float(fresh_quote[1])

                    # Check if fresh quote is invalid (fallback zeros)
                    if bid <= 0 or ask <= 0:
                        raise SpreadAnalysisError(
                            f"Invalid bid/ask prices for re-peg: bid={bid}, ask={ask}",
                            symbol=symbol,
                            bid=bid,
                            ask=ask,
                        )

                    # Phase 2: Check for spread volatility - pause re-pegging if spreads widened too much
                    current_spread_cents = (ask - bid) * 100
                    if self.execution_config.should_pause_for_volatility(
                        original_spread_cents, current_spread_cents
                    ):
                        self.logger.warning(
                            "repeg_paused_for_volatility",
                            extra={
                                "symbol": symbol,
                                "original_spread_cents": original_spread_cents,
                                "current_spread_cents": current_spread_cents,
                                "spread_change_pct": (current_spread_cents - original_spread_cents)
                                / original_spread_cents
                                * 100,
                                "attempt": attempt,
                            },
                        )
                        console.print(
                            f"[yellow]Spread volatility too high ({current_spread_cents:.1f}¢ vs {original_spread_cents:.1f}¢), pausing re-pegging[/yellow]"
                        )
                        break

                    self.logger.debug(
                        "repeg_quote_analysis",
                        extra={
                            "symbol": symbol,
                            "fresh_bid": bid,
                            "fresh_ask": ask,
                            "current_spread_cents": current_spread_cents,
                            "spread_change_cents": current_spread_cents - original_spread_cents,
                            "attempt": attempt,
                        },
                    )

                except SpreadAnalysisError:
                    raise  # Re-raise the specific error
                except Exception as e:
                    raise SpreadAnalysisError(
                        f"Failed to get fresh quote for re-peg: {str(e)}",
                        symbol=symbol,
                    )
            else:
                self.logger.warning(
                    "max_repegs_reached",
                    extra={
                        "symbol": symbol,
                        "max_repegs": max_repegs,
                        "final_order_id": order_id,
                    },
                )
                console.print(f"[yellow]Maximum re-pegs ({max_repegs}) reached[/yellow]")

        # All limit attempts exhausted - check feature flag for market order fallback
        if self.enable_market_order_fallback:
            console.print("[yellow]All limit attempts failed, using market order fallback[/yellow]")
            self.logger.info(
                "market_order_fallback_triggered",
                extra={
                    "symbol": symbol,
                    "reason": "limit_attempts_exhausted",
                    "max_repegs": max_repegs,
                    "adaptive_enabled": self.execution_config.enable_adaptive_repegging,
                },
            )
            fallback_order_id = self._order_executor.place_market_order(symbol, side, qty=qty)
            if not fallback_order_id:
                raise OrderPlacementError(
                    f"Market order fallback also failed: {symbol} {side.value} {qty}",
                    symbol=symbol,
                    order_type="market",
                    quantity=qty,
                    reason="market_fallback_none_id",
                )

            # Phase 3: Track market order fallback in lifecycle
            self._track_order_lifecycle(
                fallback_order_id,
                OrderLifecycleState.SUBMITTED,
                metadata={
                    "symbol": symbol,
                    "side": side.value,
                    "quantity": qty,
                    "order_type": "market",
                    "execution_strategy": "market_fallback",
                    "limit_attempts_failed": max_repegs + 1,
                },
            )

            return fallback_order_id
        else:
            # Feature flag disabled - raise timeout error instead of fallback
            raise OrderTimeoutError(
                f"All limit order attempts failed and market fallback disabled: {symbol} {side.value} {qty}",
                symbol=symbol,
                timeout_seconds=base_timeout_seconds * (max_repegs + 1),
                attempt_number=max_repegs + 1,
            )

    def get_order_by_id(self, order_id: str) -> Any:
        """Get order details by order ID from the trading client."""
        try:
            return self._order_executor.trading_client.get_order_by_id(order_id)
        except Exception as e:
            logging.warning(f"Could not retrieve order {order_id}: {e}")
            return None
