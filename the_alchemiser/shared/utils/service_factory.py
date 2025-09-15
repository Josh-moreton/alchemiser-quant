"""Business Unit: shared | Status: current.

Service factory using dependency injection.
"""

from __future__ import annotations

from the_alchemiser.execution_v2.core.execution_manager import ExecutionManager
from the_alchemiser.shared.config.container import (
    ApplicationContainer,
)


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
    def create_execution_manager(
        cls,
        api_key: str | None = None,
        secret_key: str | None = None,
        *,
        paper: bool | None = None,
    ) -> ExecutionManager:
        """Create ExecutionManager using DI or traditional method."""
        if cls._container is not None and all(
            x is None for x in [api_key, secret_key, paper]
        ):
            # Use DI container - get ExecutionManager from services
            # The provider returns Any due to dependency injector limitation
            return cls._container.services.execution_manager()  # type: ignore[no-any-return]

        # Direct instantiation for backward compatibility
        api_key = api_key or "default_key"
        secret_key = secret_key or "default_secret"
        paper = paper if paper is not None else True
        return ExecutionManager.create_with_config(api_key, secret_key, paper=paper)

    @classmethod
    def get_container(cls) -> ApplicationContainer | None:
        """Get the current DI container."""
        return cls._container
