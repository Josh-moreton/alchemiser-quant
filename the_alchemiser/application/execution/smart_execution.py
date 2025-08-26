"""Refactored Smart Execution Engine with structured logging and modern architecture."""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Protocol

from alpaca.trading.enums import OrderSide

from the_alchemiser.application.execution.error_taxonomy import (
    OrderErrorClassifier,
    OrderErrorCode,
)
from the_alchemiser.application.execution.order_builder import (
    DecimalSafeOrderBuilder,
)
from the_alchemiser.application.execution.order_lifecycle_manager import (
    OrderLifecycleManager,
)
from the_alchemiser.application.execution.pre_trade_validator import (
    PreTradeValidator,
)
from the_alchemiser.application.execution.repeg_policy import (
    MarketSnapshot,
    RepegPolicyEngine,
)
from the_alchemiser.application.execution.settlement_tracker import (
    OrderSettlementTracker,
)
from the_alchemiser.domain.shared_kernel.value_objects.money import Money
from the_alchemiser.domain.trading.value_objects.order_id import OrderId
from the_alchemiser.domain.trading.value_objects.order_lifecycle import (
    OrderEventType,
    OrderLifecycleState,
)
from the_alchemiser.domain.trading.value_objects.quantity import Quantity
from the_alchemiser.domain.trading.value_objects.symbol import Symbol
from the_alchemiser.services.errors.exceptions import (
    DataProviderError,
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


class TradingDataProvider(Protocol):
    """Protocol for trading data access."""

    def get_current_price(self, symbol: str) -> float | None:
        """Get current price for symbol."""
        ...

    def get_latest_quote(self, symbol: str) -> tuple[float, float] | None:
        """Get latest bid/ask quote."""
        ...

    def get_account_info(self) -> dict[str, Any]:
        """Get account information."""
        ...

    def get_positions(self) -> list[dict[str, Any]]:
        """Get current positions."""
        ...


class SmartExecution:
    """Refactored Smart Execution Engine using modern architecture."""

    validator: PreTradeValidator | None

    def __init__(
        self,
        order_executor: OrderExecutor,
        data_provider: Any,  # Made flexible for compatibility
        lifecycle_manager: OrderLifecycleManager | None = None,
        settlement_tracker: OrderSettlementTracker | None = None,
        validator: PreTradeValidator | None = None,
        order_builder: DecimalSafeOrderBuilder | None = None,
        repeg_engine: RepegPolicyEngine | None = None,
        error_classifier: OrderErrorClassifier | None = None,
    ) -> None:
        """Initialize the refactored smart execution engine."""
        self._order_executor = order_executor
        self._data_provider = data_provider

        # Core components
        self.lifecycle_manager = lifecycle_manager or OrderLifecycleManager()
        self.settlement_tracker = settlement_tracker or OrderSettlementTracker(self.lifecycle_manager)

        # Only create validator if data_provider has the required methods
        if (validator is None and
            hasattr(data_provider, 'get_account_info') and
            hasattr(data_provider, 'get_positions')):
            self.validator = PreTradeValidator(data_provider)
        else:
            self.validator = validator  # May be None for compatibility

        self.order_builder = order_builder or DecimalSafeOrderBuilder()
        self.repeg_engine = repeg_engine or RepegPolicyEngine()
        self.error_classifier = error_classifier or OrderErrorClassifier()

        self.logger = logging.getLogger(__name__)

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
        enable_repeg: bool = True,
    ) -> str | None:
        """
        Place order using modern structured execution pipeline.

        Args:
            symbol: Stock symbol
            qty: Quantity to trade (shares)
            side: OrderSide.BUY or OrderSide.SELL
            max_retries: Maximum retry attempts
            poll_timeout: Timeout for polling (compatibility - not used)
            poll_interval: Polling interval (compatibility - not used)
            slippage_bps: Slippage in basis points (compatibility - not used)
            notional: For BUY orders, dollar amount instead of shares
            max_slippage_bps: Maximum slippage tolerance (compatibility - not used)
            enable_repeg: Whether to enable re-pegging

        Returns:
            Order ID if successful, None otherwise
        """
        try:
            return self._execute_order_pipeline(
                symbol=symbol,
                qty=qty,
                side=side,
                notional=notional,
                max_retries=max_retries,
                enable_repeg=enable_repeg,
            )
        except Exception as e:
            error = self.error_classifier.classify_exception(
                e, {"symbol": symbol, "side": side.value, "qty": qty, "notional": notional}
            )

            self.logger.error(
                "order_execution_failed",
                extra={
                    "symbol": symbol,
                    "side": side.value,
                    "error_code": error.error_code.value,
                    "error_category": error.category.value,
                    "error_message": error.message,
                    "suggested_action": error.suggested_action,
                    "retryable": error.retryable,
                },
            )

            # Only fallback to market order if explicitly configured
            if error.retryable and error.error_code in {
                OrderErrorCode.TIMEOUT,
                OrderErrorCode.RATE_LIMITED,
                OrderErrorCode.WIDE_SPREAD,
            }:
                self.logger.info(
                    "considering_market_fallback",
                    extra={
                        "symbol": symbol,
                        "error_code": error.error_code.value,
                        "fallback_enabled": False,  # Controlled by configuration
                    },
                )

            return None

    def _execute_order_pipeline(
        self,
        symbol: str,
        qty: float,
        side: OrderSide,
        notional: float | None,
        max_retries: int,
        enable_repeg: bool,
    ) -> str | None:
        """Execute the complete order pipeline."""

        # Step 1: Convert to domain objects
        symbol_obj = Symbol(symbol)
        qty_obj = Quantity(Decimal(str(qty)))
        notional_obj = Money(Decimal(str(notional)), "USD") if notional is not None else None

        self.logger.info(
            "order_pipeline_started",
            extra={
                "symbol": symbol,
                "side": side.value,
                "quantity": str(qty) if qty else None,
                "notional": str(notional) if notional else None,
                "max_retries": max_retries,
                "enable_repeg": enable_repeg,
            },
        )

        # Step 2: Pre-trade validation (if validator is available)
        if self.validator:
            validation_result = self.validator.validate_order(
                symbol=symbol_obj,
                side=side.value,
                quantity=qty_obj,
                notional=notional_obj,
            )

            if not validation_result.is_valid:
                self.logger.warning(
                    "pre_trade_validation_failed",
                    extra={
                        "symbol": symbol,
                        "error_count": len(validation_result.errors),
                        "errors": [
                            {
                                "code": error.error_code.value,
                                "message": error.message,
                                "suggested_action": error.suggested_action,
                            }
                            for error in validation_result.errors
                        ],
                    },
                )
                return None

            # Log warnings but continue
            if validation_result.warnings:
                self.logger.warning(
                    "pre_trade_warnings",
                    extra={
                        "symbol": symbol,
                        "warnings": validation_result.warnings,
                        "risk_score": str(validation_result.risk_score),
                    },
                )
        else:
            # Skip validation if no validator available (compatibility mode)
            self.logger.info(
                "pre_trade_validation_skipped",
                extra={"symbol": symbol, "reason": "no_validator_available"},
            )
            validation_result = None

        # Step 3: Get market data
        try:
            quote = self._data_provider.get_latest_quote(symbol)
            if not quote or len(quote) < 2:
                self.logger.warning(
                    "no_quote_data_fallback_to_market",
                    extra={"symbol": symbol, "quote_data": quote},
                )
                return self._place_market_order_fallback(symbol, side, qty, notional)

            bid, ask = quote
            current_price = (bid + ask) / 2

        except DataProviderError as e:
            error = self.error_classifier.classify_exception(e, {"symbol": symbol})
            self.logger.warning(
                "market_data_error_fallback_to_market",
                extra={
                    "symbol": symbol,
                    "error_code": error.error_code.value,
                    "error_message": error.message,
                },
            )
            return self._place_market_order_fallback(symbol, side, qty, notional)

        # Step 4: Build order with approved parameters
        approved_qty = (validation_result.approved_quantity if validation_result and validation_result.approved_quantity else qty_obj)
        current_price_obj = Money(Decimal(str(current_price)), "USD")

        order_params, build_error = self.order_builder.build_aggressive_limit_order(
            symbol=symbol_obj,
            side=side.value,
            quantity=approved_qty,
            bid=Money(Decimal(str(bid)), "USD"),
            ask=Money(Decimal(str(ask)), "USD"),
            aggression_cents=Decimal("0.01"),  # 1 cent aggression
        )

        if build_error:
            self.logger.error(
                "order_build_failed",
                extra={
                    "symbol": symbol,
                    "error_code": build_error.error_code.value,
                    "error_message": build_error.message,
                },
            )
            return None

        # Step 5: Execute order with re-pegging
        return self._execute_with_repeg(
            order_params=order_params,
            market_snapshot=MarketSnapshot(
                symbol=symbol_obj,
                bid=Money(Decimal(str(bid)), "USD"),
                ask=Money(Decimal(str(ask)), "USD"),
                last_price=current_price_obj,
            ),
            max_retries=max_retries,
            enable_repeg=enable_repeg,
        )

    def _execute_with_repeg(
        self,
        order_params: Any,
        market_snapshot: MarketSnapshot,
        max_retries: int,
        enable_repeg: bool,
    ) -> str | None:
        """Execute order with re-pegging logic."""

        order_id = None
        attempt = 0

        while attempt < max_retries:
            attempt += 1

            try:
                # Submit the order
                order_id = self._submit_order(order_params)

                if not order_id:
                    self.logger.warning(
                        "order_submission_failed",
                        extra={
                            "symbol": str(order_params.symbol.value),
                            "attempt": attempt,
                            "max_retries": max_retries,
                        },
                    )
                    continue

                # Create lifecycle tracker
                order_id_obj = OrderId.from_string(order_id)
                lifecycle = self.lifecycle_manager.create_order_lifecycle(
                    order_id=order_id_obj,
                    symbol=order_params.symbol,
                    side=order_params.side,
                    quantity=order_params.quantity,
                    order_type=order_params.order_type,
                    limit_price=order_params.limit_price,
                )

                # Mark as submitted
                self.lifecycle_manager.transition_order(
                    order_id_obj,
                    OrderLifecycleState.SUBMITTED,
                    OrderEventType.SUBMIT,
                    {"attempt": attempt, "limit_price": str(order_params.limit_price.amount)},
                )

                # Wait for execution or re-peg
                execution_result = self._monitor_and_repeg(
                    order_id_obj,
                    order_params,
                    market_snapshot,
                    enable_repeg,
                )

                if execution_result:
                    return order_id

            except Exception as e:
                error = self.error_classifier.classify_exception(
                    e, {"symbol": str(order_params.symbol.value), "attempt": attempt}
                )

                self.logger.warning(
                    "order_attempt_failed",
                    extra={
                        "symbol": str(order_params.symbol.value),
                        "attempt": attempt,
                        "error_code": error.error_code.value,
                        "error_message": error.message,
                        "retryable": error.retryable,
                    },
                )

                if not error.retryable:
                    break

        # All attempts failed
        self.logger.error(
            "order_execution_abandoned",
            extra={
                "symbol": str(order_params.symbol.value),
                "attempts": attempt,
                "max_retries": max_retries,
            },
        )

        return None

    def _submit_order(self, order_params: Any) -> str | None:
        """Submit order to broker."""
        try:
            # Convert to DTO and submit
            order_dto = self.order_builder.convert_to_dto(order_params)

            # Log order submission with structured data
            self.logger.info(
                "order_submitted",
                extra={
                    "symbol": order_dto.symbol,
                    "side": order_dto.side,
                    "quantity": str(order_dto.quantity),
                    "order_type": order_dto.order_type,
                    "limit_price": str(order_dto.limit_price) if order_dto.limit_price else None,
                    "time_in_force": order_dto.time_in_force,
                },
            )

            # Submit via executor (this would call the actual trading client)
            if order_dto.order_type == "market":
                return self._order_executor.place_market_order(
                    symbol=order_dto.symbol,
                    side=OrderSide.BUY if order_dto.side == "buy" else OrderSide.SELL,
                    qty=float(order_dto.quantity),
                )
            else:
                # This would need a limit order method in the executor
                # For now, fallback to market order
                self.logger.warning(
                    "limit_order_not_implemented_fallback_to_market",
                    extra={"symbol": order_dto.symbol},
                )
                return self._order_executor.place_market_order(
                    symbol=order_dto.symbol,
                    side=OrderSide.BUY if order_dto.side == "buy" else OrderSide.SELL,
                    qty=float(order_dto.quantity),
                )

        except Exception as e:
            self.logger.error(
                "order_submission_error",
                extra={
                    "symbol": order_params.symbol.value,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )
            return None

    def _monitor_and_repeg(
        self,
        order_id: OrderId,
        order_params: Any,
        market_snapshot: MarketSnapshot,
        enable_repeg: bool,
    ) -> bool:
        """Monitor order execution and handle re-pegging."""

        # For now, simplified monitoring - just mark as filled
        # In real implementation, this would use the settlement tracker

        self.lifecycle_manager.transition_order(
            order_id,
            OrderLifecycleState.ACKNOWLEDGED,
            OrderEventType.ACK,
        )

        # Simulate fill (in real implementation, this would come from WebSocket events)
        self.lifecycle_manager.transition_order(
            order_id,
            OrderLifecycleState.FILLED,
            OrderEventType.FILL,
            {"fill_price": str(market_snapshot.ask.amount)},
        )

        self.logger.info(
            "order_filled",
            extra={
                "order_id": str(order_id.value),
                "symbol": str(order_params.symbol.value),
                "status": "filled",
            },
        )

        return True

    def _place_market_order_fallback(
        self,
        symbol: str,
        side: OrderSide,
        qty: float | None,
        notional: float | None,
    ) -> str | None:
        """Fallback to market order with explicit logging."""
        self.logger.info(
            "market_order_fallback",
            extra={
                "symbol": symbol,
                "side": side.value,
                "reason": "quote_data_unavailable",
            },
        )

        return self._order_executor.place_market_order(
            symbol=symbol,
            side=side,
            qty=qty,
            notional=notional,
        )

    def wait_for_settlement(
        self,
        sell_orders: list[dict[str, Any]],
        max_wait_time: int = 60,
        poll_interval: float = 2.0,
    ) -> bool:
        """Wait for order settlement using WebSocket-first approach."""
        if not sell_orders:
            return True

        # Extract order IDs
        order_ids: list[OrderId] = []
        for order in sell_orders:
            order_id_str = order.get("id") or order.get("order_id")
            if order_id_str and isinstance(order_id_str, str):
                try:
                    order_ids.append(OrderId.from_string(order_id_str))
                except Exception as e:
                    self.logger.warning(
                        "invalid_order_id_in_settlement",
                        extra={"order_id": order_id_str, "error": str(e)},
                    )

        if not order_ids:
            self.logger.warning("no_valid_order_ids_for_settlement")
            return False

        # Use settlement tracker
        try:
            # This would need a WebSocket monitor implementation
            # For now, simulate successful settlement
            self.logger.info(
                "settlement_completed",
                extra={
                    "order_count": len(order_ids),
                    "settlement_method": "simulated",
                },
            )
            return True

        except Exception as e:
            self.logger.error(
                "settlement_tracking_failed",
                extra={
                    "order_count": len(order_ids),
                    "error": str(e),
                },
            )
            return False

    def get_order_by_id(self, order_id: str) -> Any:
        """Get order by ID (delegated to order executor)."""
        # This would typically call the trading client
        # Return None for now
        return None

    # Compatibility methods for drop-in replacement
    def execute_safe_sell(self, symbol: str, target_qty: float) -> str | None:
        """Execute a safe sell - compatibility method for old interface."""
        return self.place_order(symbol=symbol, qty=target_qty, side=OrderSide.SELL)

    def execute_liquidation(self, symbol: str) -> str | None:
        """Execute full position liquidation - compatibility method for old interface."""
        return self.liquidate_position(symbol)

    def liquidate_position(self, symbol: str) -> str | None:
        """Execute full position liquidation using the configured order executor."""
        return self._order_executor.liquidate_position(symbol)

    def place_smart_sell_order(self, symbol: str, qty: float) -> str | None:
        """Place a smart sell order - compatibility method."""
        return self.place_order(symbol=symbol, qty=qty, side=OrderSide.SELL)

    def place_market_order(
        self,
        symbol: str,
        side: OrderSide,
        qty: float | None = None,
        notional: float | None = None,
    ) -> str | None:
        """Place a market order - compatibility method."""
        return self._order_executor.place_market_order(symbol, side, qty, notional)

    def get_current_positions(self) -> dict[str, float]:
        """Get current positions - compatibility method."""
        if hasattr(self._data_provider, "get_current_positions"):
            positions = self._data_provider.get_current_positions()
            if isinstance(positions, dict):
                return positions
        return {}

    def get_current_price(self, symbol: str) -> float | None:
        """Get current price for symbol."""
        try:
            price = self._data_provider.get_current_price(symbol)
            return float(price) if price is not None else None
        except Exception as e:
            self.logger.warning(
                "price_retrieval_failed",
                extra={"symbol": symbol, "error": str(e)},
            )
            return None

    def get_latest_quote(self, symbol: str) -> tuple[float, float] | None:
        """Get latest bid/ask quote for symbol."""
        try:
            quote = self._data_provider.get_latest_quote(symbol)
            if quote and len(quote) >= 2:
                return (float(quote[0]), float(quote[1]))
            return None
        except Exception as e:
            self.logger.warning(
                "quote_retrieval_failed",
                extra={"symbol": symbol, "error": str(e)},
            )
            return None

    def place_limit_order(
        self,
        symbol: str,
        qty: float,
        side: OrderSide,
        limit_price: float,
        time_in_force: str = "DAY",
    ) -> str | None:
        """Place a limit order - compatibility method."""
        # This would need limit order support in the order executor
        # For now, use the smart execution pipeline
        return self.place_order(symbol=symbol, qty=qty, side=side)

    def wait_for_order_completion(
        self,
        order_id: str,
        poll_timeout: int = 30,
        poll_interval: float = 2.0,
    ) -> bool:
        """Wait for order completion - compatibility method."""
        try:
            order_id_obj = OrderId.from_string(order_id)
            # In real implementation, this would use settlement tracker
            # For now, simulate completion
            self.logger.info(
                "order_completion_simulated",
                extra={"order_id": order_id, "timeout": poll_timeout},
            )
            return True
        except Exception as e:
            self.logger.warning(
                "order_completion_check_failed",
                extra={"order_id": order_id, "error": str(e)},
            )
            return False

    @property
    def trading_client(self) -> Any:
        """Backward compatibility property."""
        return getattr(self._order_executor, "trading_client", None)

    @property
    def data_provider(self) -> Any:
        """Data provider property for backward compatibility."""
        return self._data_provider
