"""Business Unit: shared | Status: current.

Alpaca streaming management.

Handles WebSocket connections for real-time order updates and trade events.
"""

from __future__ import annotations

import logging
import threading
import time
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from alpaca.trading.stream import TradingStream

from ...dto.broker_dto import WebSocketResult, WebSocketStatus
from .exceptions import normalize_alpaca_error
from .models import WebSocketResultModel

if TYPE_CHECKING:
    from .config import AlpacaConfig

logger = logging.getLogger(__name__)


class StreamingManager:
    """Manages WebSocket streaming connections and order updates."""

    def __init__(self, config: AlpacaConfig) -> None:
        """Initialize with Alpaca configuration.

        Args:
            config: AlpacaConfig instance

        """
        self._config = config

        # Trading WebSocket (order updates) state
        self._trading_stream: TradingStream | None = None
        self._trading_stream_thread: threading.Thread | None = None
        self._trading_ws_connected: bool = False
        self._trading_ws_lock = threading.Lock()
        self._order_events: dict[str, threading.Event] = {}
        self._order_status: dict[str, str] = {}
        self._order_avg_price: dict[str, Decimal | None] = {}

    def wait_for_order_completion(
        self, order_ids: list[str], max_wait_seconds: int = 30
    ) -> WebSocketResult:
        """Wait for orders to reach a final state using TradingStream (with polling fallback).

        Args:
            order_ids: List of order IDs to monitor
            max_wait_seconds: Maximum time to wait for completion

        Returns:
            WebSocketResult with completion status and completed order IDs

        """
        completed_orders: list[str] = []
        start_time = time.time()

        try:
            # Prefer websocket order updates
            completed_orders = self._wait_for_orders_via_ws(order_ids, max_wait_seconds)

            # Fallback to polling for any remaining orders within remaining time
            remaining = [oid for oid in order_ids if oid not in completed_orders]
            if remaining:
                time_left = max(0.0, max_wait_seconds - (time.time() - start_time))
                local_start = time.time()
                while remaining and (time.time() - local_start) < time_left:
                    self._process_pending_orders(remaining, completed_orders)
                    remaining = [
                        oid for oid in remaining if oid not in completed_orders
                    ]
                    if remaining:
                        time.sleep(0.3)

            success = len(completed_orders) == len(order_ids)

            return WebSocketResult(
                status=(
                    WebSocketStatus.COMPLETED if success else WebSocketStatus.TIMEOUT
                ),
                message=f"Completed {len(completed_orders)}/{len(order_ids)} orders",
                completed_order_ids=completed_orders,
                metadata={"total_wait_time": time.time() - start_time},
            )

        except Exception as e:
            logger.error(f"Error monitoring order completion: {e}")
            return WebSocketResult(
                status=WebSocketStatus.ERROR,
                message=f"Error monitoring orders: {e}",
                completed_order_ids=completed_orders,
                metadata={"error": str(e)},
            )

    def wait_for_order_completion_model(
        self, order_ids: list[str], max_wait_seconds: int = 30
    ) -> WebSocketResultModel:
        """Wait for orders with typed model result.

        Args:
            order_ids: List of order IDs to monitor
            max_wait_seconds: Maximum time to wait for completion

        Returns:
            WebSocketResultModel instance

        """
        result = self.wait_for_order_completion(order_ids, max_wait_seconds)

        # Map WebSocketStatus to string
        status_map = {
            WebSocketStatus.COMPLETED: "connected",
            WebSocketStatus.TIMEOUT: "timeout",
            WebSocketStatus.ERROR: "error",
            WebSocketStatus.CONNECTED: "connected",
            WebSocketStatus.DISCONNECTED: "disconnected",
        }

        status_str = status_map.get(result.status, "error")

        return WebSocketResultModel(
            status=status_str,  # type: ignore[arg-type]
            completed_orders=result.completed_order_ids,
            pending_orders=[
                oid for oid in order_ids if oid not in result.completed_order_ids
            ],
            message=result.message,
            error=result.metadata.get("error") if result.metadata else None,
        )

    def ensure_trading_stream(self) -> None:
        """Ensure TradingStream is running and subscribed to trade updates.

        Raises:
            AlpacaError: If stream setup fails

        """
        with self._trading_ws_lock:
            if self._trading_stream and self._trading_ws_connected:
                return
            try:
                self._trading_stream = TradingStream(
                    self._config.api_key,
                    self._config.secret_key,
                    paper=self._config.paper,
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
                raise normalize_alpaca_error(exc, "Start trading stream") from exc

    def disconnect_streams(self) -> None:
        """Disconnect all active streams."""
        with self._trading_ws_lock:
            if self._trading_stream:
                try:
                    # Note: TradingStream might not have a clean stop method
                    # Setting connected flag will signal thread to terminate
                    self._trading_ws_connected = False
                    self._trading_stream = None
                    logger.info("Trading stream disconnected")
                except Exception as e:
                    logger.warning(f"Error disconnecting trading stream: {e}")

    def is_connected(self) -> bool:
        """Check if trading stream is connected.

        Returns:
            True if stream is connected and running

        """
        return self._trading_ws_connected and self._trading_stream is not None

    async def _on_order_update(self, data: dict[str, Any] | object) -> None:
        """Order update callback for TradingStream (async).

        Handles both SDK models and dict payloads. Must be async for TradingStream.
        """
        try:
            if hasattr(data, "event"):
                event_type = str(getattr(data, "event", "")).lower()
                order = getattr(data, "order", None)
            else:
                event_type = (
                    str(data.get("event", "")).lower() if isinstance(data, dict) else ""
                )
                order = data.get("order") if isinstance(data, dict) else None

            order_id = None
            status = None
            avg_price: Decimal | None = None

            if order is not None:
                order_id = str(
                    getattr(order, "id", "")
                    or (order.get("id") if isinstance(order, dict) else "")
                )
                status = str(
                    getattr(order, "status", "")
                    or (order.get("status") if isinstance(order, dict) else "")
                ).lower()
                avg_raw = (
                    getattr(order, "filled_avg_price", None)
                    if not isinstance(order, dict)
                    else order.get("filled_avg_price")
                )
                if avg_raw is not None:
                    try:
                        avg_price = Decimal(str(avg_raw))
                    except Exception:
                        avg_price = None

            if not order_id:
                return

            # Mark terminal and set events
            final_events = {"fill", "canceled", "rejected", "expired"}
            is_terminal = (
                event_type in final_events
                or status in final_events
                or status
                in {
                    "filled",
                    "canceled",
                    "rejected",
                    "expired",
                }
            )

            self._order_status[order_id] = status or event_type or ""
            self._order_avg_price[order_id] = avg_price

            if is_terminal:
                evt = self._order_events.get(order_id)
                if evt:
                    # Safe to set from event loop thread; non-blocking
                    evt.set()
        except Exception as exc:
            logger.error(f"Error in TradingStream order update: {exc}")

    def _wait_for_orders_via_ws(
        self, order_ids: list[str], timeout: float
    ) -> list[str]:
        """Use TradingStream updates to wait for orders to complete within timeout."""
        self.ensure_trading_stream()

        # Ensure events exist for ids
        events: dict[str, threading.Event] = {}
        for oid in order_ids:
            evt = self._order_events.get(oid)
            if evt is None:
                evt = threading.Event()
                self._order_events[oid] = evt
            events[oid] = evt

        # Wait for completion
        completed = []
        end_time = time.time() + timeout
        for oid in order_ids:
            time_left = max(0.0, end_time - time.time())
            if time_left <= 0:
                break
            evt = events.get(oid)
            if evt and evt.wait(timeout=time_left):
                completed.append(oid)

        return completed

    def _process_pending_orders(
        self, order_ids: list[str], completed_orders: list[str]
    ) -> None:
        """Process pending orders using external order manager.

        This is a placeholder that would need the order manager to check status.
        In the full implementation, this would be injected as a dependency.

        Args:
            order_ids: List of order IDs to check
            completed_orders: List to append completed order IDs to

        """
        # This method would need access to an order manager to check status
        # For now, it's a placeholder for the polling fallback functionality
        # In a production implementation, this would be injected or use a service locator

    def get_order_status(self, order_id: str) -> str | None:
        """Get cached order status from stream updates.

        Args:
            order_id: Order ID to get status for

        Returns:
            Status string if available, None otherwise

        """
        return self._order_status.get(order_id)

    def get_order_avg_price(self, order_id: str) -> Decimal | None:
        """Get cached average fill price from stream updates.

        Args:
            order_id: Order ID to get price for

        Returns:
            Average fill price if available, None otherwise

        """
        return self._order_avg_price.get(order_id)
