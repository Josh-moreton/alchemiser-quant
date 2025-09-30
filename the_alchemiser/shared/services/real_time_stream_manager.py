"""Business Unit: shared | Status: current.

Stream lifecycle management for real-time market data.

This module handles WebSocket stream setup, lifecycle management,
connection monitoring, and reconnection logic.
"""

from __future__ import annotations

import asyncio
import threading
import time
from typing import TYPE_CHECKING, Callable

from the_alchemiser.shared.brokers.alpaca_utils import create_stock_data_stream
from the_alchemiser.shared.logging.logging_utils import get_logger

if TYPE_CHECKING:
    from alpaca.data.live import StockDataStream
    from alpaca.data.models import Quote, Trade

    AlpacaQuoteData = dict[str, str | float | int] | Quote
    AlpacaTradeData = dict[str, str | float | int] | Trade
else:
    AlpacaQuoteData = dict[str, str | float | int] | object
    AlpacaTradeData = dict[str, str | float | int] | object


class RealTimeStreamManager:
    """Manages WebSocket stream lifecycle for real-time market data."""

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        feed: str = "iex",
        on_quote: Callable[[AlpacaQuoteData], None] | None = None,
        on_trade: Callable[[AlpacaTradeData], None] | None = None,
    ) -> None:
        """Initialize the stream manager.
        
        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key
            feed: Data feed to use (iex or sip)
            on_quote: Callback for quote events
            on_trade: Callback for trade events
        """
        self._api_key = api_key
        self._secret_key = secret_key
        self._feed = feed
        self._on_quote = on_quote
        self._on_trade = on_trade
        
        self._stream: StockDataStream | None = None
        self._stream_thread: threading.Thread | None = None
        self._should_reconnect = False
        self._connected = False
        
        # Circuit breaker for connection management
        from the_alchemiser.shared.utils.circuit_breaker import ConnectionCircuitBreaker
        self._circuit_breaker = ConnectionCircuitBreaker()
        
        self.logger = get_logger(__name__)

    def is_connected(self) -> bool:
        """Check if stream is currently connected.
        
        Returns:
            True if connected
        """
        return self._connected

    def start(
        self,
        get_symbols_callback: Callable[[], list[str]],
    ) -> bool:
        """Start the stream in a background thread.
        
        Args:
            get_symbols_callback: Callback to get current subscribed symbols
            
        Returns:
            True if started successfully
        """
        try:
            if self._stream_thread and self._stream_thread.is_alive():
                self.logger.warning("Stream already running")
                return True

            self._should_reconnect = True
            self._get_symbols = get_symbols_callback
            self._stream_thread = threading.Thread(
                target=self._run_stream_with_event_loop,
                name="RealTimePricing",
                daemon=True,
            )
            self._stream_thread.start()

            # Wait for connection with exponential backoff
            max_wait_time = 5.0
            check_interval = 0.05
            max_interval = 0.5
            elapsed_time = 0.0

            while elapsed_time < max_wait_time:
                if self._connected:
                    break
                time.sleep(check_interval)
                elapsed_time += check_interval
                check_interval = min(check_interval * 1.2, max_interval)

            if self._connected:
                self.logger.info("✅ Real-time stream started successfully")
                return True
                
            self.logger.error("❌ Failed to establish stream connection")
            return False

        except Exception as e:
            self.logger.error(f"Error starting stream: {e}")
            return False

    def stop(self) -> None:
        """Stop the stream."""
        try:
            self._should_reconnect = False

            if self._stream:
                self._stream.stop()
                self._stream = None

            if self._stream_thread and self._stream_thread.is_alive():
                self._stream_thread.join(timeout=5.0)

            self._connected = False
            self.logger.info("🛑 Real-time stream stopped")

        except Exception as e:
            self.logger.error(f"Error stopping stream: {e}")

    def restart(self) -> None:
        """Restart the stream to pick up new subscriptions."""
        try:
            # Signal the current stream to stop
            self._should_reconnect = False
            if self._stream:
                try:
                    self._stream.stop()
                    time.sleep(0.5)  # Give time to close connection
                    self._stream = None
                except Exception as e:
                    self.logger.debug(f"Error stopping stream for restart: {e}")

            # Wait for the stream thread to finish
            if self._stream_thread and self._stream_thread.is_alive():
                self._stream_thread.join(timeout=5.0)
                if self._stream_thread.is_alive():
                    self.logger.warning("⚠️ Stream thread didn't terminate cleanly")
                    return

            # Add backoff delay before reconnecting
            time.sleep(1.0)

            # Restart with new subscriptions
            self._should_reconnect = True
            self._connected = False
            self._stream_thread = threading.Thread(
                target=self._run_stream_with_event_loop,
                name="RealTimePricing",
                daemon=True,
            )
            self._stream_thread.start()

            # Wait for reconnection
            start_time = time.time()
            while time.time() - start_time < 10.0:
                if self._connected:
                    self.logger.info("✅ Stream restarted successfully")
                    break
                time.sleep(0.1)
            else:
                self.logger.warning("⚠️ Stream restart timed out")

        except Exception as e:
            self.logger.error(f"Error restarting stream: {e}")
            self._connected = False

    def _run_stream_with_event_loop(self) -> None:
        """Run the WebSocket stream in a new event loop."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(self._run_stream_async())
        except Exception as e:
            self.logger.error(f"Error in stream event loop: {e}")
        finally:
            try:
                # Cancel any remaining tasks
                pending = asyncio.all_tasks(loop)
                for task in pending:
                    task.cancel()

                if pending:
                    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))

                loop.close()
            except Exception as e:
                self.logger.error(f"Error cleaning up event loop: {e}")

    async def _run_stream_async(self) -> None:
        """Async method to run the WebSocket stream."""
        retry_count = 0
        max_retries = 5
        base_delay = 1.0

        while self._should_reconnect and retry_count < max_retries:
            try:
                should_break = await self._execute_stream_attempt(retry_count + 1)
                if should_break:
                    break

            except Exception as e:
                retry_count += 1
                should_retry = await self._handle_stream_error(
                    e, retry_count, max_retries, base_delay
                )
                if not should_retry:
                    break
            finally:
                self._connected = False

        self.logger.info("📡 Stream thread exiting")

    async def _execute_stream_attempt(self, attempt_number: int) -> bool:
        """Execute a single stream attempt with circuit breaker protection.
        
        Args:
            attempt_number: Current attempt number
            
        Returns:
            True if should break from retry loop
        """
        self.logger.info(f"🔄 Attempting to start stream (attempt {attempt_number})")

        symbols_to_subscribe = self._get_symbols()

        try:
            if symbols_to_subscribe:
                result = await self._setup_and_run_stream_with_symbols(symbols_to_subscribe)
            else:
                result = await self._handle_no_symbols_to_subscribe()

            if result:
                self._circuit_breaker.record_success()
            return result

        except Exception as e:
            error_msg = str(e)
            if "connection limit exceeded" in error_msg.lower() or "http 429" in error_msg.lower():
                self._circuit_breaker.record_failure(f"Connection limit exceeded: {error_msg}")
            else:
                self._circuit_breaker.record_failure(f"Stream error: {error_msg}")
            raise

    async def _setup_and_run_stream_with_symbols(self, symbols_to_subscribe: list[str]) -> bool:
        """Set up stream with symbols and run it.
        
        Args:
            symbols_to_subscribe: List of symbols to subscribe to
            
        Returns:
            True if stream closed normally
        """
        self.logger.info(
            f"📡 Setting up subscriptions for {len(symbols_to_subscribe)} symbols: "
            f"{sorted(symbols_to_subscribe)}"
        )

        # Create a fresh stream instance
        self._stream = create_stock_data_stream(
            api_key=self._api_key,
            secret_key=self._secret_key,
            feed=self._feed,
        )

        # Subscribe to quotes and trades
        if self._on_quote:
            self._stream.subscribe_quotes(self._on_quote, *symbols_to_subscribe)
        if self._on_trade:
            self._stream.subscribe_trades(self._on_trade, *symbols_to_subscribe)

        self.logger.info("✅ All subscriptions set up successfully")

        # Mark as connected
        self._connected = True

        # Run the stream
        await self._stream._run_forever()

        # If we get here, the stream closed normally
        self.logger.info("📡 Stream closed normally")
        return True

    async def _handle_no_symbols_to_subscribe(self) -> bool:
        """Handle case when no symbols are available.
        
        Returns:
            True if should break from retry loop
        """
        await self._wait_for_subscription_requests()
        symbols_to_subscribe = self._get_symbols()

        if symbols_to_subscribe:
            self.logger.info(f"📡 New subscriptions detected: {sorted(symbols_to_subscribe)}")
            self._connected = False
            return False  # Continue retry loop

        self.logger.info("📡 Shutting down stream - no reconnection requested")
        return True  # Break from retry loop

    async def _wait_for_subscription_requests(self) -> None:
        """Wait for subscriptions to be added."""
        self.logger.info("📡 No symbols to subscribe to, waiting...")
        self._connected = True  # Mark as ready

        symbols_to_subscribe: list[str] = []
        while self._should_reconnect and not symbols_to_subscribe:
            await asyncio.sleep(1.0)
            symbols_to_subscribe = self._get_symbols()

    async def _handle_stream_error(
        self, error: Exception, retry_count: int, max_retries: int, base_delay: float
    ) -> bool:
        """Handle stream errors and determine if retry should continue.
        
        Args:
            error: The exception that occurred
            retry_count: Current retry attempt number
            max_retries: Maximum number of retries allowed
            base_delay: Base delay for exponential backoff
            
        Returns:
            True if should continue retrying
        """
        delay = min(base_delay * (2 ** (retry_count - 1)), 30.0)
        self.logger.error(f"❌ Stream error (attempt {retry_count}): {error}")

        if retry_count < max_retries and self._should_reconnect:
            self.logger.info(f"⏱️ Retrying in {delay:.1f} seconds...")
            await asyncio.sleep(delay)
            return True

        self.logger.error("🚨 Max retries exceeded")
        return False
