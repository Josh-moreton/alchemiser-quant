"""Business Unit: utilities; Status: current.

Service factory using dependency injection.
"""

from __future__ import annotations

from typing import cast

from the_alchemiser.infrastructure.dependency_injection.application_container import (
    ApplicationContainer,
)
from the_alchemiser.application.trading.service_manager import TradingServiceManager


class ServiceFactory:
    """Factory for creating services using dependency injection."""

    _container: ApplicationContainer | None = None

    @classmethod
    def initialize(cls, container: ApplicationContainer | None = None) -> None:
        """Initialize factory with DI container."""
        if container is None:
            container = ApplicationContainer()
        cls._container = container

    @classmethod
    def create_trading_service_manager(
        cls,
        api_key: str | None = None,
        secret_key: str | None = None,
        paper: bool | None = None,
    ) -> TradingServiceManager:
        """Create TradingServiceManager using DI or traditional method."""
        if cls._container is not None and all(x is None for x in [api_key, secret_key, paper]):
            # Use DI container
            return cast(TradingServiceManager, cls._container.services.trading_service_manager())
        # Backward compatibility: direct instantiation
        api_key = api_key or "default_key"
        secret_key = secret_key or "default_secret"
        paper = paper if paper is not None else True
        return TradingServiceManager(api_key, secret_key, paper)

    @classmethod
    def get_container(cls) -> ApplicationContainer | None:
        """Get the current DI container."""
        return cls._container
