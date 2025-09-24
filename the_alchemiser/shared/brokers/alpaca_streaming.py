"""Business Unit: shared | Status: current.

Alpaca streaming operations for WebSocket management and order event handling.

This module encapsulates TradingStream lifecycle, reconnection logic, and provides
idempotent handlers for order status updates. It ensures event-driven reliability
with correlation ID propagation and at-least-once delivery tolerance.
"""

from __future__ import annotations

import logging
import threading
import time
from decimal import Decimal
from typing import Any

from alpaca.trading.stream import TradingStream

from the_alchemiser.shared.brokers.alpaca_utils import create_trading_stream
from the_alchemiser.shared.dto.broker_dto import WebSocketResult, WebSocketStatus

logger = logging.getLogger(__name__)


class AlpacaStreamingManager:
    """Manages Alpaca TradingStream lifecycle and order event handling.
    
    Provides idempotent order event handling with correlation ID support
    and ensures handlers are safe under at-least-once delivery semantics.
    """

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        *,
        paper: bool = True,
    ) -> None:
        """Initialize the streaming manager.
        
        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key
            paper: Whether to use paper trading (default: True)
        """
        self._api_key = api_key
        self._secret_key = secret_key
        self._paper = paper
        
        # TradingStream state
        self._trading_stream: TradingStream | None = None
        self._trading_stream_thread: threading.Thread | None = None
        self._trading_ws_connected: bool = False
        self._trading_ws_lock = threading.Lock()
        
        # Order tracking for event deduplication and status updates
        self._order_events: dict[str, threading.Event] = {}
        self._order_status: dict[str, str] = {}
        self._order_avg_price: dict[str, Decimal | None] = {}
        
        logger.info(f"AlpacaStreamingManager initialized - Paper: {paper}")

    def ensure_trading_stream(self) -> None:
        """Ensure TradingStream is running and subscribed to trade updates.
        
        This method is idempotent and safe to call multiple times.
        """
        with self._trading_ws_lock:
            if self._trading_stream and self._trading_ws_connected:
                return
                
            try:
                self._trading_stream = create_trading_stream(
                    api_key=self._api_key,
                    secret_key=self._secret_key,
                    paper=self._paper
                )
                self._trading_stream.subscribe_trade_updates(self._on_order_update)

                def _runner() -> None:
                    try:
                        ts = self._trading_stream
                        if ts is not None:
                            ts.run()
                    except Exception as exc:
                        logger.error(f"TradingStream terminated: {exc}")
                    finally:
                        self._trading_ws_connected = False

                self._trading_ws_connected = True
                self._trading_stream_thread = threading.Thread(
                    target=_runner, name="AlpacaTradingWS", daemon=True
                )
                self._trading_stream_thread.start()
                logger.info("✅ TradingStream started (order updates)")
                
            except Exception as exc:
                logger.error(f"Failed to start TradingStream: {exc}")
                self._trading_ws_connected = False

    def wait_for_order_completion(
        self, order_ids: list[str], max_wait_seconds: int = 30
    ) -> WebSocketResult:
        """Wait for orders to complete via WebSocket events.
        
        This method handles at-least-once delivery by deduplicating events
        and tolerating reordering.
        
        Args:
            order_ids: List of order IDs to wait for
            max_wait_seconds: Maximum time to wait for completion
            
        Returns:
            WebSocketResult with completion status and details
        """
        if not order_ids:
            return WebSocketResult(
                status=WebSocketStatus.SUCCESS,
                completed_orders=[],
                message="No orders to wait for"
            )

        logger.info(f"🔍 Waiting for {len(order_ids)} orders via WebSocket")
        
        # Ensure streaming is active
        self.ensure_trading_stream()
        
        # Initialize tracking events for new orders
        for order_id in order_ids:
            if order_id not in self._order_events:
                self._order_events[order_id] = threading.Event()
        
        return self._wait_for_orders_via_ws(order_ids, max_wait_seconds)

    def _wait_for_orders_via_ws(
        self, order_ids: list[str], max_wait_seconds: int
    ) -> WebSocketResult:
        """Internal method to wait for orders via WebSocket with timeout."""
        start_time = time.time()
        completed_orders: list[str] = []
        
        while self._should_continue_waiting(
            completed_orders, order_ids, start_time, max_wait_seconds
        ):
            # Process pending orders and update completed list
            self._process_pending_orders(order_ids, completed_orders)
            
            if len(completed_orders) == len(order_ids):
                break
                
            # Short sleep to avoid tight polling
            time.sleep(0.1)
        
        # Final status check
        elapsed = time.time() - start_time
        success_rate = len(completed_orders) / len(order_ids) if order_ids else 1.0
        
        if len(completed_orders) == len(order_ids):
            status = WebSocketStatus.SUCCESS
            message = f"All {len(order_ids)} orders completed in {elapsed:.1f}s"
        elif completed_orders:
            status = WebSocketStatus.PARTIAL
            message = f"{len(completed_orders)}/{len(order_ids)} orders completed ({success_rate:.1%})"
        else:
            status = WebSocketStatus.TIMEOUT
            message = f"No orders completed in {max_wait_seconds}s"
        
        logger.info(f"🏁 WebSocket wait result: {message}")
        
        return WebSocketResult(
            status=status,
            completed_orders=completed_orders,
            message=message
        )

    def _process_pending_orders(
        self, order_ids: list[str], completed_orders: list[str]
    ) -> None:
        """Process pending orders and update completed list (idempotent)."""
        for order_id in order_ids:
            if order_id in completed_orders:
                continue  # Already completed
                
            event = self._order_events.get(order_id)
            if event and event.is_set():
                if order_id not in completed_orders:
                    completed_orders.append(order_id)
                    logger.debug(f"✅ Order {order_id} marked as completed")

    def _should_continue_waiting(
        self,
        completed_orders: list[str],
        order_ids: list[str],
        start_time: float,
        max_wait_seconds: int,
    ) -> bool:
        """Check if we should continue waiting for orders."""
        # All orders completed
        if len(completed_orders) >= len(order_ids):
            return False
            
        # Timeout reached
        if time.time() - start_time >= max_wait_seconds:
            return False
            
        # WebSocket not connected
        if not self._trading_ws_connected:
            logger.warning("WebSocket disconnected, stopping wait")
            return False
            
        return True

    def _on_order_update(self, data: dict[str, Any] | object) -> None:
        """Handle order updates from TradingStream.
        
        This handler is idempotent and safe for at-least-once delivery.
        Includes correlation ID logging for traceability.
        """
        try:
            event_type, order = self._extract_event_and_order(data)
            order_id, status, avg_price = self._extract_order_info(order)
            
            if not order_id:
                logger.debug("Received order update without order ID, skipping")
                return
                
            # Log with structured context for correlation
            logger.info(
                f"📡 Order update: {order_id} -> {event_type}/{status}",
                extra={
                    "order_id": order_id,
                    "event_type": event_type,
                    "status": status,
                    "avg_price": str(avg_price) if avg_price else None,
                    "module": "alpaca_streaming",
                }
            )
            
            # Idempotent status update
            self._order_status[order_id] = status or "unknown"
            if avg_price is not None:
                self._order_avg_price[order_id] = avg_price
            
            # Signal completion for terminal events (idempotent)
            if self._is_terminal_event(event_type, status):
                event = self._order_events.get(order_id)
                if event and not event.is_set():
                    event.set()
                    logger.debug(f"🏁 Terminal event for order {order_id}")
                    
        except Exception as exc:
            logger.error(f"Error processing order update: {exc}")

    def _extract_event_and_order(
        self, data: dict[str, Any] | object
    ) -> tuple[str, dict[str, Any] | object | None]:
        """Extract event type and order from streaming data."""
        if hasattr(data, "event"):
            event_type = str(getattr(data, "event", "")).lower()
            order = getattr(data, "order", None)
        else:
            event_type = (
                str(data.get("event", "")).lower() if isinstance(data, dict) else ""
            )
            order = data.get("order") if isinstance(data, dict) else None
        return event_type, order

    def _extract_order_info(
        self, order: dict[str, Any] | object | None
    ) -> tuple[str | None, str | None, Decimal | None]:
        """Extract order ID, status, and average price from order object."""
        if order is None:
            return None, None, None
            
        # Extract order ID
        order_id = None
        if hasattr(order, "id"):
            order_id = str(getattr(order, "id"))
        elif isinstance(order, dict) and "id" in order:
            order_id = str(order["id"])
            
        # Extract status
        status = None
        if hasattr(order, "status"):
            status = str(getattr(order, "status", "")).lower()
        elif isinstance(order, dict) and "status" in order:
            status = str(order.get("status", "")).lower()
            
        # Extract average price
        avg_price = self._convert_avg_price(order)
        
        return order_id, status, avg_price

    def _convert_avg_price(self, order: dict[str, Any] | object) -> Decimal | None:
        """Convert order average price to Decimal."""
        try:
            avg_price_raw = None
            if hasattr(order, "filled_avg_price"):
                avg_price_raw = getattr(order, "filled_avg_price", None)
            elif isinstance(order, dict) and "filled_avg_price" in order:
                avg_price_raw = order.get("filled_avg_price")
                
            if avg_price_raw is not None:
                return Decimal(str(avg_price_raw))
        except (ValueError, TypeError, AttributeError):
            pass
        return None

    def _is_terminal_event(self, event_type: str, status: str | None) -> bool:
        """Check if event represents a terminal order state."""
        terminal_events = {"fill", "partial_fill", "canceled", "expired", "rejected"}
        terminal_statuses = {"filled", "canceled", "expired", "rejected"}
        
        return (
            event_type.lower() in terminal_events
            or (status and status.lower() in terminal_statuses)
        )

    def disconnect(self) -> None:
        """Disconnect and cleanup streaming resources."""
        with self._trading_ws_lock:
            if self._trading_stream:
                try:
                    self._trading_stream.stop()
                except Exception as e:
                    logger.warning(f"Error stopping TradingStream: {e}")
                    
            self._trading_ws_connected = False
            self._trading_stream = None
            
            # Clear event state
            self._order_events.clear()
            self._order_status.clear()
            self._order_avg_price.clear()
            
            logger.info("TradingStream disconnected and cleaned up")

    @property
    def is_connected(self) -> bool:
        """Check if TradingStream is connected."""
        return self._trading_ws_connected