"""WebSocket-first order settlement tracking with controlled polling fallback."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any, Callable, Dict, List, Set

from the_alchemiser.application.execution.error_taxonomy import (
    OrderError,
    OrderErrorCode,
)
from the_alchemiser.application.execution.order_lifecycle_manager import (
    OrderLifecycleManager,
)
from the_alchemiser.domain.trading.value_objects.order_id import OrderId
from the_alchemiser.domain.trading.value_objects.order_lifecycle import (
    OrderEventType,
    OrderLifecycleState,
)
from the_alchemiser.interfaces.schemas.execution import WebSocketResultDTO, WebSocketStatus


@dataclass(frozen=True)
class SettlementConfig:
    """Configuration for order settlement tracking."""

    # WebSocket settings
    websocket_timeout_seconds: int = 60
    websocket_grace_timeout: int = 5  # Grace period for late events
    
    # Polling fallback settings
    enable_polling_fallback: bool = True
    polling_interval_seconds: float = 2.0
    max_polling_attempts: int = 5
    
    # Settlement criteria
    terminal_states: Set[str] = field(default_factory=lambda: {
        "filled", "canceled", "cancelled", "rejected", "expired"
    })
    
    # Retry settings
    max_settlement_retries: int = 3
    retry_backoff_seconds: float = 1.0


@dataclass
class SettlementStatus:
    """Status of order settlement monitoring."""

    order_id: OrderId
    submitted_at: datetime
    last_update: datetime
    current_status: str
    websocket_events_received: int = 0
    polling_attempts: int = 0
    settlement_method: str = "pending"  # websocket, polling, timeout, error
    error_message: str | None = None


class OrderSettlementTracker:
    """WebSocket-first order settlement tracking with controlled polling fallback."""

    def __init__(
        self,
        lifecycle_manager: OrderLifecycleManager,
        config: SettlementConfig | None = None,
    ) -> None:
        """Initialize the settlement tracker."""
        self.lifecycle_manager = lifecycle_manager
        self.config = config or SettlementConfig()
        self.logger = logging.getLogger(__name__)
        
        # Active settlement tracking
        self._tracking: Dict[OrderId, SettlementStatus] = {}
        self._settlement_callbacks: Dict[OrderId, List[Callable[[SettlementStatus], None]]] = {}

    async def track_settlement(
        self,
        order_ids: List[OrderId],
        websocket_monitor: Any,  # WebSocket monitoring service
        trading_client: Any | None = None,
    ) -> Dict[OrderId, SettlementStatus]:
        """Track settlement for multiple orders using WebSocket-first approach."""
        if not order_ids:
            return {}

        self.logger.info(
            "settlement_tracking_started",
            extra={
                "order_count": len(order_ids),
                "order_ids": [str(oid.value) for oid in order_ids],
                "websocket_timeout": self.config.websocket_timeout_seconds,
                "polling_fallback_enabled": self.config.enable_polling_fallback,
            },
        )

        # Initialize tracking for all orders
        now = datetime.now(UTC)
        for order_id in order_ids:
            self._tracking[order_id] = SettlementStatus(
                order_id=order_id,
                submitted_at=now,
                last_update=now,
                current_status="submitted",
            )

        # Start WebSocket monitoring
        try:
            websocket_result = await self._monitor_via_websocket(
                order_ids, websocket_monitor
            )
            settled_orders = set(websocket_result.orders_completed)
            
            # Mark WebSocket-settled orders
            for order_id_str in settled_orders:
                order_id = OrderId.from_string(order_id_str)  # Convert string to OrderId
                if order_id in self._tracking:
                    status = self._tracking[order_id]
                    status.settlement_method = "websocket"
                    status.last_update = datetime.now(UTC)
                    status.websocket_events_received += 1
                    
        except Exception as e:
            self.logger.error(
                "websocket_monitoring_failed",
                extra={
                    "error": str(e),
                    "order_count": len(order_ids),
                },
            )
            settled_orders = set()

        # Handle orders not settled via WebSocket
        unsettled_orders = [oid for oid in order_ids if str(oid.value) not in settled_orders]
        
        if unsettled_orders and self.config.enable_polling_fallback:
            await self._fallback_to_polling(unsettled_orders, trading_client)
        elif unsettled_orders:
            # Mark as timeout if polling fallback is disabled
            for order_id in unsettled_orders:
                if order_id in self._tracking:
                    status = self._tracking[order_id]
                    status.settlement_method = "timeout"
                    status.error_message = "WebSocket timeout, polling disabled"
                    
        # Final settlement status
        settlement_results = {oid: self._tracking[oid] for oid in order_ids}
        
        # Log final results
        self._log_settlement_summary(settlement_results)
        
        # Cleanup tracking data
        for order_id in order_ids:
            self._tracking.pop(order_id, None)
            self._settlement_callbacks.pop(order_id, None)
        
        return settlement_results

    async def _monitor_via_websocket(
        self,
        order_ids: List[OrderId],
        websocket_monitor: Any,
    ) -> WebSocketResultDTO:
        """Monitor orders via WebSocket with timeout."""
        self.logger.info(
            "websocket_monitoring_started",
            extra={
                "order_count": len(order_ids),
                "timeout_seconds": self.config.websocket_timeout_seconds,
            },
        )

        try:
            # Convert OrderId objects to strings for the monitor
            order_id_strings = [str(oid.value) for oid in order_ids]
            
            # Monitor with timeout
            result: WebSocketResultDTO = await asyncio.wait_for(
                websocket_monitor.wait_for_order_completion(order_id_strings),
                timeout=self.config.websocket_timeout_seconds,
            )
            
            self.logger.info(
                "websocket_monitoring_completed",
                extra={
                    "orders_completed": len(result.orders_completed),
                    "status": result.status.value,
                    "total_monitored": len(order_id_strings),
                },
            )
            
            return result
            
        except asyncio.TimeoutError:
            self.logger.warning(
                "websocket_monitoring_timeout",
                extra={
                    "timeout_seconds": self.config.websocket_timeout_seconds,
                    "order_count": len(order_ids),
                },
            )
            # Return empty result on timeout
            return WebSocketResultDTO(
                status=WebSocketStatus.TIMEOUT,
                message="WebSocket monitoring timeout",
                orders_completed=[],
            )

    async def _fallback_to_polling(
        self,
        order_ids: List[OrderId],
        trading_client: Any | None = None,
    ) -> None:
        """Fallback to polling for unsettled orders."""
        if trading_client is None:
            self.logger.warning(
                "polling_fallback_skipped",
                extra={
                    "reason": "no_trading_client",
                    "order_count": len(order_ids),
                },
            )
            return

        self.logger.info(
            "polling_fallback_started",
            extra={
                "order_count": len(order_ids),
                "max_attempts": self.config.max_polling_attempts,
                "interval_seconds": self.config.polling_interval_seconds,
            },
        )

        for attempt in range(self.config.max_polling_attempts):
            settled_in_attempt = []
            
            for order_id in order_ids:
                try:
                    # Check order status via API
                    order_status = await self._check_order_status_polling(
                        order_id, trading_client
                    )
                    
                    if order_id in self._tracking:
                        status = self._tracking[order_id]
                        status.polling_attempts += 1
                        status.current_status = order_status
                        status.last_update = datetime.now(UTC)
                        
                        if order_status.lower() in self.config.terminal_states:
                            status.settlement_method = "polling"
                            settled_in_attempt.append(order_id)
                            
                            self.logger.info(
                                "order_settled_via_polling",
                                extra={
                                    "order_id": str(order_id.value),
                                    "status": order_status,
                                    "attempt": attempt + 1,
                                },
                            )
                        
                except Exception as e:
                    self.logger.warning(
                        "polling_attempt_failed",
                        extra={
                            "order_id": str(order_id.value),
                            "attempt": attempt + 1,
                            "error": str(e),
                        },
                    )
                    
                    if order_id in self._tracking:
                        status = self._tracking[order_id]
                        status.polling_attempts += 1
                        status.error_message = str(e)

            # Remove settled orders from remaining list
            order_ids = [oid for oid in order_ids if oid not in settled_in_attempt]
            
            if not order_ids:
                # All orders settled
                break
                
            # Wait before next attempt
            if attempt < self.config.max_polling_attempts - 1:
                await asyncio.sleep(self.config.polling_interval_seconds)

        # Mark remaining orders as timeout
        for order_id in order_ids:
            if order_id in self._tracking:
                status = self._tracking[order_id]
                status.settlement_method = "timeout"
                status.error_message = f"Not settled after {self.config.max_polling_attempts} polling attempts"

    async def _check_order_status_polling(
        self,
        order_id: OrderId,
        trading_client: Any,
    ) -> str:
        """Check order status via polling API call."""
        try:
            order_obj = trading_client.get_order_by_id(str(order_id.value))
            status = str(getattr(order_obj, "status", "unknown")).lower()
            
            # Normalize status format
            if "orderstatus." in status:
                status = status.split(".")[-1]
                
            return status
            
        except Exception as e:
            self.logger.warning(
                "polling_status_check_failed",
                extra={
                    "order_id": str(order_id.value),
                    "error": str(e),
                },
            )
            raise

    def is_settled(self, order_id: OrderId) -> bool:
        """Check if an order is settled."""
        if order_id not in self._tracking:
            return False
            
        status = self._tracking[order_id]
        return status.current_status.lower() in self.config.terminal_states

    def get_settlement_status(self, order_id: OrderId) -> SettlementStatus | None:
        """Get current settlement status for an order."""
        return self._tracking.get(order_id)

    def _log_settlement_summary(self, results: Dict[OrderId, SettlementStatus]) -> None:
        """Log comprehensive settlement summary."""
        total_orders = len(results)
        websocket_settled = sum(1 for s in results.values() if s.settlement_method == "websocket")
        polling_settled = sum(1 for s in results.values() if s.settlement_method == "polling")
        timeouts = sum(1 for s in results.values() if s.settlement_method == "timeout")
        errors = sum(1 for s in results.values() if s.error_message is not None)

        self.logger.info(
            "settlement_summary",
            extra={
                "total_orders": total_orders,
                "websocket_settled": websocket_settled,
                "polling_settled": polling_settled,
                "timeouts": timeouts,
                "errors": errors,
                "websocket_success_rate": f"{websocket_settled/total_orders:.1%}" if total_orders > 0 else "0%",
                "overall_success_rate": f"{(websocket_settled + polling_settled)/total_orders:.1%}" if total_orders > 0 else "0%",
            },
        )

        # Log details for failed settlements
        for order_id, status in results.items():
            if status.settlement_method in ["timeout", "error"] or status.error_message:
                self.logger.warning(
                    "settlement_failed",
                    extra={
                        "order_id": str(order_id.value),
                        "method": status.settlement_method,
                        "current_status": status.current_status,
                        "websocket_events": status.websocket_events_received,
                        "polling_attempts": status.polling_attempts,
                        "error": status.error_message,
                    },
                )


class SettlementTimeoutError(Exception):
    """Raised when order settlement times out."""

    def __init__(self, order_ids: List[OrderId], message: str = "Order settlement timeout") -> None:
        self.order_ids = order_ids
        super().__init__(message)


class SettlementError(Exception):
    """Raised when order settlement fails."""

    def __init__(self, order_id: OrderId, error: OrderError, message: str | None = None) -> None:
        self.order_id = order_id
        self.error = error
        super().__init__(message or f"Settlement failed for {order_id}: {error.message}")