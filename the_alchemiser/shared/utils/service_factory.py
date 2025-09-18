"""Business Unit: shared | Status: current.

Service factory using dependency injection.
"""

from __future__ import annotations

from typing import Protocol

from the_alchemiser.shared.config.container import (
    ApplicationContainer,
)


class ExecutionManagerProtocol(Protocol):
    """Protocol for execution manager to avoid direct imports."""

    def execute_orders(self, orders: list[dict[str, str | int | bool | None]]) -> dict[str, str | int | bool | None]:  # type: ignore[misc]
        """Execute orders - implementation in execution_v2 module."""
        ...


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
    ) -> ExecutionManagerProtocol:
        """Create ExecutionManager using DI or traditional method."""
        if cls._container is not None and all(x is None for x in [api_key, secret_key, paper]):
            # Use DI container - get ExecutionManager from services
            # The provider returns Any due to dependency injector limitation
            return cls._container.services.execution_manager()  # type: ignore[no-any-return]

        # Direct instantiation for backward compatibility
        # TODO: Replace with proper factory method from execution_v2
        # This is a temporary placeholder - actual implementation should be in execution_v2
        raise NotImplementedError(
            "ExecutionManager creation should be handled by orchestration layer, "
            "not by shared service factory. This violates module boundaries."
        )

    @classmethod
    def get_container(cls) -> ApplicationContainer | None:
        """Get the current DI container."""
        return cls._container
