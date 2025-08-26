"""Canonical Order Executor (Phase 3 - Unified Policy Layer).

Enhanced implementation with policy orchestrator integration:
* Integrates PolicyOrchestrator for unified pre-placement validation
* Accepts an injected lifecycle monitor (Protocol) instead of instantiating infra class directly
* Shadow mode now returns a synthetic, clearly non-executed result (success=False)
* No private attribute access on repository
* Structured logging via contextual `extra` data
* Policy-based validation with comprehensive error handling
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from the_alchemiser.domain.trading.value_objects.order_request import OrderRequest
from the_alchemiser.interfaces.schemas.orders import (
    AdjustedOrderRequestDTO,
    OrderExecutionResultDTO,
    OrderRequestDTO,
)
from the_alchemiser.services.errors.handler import TradingSystemErrorHandler

if TYPE_CHECKING:  # typing-only imports
    from the_alchemiser.application.policies.policy_orchestrator import PolicyOrchestrator
    from the_alchemiser.domain.trading.protocols.order_lifecycle import (
        OrderLifecycleMonitor,
    )

if TYPE_CHECKING:
    from the_alchemiser.services.repository.alpaca_manager import AlpacaManager

logger = logging.getLogger(__name__)


class CanonicalOrderExecutor:
    """Canonical order executor implementing domain-driven order execution with unified policy layer."""

    def __init__(
        self,
        repository: AlpacaManager,
        policy_orchestrator: PolicyOrchestrator | None = None,
        shadow_mode: bool = False,
        lifecycle_monitor: OrderLifecycleMonitor | None = None,
    ) -> None:
        self.repository = repository
        self.policy_orchestrator = policy_orchestrator
        self.shadow_mode = shadow_mode
        self.lifecycle_monitor = lifecycle_monitor
        self.error_handler = TradingSystemErrorHandler()

    def execute(self, order_request: OrderRequest) -> OrderExecutionResultDTO:
        """Execute an order request through the canonical pathway with policy validation."""
        self._validate_order_request(order_request)

        from datetime import UTC, datetime

        # Convert domain OrderRequest to DTO for policy validation
        order_dto = self._convert_to_order_dto(order_request)

        # Apply policy validation if orchestrator is available
        if self.policy_orchestrator:
            logger.info(
                "Applying policy validation",
                extra={
                    "component": "CanonicalOrderExecutor.execute",
                    "symbol": order_request.symbol.value,
                    "side": order_request.side.value,
                    "qty": str(order_request.quantity.value),
                    "order_type": order_request.order_type.value,
                },
            )

            try:
                adjusted_order = self.policy_orchestrator.validate_and_adjust_order(order_dto)

                if not adjusted_order.is_approved:
                    logger.warning(
                        "Order rejected by policy validation",
                        extra={
                            "component": "CanonicalOrderExecutor.execute",
                            "symbol": order_request.symbol.value,
                            "rejection_reason": adjusted_order.rejection_reason,
                            "warnings": len(adjusted_order.warnings),
                        },
                    )
                    return OrderExecutionResultDTO(
                        success=False,
                        error=f"Policy rejection: {adjusted_order.rejection_reason}",
                        order_id="policy_rejected",
                        status="rejected",
                        filled_qty=Decimal("0"),
                        avg_fill_price=None,
                        submitted_at=datetime.now(UTC),
                        completed_at=datetime.now(UTC),
                    )

                # Log policy warnings
                if adjusted_order.warnings:
                    logger.info(
                        "Policy warnings generated",
                        extra={
                            "component": "CanonicalOrderExecutor.execute",
                            "symbol": order_request.symbol.value,
                            "warnings": [w.message for w in adjusted_order.warnings],
                            "warning_count": len(adjusted_order.warnings),
                        },
                    )

                # Update order request with policy adjustments
                if adjusted_order.has_adjustments:
                    logger.info(
                        "Order adjusted by policies",
                        extra={
                            "component": "CanonicalOrderExecutor.execute",
                            "symbol": order_request.symbol.value,
                            "original_qty": str(order_request.quantity.value),
                            "adjusted_qty": str(adjusted_order.quantity),
                            "adjustment_reason": adjusted_order.adjustment_reason,
                        },
                    )
                    # Create new order request with adjusted values
                    order_request = self._update_order_request_from_dto(order_request, adjusted_order)

            except Exception as e:
                self.error_handler.handle_error(
                    error=e,
                    component="CanonicalOrderExecutor.execute",
                    context="policy_validation",
                    additional_data={
                        "symbol": order_request.symbol.value,
                        "side": order_request.side.value,
                        "qty": str(order_request.quantity.value),
                    },
                )
                return OrderExecutionResultDTO(
                    success=False,
                    error=f"Policy validation failed: {e}",
                    order_id="policy_error",
                    status="rejected",
                    filled_qty=Decimal("0"),
                    avg_fill_price=None,
                    submitted_at=datetime.now(UTC),
                    completed_at=datetime.now(UTC),
                )

        if self.shadow_mode:
            logger.info(
                "Shadow mode canonical order (not executed)",
                extra={
                    "component": "CanonicalOrderExecutor.execute",
                    "symbol": order_request.symbol.value,
                    "side": order_request.side.value,
                    "qty": str(order_request.quantity.value),
                    "order_type": order_request.order_type.value,
                },
            )
            return OrderExecutionResultDTO(
                success=False,
                error="Shadow mode - order not submitted",
                order_id="shadow_mode_synthetic",
                status="accepted",
                filled_qty=Decimal("0"),
                avg_fill_price=None,
                submitted_at=datetime.now(UTC),
                completed_at=None,
            )

        try:
            alpaca_order_request = self._convert_to_alpaca_request(order_request)
            logger.info(
                "Submitting canonical order",
                extra={
                    "component": "CanonicalOrderExecutor.execute",
                    "symbol": order_request.symbol.value,
                    "side": order_request.side.value,
                    "qty": str(order_request.quantity.value),
                    "order_type": order_request.order_type.value,
                },
            )
            execution_result = self.repository.place_order(alpaca_order_request)
        except Exception as e:  # infra failure
            self.error_handler.handle_error(
                error=e,
                component="CanonicalOrderExecutor.execute",
                context="order_submission",
                additional_data={
                    "symbol": order_request.symbol.value,
                    "side": order_request.side.value,
                    "qty": str(order_request.quantity.value),
                    "order_type": order_request.order_type.value,
                },
            )
            return OrderExecutionResultDTO(
                success=False,
                error=f"Canonical submission failed: {e}",
                order_id="unknown",
                status="rejected",
                filled_qty=Decimal("0"),
                avg_fill_price=None,
                submitted_at=datetime.now(UTC),
                completed_at=datetime.now(UTC),
            )

        if not execution_result.success:
            logger.error(
                "Canonical order placement failed",
                extra={
                    "component": "CanonicalOrderExecutor.execute",
                    "error": execution_result.error,
                    "order_id": execution_result.order_id,
                },
            )
            return execution_result

        if self.lifecycle_monitor is None:
            logger.info(
                "No lifecycle monitor injected – returning immediate placement result",
                extra={
                    "component": "CanonicalOrderExecutor.execute",
                    "order_id": execution_result.order_id,
                },
            )
            return execution_result

        try:
            monitor_result = self.lifecycle_monitor.wait_for_order_completion(
                [execution_result.order_id], max_wait_seconds=60
            )
            if execution_result.order_id in monitor_result.orders_completed:
                try:
                    updated = self.repository.get_order_execution_result(execution_result.order_id)
                    logger.info(
                        "Order lifecycle completed",
                        extra={
                            "component": "CanonicalOrderExecutor.execute",
                            "order_id": execution_result.order_id,
                            "final_status": updated.status,
                        },
                    )
                    return updated
                except Exception as e:  # fetch failure – keep original result
                    self.error_handler.handle_error(
                        error=e,
                        component="CanonicalOrderExecutor.execute",
                        context="post_fill_fetch",
                        additional_data={"order_id": execution_result.order_id},
                    )
            else:
                logger.warning(
                    "Order not completed within monitoring window",
                    extra={
                        "component": "CanonicalOrderExecutor.execute",
                        "order_id": execution_result.order_id,
                        "monitor_status": getattr(monitor_result, "status", "unknown"),
                    },
                )
        except Exception as e:
            self.error_handler.handle_error(
                error=e,
                component="CanonicalOrderExecutor.execute",
                context="lifecycle_monitoring",
                additional_data={"order_id": execution_result.order_id},
            )

        return execution_result

    def _validate_order_request(self, order_request: OrderRequest) -> None:
        """Validation stub for order requests.

        Args:
            order_request: Order request to validate

        Raises:
            ValueError: If validation fails

        """
        # Basic validation - domain value objects already handle most validation
        if order_request.quantity.value <= Decimal("0"):
            raise ValueError("Order quantity must be positive")

        # Additional business rule validation can be added here
        logger.debug(f"Order request validation passed for {order_request.symbol.value}")

    def _convert_to_order_dto(self, order_request: OrderRequest) -> OrderRequestDTO:
        """Convert domain OrderRequest to OrderRequestDTO for policy validation.

        Args:
            order_request: Domain order request value object

        Returns:
            OrderRequestDTO for policy processing
        """
        return OrderRequestDTO(
            symbol=order_request.symbol.value,
            side=order_request.side.value,
            quantity=order_request.quantity.value,
            order_type=order_request.order_type.value,
            time_in_force=order_request.time_in_force.value,
            limit_price=order_request.limit_price.amount if order_request.limit_price else None,
            client_order_id=order_request.client_order_id,
        )

    def _update_order_request_from_dto(
        self,
        original_request: OrderRequest,
        adjusted_dto: AdjustedOrderRequestDTO
    ) -> OrderRequest:
        """Update domain OrderRequest with policy adjustments.

        Args:
            original_request: Original domain order request
            adjusted_dto: Adjusted order from policy validation

        Returns:
            Updated OrderRequest with policy adjustments
        """
        from the_alchemiser.domain.shared_kernel.value_objects.money import Money
        from the_alchemiser.domain.trading.value_objects.order_request import (
            OrderRequest as NewOrderRequest,
        )
        from the_alchemiser.domain.trading.value_objects.order_type import OrderType
        from the_alchemiser.domain.trading.value_objects.quantity import Quantity
        from the_alchemiser.domain.trading.value_objects.side import Side
        from the_alchemiser.domain.trading.value_objects.symbol import Symbol
        from the_alchemiser.domain.trading.value_objects.time_in_force import TimeInForce

        # Create new value objects with adjusted values
        return NewOrderRequest(
            symbol=Symbol(adjusted_dto.symbol),
            side=Side(adjusted_dto.side),
            quantity=Quantity(adjusted_dto.quantity),
            order_type=OrderType(adjusted_dto.order_type),
            time_in_force=TimeInForce(adjusted_dto.time_in_force),
            limit_price=Money(adjusted_dto.limit_price, "USD") if adjusted_dto.limit_price else None,
            client_order_id=adjusted_dto.client_order_id,
        )

    def _convert_to_alpaca_request(self, order_request: OrderRequest) -> Any:
        """Convert domain OrderRequest to Alpaca API format.

        Args:
            order_request: Domain order request value object

        Returns:
            MarketOrderRequest or LimitOrderRequest: Alpaca API compatible order request

        """
        from alpaca.trading.enums import OrderSide
        from alpaca.trading.enums import TimeInForce as AlpacaTimeInForce
        from alpaca.trading.requests import LimitOrderRequest, MarketOrderRequest

        # Convert domain values to Alpaca enums
        alpaca_side = OrderSide.BUY if order_request.side.value == "buy" else OrderSide.SELL

        # Map time in force
        tif_mapping = {
            "day": AlpacaTimeInForce.DAY,
            "gtc": AlpacaTimeInForce.GTC,
            "ioc": AlpacaTimeInForce.IOC,
            "fok": AlpacaTimeInForce.FOK,
        }
        alpaca_tif = tif_mapping[order_request.time_in_force.value]

        # Create appropriate request based on order type
        if order_request.order_type.value == "market":
            return MarketOrderRequest(
                symbol=order_request.symbol.value,
                qty=str(order_request.quantity.value),
                side=alpaca_side,
                time_in_force=alpaca_tif,
                client_order_id=order_request.client_order_id,
            )
        # limit order
        if order_request.limit_price is None:
            raise ValueError("Limit price required for limit orders")

        return LimitOrderRequest(
            symbol=order_request.symbol.value,
            qty=str(order_request.quantity.value),
            side=alpaca_side,
            time_in_force=alpaca_tif,
            limit_price=str(order_request.limit_price.amount),
            client_order_id=order_request.client_order_id,
        )

    # NOTE: Lifecycle monitoring handled externally via injected lifecycle_monitor.
