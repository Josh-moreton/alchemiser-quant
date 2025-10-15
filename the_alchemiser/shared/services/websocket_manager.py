"""Business Unit: shared | Status: current.

WebSocket Connection Manager for Alpaca Trading.

Centralizes ALL WebSocket connections to prevent connection limit exceeded errors
by ensuring only one connection of each type exists per credentials.
Manages both StockDataStream (pricing) and TradingStream (order updates).

Thread Safety:
    All public methods are thread-safe. Uses locks to protect shared state.
    Singleton pattern ensures one instance per credential set.
"""

from __future__ import annotations

import hashlib
import threading
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any, ClassVar

from alpaca.trading.stream import TradingStream

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.services.real_time_pricing import RealTimePricingService

if TYPE_CHECKING:
    pass

# Module-level PBKDF2 salt for hashing credential keys (do not treat as secret, but do not change in production environments)
_CREDENTIAL_HASH_SALT = b"WebSocketManagerPBKDF2Salt001"  # You may derive this from a config/env var for extra safety.
logger = get_logger(__name__)


class WebSocketConnectionManager:
    """Singleton manager for ALL Alpaca WebSocket connections.

    Ensures only one connection of each type exists per set of credentials,
    preventing connection limit exceeded errors. Manages both:
    - StockDataStream (for real-time pricing data)
    - TradingStream (for order updates)

    Thread Safety:
        All operations are protected by locks. Singleton pattern ensures
        one instance per credential set. Uses threading.Event for cleanup
        synchronization to avoid busy-wait polling.

    Raises:
        WebSocketError: When WebSocket connections fail to start or encounter errors
        ValueError: When invalid credentials are provided

    """

    _instances: ClassVar[dict[str, WebSocketConnectionManager]] = {}
    _lock: ClassVar[threading.Lock] = threading.Lock()
    _cleanup_event: ClassVar[threading.Event] = threading.Event()
    _cleanup_in_progress: ClassVar[bool] = False

    @staticmethod
    def _hash_credentials(api_key: str, secret_key: str, *, paper_trading: bool) -> str:
        """Hash credentials for secure storage in dictionary keys.

        Args:
            api_key: API key (will be hashed)
            secret_key: Secret key (will be hashed)
            paper_trading: Paper trading flag

        Returns:
            SHA-256 hash of credentials

        """
        credentials_str = f"{api_key}:{secret_key}:{paper_trading}"
        # Use PBKDF2 for computationally expensive hashing of credential keys
        hash_bytes = hashlib.pbkdf2_hmac(
            "sha256",
            credentials_str.encode(),
            _CREDENTIAL_HASH_SALT,
            100_000,  # Recommended minimum iterations
        )
        return hash_bytes.hex()

    def __new__(
        cls, api_key: str, secret_key: str, *, paper_trading: bool = True
    ) -> WebSocketConnectionManager:
        """Create or return existing instance for the given credentials.

        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key
            paper_trading: Whether to use paper trading (default: True)

        Returns:
            Singleton instance for the credential set

        Note:
            Credentials are hashed before being used as dictionary keys
            for security. The cleanup event is used instead of busy-wait
            polling for better performance and responsiveness.

        """
        credentials_key = cls._hash_credentials(api_key, secret_key, paper_trading=paper_trading)

        with cls._lock:
            # Wait for cleanup to complete using Event (non-busy wait)
            if cls._cleanup_in_progress:
                cls._cleanup_event.clear()
            # Release lock while waiting
            if cls._cleanup_in_progress:
                cls._lock.release()
                cls._cleanup_event.wait(timeout=5.0)
                cls._lock.acquire()

            if credentials_key not in cls._instances:
                instance = super().__new__(cls)
                cls._instances[credentials_key] = instance
                instance._initialized = False
                instance._credentials_hash = credentials_key
            return cls._instances[credentials_key]

    def __init__(self, api_key: str, secret_key: str, *, paper_trading: bool = True) -> None:
        """Initialize the connection manager (only once per credentials).

        Args:
            api_key: Alpaca API key (stored internally, not logged)
            secret_key: Alpaca secret key (stored internally, not logged)
            paper_trading: Whether to use paper trading

        Note:
            Credentials are stored for SDK usage but never logged.
            Only credential hashes are used for identification.

        """
        if hasattr(self, "_initialized") and self._initialized:
            return

        # Store credentials securely (not logged) - hash is set in __new__
        self._api_key = api_key
        self._secret_key = secret_key
        self._paper_trading = paper_trading
        self._credentials_hash: str  # Set in __new__, type annotation for mypy

        # Pricing service (StockDataStream)
        self._pricing_service: RealTimePricingService | None = None
        self._pricing_ref_count = 0

        # Trading service (TradingStream)
        self._trading_stream: TradingStream | None = None
        self._trading_stream_thread: threading.Thread | None = None
        self._trading_ws_connected: bool = False
        self._trading_callback: Callable[[Any], Awaitable[None]] | None = None
        self._trading_ref_count = 0

        # Shared locks
        self._service_lock = threading.Lock()
        self._trading_lock = threading.Lock()
        self._initialized: bool = True

        logger.debug(
            "WebSocket connection manager initialized",
            mode="paper" if paper_trading else "live",
            credentials_hash=(
                self._credentials_hash[:8] if hasattr(self, "_credentials_hash") else "unknown"
            ),
        )

    def get_pricing_service(self, correlation_id: str | None = None) -> RealTimePricingService:
        """Get or create the shared pricing service.

        Args:
            correlation_id: Optional correlation ID for distributed tracing

        Returns:
            Shared RealTimePricingService instance

        Raises:
            WebSocketError: If the pricing service fails to start

        """
        with self._service_lock:
            if self._pricing_service is None:
                logger.info(
                    "Creating shared real-time pricing service (lazy connection)",
                    correlation_id=correlation_id,
                    credentials_hash=self._credentials_hash[:8],
                )
                self._pricing_service = RealTimePricingService(
                    api_key=self._api_key,
                    secret_key=self._secret_key,
                    paper_trading=self._paper_trading,
                    max_symbols=50,  # Increased limit for shared service
                    correlation_id=correlation_id,  # Propagate correlation ID for tracing
                )

                # DO NOT start the service here - let it start lazily when symbols are added
                # This avoids the "no symbols to subscribe to" timeout issue
                # The service will automatically start when first subscription is added
                logger.info(
                    "Shared real-time pricing service created (will connect on first subscription)",
                    correlation_id=correlation_id,
                )

            self._pricing_ref_count += 1
            logger.debug(
                "Pricing service reference count updated",
                ref_count=self._pricing_ref_count,
                correlation_id=correlation_id,
            )
            return self._pricing_service

    def release_pricing_service(self, correlation_id: str | None = None) -> None:
        """Release a reference to the pricing service.

        Stops the service when no more references exist.

        Note: This is synchronous to support cleanup from __del__ contexts.
        The service stop is handled synchronously - background task cleanup
        happens via daemon threads which will terminate naturally.

        Args:
            correlation_id: Optional correlation ID for distributed tracing

        """
        with self._service_lock:
            old_count = self._pricing_ref_count
            self._pricing_ref_count = max(0, self._pricing_ref_count - 1)

            # Warn if reference count went negative (indicates bug)
            if old_count < 1:
                logger.warning(
                    "Pricing service reference count was already 0 or negative",
                    old_count=old_count,
                    new_count=self._pricing_ref_count,
                    correlation_id=correlation_id,
                )

            logger.debug(
                "Pricing service reference count updated",
                ref_count=self._pricing_ref_count,
                correlation_id=correlation_id,
            )

            if self._pricing_ref_count == 0 and self._pricing_service is not None:
                logger.info(
                    "Stopping shared real-time pricing service (no more references)",
                    correlation_id=correlation_id,
                )
                # Stop synchronously - stream threads are daemon threads
                # and will terminate naturally without awaiting async cleanup
                if self._pricing_service._stream_manager:
                    self._pricing_service._stream_manager.stop()
                self._pricing_service._price_store.stop_cleanup()
                self._pricing_service = None

    def get_trading_service(
        self,
        callback: Callable[[Any], Awaitable[None]],
        correlation_id: str | None = None,
    ) -> bool:
        """Get or create the shared trading service for order updates.

        Args:
            callback: Async callback function for order updates
            correlation_id: Optional correlation ID for distributed tracing

        Returns:
            True if service is available, False if failed to start

        Raises:
            WebSocketError: If the trading service encounters critical errors

        """
        with self._trading_lock:
            if self._trading_stream is None or not self._trading_ws_connected:
                try:
                    logger.info(
                        "Creating shared TradingStream service",
                        correlation_id=correlation_id,
                        credentials_hash=self._credentials_hash[:8],
                    )
                    self._trading_stream = TradingStream(
                        self._api_key, self._secret_key, paper=self._paper_trading
                    )
                    self._trading_callback = callback
                    self._trading_stream.subscribe_trade_updates(callback)

                    # Extract runner to module level for better testability
                    def _runner() -> None:
                        try:
                            # Check stream validity inside the try block to handle concurrent nullification
                            with self._trading_lock:
                                if self._trading_stream is None:
                                    return
                                ts = self._trading_stream

                            if ts is not None:
                                ts.run()
                        except Exception as exc:
                            logger.error(
                                "TradingStream terminated",
                                error=str(exc),
                                error_type=type(exc).__name__,
                                correlation_id=correlation_id,
                            )
                        finally:
                            with self._trading_lock:
                                self._trading_ws_connected = False

                    self._trading_ws_connected = True
                    self._trading_stream_thread = threading.Thread(
                        target=_runner, name="SharedTradingWS", daemon=True
                    )
                    self._trading_stream_thread.start()
                    logger.info(
                        "Shared TradingStream started successfully",
                        correlation_id=correlation_id,
                    )

                except Exception as exc:
                    logger.error(
                        "Failed to start shared TradingStream",
                        error=str(exc),
                        error_type=type(exc).__name__,
                        operation="start",
                        correlation_id=correlation_id,
                    )
                    self._trading_ws_connected = False
                    return False

            self._trading_ref_count += 1
            logger.debug(
                "Trading service reference count updated",
                ref_count=self._trading_ref_count,
                correlation_id=correlation_id,
            )
            return self._trading_ws_connected

    def release_trading_service(self, correlation_id: str | None = None) -> None:
        """Release a reference to the trading service.

        Stops the service when no more references exist with timeout protection.

        Args:
            correlation_id: Optional correlation ID for distributed tracing

        """
        with self._trading_lock:
            old_count = self._trading_ref_count
            self._trading_ref_count = max(0, self._trading_ref_count - 1)

            # Warn if reference count went negative (indicates bug)
            if old_count < 1:
                logger.warning(
                    "Trading service reference count was already 0 or negative",
                    old_count=old_count,
                    new_count=self._trading_ref_count,
                    correlation_id=correlation_id,
                )

            logger.debug(
                "Trading service reference count updated",
                ref_count=self._trading_ref_count,
                correlation_id=correlation_id,
            )

            if self._trading_ref_count == 0 and self._trading_stream is not None:
                logger.info(
                    "Stopping shared TradingStream (no more references)",
                    correlation_id=correlation_id,
                )
                try:
                    # Set to None BEFORE calling stop() to prevent race conditions
                    stream = self._trading_stream
                    self._trading_stream = None
                    self._trading_ws_connected = False

                    if stream:
                        # Use timer for timeout protection
                        stop_complete = threading.Event()

                        def _stop_with_timeout(
                            s: TradingStream = stream,
                            evt: threading.Event = stop_complete,
                        ) -> None:
                            try:
                                s.stop()
                            finally:
                                evt.set()

                        stop_thread = threading.Thread(target=_stop_with_timeout, daemon=True)
                        stop_thread.start()

                        # Wait with timeout
                        if not stop_complete.wait(timeout=5.0):
                            logger.warning(
                                "TradingStream stop() timed out after 5 seconds",
                                correlation_id=correlation_id,
                            )
                except Exception as e:
                    logger.error(
                        "Error stopping TradingStream",
                        error=str(e),
                        error_type=type(e).__name__,
                        operation="stop",
                        correlation_id=correlation_id,
                    )
                finally:
                    self._trading_callback = None

    def is_service_available(self) -> bool:
        """Check if the pricing service is available and connected."""
        with self._service_lock:
            return self._pricing_service is not None and self._pricing_service.is_connected()

    def is_trading_service_available(self) -> bool:
        """Check if the trading service is available and connected."""
        with self._trading_lock:
            return self._trading_stream is not None and self._trading_ws_connected

    def get_service_stats(self) -> dict[str, Any]:
        """Get statistics from both pricing and trading services."""
        stats: dict[str, Any] = {}

        # Pricing service stats
        with self._service_lock:
            if self._pricing_service is None:
                stats["pricing"] = {
                    "status": "not_initialized",
                    "ref_count": self._pricing_ref_count,
                }
            else:
                pricing_stats = self._pricing_service.get_stats()
                pricing_stats["ref_count"] = self._pricing_ref_count
                stats["pricing"] = pricing_stats

        # Trading service stats
        with self._trading_lock:
            stats["trading"] = {
                "status": "connected" if self._trading_ws_connected else "disconnected",
                "ref_count": self._trading_ref_count,
                "stream_active": self._trading_stream is not None,
            }

        return stats

    @classmethod
    def get_connection_health(cls) -> dict[str, Any]:
        """Get health status of all connection managers.

        Returns:
            Health information with credential hashes redacted for security

        Note:
            Instance keys are hashed credentials, not raw credentials

        """
        with cls._lock:
            health_info: dict[str, Any] = {
                "total_instances": len(cls._instances),
                "cleanup_in_progress": cls._cleanup_in_progress,
                "instances": {},
            }

            for key, instance in cls._instances.items():
                try:
                    stats = instance.get_service_stats()
                    # Use hash prefix instead of full key for security
                    safe_key = key[:8] + "..." if len(key) > 8 else key
                    health_info["instances"][safe_key] = {
                        "pricing_status": stats.get("pricing", {}).get("status", "unknown"),
                        "pricing_ref_count": stats.get("pricing", {}).get("ref_count", 0),
                        "pricing_connected": instance.is_service_available(),
                        "trading_status": stats.get("trading", {}).get("status", "unknown"),
                        "trading_ref_count": stats.get("trading", {}).get("ref_count", 0),
                        "trading_connected": instance.is_trading_service_available(),
                    }
                except Exception as e:
                    safe_key = key[:8] + "..." if len(key) > 8 else key
                    health_info["instances"][safe_key] = {
                        "status": "error",
                        "error": str(e),
                        "error_type": type(e).__name__,
                    }

            return health_info

    @classmethod
    def cleanup_all_instances(cls, correlation_id: str | None = None) -> None:
        """Clean up all connection manager instances.

        Args:
            correlation_id: Optional correlation ID for distributed tracing

        Note:
            Uses Event-based synchronization instead of busy-wait polling

        """
        with cls._lock:
            cls._cleanup_in_progress = True
            cls._cleanup_event.clear()
            try:
                # Create a copy of instances to avoid dictionary modification during iteration
                instances_to_cleanup = list(cls._instances.values())

                for instance in instances_to_cleanup:
                    try:
                        # Clean up pricing service
                        if hasattr(instance, "_pricing_service") and instance._pricing_service:
                            instance._pricing_service.stop()  # type: ignore[unused-coroutine]

                        # Clean up trading service with timeout
                        if hasattr(instance, "_trading_stream") and instance._trading_stream:
                            logger.info(
                                "Stopping TradingStream for cleanup",
                                correlation_id=correlation_id,
                                credentials_hash=instance._credentials_hash[:8],
                            )

                            stream = instance._trading_stream
                            instance._trading_stream = None
                            instance._trading_ws_connected = False

                            # Stop with timeout protection
                            stop_complete = threading.Event()

                            def _stop_with_timeout(
                                s: TradingStream = stream,
                                evt: threading.Event = stop_complete,
                            ) -> None:
                                try:
                                    s.stop()
                                finally:
                                    evt.set()

                            stop_thread = threading.Thread(target=_stop_with_timeout, daemon=True)
                            stop_thread.start()

                            if not stop_complete.wait(timeout=5.0):
                                logger.warning(
                                    "TradingStream cleanup timed out",
                                    correlation_id=correlation_id,
                                )

                    except Exception as e:
                        logger.error(
                            "Error cleaning up connection manager",
                            error=str(e),
                            error_type=type(e).__name__,
                            operation="cleanup",
                            correlation_id=correlation_id,
                        )

                cls._instances.clear()
                logger.info(
                    "All WebSocket connection managers cleaned up",
                    correlation_id=correlation_id,
                )
            finally:
                cls._cleanup_in_progress = False
                cls._cleanup_event.set()  # Signal that cleanup is complete
