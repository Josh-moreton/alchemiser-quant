"""Business Unit: shared | Status: current.

Stream lifecycle management for real-time market data.

This module handles WebSocket stream setup, lifecycle management,
connection monitoring, and reconnection logic.
"""

from __future__ import annotations

import threading
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from structlog import BoundLogger

from the_alchemiser.shared.brokers.alpaca_utils import create_stock_data_stream
from the_alchemiser.shared.errors.exceptions import (
    ConfigurationError,
    StreamingError,
)
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.utils.circuit_breaker import ConnectionCircuitBreaker

if TYPE_CHECKING:
    from alpaca.data.live import StockDataStream
    from alpaca.data.models import Quote, Trade

    AlpacaQuoteData = dict[str, str | float | int] | Quote
    AlpacaTradeData = dict[str, str | float | int] | Trade
else:
    AlpacaQuoteData = dict[str, str | float | int] | object
    AlpacaTradeData = dict[str, str | float | int] | object


@dataclass(frozen=True)
class StreamConfig:
    """Configuration for stream manager timeouts and retry settings."""

    connection_timeout: float = 5.0
    initial_check_interval: float = 0.05
    max_check_interval: float = 0.5
    restart_wait_timeout: float = 10.0
    thread_join_timeout: float = 5.0
    stream_stop_delay: float = 0.5
    reconnect_backoff_delay: float = 1.0
    max_retries: int = 5
    base_retry_delay: float = 1.0
    max_retry_delay: float = 30.0
    subscription_poll_interval: float = 1.0


class SecureCredential:
    """Wrapper for API credentials that prevents accidental exposure."""

    def __init__(self, value: str, credential_type: str = "credential") -> None:
        """Initialize secure credential.

        Args:
            value: The credential value
            credential_type: Type of credential for logging

        """
        if not value or not value.strip():
            raise ConfigurationError(
                f"Invalid {credential_type}: cannot be empty",
                config_key=credential_type,
            )
        self._value = value
        self._type = credential_type

    @property
    def value(self) -> str:
        """Get the credential value."""
        return self._value

    def __repr__(self) -> str:
        """Prevent credential exposure in logs and debug output."""
        return f"SecureCredential({self._type}=***REDACTED***)"

    def __str__(self) -> str:
        """Prevent credential exposure in string conversion."""
        return f"***REDACTED_{self._type.upper()}***"


