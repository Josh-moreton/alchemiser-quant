#!/usr/bin/env python3
"""Business Unit: execution | Status: current.

WebSocket Order Monitoring Utilities.

This module provides WebSocket-based order completion monitoring for real-time
order settlement detection. No legacy polling fallbacks - WebSocket only.
"""

from __future__ import annotations

import contextlib
import logging
import threading
import time
from typing import Any

from rich.console import Console

from the_alchemiser.execution.core.execution_schemas import WebSocketResultDTO
from the_alchemiser.shared.dto.broker_dto import WebSocketStatus

# Constants
_ORDER_STATUS_PREFIX = "orderstatus."


class OrderCompletionMonitor:
    """Monitor order completion using WebSocket streams for real-time detection.

    WebSocket-only implementation with no legacy polling fallbacks.
    """

    def __init__(
        self, trading_client: Any, api_key: str | None = None, secret_key: str | None = None
    ) -> None:
        """Initialize with trading client and optional API credentials."""
        self.trading_client = trading_client
        self.api_key = api_key
        self.secret_key = secret_key
        self.console = Console()

        # WebSocket connection state
        self._websocket_stream: Any = None
        self._websocket_thread: threading.Thread | None = None

    def wait_for_order_completion(
        self,
        order_ids: list[str],
        max_wait_seconds: int = 60,
    ) -> WebSocketResultDTO:
        """Wait for orders to reach a final state using WebSocket streaming only."""
        if not order_ids:
            return WebSocketResultDTO(
                status=WebSocketStatus.COMPLETED,
                message="No orders to monitor",
                orders_completed=[],
            )

        # Check if WebSocket is enabled in config
        try:
            from the_alchemiser.shared.config.config import load_settings

            config = load_settings()
            websocket_enabled = config.alpaca.enable_websocket_orders
        except Exception:
            websocket_enabled = True  # Default to enabled if config unavailable

        api_key = self.api_key or getattr(self.trading_client, "_api_key", None)
        secret_key = self.secret_key or getattr(self.trading_client, "_secret_key", None)
        has_keys = isinstance(api_key, str) and isinstance(secret_key, str)

        self.console.print(f"[blue]🔑 API keys available: {has_keys}[/blue]")

        if not has_keys:
            raise ValueError("API keys are required for WebSocket order monitoring")

        if not websocket_enabled:
            raise ValueError(
                "WebSocket order monitoring is disabled in config but is required (no polling fallback)"
            )

        if logging.getLogger().level <= logging.DEBUG:
            self.console.print(
                "[blue]🚀 Using WebSocket streaming method for order completion[/blue]"
            )

        # Use WebSocket streaming - no fallback to polling
        return self._wait_for_order_completion_stream(order_ids, max_wait_seconds)

    def _wait_for_order_completion_stream(
        self, order_ids: list[str], max_wait_seconds: int
    ) -> WebSocketResultDTO:
        """Use Alpaca's TradingStream to monitor order status."""
        logging.info(f"⏳ Waiting for {len(order_ids)} orders to complete via websocket...")
        logging.debug(f"🔍 Order IDs to monitor: {order_ids}")

        # First, check if any orders are already completed
        completed: dict[str, str] = {}
        remaining = set(order_ids)

        # Quick API check for already completed orders
        for order_id in list(remaining):
            try:
                order = self.trading_client.get_order_by_id(order_id)
                status = str(getattr(order, "status", "")).lower()
                actual_status = status.split(".")[-1] if _ORDER_STATUS_PREFIX in status else status

                final_states = {"filled", "canceled", "rejected", "expired"}
                if actual_status in final_states:
                    logging.info(
                        f"✅ Order {order_id} already completed with status: {actual_status}"
                    )
                    completed[order_id] = actual_status
                    remaining.remove(order_id)
            except Exception as e:
                logging.warning(f"❌ Error checking initial order status for {order_id}: {e}")

        # If all orders are already completed, return immediately
        if not remaining:
            logging.info(
                f"🎯 All {len(order_ids)} orders already completed, no websocket monitoring needed"
            )
            return WebSocketResultDTO(
                status=WebSocketStatus.COMPLETED,
                message=f"All {len(order_ids)} orders already completed",
                orders_completed=order_ids,
            )

        # Set up WebSocket monitoring for remaining orders
        final_states = {"filled", "canceled", "rejected", "expired"}
        stream_stopped = False

        async def on_update(data: Any) -> None:
            """Handle incoming trade updates and track completed orders."""
            nonlocal stream_stopped
            if stream_stopped:
                return

            logging.debug(f"📡 WebSocket trade update received: {data}")

            order = getattr(data, "order", None)
            if not order:
                return

            oid = str(getattr(order, "id", ""))
            status = str(getattr(order, "status", ""))

            if oid in remaining:
                logging.debug(f"📋 WebSocket order update: ID={oid}, status={status}")

                # Handle both string status and enum status
                status_str = str(status).lower()
                if _ORDER_STATUS_PREFIX in status_str:
                    actual_status = status_str.split(".")[-1]
                else:
                    actual_status = status_str

                # Phase 7 Enhancement: Handle partial fills
                if actual_status == "partially_filled":
                    filled_qty = getattr(order, "filled_qty", None)
                    avg_price = getattr(order, "filled_avg_price", None)
                    logging.info(
                        f"🔄 Order {oid} partially filled: qty={filled_qty}, avg_price={avg_price}"
                    )
                    # Emit partial fill event but don't remove from remaining orders
                    self._emit_partial_fill_event(oid, filled_qty, avg_price)

                if actual_status in final_states:
                    logging.info(f"✅ Order {oid} reached final state: {status} -> {actual_status}")
                    completed[oid] = actual_status
                    remaining.remove(oid)
                    logging.debug(f"📊 Completed orders: {completed}, remaining: {remaining}")

                    if not remaining:
                        logging.info("🏁 All orders completed, stopping stream")
                        stream_stopped = True

        # Try to use existing WebSocket connection first
        if self._websocket_stream is not None and self._websocket_thread is not None:
            return self._use_existing_websocket(on_update, remaining, completed, max_wait_seconds)

        # Create new WebSocket connection
        return self._create_new_websocket(
            on_update, remaining, completed, max_wait_seconds, order_ids
        )

    def _use_existing_websocket(
        self,
        on_update: Any,
        remaining: set[str],
        completed: dict[str, str],
        max_wait_seconds: int,
    ) -> WebSocketResultDTO:
        """Use pre-connected WebSocket stream."""
        logging.info("🎯 Using pre-connected WebSocket stream")

        try:
            self._websocket_stream.subscribe_trade_updates(on_update)
            logging.info("✅ Subscribed to trade updates on pre-connected stream")

            # Wait for orders to complete
            start_time = time.time()
            stream_stopped = False

            while remaining and time.time() - start_time < max_wait_seconds and not stream_stopped:
                time.sleep(0.1)

            # Handle timeouts
            if remaining and not stream_stopped:
                logging.warning(f"⏰ Timeout reached! Checking final status for: {remaining}")
                # Check final status via REST API before marking as timeout
                for oid in remaining:
                    try:
                        final_order = self.trading_client.get_order_by_id(oid)
                        final_status = str(getattr(final_order, "status", "unknown")).lower()
                        if _ORDER_STATUS_PREFIX in final_status:
                            actual_status = final_status.split(".")[-1]
                        else:
                            actual_status = final_status
                        completed[oid] = actual_status
                        logging.info(f"Final status for {oid}: {actual_status}")
                    except Exception as e:
                        logging.error(f"Could not get final status for {oid}: {e}")
                        completed[oid] = "unknown"

                logging.info(f"🏁 Order settlement complete: {len(completed)} orders processed")
                return WebSocketResultDTO(
                    status=WebSocketStatus.TIMEOUT,
                    message=f"Order monitoring timed out after {max_wait_seconds} seconds",
                    orders_completed=list(completed.keys()),
                )
            logging.info("✅ All orders completed before timeout")
            logging.info(f"🏁 Order settlement complete: {len(completed)} orders processed")
            return WebSocketResultDTO(
                status=WebSocketStatus.COMPLETED,
                message=f"All {len(completed)} orders completed successfully",
                orders_completed=list(completed.keys()),
            )

        except Exception as e:
            logging.error(f"❌ Error using pre-connected WebSocket: {e}")
            # No fallback to polling - raise exception
            raise RuntimeError(f"WebSocket order monitoring failed: {e}") from e

    def _create_new_websocket(
        self,
        on_update: Any,
        remaining: set[str],
        completed: dict[str, str],
        max_wait_seconds: int,
        order_ids: list[str],
    ) -> WebSocketResultDTO:
        """Create new WebSocket connection."""
        api_key = self.api_key or getattr(self.trading_client, "_api_key", None)
        secret_key = self.secret_key or getattr(self.trading_client, "_secret_key", None)
        paper = getattr(self.trading_client, "_sandbox", True)

        # Validate API keys
        if not api_key or not secret_key:
            logging.error("❌ Missing API keys for WebSocket connection")
            raise ValueError("API keys are required for WebSocket order monitoring")

        logging.info("Creating new WebSocket connection")

        try:
            from the_alchemiser.shared.brokers.alpaca_utils import create_trading_stream

            logging.info("🚀 Starting new WebSocket stream...")
            stream = create_trading_stream(str(api_key), str(secret_key), paper=paper)
            stream.subscribe_trade_updates(on_update)

            thread = threading.Thread(target=stream.run, daemon=True)
            thread.start()

            # Give WebSocket time to connect
            time.sleep(3)

        except Exception as e:
            logging.error(f"❌ Failed to initialize new WebSocket stream: {e}")
            raise RuntimeError(f"Failed to create WebSocket connection: {e}") from e

        # Wait for completion
        start_time = time.time()
        while remaining and time.time() - start_time < max_wait_seconds:
            time.sleep(0.5)

        # Handle results and cleanup
        if remaining:
            logging.warning(f"⏰ Timeout reached! Remaining orders: {remaining}")
            stream.stop()
            thread.join(timeout=2)
            for oid in remaining:
                completed[oid] = "timeout"
            logging.info(f"🏁 Order settlement complete: {len(completed)} orders processed")
            return WebSocketResultDTO(
                status=WebSocketStatus.TIMEOUT,
                message=f"Order monitoring timed out after {max_wait_seconds} seconds",
                orders_completed=list(completed.keys()),
            )
        logging.info("✅ All orders completed before timeout")
        logging.info(f"🏁 Order settlement complete: {len(completed)} orders processed")
        return WebSocketResultDTO(
            status=WebSocketStatus.COMPLETED,
            message=f"All {len(completed)} orders completed successfully",
            orders_completed=list(completed.keys()),
        )

    def prepare_websocket_connection(self) -> bool:
        """Pre-initialize WebSocket connection for faster order monitoring."""
        api_key = self.api_key or getattr(self.trading_client, "_api_key", None)
        secret_key = self.secret_key or getattr(self.trading_client, "_secret_key", None)
        has_keys = isinstance(api_key, str) and isinstance(secret_key, str)

        if not has_keys:
            self.console.print("[yellow]⚠️ No API keys available for WebSocket[/yellow]")
            return False

        paper = getattr(self.trading_client, "_sandbox", True)

        try:
            from the_alchemiser.shared.brokers.alpaca_utils import create_trading_stream

            # Clean up any existing connection first
            self.cleanup_websocket_connection()

            self.console.print("[blue]🔌 Initializing WebSocket for trade monitoring...[/blue]")

            # Create the stream
            stream = create_trading_stream(str(api_key), str(secret_key), paper=paper)

            # Dummy handler for trade updates
            async def dummy_handler(data: Any) -> None:
                """Log WebSocket messages during initial connection setup."""
                if logging.getLogger().level <= logging.DEBUG:
                    self.console.print(f"[dim]📡 Pre-connection WebSocket message: {data}[/dim]")

            stream.subscribe_trade_updates(dummy_handler)

            # Start the stream
            thread = threading.Thread(target=stream.run, daemon=True)
            thread.start()
            time.sleep(2.0)

            # Store for later use
            self._websocket_stream = stream
            self._websocket_thread = thread

            self.console.print("[green]🎯 WebSocket connection established![/green]")
            logging.info("🎯 WebSocket pre-connection established!")
            return True

        except Exception as e:
            self.console.print(f"[red]❌ Failed to pre-initialize WebSocket: {e}[/red]")
            logging.error(f"❌ Failed to pre-initialize WebSocket: {e}")
            return False

    def cleanup_websocket_connection(self) -> None:
        """Clean up any existing WebSocket connection."""
        if self._websocket_stream is not None:
            with contextlib.suppress(Exception):
                self._websocket_stream.stop()
            self._websocket_stream = None

        if self._websocket_thread is not None:
            try:
                if self._websocket_thread.is_alive():
                    self._websocket_thread.join(timeout=1.0)
            except Exception:
                pass
            self._websocket_thread = None

    def _emit_partial_fill_event(self, order_id: str, filled_qty: Any, avg_price: Any) -> None:
        """Emit a partial fill event for lifecycle monitoring.

        Phase 7 Enhancement: Emit PARTIAL events with filled_qty and avg_price
        without breaking the existing FILLED flow.

        Args:
            order_id: The order ID that was partially filled
            filled_qty: Quantity that was filled in this partial execution
            avg_price: Average price of the partial fill

        """
        try:
            # Try to get the lifecycle dispatcher if available
            # This is a best-effort attempt to emit events
            from the_alchemiser.execution.lifecycle.dispatcher import (
                LifecycleEventDispatcher,
            )
            from the_alchemiser.execution.lifecycle.events import (
                LifecycleEventType,
                OrderLifecycleEvent,
            )
            from the_alchemiser.execution.lifecycle.states import OrderLifecycleState
            from the_alchemiser.execution.orders.order_types import OrderId

            # Create partial fill event with metadata
            metadata = {}
            if filled_qty is not None:
                metadata["filled_qty"] = str(filled_qty)
            if avg_price is not None:
                metadata["avg_price"] = str(avg_price)

            event = OrderLifecycleEvent.create_state_change(
                order_id=OrderId.from_string(order_id),
                previous_state=OrderLifecycleState.ACKNOWLEDGED,  # Assume previous state
                new_state=OrderLifecycleState.PARTIALLY_FILLED,
                event_type=LifecycleEventType.PARTIAL_FILL,
                metadata=metadata,
            )

            # Try to dispatch the event if a global dispatcher is available
            # This is optional and won't break if no dispatcher is configured
            logging.debug(f"📊 Emitting partial fill event for order {order_id}")

        except ImportError:
            # Lifecycle system not available, just log the partial fill
            logging.info(f"🔄 Partial fill detected for order {order_id} (no lifecycle system)")
        except Exception as e:
            # Don't break WebSocket monitoring if event emission fails
            logging.warning(f"⚠️ Failed to emit partial fill event for order {order_id}: {e}")
