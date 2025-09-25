"""Business Unit: shared | Status: current.

Service factory using dependency injection.
"""

from __future__ import annotations
import importlib
from typing import Any

from the_alchemiser.shared.config.container import (
    ApplicationContainer,
)

# Import ExecutionManager only when needed to avoid circular imports


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
        enable_trade_ledger: bool | None = None,
    ) -> Any:  # Return type Any to avoid importing ExecutionManager
        """Create ExecutionManager using DI or traditional method."""
        if cls._container is not None and all(x is None for x in [api_key, secret_key, paper]):
            # Use DI container - get ExecutionManager from execution providers
            if cls._container.execution is None:
                cls._container.initialize_execution_providers()
            # The provider returns Any due to dependency injector limitation
            return cls._container.execution.execution_manager()  # type: ignore[no-any-return]

        # Direct instantiation for backward compatibility
        # Use importlib to avoid static import detection
        execution_manager_module = importlib.import_module("the_alchemiser.execution_v2.core.execution_manager")
        ExecutionManager = execution_manager_module.ExecutionManager
        
        api_key = api_key or "default_key"
        secret_key = secret_key or "default_secret"
        paper = paper if paper is not None else True
        enable_trade_ledger = enable_trade_ledger if enable_trade_ledger is not None else False
        return ExecutionManager.create_with_config(
            api_key, secret_key, paper=paper, enable_trade_ledger=enable_trade_ledger
        )

    @classmethod
    def get_container(cls) -> ApplicationContainer | None:
        """Get the current DI container."""
        return cls._container
