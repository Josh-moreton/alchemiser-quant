"""Canonical Order Executor (Phase 3 - Unified Policy Layer).

Enhanced implementation with policy orchestrator integration:
* Integrates PolicyOrchestrator for unified pre-placement validation
* Accepts an injected lifecycle monitor (Protocol) instead of instantiating infra class directly
* Removes mock fill fabrication - optionally fetches updated order execution result
* Shadow mode now returns a synthetic, clearly non-executed result (success=False)
* No private attribute access on repository
* Structured logging via contextual `extra` data
* Policy-based validation with comprehensive error handling
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import TYPE_CHECKING

from alpaca.trading.requests import LimitOrderRequest, MarketOrderRequest

from the_alchemiser.domain.trading.value_objects.order_request import OrderRequest
from the_alchemiser.interfaces.schemas.orders import (
    OrderExecutionResultDTO,
    RawOrderEnvelope,
)
from the_alchemiser.services.errors.handler import TradingSystemErrorHandler

if TYPE_CHECKING:  # typing-only imports
    from the_alchemiser.application.policies.policy_orchestrator import (
        PolicyOrchestrator,
    )
    from the_alchemiser.application.trading.lifecycle import (
        LifecycleEventDispatcher,
        OrderLifecycleManager,
    )
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
        lifecycle_dispatcher: LifecycleEventDispatcher | None = None,
        lifecycle_manager: OrderLifecycleManager | None = None,
    ) -> None:
        self.repository = repository
        self.policy_orchestrator = policy_orchestrator
        self.shadow_mode = shadow_mode
        self.lifecycle_monitor = lifecycle_monitor
        self.lifecycle_dispatcher = lifecycle_dispatcher
        self.lifecycle_manager = lifecycle_manager
        self.error_handler = TradingSystemErrorHandler()

    def execute(self, order_request: OrderRequest) -> OrderExecutionResultDTO:
        """Execute an order request through the canonical pathway with policy validation."""
        self._validate_order_request(order_request)

        from datetime import UTC, datetime

        # Apply policy validation if orchestrator is available (domain pathway preferred)
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
                policy_result = self.policy_orchestrator.validate_and_adjust_domain(order_request)

                if not policy_result.is_approved:
                    logger.warning(
                        "Order rejected by policy validation",
                        extra={
                            "component": "CanonicalOrderExecutor.execute",
                            "symbol": order_request.symbol.value,
                            "rejection_reason": policy_result.rejection_reason,
                            "warnings": len(policy_result.warnings),
                        },
                    )
                    return OrderExecutionResultDTO(
                        success=False,
                        error=f"Policy rejection: {policy_result.rejection_reason}",
                        order_id="policy_rejected",
                        status="rejected",
                        filled_qty=Decimal("0"),
                        avg_fill_price=None,
                        submitted_at=datetime.now(UTC),
                        completed_at=datetime.now(UTC),
                    )

                # Log policy warnings
                if policy_result.warnings:
                    logger.info(
                        "Policy warnings generated",
                        extra={
                            "component": "CanonicalOrderExecutor.execute",
                            "symbol": order_request.symbol.value,
                            "warnings": [w.message for w in policy_result.warnings],
                            "warning_count": len(policy_result.warnings),
                        },
                    )

                # Update order request with policy adjustments
                if policy_result.has_adjustments:
                    logger.info(
                        "Order adjusted by policies",
                        extra={
                            "component": "CanonicalOrderExecutor.execute",
                            "symbol": order_request.symbol.value,
                            "original_qty": str(order_request.quantity.value),
                            "adjusted_qty": str(policy_result.order_request.quantity.value),
                            "adjustment_reason": policy_result.adjustment_reason,
                        },
                    )
                    # Replace with adjusted domain order request
                    order_request = policy_result.order_request

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
            # Use centralized order request builder

            from alpaca.trading.requests import LimitOrderRequest, MarketOrderRequest

            from the_alchemiser.application.execution.order_request_builder import (
                OrderRequestBuilder,
            )

            alpaca_order_request: MarketOrderRequest | LimitOrderRequest

            if order_request.order_type.value == "market":
                alpaca_order_request = OrderRequestBuilder.build_market_order_request(
                    symbol=order_request.symbol.value,
                    side=order_request.side.value,
                    qty=order_request.quantity.value,
                    time_in_force=order_request.time_in_force.value,
                    client_order_id=order_request.client_order_id,
                )
            else:  # limit order
                if order_request.limit_price is None:
                    raise ValueError("Limit price required for limit orders")

                alpaca_order_request = OrderRequestBuilder.build_limit_order_request(
                    symbol=order_request.symbol.value,
                    side=order_request.side.value,
                    quantity=order_request.quantity.value,
                    limit_price=order_request.limit_price.amount,
                    time_in_force=order_request.time_in_force.value,
                    client_order_id=order_request.client_order_id,
                )

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
            # Repository now returns RawOrderEnvelope, need to convert to DTO
            raw_envelope = self.repository.place_order(alpaca_order_request)

            # Convert envelope to OrderExecutionResultDTO
            from the_alchemiser.application.mapping.order_mapping import (
                raw_order_envelope_to_execution_result_dto,
            )

            execution_result = raw_order_envelope_to_execution_result_dto(raw_envelope)
            
            # Emit lifecycle events if dispatcher available (Phase 5)
            self._emit_submission_lifecycle_events(execution_result, raw_envelope)
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
                "No lifecycle monitor injected - returning immediate placement result",
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
                    
                    # Emit completion lifecycle events (Phase 5)
                    self._emit_completion_lifecycle_events(updated)
                    
                    return updated
                except Exception as e:  # fetch failure - keep original result
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

    # Removed obsolete DTO conversion helpers after domain pathway adoption.

    def _convert_to_alpaca_request(self, order_request: OrderRequest) -> MarketOrderRequest | LimitOrderRequest:
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

    def _emit_submission_lifecycle_events(
        self, execution_result: OrderExecutionResultDTO, raw_envelope: RawOrderEnvelope
    ) -> None:
        """Emit lifecycle events for order submission from repository responses.
        
        Phase 5: Uniform lifecycle event emission from canonical executor path.
        
        Args:
            execution_result: Processed execution result DTO
            raw_envelope: Raw repository response envelope with metadata
        """
        if not self.lifecycle_dispatcher or not self.lifecycle_manager:
            return

        try:
            from the_alchemiser.domain.trading.lifecycle import (
                LifecycleEventType,
                OrderLifecycleState,
            )
            from the_alchemiser.domain.trading.value_objects.order_id import OrderId

            order_id = OrderId.from_string(execution_result.order_id)
            
            # Build metadata from execution result and envelope
            submission_metadata = {
                "component": "CanonicalOrderExecutor",
                "submission_time": execution_result.submitted_at.isoformat() if execution_result.submitted_at else None,
                "success": execution_result.success,
                "order_type": getattr(raw_envelope.original_request, "order_type", "unknown"),
                "symbol": getattr(raw_envelope.original_request, "symbol", "unknown"),
                "side": getattr(raw_envelope.original_request, "side", "unknown"),
                "qty": getattr(raw_envelope.original_request, "qty", "unknown"),
                "request_timestamp": raw_envelope.request_timestamp.isoformat() if hasattr(raw_envelope, "request_timestamp") else None,
                "response_timestamp": raw_envelope.response_timestamp.isoformat() if hasattr(raw_envelope, "response_timestamp") else None,
            }

            if execution_result.success:
                # Successful submission - emit SUBMITTED event
                event = self.lifecycle_manager.advance(
                    order_id,
                    OrderLifecycleState.SUBMITTED,
                    event_type=LifecycleEventType.STATE_CHANGED,
                    metadata=submission_metadata,
                    dispatcher=self.lifecycle_dispatcher,
                )
                self.lifecycle_dispatcher.dispatch(event)
                
                logger.debug(
                    "Emitted SUBMITTED lifecycle event",
                    extra={
                        "component": "CanonicalOrderExecutor._emit_submission_lifecycle_events",
                        "order_id": str(order_id),
                        "status": execution_result.status,
                    },
                )
            else:
                # Failed submission - emit REJECTED event
                rejection_metadata = {
                    **submission_metadata,
                    "error": execution_result.error,
                    "rejection_reason": execution_result.error,
                }
                
                event = self.lifecycle_manager.advance(
                    order_id,
                    OrderLifecycleState.REJECTED,
                    event_type=LifecycleEventType.REJECTED,
                    metadata=rejection_metadata,
                    dispatcher=self.lifecycle_dispatcher,
                )
                self.lifecycle_dispatcher.dispatch(event)
                
                logger.debug(
                    "Emitted REJECTED lifecycle event",
                    extra={
                        "component": "CanonicalOrderExecutor._emit_submission_lifecycle_events",
                        "order_id": str(order_id),
                        "error": execution_result.error,
                    },
                )

        except Exception as e:
            # Don't let lifecycle emission failures break order execution
            logger.warning(
                "Failed to emit submission lifecycle events",
                extra={
                    "component": "CanonicalOrderExecutor._emit_submission_lifecycle_events",
                    "order_id": execution_result.order_id,
                    "error": str(e),
                },
            )

    def _emit_completion_lifecycle_events(
        self, execution_result: OrderExecutionResultDTO
    ) -> None:
        """Emit lifecycle events for order completion monitoring.
        
        Phase 5: Emit FILLED/TIMEOUT/REJECTED events based on final order state.
        
        Args:
            execution_result: Final execution result after monitoring
        """
        if not self.lifecycle_dispatcher or not self.lifecycle_manager:
            return

        try:
            from the_alchemiser.domain.trading.lifecycle import (
                LifecycleEventType,
                OrderLifecycleState,
            )
            from the_alchemiser.domain.trading.value_objects.order_id import OrderId

            order_id = OrderId.from_string(execution_result.order_id)
            
            # Build completion metadata
            completion_metadata = {
                "component": "CanonicalOrderExecutor",
                "final_status": execution_result.status,
                "filled_qty": str(execution_result.filled_qty) if execution_result.filled_qty else "0",
                "avg_fill_price": str(execution_result.avg_fill_price) if execution_result.avg_fill_price else None,
                "completed_at": execution_result.completed_at.isoformat() if execution_result.completed_at else None,
                "submission_time": execution_result.submitted_at.isoformat() if execution_result.submitted_at else None,
            }
            
            # Calculate time to fill if available
            if execution_result.submitted_at and execution_result.completed_at:
                time_diff = execution_result.completed_at - execution_result.submitted_at
                completion_metadata["time_to_fill_ms"] = str(time_diff.total_seconds() * 1000)

            # Map status to lifecycle state and event type
            status_lower = execution_result.status.lower()
            if status_lower in ["filled", "completely_filled"]:
                target_state = OrderLifecycleState.FILLED
                event_type = LifecycleEventType.STATE_CHANGED
            elif status_lower in ["partially_filled"]:
                target_state = OrderLifecycleState.PARTIALLY_FILLED
                event_type = LifecycleEventType.PARTIAL_FILL
            elif status_lower in ["rejected"]:
                target_state = OrderLifecycleState.REJECTED
                event_type = LifecycleEventType.REJECTED
            elif status_lower in ["cancelled"]:
                target_state = OrderLifecycleState.CANCELLED
                event_type = LifecycleEventType.CANCEL_CONFIRMED
            elif status_lower in ["expired"]:
                target_state = OrderLifecycleState.EXPIRED
                event_type = LifecycleEventType.EXPIRED
            else:
                # Unknown status - log and skip
                logger.warning(
                    "Unknown order status for lifecycle event emission",
                    extra={
                        "component": "CanonicalOrderExecutor._emit_completion_lifecycle_events",
                        "order_id": str(order_id),
                        "status": execution_result.status,
                    },
                )
                return

            # Emit completion event
            event = self.lifecycle_manager.advance(
                order_id,
                target_state,
                event_type=event_type,
                metadata=completion_metadata,
                dispatcher=self.lifecycle_dispatcher,
            )
            self.lifecycle_dispatcher.dispatch(event)
            
            logger.debug(
                "Emitted completion lifecycle event",
                extra={
                    "component": "CanonicalOrderExecutor._emit_completion_lifecycle_events",
                    "order_id": str(order_id),
                    "final_state": target_state.value,
                    "event_type": event_type.value,
                },
            )

        except Exception as e:
            # Don't let lifecycle emission failures break order execution
            logger.warning(
                "Failed to emit completion lifecycle events",
                extra={
                    "component": "CanonicalOrderExecutor._emit_completion_lifecycle_events",
                    "order_id": execution_result.order_id,
                    "error": str(e),
                },
            )

    # NOTE: Lifecycle monitoring and event emission handled via injected components.