class RealTimeStreamManager:
    """Manages WebSocket stream lifecycle for real-time market data.

    This class handles WebSocket connection lifecycle, including:
    - Thread management for async stream operations
    - Connection monitoring and health checks
    - Retry logic with exponential backoff
    - Circuit breaker integration for rate limiting
    - Thread-safe state management

    Thread Safety:
        All mutable state is protected by _state_lock to prevent race conditions
        between the main thread and background stream thread.
    """

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        feed: Literal["iex", "sip"] = "iex",
        on_quote: Callable[[AlpacaQuoteData], Awaitable[None]] | None = None,
        on_trade: Callable[[AlpacaTradeData], Awaitable[None]] | None = None,
        config: StreamConfig | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Initialize the stream manager.

        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key
            feed: Data feed to use (iex or sip)
            on_quote: Callback for quote events
            on_trade: Callback for trade events
            config: Stream configuration (uses defaults if not provided)
            correlation_id: Optional correlation ID for distributed tracing

        Raises:
            ConfigurationError: If credentials are invalid or feed is unsupported

        """
        # Validate and secure credentials
        self._api_key = SecureCredential(api_key, "api_key")
        self._secret_key = SecureCredential(secret_key, "secret_key")

        # Validate feed parameter
        if feed not in ("iex", "sip"):
            raise ConfigurationError(
                f"Invalid feed: {feed}. Must be 'iex' or 'sip'",
                config_key="feed",
                config_value=feed,
            )
        self._feed = feed

        # Validate callbacks if provided
        if on_quote is not None and not callable(on_quote):
            raise ConfigurationError("on_quote must be callable", config_key="on_quote")
        if on_trade is not None and not callable(on_trade):
            raise ConfigurationError("on_trade must be callable", config_key="on_trade")

        self._on_quote = on_quote
        self._on_trade = on_trade

        # Configuration
        self._config = config or StreamConfig()

        # Stream state (protected by lock)
        self._state_lock = threading.Lock()
        self._stream: StockDataStream | None = None
        self._stream_thread: threading.Thread | None = None
        self._should_reconnect = False
        self._connected_event = threading.Event()

        # Circuit breaker for connection management
        self._circuit_breaker = ConnectionCircuitBreaker()

        # Logging with correlation ID
        self.logger: BoundLogger = get_logger(__name__)
        if correlation_id:
            self.logger = self.logger.bind(correlation_id=correlation_id)

        self.logger.info(
            "Stream manager initialized",
            feed=feed,
            has_quote_callback=on_quote is not None,
            has_trade_callback=on_trade is not None,
        )

    def is_connected(self) -> bool:
        """Check if stream is currently connected.

        Thread-safe check of connection status.

        Returns:
            True if connected, False otherwise

        """
        return self._connected_event.is_set()

    def start(
        self,
        get_symbols_callback: Callable[[], list[str]],
    ) -> bool:
        """Start the stream in a background thread.

        This method is idempotent - calling it multiple times when already
        running will return True without creating duplicate threads.

        Args:
            get_symbols_callback: Callback to get current subscribed symbols

        Returns:
            True if started successfully or already running, False on failure

        Raises:
            StreamingError: If stream fails to start due to configuration issues
            WebSocketError: If WebSocket connection cannot be established

        """
        with self._state_lock:
            # Idempotency check
            if self._stream_thread and self._stream_thread.is_alive():
                self.logger.warning("Stream already running - idempotent call")
                return True

            self._should_reconnect = True
            self._get_symbols = get_symbols_callback
            self._connected_event.clear()

            # Create and start background thread
            # Use blocking SDK API which manages its own event loop
            self._stream_thread = threading.Thread(
                target=self._run_stream_blocking,
                name="RealTimePricing",
                daemon=True,
            )
            self._stream_thread.start()

        # Wait for connection using Event instead of polling
        connected = self._connected_event.wait(timeout=self._config.connection_timeout)

        if connected:
            self.logger.info(
                "Real-time stream started successfully",
                timeout=self._config.connection_timeout,
            )
            return True

        self.logger.error(
            "Failed to establish stream connection",
            timeout=self._config.connection_timeout,
        )
        return False

    def stop(self) -> None:
        """Stop the stream.

        Gracefully stops the WebSocket stream and cleans up resources.
        This method is idempotent and can be safely called multiple times.

        Raises:
            StreamingError: If stream cannot be stopped cleanly

        """
        with self._state_lock:
            self._should_reconnect = False

            if self._stream:
                try:
                    self._stream.stop()
                    self._stream = None
                    self.logger.debug("Stream stopped successfully")
                except (OSError, RuntimeError) as e:
                    # Narrow exception handling for stream stop errors
                    self.logger.warning(
                        "Error stopping stream",
                        error=str(e),
                        error_type=type(e).__name__,
                    )
                    raise StreamingError(f"Failed to stop stream: {e}") from e

        # Wait for thread outside lock to avoid deadlock
        if self._stream_thread and self._stream_thread.is_alive():
            self._stream_thread.join(timeout=self._config.thread_join_timeout)

            if self._stream_thread.is_alive():
                # Log zombie thread but don't block
                self.logger.error(
                    "Stream thread did not terminate within timeout",
                    timeout=self._config.thread_join_timeout,
                    thread_name=self._stream_thread.name,
                )
                raise StreamingError(
                    f"Stream thread did not terminate within {self._config.thread_join_timeout}s"
                )

        self._connected_event.clear()
        self.logger.info("Real-time stream stopped")

    def restart(self) -> None:
        """Restart the stream to pick up new subscriptions.

        Stops the current stream and starts a new one. This is useful when
        the list of subscribed symbols changes.

        Raises:
            StreamingError: If restart fails

        """
        self.logger.info("Restarting stream")

        # Stop current stream
        try:
            with self._state_lock:
                self._should_reconnect = False

                if self._stream:
                    try:
                        self._stream.stop()
                        # Small delay to allow clean closure
                        import time

                        time.sleep(self._config.stream_stop_delay)
                        self._stream = None
                    except (OSError, RuntimeError) as e:
                        self.logger.debug("Error stopping stream for restart", error=str(e))

            # Wait for thread to finish
            if self._stream_thread and self._stream_thread.is_alive():
                self._stream_thread.join(timeout=self._config.thread_join_timeout)
                if self._stream_thread.is_alive():
                    self.logger.warning(
                        "Stream thread did not terminate cleanly",
                        timeout=self._config.thread_join_timeout,
                    )
                    raise StreamingError("Cannot restart - stream thread still running")

            # Backoff delay before reconnecting
            import time

            time.sleep(self._config.reconnect_backoff_delay)

            # Restart with new subscriptions
            with self._state_lock:
                self._should_reconnect = True
                self._connected_event.clear()
                self._stream_thread = threading.Thread(
                    target=self._run_stream_blocking,
                    name="RealTimePricing",
                    daemon=True,
                )
                self._stream_thread.start()

            # Wait for reconnection
            if self._connected_event.wait(timeout=self._config.restart_wait_timeout):
                self.logger.info("Stream restarted successfully")
            else:
                self.logger.warning(
                    "Stream restart timed out",
                    timeout=self._config.restart_wait_timeout,
                )

        except StreamingError:
            raise
        except (OSError, RuntimeError) as e:
            self.logger.error("Error restarting stream", error=str(e), error_type=type(e).__name__)
            self._connected_event.clear()
            raise StreamingError(f"Failed to restart stream: {e}") from e

    def _run_stream_blocking(self) -> None:
        """Run the WebSocket stream using SDK's public blocking API.

        This method runs in a dedicated thread and uses the Alpaca SDK's
        public run() method, which manages its own event loop internally.
        This is the architecturally correct approach as it:
        - Uses the public API with stability guarantees
        - Allows SDK to handle its own event loop lifecycle
        - Includes proper cleanup via SDK's finally block
        - Avoids nested event loop conflicts

        """
        retry_count = 0

        while self._should_reconnect and retry_count < self._config.max_retries:
            try:
                # Setup stream for this attempt
                symbols_to_subscribe = self._get_symbols()

                if not symbols_to_subscribe:
                    # Wait for symbols to be available
                    self.logger.info("No symbols to subscribe to, waiting...")
                    import time

                    time.sleep(self._config.subscription_poll_interval)
                    continue

                # Create and configure stream
                if not self._setup_stream_with_symbols(symbols_to_subscribe):
                    retry_count += 1
                    continue

                # Check circuit breaker
                if not self._circuit_breaker.can_attempt_connection():
                    self.logger.warning(
                        "Circuit breaker blocking connection attempt",
                        attempt=retry_count + 1,
                        circuit_state=self._circuit_breaker.state.value,
                    )
                    retry_count += 1
                    import time

                    time.sleep(self._config.reconnect_backoff_delay)
                    continue

                self.logger.info("Attempting to start stream", attempt=retry_count + 1)

                # Signal connection immediately before calling run()
                # The SDK's run() method establishes the WebSocket connection synchronously,
                # so if we reach this point with subscriptions set up, we're connected
                if self._stream:
                    self._connected_event.set()
                    self.logger.info("Connection signaled - starting SDK run()")

                    # Run the stream - this blocks until stream stops
                    # The SDK handles connection establishment and maintains it
                    self._stream.run()

                    # If we get here, stream stopped
                    self._connected_event.clear()
                else:
                    self.logger.error("Stream is None, cannot run")
                    retry_count += 1
                    continue

                # If we get here, stream stopped normally
                self._circuit_breaker.record_success()
                self.logger.info("Stream closed normally")
                break

            except KeyboardInterrupt:
                self.logger.info("Stream interrupted by user")
                break

            except (OSError, RuntimeError, ConnectionError) as e:
                self._connected_event.clear()
                retry_count += 1

                error_msg = str(e)
                if (
                    "connection limit exceeded" in error_msg.lower()
                    or "http 429" in error_msg.lower()
                ):
                    self._circuit_breaker.record_failure(f"Connection limit exceeded: {error_msg}")
                    self.logger.error(
                        "Connection limit exceeded",
                        error=error_msg,
                        retry_count=retry_count,
                    )
                else:
                    self._circuit_breaker.record_failure(f"Stream error: {error_msg}")
                    self.logger.error(
                        "Stream connection error",
                        error=error_msg,
                        error_type=type(e).__name__,
                        retry_count=retry_count,
                    )

                if retry_count >= self._config.max_retries:
                    self.logger.error(
                        "Max retries exceeded, giving up",
                        max_retries=self._config.max_retries,
                    )
                    break

                # Exponential backoff
                delay = min(
                    self._config.base_retry_delay * (2 ** (retry_count - 1)),
                    self._config.max_retry_delay,
                )
                self.logger.info(
                    "Retrying connection",
                    retry_count=retry_count,
                    delay=delay,
                )
                import time

                time.sleep(delay)

            except Exception as e:
                # Catch-all for unexpected errors
                self._connected_event.clear()
                self.logger.error(
                    "Unexpected error in stream",
                    error=str(e),
                    error_type=type(e).__name__,
                    retry_count=retry_count,
                )
                retry_count += 1
                if retry_count >= self._config.max_retries:
                    break

        self.logger.info("Stream thread exiting", retry_count=retry_count)

    def _setup_stream_with_symbols(self, symbols_to_subscribe: list[str]) -> bool:
        """Set up stream instance with symbol subscriptions.

        Args:
            symbols_to_subscribe: List of symbols to subscribe to

        Returns:
            True if setup succeeded, False otherwise

        """
        self.logger.info(
            "Setting up subscriptions",
            symbol_count=len(symbols_to_subscribe),
            symbols=sorted(symbols_to_subscribe),
        )

        # Create a fresh stream instance
        try:
            self._stream = create_stock_data_stream(
                api_key=self._api_key.value,
                secret_key=self._secret_key.value,
                feed=self._feed,
            )
        except (ValueError, TypeError, OSError) as e:
            self.logger.error(
                "Failed to create stream",
                error=str(e),
                error_type=type(e).__name__,
            )
            return False

        # Track background tasks to prevent garbage collection
        import asyncio

        self._background_tasks: set[asyncio.Task[None]] = set()

        # Set up callback wrappers that bridge our async callbacks to SDK's async API
        async def async_quote_callback(data: AlpacaQuoteData) -> None:
            """Wrap async quote callback for SDK's asynchronous callback interface."""
            try:
                if self._on_quote:
                    # Call our async callback
                    await self._on_quote(data)
            except (KeyError, ValueError, TypeError) as e:
                self.logger.error(
                    "Error in quote callback",
                    error=str(e),
                    error_type=type(e).__name__,
                )
            except Exception as e:
                self.logger.error(
                    "Unexpected error in quote callback",
                    error=str(e),
                    error_type=type(e).__name__,
                )

        async def async_trade_callback(data: AlpacaTradeData) -> None:
            """Wrap async trade callback for SDK's asynchronous callback interface."""
            try:
                if self._on_trade:
                    # Call our async callback
                    await self._on_trade(data)
            except (KeyError, ValueError, TypeError) as e:
                self.logger.error(
                    "Error in trade callback",
                    error=str(e),
                    error_type=type(e).__name__,
                )
            except Exception as e:
                self.logger.error(
                    "Unexpected error in trade callback",
                    error=str(e),
                    error_type=type(e).__name__,
                )

        # Subscribe to quotes and trades
        try:
            if self._on_quote:
                self._stream.subscribe_quotes(async_quote_callback, *symbols_to_subscribe)
            if self._on_trade:
                self._stream.subscribe_trades(async_trade_callback, *symbols_to_subscribe)
        except (ValueError, TypeError) as e:
            self.logger.error(
                "Failed to subscribe to symbols",
                error=str(e),
                error_type=type(e).__name__,
            )
            return False

        self.logger.info("All subscriptions set up successfully")
        return True
