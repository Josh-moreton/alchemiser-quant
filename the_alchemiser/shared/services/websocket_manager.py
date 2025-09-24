"""Business Unit: shared | Status: current.

WebSocket Connection Manager for Alpaca Trading.

Centralizes ALL WebSocket connections to prevent connection limit exceeded errors
by ensuring only one connection of each type exists per credentials.
Manages both StockDataStream (pricing) and TradingStream (order updates).
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any, ClassVar

from the_alchemiser.shared.services.real_time_pricing import RealTimePricingService

if TYPE_CHECKING:
    from alpaca.trading.stream import TradingStream

logger = logging.getLogger(__name__)


class WebSocketConnectionManager:
    """Singleton manager for ALL Alpaca WebSocket connections.

    Ensures only one connection of each type exists per set of credentials,
    preventing connection limit exceeded errors. Manages both:
    - StockDataStream (for real-time pricing data)
    - TradingStream (for order updates)
    """

    _instances: ClassVar[dict[str, WebSocketConnectionManager]] = {}
    _lock: ClassVar[threading.Lock] = threading.Lock()
    _cleanup_in_progress: ClassVar[bool] = False

    def __new__(
        cls, api_key: str, secret_key: str, *, paper_trading: bool = True
    ) -> WebSocketConnectionManager:
        """Create or return existing instance for the given credentials."""
        credentials_key = f"{api_key}:{secret_key}:{paper_trading}"

        with cls._lock:
            # Wait for any cleanup to complete
            while cls._cleanup_in_progress:
                time.sleep(0.001)  # Brief wait for cleanup to finish

            if credentials_key not in cls._instances:
                instance = super().__new__(cls)
                cls._instances[credentials_key] = instance
                instance._initialized = False
            return cls._instances[credentials_key]

    def __init__(self, api_key: str, secret_key: str, *, paper_trading: bool = True) -> None:
        """Initialize the connection manager (only once per credentials)."""
        if hasattr(self, "_initialized") and self._initialized:
            return

        self.api_key = api_key
        self.secret_key = secret_key
        self.paper_trading = paper_trading

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

        logger.info(
            f"📡 WebSocket connection manager initialized ({'paper' if paper_trading else 'live'})"
        )

    def get_pricing_service(self) -> RealTimePricingService:
        """Get or create the shared pricing service.

        Returns:
            Shared RealTimePricingService instance

        """
        with self._service_lock:
            if self._pricing_service is None:
                logger.info("📡 Creating shared real-time pricing service")
                self._pricing_service = RealTimePricingService(
                    api_key=self.api_key,
                    secret_key=self.secret_key,
                    paper_trading=self.paper_trading,
                    max_symbols=50,  # Increased limit for shared service
                )

                # Start the service
                if not self._pricing_service.start():
                    logger.error("❌ Failed to start shared real-time pricing service")
                    raise RuntimeError("Failed to start real-time pricing service")

                logger.info("✅ Shared real-time pricing service started successfully")

            self._pricing_ref_count += 1
            logger.debug(f"📊 Pricing service reference count: {self._pricing_ref_count}")
            return self._pricing_service

    def release_pricing_service(self) -> None:
        """Release a reference to the pricing service.

        Stops the service when no more references exist.
        """
        with self._service_lock:
            self._pricing_ref_count = max(0, self._pricing_ref_count - 1)
            logger.debug(f"📊 Pricing service reference count: {self._pricing_ref_count}")

            if self._pricing_ref_count == 0 and self._pricing_service is not None:
                logger.info("📡 Stopping shared real-time pricing service (no more references)")
                self._pricing_service.stop()
                self._pricing_service = None

    def get_trading_service(self, callback: Callable[[Any], Awaitable[None]]) -> bool:
        """Get or create the shared trading service for order updates.

        Args:
            callback: Async callback function for order updates

        Returns:
            True if service is available, False if failed to start

        """
        with self._trading_lock:
            if self._trading_stream is None or not self._trading_ws_connected:
                try:
                    from alpaca.trading.stream import TradingStream

                    logger.info("📡 Creating shared TradingStream service")
                    self._trading_stream = TradingStream(
                        self.api_key, self.secret_key, paper=self.paper_trading
                    )
                    self._trading_callback = callback
                    self._trading_stream.subscribe_trade_updates(callback)

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
                            logger.error(f"TradingStream terminated: {exc}")
                        finally:
                            with self._trading_lock:
                                self._trading_ws_connected = False

                    self._trading_ws_connected = True
                    self._trading_stream_thread = threading.Thread(
                        target=_runner, name="SharedTradingWS", daemon=True
                    )
                    self._trading_stream_thread.start()
                    logger.info("✅ Shared TradingStream started successfully")

                except Exception as exc:
                    logger.error(f"Failed to start shared TradingStream: {exc}")
                    self._trading_ws_connected = False
                    return False

            self._trading_ref_count += 1
            logger.debug(f"📊 Trading service reference count: {self._trading_ref_count}")
            return self._trading_ws_connected

    def release_trading_service(self) -> None:
        """Release a reference to the trading service.

        Stops the service when no more references exist.
        """
        with self._trading_lock:
            self._trading_ref_count = max(0, self._trading_ref_count - 1)
            logger.debug(f"📊 Trading service reference count: {self._trading_ref_count}")

            if self._trading_ref_count == 0 and self._trading_stream is not None:
                logger.info("📡 Stopping shared TradingStream (no more references)")
                try:
                    # Set to None BEFORE calling stop() to prevent race conditions
                    stream = self._trading_stream
                    self._trading_stream = None
                    self._trading_ws_connected = False

                    if stream:
                        stream.stop()
                except Exception as e:
                    logger.error(f"Error stopping TradingStream: {e}")
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
        """Get health status of all connection managers."""
        with cls._lock:
            health_info: dict[str, Any] = {
                "total_instances": len(cls._instances),
                "cleanup_in_progress": cls._cleanup_in_progress,
                "instances": {},
            }

            for key, instance in cls._instances.items():
                try:
                    stats = instance.get_service_stats()
                    health_info["instances"][key] = {
                        "pricing_status": stats.get("pricing", {}).get("status", "unknown"),
                        "pricing_ref_count": stats.get("pricing", {}).get("ref_count", 0),
                        "pricing_connected": instance.is_service_available(),
                        "trading_status": stats.get("trading", {}).get("status", "unknown"),
                        "trading_ref_count": stats.get("trading", {}).get("ref_count", 0),
                        "trading_connected": instance.is_trading_service_available(),
                    }
                except Exception as e:
                    health_info["instances"][key] = {"status": "error", "error": str(e)}

            return health_info

    @classmethod
    def cleanup_all_instances(cls) -> None:
        """Clean up all connection manager instances."""
        with cls._lock:
            cls._cleanup_in_progress = True
            try:
                # Create a copy of instances to avoid dictionary modification during iteration
                instances_to_cleanup = list(cls._instances.values())

                for instance in instances_to_cleanup:
                    try:
                        # Clean up pricing service
                        if hasattr(instance, "_pricing_service") and instance._pricing_service:
                            instance._pricing_service.stop()

                        # Clean up trading service
                        if hasattr(instance, "_trading_stream") and instance._trading_stream:
                            logger.info("Stopping TradingStream for cleanup")
                            instance._trading_stream.stop()
                            instance._trading_stream = None
                            instance._trading_ws_connected = False

                    except Exception as e:
                        logger.error(f"Error cleaning up connection manager: {e}")

                cls._instances.clear()
                logger.info("📡 All WebSocket connection managers cleaned up")
            finally:
                cls._cleanup_in_progress = False
