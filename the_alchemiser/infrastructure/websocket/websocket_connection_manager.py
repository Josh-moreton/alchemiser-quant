#!/usr/bin/env python3
"""WebSocket Connection Manager.

This module manages WebSocket connections for order monitoring and real-time data,
providing connection lifecycle management and cleanup utilities.
"""

import contextlib
import logging
import threading
import time
from typing import Any

from rich.console import Console


class WebSocketConnectionManager:
    """Manages WebSocket connections for the AlpacaClient.

    Provides connection setup, cleanup, and lifecycle management for both
    trading streams and data streams.
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

    def prepare_websocket_connection(self) -> bool:
        """Pre-initialize WebSocket connection and wait for it to be ready.

        Returns:
            True if WebSocket is ready, False if it failed to connect

        """
        api_key = self.api_key or getattr(self.trading_client, "_api_key", None)
        secret_key = self.secret_key or getattr(self.trading_client, "_secret_key", None)
        has_keys = isinstance(api_key, str) and isinstance(secret_key, str)

        if not has_keys:
            self.console.print("[yellow]⚠️ No API keys available for WebSocket[/yellow]")
            return False

        paper = getattr(self.trading_client, "_sandbox", True)

        try:
            from alpaca.trading.stream import TradingStream

            # Clean up any existing connection first
            self.cleanup_websocket_connection()

            self.console.print("[blue]🔌 Initializing WebSocket for trade monitoring...[/blue]")

            # Create the stream
            stream = TradingStream(str(api_key), str(secret_key), paper=paper)

            # Dummy handler for trade updates (we'll replace this later)
            async def dummy_handler(data: Any) -> None:
                """Log trade update messages during initial connection testing."""
                if logging.getLogger().level <= logging.DEBUG:
                    self.console.print(f"[dim]📡 Pre-connection WebSocket message: {data}[/dim]")

            # Subscribe to trade updates
            stream.subscribe_trade_updates(dummy_handler)

            # Start the stream
            thread = threading.Thread(target=stream.run, daemon=True)
            thread.start()

            # Give it a short time to connect
            time.sleep(2.0)

            # Store the stream for later use
            self._websocket_stream = stream
            self._websocket_thread = thread

            self.console.print("[green]🎯 WebSocket connection established![/green]")
            logging.info("🎯 WebSocket pre-connection established!")
            return True

        except Exception as e:
            error_msg = str(e).lower()
            if "insufficient subscription" in error_msg:
                self.console.print(
                    "[yellow]⚠️ WebSocket subscription insufficient for TradingStream[/yellow]"
                )
                logging.warning(
                    "⚠️ TradingStream WebSocket subscription insufficient - this is normal for some Alpaca account types"
                )
            else:
                self.console.print(f"[red]❌ Failed to pre-initialize WebSocket: {e}[/red]")
                logging.error(f"❌ Failed to pre-initialize WebSocket: {e}")
            return False

    def cleanup_websocket_connection(self) -> None:
        """Clean up any existing WebSocket connection."""
        if hasattr(self, "_websocket_stream") and self._websocket_stream:
            with contextlib.suppress(Exception):
                self._websocket_stream.stop()
            self._websocket_stream = None

        if hasattr(self, "_websocket_thread") and self._websocket_thread:
            try:
                if self._websocket_thread.is_alive():
                    self._websocket_thread.join(timeout=1.0)
            except Exception:
                pass
            self._websocket_thread = None

    def get_websocket_stream(self) -> Any:
        """Get current WebSocket stream if available."""
        return getattr(self, "_websocket_stream", None)

    def get_websocket_thread(self) -> Any:
        """Get current WebSocket thread if available."""
        return getattr(self, "_websocket_thread", None)

    def has_active_connection(self) -> bool:
        """Check if we have an active WebSocket connection."""
        stream = self.get_websocket_stream()
        thread = self.get_websocket_thread()
        return stream is not None and thread is not None and thread.is_alive()
