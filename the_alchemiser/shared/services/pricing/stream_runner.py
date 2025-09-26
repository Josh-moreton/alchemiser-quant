"""Business Unit: shared | Status: current.

Retry loop, async/thread bridging, and circuit-breaker coordination for pricing streams.
"""

from __future__ import annotations

import asyncio
import logging
import threading
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from the_alchemiser.shared.brokers.alpaca_utils import create_stock_data_stream
from the_alchemiser.shared.utils.circuit_breaker import ConnectionCircuitBreaker

if TYPE_CHECKING:
    from alpaca.data.live import StockDataStream

    from .models import AlpacaQuoteData, AlpacaTradeData

logger = logging.getLogger(__name__)


class StreamRunner:
    """Manages WebSocket stream lifecycle with retry logic and circuit breaker."""

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        feed: str,
        quote_handler: Callable[[AlpacaQuoteData], Awaitable[None]],
        trade_handler: Callable[[AlpacaTradeData], Awaitable[None]],
        get_symbols_callback: Callable[[], list[str]],
    ) -> None:
        """Initialize stream runner.
        
        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key
            feed: Data feed to use ("iex" or "sip")
            quote_handler: Async callback for quote data
            trade_handler: Async callback for trade data
            get_symbols_callback: Callback to get current symbol subscriptions

        """
        self._api_key = api_key
        self._secret_key = secret_key
        self._feed = feed
        self._quote_handler = quote_handler
        self._trade_handler = trade_handler
        self._get_symbols_callback = get_symbols_callback
        
        # Stream management
        self._stream: StockDataStream | None = None
        self._stream_thread: threading.Thread | None = None
        self._should_reconnect = False
        self._connected = False
        
        # Background task management
        self._background_tasks: set[asyncio.Task[None]] = set()
        
        # Circuit breaker for connection management
        self._circuit_breaker = ConnectionCircuitBreaker()

    def start(self) -> bool:
        """Start the stream in a background thread.
        
        Returns:
            True if stream started successfully

        """
        if self._stream_thread is not None and self._stream_thread.is_alive():
            logger.warning("Stream already running")
            return True

        self._should_reconnect = True
        self._stream_thread = threading.Thread(
            target=self._run_stream_with_event_loop,
            name="PricingStream",
            daemon=True,
        )
        self._stream_thread.start()

        # Wait for connection with exponential backoff
        return self._wait_for_connection()

    def stop(self) -> None:
        """Stop the stream and clean up resources."""
        logger.info("🛑 Stopping real-time pricing stream...")
        self._should_reconnect = False
        self._connected = False

        if self._stream:
            try:
                # Use stop() method as in the original implementation
                self._stream.stop()
            except Exception as e:
                logger.warning(f"Error stopping stream: {e}")

        if self._stream_thread and self._stream_thread.is_alive():
            self._stream_thread.join(timeout=5.0)
            if self._stream_thread.is_alive():
                logger.warning("Stream thread did not stop gracefully")

        logger.info("🛑 Real-time pricing stream stopped")

    def is_connected(self) -> bool:
        """Check if the stream is connected.
        
        Returns:
            Connection status

        """
        return self._connected

    def restart_for_new_subscription(self) -> None:
        """Restart stream to add new subscriptions."""
        if not self._connected:
            logger.debug("Stream not connected, ignoring restart request")
            return

        logger.info("🔄 Restarting stream for new subscriptions...")
        self._connected = False

        if self._stream:
            try:
                # Use stop() method as in the original implementation
                self._stream.stop()
            except Exception as e:
                logger.warning(f"Error stopping stream during restart: {e}")

    def _run_stream_with_event_loop(self) -> None:
        """Run stream in dedicated event loop (thread target)."""
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                loop.run_until_complete(self._run_stream_async())
            finally:
                # Clean up background tasks
                if self._background_tasks:
                    logger.debug(f"Cleaning up {len(self._background_tasks)} background tasks")
                    for task in list(self._background_tasks):
                        if not task.done():
                            task.cancel()
                    
                    # Wait for tasks to complete
                    if self._background_tasks:
                        loop.run_until_complete(
                            asyncio.gather(*self._background_tasks, return_exceptions=True)
                        )

                # Close the loop
                loop.close()

        except Exception as e:
            logger.error(f"Error in stream event loop: {e}", exc_info=True)
        finally:
            self._connected = False

    async def _run_stream_async(self) -> None:
        """Run main async stream loop with retry logic."""
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

        logger.info("📡 Real-time pricing stream thread exiting")

    async def _execute_stream_attempt(self, attempt_number: int) -> bool:
        """Execute a single stream attempt with circuit breaker protection.
        
        Args:
            attempt_number: Current attempt number for logging
            
        Returns:
            True if should break from retry loop, False to continue

        """
        logger.info(f"🔄 Attempting to start real-time data stream (attempt {attempt_number})")

        symbols_to_subscribe = self._get_symbols_callback()

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

    async def _handle_no_symbols_to_subscribe(self) -> bool:
        """Handle case when no symbols are available to subscribe.
        
        Returns:
            True if should break from retry loop, False to continue

        """
        await self._wait_for_subscription_requests()
        symbols_to_subscribe = self._get_symbols_callback()

        if symbols_to_subscribe:
            logger.info(f"📡 New subscriptions detected: {sorted(symbols_to_subscribe)}")
            self._connected = False
            return False  # Continue retry loop

        logger.info("📡 Shutting down stream - no reconnection requested")
        return True  # Break from retry loop

    async def _setup_and_run_stream_with_symbols(self, symbols_to_subscribe: list[str]) -> bool:
        """Set up stream with symbols and run it.
        
        Args:
            symbols_to_subscribe: List of symbols to subscribe to
            
        Returns:
            True if stream closed normally, False if should retry

        """
        logger.info(
            f"📡 Setting up subscriptions for {len(symbols_to_subscribe)} symbols: {sorted(symbols_to_subscribe)}"
        )

        # Create a fresh stream instance for each attempt
        self._stream = create_stock_data_stream(
            api_key=self._api_key,
            secret_key=self._secret_key,
            feed=self._feed,
        )

        # Subscribe to quotes and trades for all symbols at once
        self._stream.subscribe_quotes(self._quote_handler, *symbols_to_subscribe)
        self._stream.subscribe_trades(self._trade_handler, *symbols_to_subscribe)

        logger.info("✅ All subscriptions set up successfully")

        # Mark as connected before starting the stream
        self._connected = True

        # Run the stream's internal async method directly
        await self._stream._run_forever()

        # If we get here, the stream closed normally
        logger.info("📡 Real-time data stream closed normally")
        return True

    async def _wait_for_subscription_requests(self) -> None:
        """Wait for subscriptions to be added."""
        logger.info("📡 No symbols to subscribe to, waiting for subscription requests...")
        self._connected = True  # Mark as ready to receive subscriptions

        symbols_to_subscribe: list[str] = []
        while self._should_reconnect and not symbols_to_subscribe:
            await asyncio.sleep(1.0)  # Check every second
            symbols_to_subscribe = self._get_symbols_callback()

    async def _handle_stream_error(
        self,
        error: Exception,
        retry_count: int,
        max_retries: int,
        base_delay: float,
    ) -> bool:
        """Handle stream errors and determine if retry should continue.
        
        Args:
            error: The exception that occurred
            retry_count: Current retry attempt number
            max_retries: Maximum number of retries allowed
            base_delay: Base delay for exponential backoff
            
        Returns:
            True if should continue retrying, False otherwise

        """
        delay = min(base_delay * (2 ** (retry_count - 1)), 30.0)  # Cap at 30 seconds
        logger.error(f"❌ Real-time data stream error (attempt {retry_count}): {error}")

        if retry_count < max_retries and self._should_reconnect:
            logger.info(f"⏱️ Retrying in {delay:.1f} seconds...")
            await asyncio.sleep(delay)
            return True

        logger.error("🚨 Max retries exceeded, stopping real-time pricing service")
        return False

    def _wait_for_connection(self) -> bool:
        """Wait for connection with exponential backoff.
        
        Returns:
            True if connected successfully

        """
        import time
        
        max_wait_time = 5.0  # 5 second timeout
        check_interval = 0.05  # Start with 50ms
        max_interval = 0.5  # Cap at 500ms
        elapsed_time = 0.0

        while elapsed_time < max_wait_time:
            if self._connected:
                break
            time.sleep(check_interval)
            elapsed_time += check_interval
            # Exponential backoff for less aggressive polling
            check_interval = min(check_interval * 1.2, max_interval)

        if self._connected:
            logger.info("✅ Stream connected successfully")
            return True
        logger.warning("⚠️ Stream connection timeout")
        return False

    def add_background_task(self, task: asyncio.Task[None]) -> None:
        """Add a background task for cleanup tracking.
        
        Args:
            task: Task to track

        """
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)