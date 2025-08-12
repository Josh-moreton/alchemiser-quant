"""Service factory using dependency injection."""

from typing import Optional

from the_alchemiser.container.application_container import ApplicationContainer
from the_alchemiser.services.enhanced.trading_service_manager import TradingServiceManager


class ServiceFactory:
    """Factory for creating services using dependency injection."""

    _container: Optional[ApplicationContainer] = None

    @classmethod
    def initialize(cls, container: Optional[ApplicationContainer] = None) -> None:
        """Initialize factory with DI container."""
        if container is None:
            container = ApplicationContainer()
        cls._container = container

    @classmethod
    def create_trading_service_manager(
        cls,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        paper: Optional[bool] = None,
    ) -> TradingServiceManager:
        """Create TradingServiceManager using DI or traditional method."""

        if cls._container is not None and all(x is None for x in [api_key, secret_key, paper]):
            # Use DI container
            return cls._container.services.trading_service_manager()
        else:
            # Backward compatibility: direct instantiation
            api_key = api_key or "default_key"
            secret_key = secret_key or "default_secret"
            paper = paper if paper is not None else True
            return TradingServiceManager(api_key, secret_key, paper)

    @classmethod
    def get_container(cls) -> Optional[ApplicationContainer]:
        """Get the current DI container."""
        return cls._container
