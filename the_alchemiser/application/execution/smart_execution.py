#!/usr/bin/env python3
"""Business Unit: order execution/placement; Status: current.

Smart Execution Engine with Professional Order Strategy.

This module provides sophisticated order execution using the Better Orders strategy:
- Aggressive marketable limits (ask+1¢ for buys, bid-            # Get alpaca manager from order executor for canonical executor
            alpaca_manager = getattr(self._order_executor, "alpaca_manager", None)
            if not alpaca_manager:
                # If not available, get underlying trading repository
                alpaca_manager = getattr(self._order_executor, "_trading", self._order_executor)

            order_request = OrderRequest(
                symbol=DomainSymbol(symbol),
                side=DomainSide("buy" if side.value.lower() == "buy" else "sell"),
                quantity=DomainQuantity(Decimal(str(qty))),
                order_type=DomainOrderType("limit"),
                time_in_force=DomainTimeInForce("day"),
                limit_price=DomainMoney(amount=Decimal(str(limit_price)), currency="USD"),
            )
            executor = CanonicalOrderExecutor(alpaca_manager)lls)
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

from alpaca.trading.enums import OrderSide

from the_alchemiser.application.execution.canonical_executor import (
    CanonicalOrderExecutor,
)
from the_alchemiser.domain.shared_kernel.value_objects.money import Money
from the_alchemiser.domain.trading.value_objects.order_request import OrderRequest
from the_alchemiser.domain.trading.value_objects.order_type import (
    OrderType as DomainOrderType,
)
from the_alchemiser.domain.trading.value_objects.quantity import (
    Quantity as DomainQuantity,
)
from the_alchemiser.domain.trading.value_objects.side import Side as DomainSide
from the_alchemiser.domain.trading.value_objects.symbol import Symbol as DomainSymbol
from the_alchemiser.domain.trading.value_objects.time_in_force import (
    TimeInForce as DomainTimeInForce,
)
from the_alchemiser.infrastructure.config.execution_config import (
    ExecutionConfig,
    get_execution_config,
)
from the_alchemiser.interfaces.schemas.execution import WebSocketResultDTO

if TYPE_CHECKING:
    pass
from the_alchemiser.services.errors.exceptions import (
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
    def trading_client(self) -> Any: ...  # Backward compatibility

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
        order_executor: OrderExecutor,
        data_provider: DataProvider,
        ignore_market_hours: bool = False,
        config: Any = None,
        account_info_provider: Any = None,
        enable_market_order_fallback: bool = False,  # Feature flag for market order fallback
        execution_config: (ExecutionConfig | None) = None,  # Phase 2: Adaptive configuration
        # Phase 5: Lifecycle tracking removed - delegated to canonical executor
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

        self.logger = logging.getLogger(__name__)

    # Canonical order submission helpers replacing legacy market/limit methods
    def _submit_canonical_market_order(
        self,
        symbol: str,
        side: OrderSide,
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

            # Get alpaca manager from order executor for canonical executor
            alpaca_manager = getattr(self._order_executor, "alpaca_manager", None)
            if not alpaca_manager:
                # If not available, get underlying trading repository
                alpaca_manager = getattr(self._order_executor, "_trading", self._order_executor)

            # Ensure we have a proper AlpacaManager instance, type cast as needed
            from the_alchemiser.execution.infrastructure.brokers.alpaca_manager import AlpacaManager

            if not isinstance(alpaca_manager, AlpacaManager):
                raise ValueError("Unable to get AlpacaManager instance for canonical executor")

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
            executor = CanonicalOrderExecutor(alpaca_manager)
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
        side: OrderSide,
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

            # Get alpaca manager for canonical executor (same as market order)
            from the_alchemiser.execution.infrastructure.brokers.alpaca_manager import AlpacaManager

            alpaca_manager = getattr(self._order_executor, "alpaca_manager", None)
            if not alpaca_manager:
                alpaca_manager = getattr(self._order_executor, "_trading", self._order_executor)
            if not isinstance(alpaca_manager, AlpacaManager):
                raise ValueError("Unable to get AlpacaManager instance for canonical executor")

            executor = CanonicalOrderExecutor(alpaca_manager)
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
        side: OrderSide,
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
        from the_alchemiser.application.execution.spread_assessment import (
            SpreadAssessment,
        )
        from the_alchemiser.domain.math.market_timing_utils import (
            MarketOpenTimingEngine,
        )

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
                    return self._submit_canonical_market_order(symbol, side, notional=notional)

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
                    return self._submit_canonical_market_order(symbol, side, notional=notional)

            except DataProviderError:
                self.logger.warning(
                    "price_unavailable_using_market_order",
                    extra={
                        "symbol": symbol,
                        "side": side.value,
                        "quantity": qty,
                    },
                )
                return self._submit_canonical_market_order(symbol, side, notional=notional)

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
                return self._submit_canonical_market_order(symbol, side, qty=qty)
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
                return self._submit_canonical_market_order(symbol, side, qty=qty)
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
                    return self._submit_canonical_market_order(symbol, side, qty=qty)
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
            return self._execute_aggressive_limit_sequence(symbol, qty, side, bid, ask, strategy)

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
                return self._submit_canonical_market_order(symbol, side, qty=qty)
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
                return self._submit_canonical_market_order(symbol, side, qty=qty)
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
                    f"Classified buying power error: {e!s}",
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
                self.logger.error(
                    "insufficient_buying_power_detected_before_order",
                    extra={
                        "symbol": symbol,
                        "error": str(e),
                    },
                )
                raise buying_power_error
            if "order" in error_message and (
                "failed" in error_message or "reject" in error_message
            ):
                placement_error = OrderPlacementError(
                    f"Order placement failed: {e!s}",
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
                    self.logger.info(
                        "market_order_fallback_triggered",
                        extra={
                            "symbol": symbol,
                            "reason": "order_placement_failed",
                            "original_error": str(e),
                        },
                    )
                    return self._submit_canonical_market_order(symbol, side, qty=qty)
                self.logger.error(
                    "order_placement_failed_fallback_disabled",
                    extra={
                        "symbol": symbol,
                        "error": str(e),
                        "fallback_enabled": False,
                    },
                )
                raise placement_error
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
                self.logger.warning(
                    "market_order_fallback_triggered",
                    extra={
                        "symbol": symbol,
                        "reason": "unclassified_error",
                        "original_error": str(e),
                    },
                )
                self.logger.warning(
                    "market_order_fallback_triggered",
                    extra={
                        "symbol": symbol,
                        "reason": "unclassified_error",
                        "original_error": str(e),
                    },
                )
                return self._submit_canonical_market_order(symbol, side, qty=qty)
            self.logger.error(
                "unexpected_error_fallback_disabled",
                extra={
                    "symbol": symbol,
                    "error": str(e),
                    "fallback_enabled": False,
                },
            )
            raise OrderExecutionError(
                f"Unclassified execution error: {e!s}",
                symbol=symbol,
            )

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
                actual_status = status.split(".")[-1] if "orderstatus." in status else status

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
        """Calculate a dynamic limit price based on the bid-ask spread and step.

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
    ) -> str | None:
        """Execute the aggressive marketable limit sequence with adaptive re-pegging.

        Phase 2 Enhancement:
        - Delegates to AggressiveLimitStrategy for all pricing and timing logic
        - Maintains orchestration shell only
        - Preserves existing error handling and lifecycle management
        """
        from decimal import Decimal

        from the_alchemiser.application.execution.strategies import (
            AggressiveLimitStrategy,
            ExecutionContextAdapter,
        )
        from the_alchemiser.infrastructure.config.execution_config import (
            create_strategy_config,
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

    def get_order_by_id(self, order_id: str) -> Any:
        """Get order details by order ID from the trading client."""
        try:
            return self._order_executor.trading_client.get_order_by_id(order_id)
        except Exception as e:
            logging.warning(f"Could not retrieve order {order_id}: {e}")
            return None
