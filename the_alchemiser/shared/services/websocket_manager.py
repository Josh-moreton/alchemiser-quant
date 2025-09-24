"""Business Unit: shared | Status: current.

WebSocket Connection Manager for Alpaca Trading.

Centralizes WebSocket connections to prevent connection limit exceeded errors
by ensuring only one data stream connection exists per credentials.
"""

import logging
import threading
import time
from typing import Any, ClassVar

from the_alchemiser.shared.services.real_time_pricing import RealTimePricingService

logger = logging.getLogger(__name__)


class WebSocketConnectionManager:
    """Singleton manager for Alpaca WebSocket connections.

    Ensures only one data stream connection exists per set of credentials,
    preventing connection limit exceeded errors.
    """

    _instances: ClassVar[dict[str, "WebSocketConnectionManager"]] = {}
    _lock: ClassVar[threading.Lock] = threading.Lock()
    _cleanup_in_progress: ClassVar[bool] = False

    def __new__(
        cls, api_key: str, secret_key: str, *, paper_trading: bool = True
    ) -> "WebSocketConnectionManager":
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
        self._pricing_service: RealTimePricingService | None = None
        self._service_lock = threading.Lock()
        self._ref_count = 0
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

            self._ref_count += 1
            logger.debug(f"📊 Pricing service reference count: {self._ref_count}")
            return self._pricing_service

    def release_pricing_service(self) -> None:
        """Release a reference to the pricing service.

        Stops the service when no more references exist.
        """
        with self._service_lock:
            self._ref_count = max(0, self._ref_count - 1)
            logger.debug(f"📊 Pricing service reference count: {self._ref_count}")

            if self._ref_count == 0 and self._pricing_service is not None:
                logger.info("📡 Stopping shared real-time pricing service (no more references)")
                self._pricing_service.stop()
                self._pricing_service = None

    def is_service_available(self) -> bool:
        """Check if the pricing service is available and connected."""
        with self._service_lock:
            return self._pricing_service is not None and self._pricing_service.is_connected()

    def get_service_stats(self) -> dict[str, Any]:
        """Get statistics from the pricing service."""
        with self._service_lock:
            if self._pricing_service is None:
                return {"status": "not_initialized", "ref_count": self._ref_count}

            stats = self._pricing_service.get_stats()
            stats["ref_count"] = self._ref_count
            return stats
    
    @classmethod
    def get_connection_health(cls) -> dict[str, Any]:
        """Get health status of all connection managers."""
        with cls._lock:
            health_info = {
                "total_instances": len(cls._instances),
                "cleanup_in_progress": cls._cleanup_in_progress,
                "instances": {}
            }
            
            for key, instance in cls._instances.items():
                try:
                    stats = instance.get_service_stats()
                    health_info["instances"][key] = {
                        "status": stats.get("status", "unknown"),
                        "ref_count": stats.get("ref_count", 0),
                        "connected": instance.is_service_available()
                    }
                except Exception as e:
                    health_info["instances"][key] = {
                        "status": "error",
                        "error": str(e)
                    }
            
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
                        if hasattr(instance, '_pricing_service') and instance._pricing_service:
                            instance._pricing_service.stop()
                    except Exception as e:
                        logger.error(f"Error cleaning up connection manager: {e}")
                
                cls._instances.clear()
                logger.info("📡 All WebSocket connection managers cleaned up")
            finally:
                cls._cleanup_in_progress = False
