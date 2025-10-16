"""Business Unit: shared | Status: current.

Service factory using dependency injection.

This module provides a factory pattern for creating services with support for
both dependency injection (DI) and direct instantiation. It serves as the
primary entry point for service creation throughout the application.

Security: No secrets in code. Fail-closed on missing credentials.
Thread-safety: Not thread-safe. Initialize once during startup.
"""

from __future__ import annotations

import importlib
from typing import Protocol, cast

from the_alchemiser.shared.config.container import ApplicationContainer
from the_alchemiser.shared.errors import ConfigurationError
from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)

# Module path for dynamic import (to avoid circular dependencies)
_EXECUTION_MANAGER_MODULE = "the_alchemiser.execution_v2.core.execution_manager"


class ExecutionManagerProtocol(Protocol):
    """Subset of ExecutionManager interface required by ServiceFactory.

    Note: Protocol is intentionally minimal to avoid importing execution_v2
    types at module level and causing circular dependencies. The full interface
    is defined in the ExecutionManager class itself.

    This protocol is only used for type hints in the factory methods.
    """

    # Minimal protocol - no methods required for factory pattern
    # Full interface includes: execute_rebalance_plan, enable_smart_execution, etc.
    ...


ExecutionManagerType = ExecutionManagerProtocol


class ServiceFactory:
    """Factory for creating services using dependency injection.

    This factory provides a centralized way to create services with support
    for both DI container-based instantiation and direct instantiation for
    backward compatibility.

    Thread-safety: Not thread-safe. The _container class variable should be
    set once during application startup before any concurrent access.

    Example:
        >>> # Initialize with DI container
        >>> container = ApplicationContainer()
        >>> ServiceFactory.initialize(container)
        >>> manager = ServiceFactory.create_execution_manager()
        >>>
        >>> # Or use direct instantiation
        >>> manager = ServiceFactory.create_execution_manager(
        ...     api_key="key", secret_key="secret", paper=True
        ... )

    """

    _container: ApplicationContainer | None = None

    @classmethod
    def initialize(cls, container: ApplicationContainer | None = None) -> None:
        """Initialize factory with DI container.

        This method is idempotent - calling multiple times is safe but will
        replace any existing container reference. Should be called during
        application startup before any concurrent access.

        Args:
            container: DI container to use. If None, creates a new
                ApplicationContainer instance.

        Thread-safety: Not thread-safe. Call once during startup.

        Example:
            >>> container = ApplicationContainer()
            >>> ServiceFactory.initialize(container)

        """
        if container is None:
            logger.info("Creating new ApplicationContainer for ServiceFactory")
            try:
                container = ApplicationContainer.create_for_environment("development")
            except Exception as e:
                logger.error(
                    "Failed to create ApplicationContainer",
                    extra={"error": str(e), "error_type": type(e).__name__},
                )
                raise ConfigurationError(f"Failed to create ApplicationContainer: {e}") from e

        logger.info("ServiceFactory initialized with DI container")
        cls._container = container

    @classmethod
    def _validate_credentials(
        cls,
        api_key: str | None,
        secret_key: str | None,
    ) -> tuple[str | None, str | None]:
        """Validate and normalize credential parameters.

        Args:
            api_key: Alpaca API key to validate.
            secret_key: Alpaca secret key to validate.

        Returns:
            Tuple of normalized (api_key, secret_key), treating empty strings as None.

        Raises:
            TypeError: If credentials are not strings when provided.

        """
        # Validate string parameters if provided
        if api_key is not None and not isinstance(api_key, str):
            raise TypeError(f"api_key must be str, got {type(api_key).__name__}")
        if secret_key is not None and not isinstance(secret_key, str):
            raise TypeError(f"secret_key must be str, got {type(secret_key).__name__}")

        # Treat empty strings as None
        api_key = api_key if api_key else None
        secret_key = secret_key if secret_key else None

        return api_key, secret_key

    @classmethod
    def _create_via_di_container(cls) -> ExecutionManagerType:
        """Create ExecutionManager via DI container.

        Returns:
            ExecutionManagerType: Configured ExecutionManager instance from DI container.

        Raises:
            ConfigurationError: If container is None or execution_manager provider is None.

        """
        logger.debug("Initializing execution providers via DI container")

        # Type guard: we know _container is not None here due to use_di check
        container = cls._container
        if container is None:
            # Should never happen due to use_di logic, but satisfy type checker
            raise ConfigurationError("Container is None despite use_di check")

        execution_manager_provider = getattr(container, "execution_manager", None)
        if execution_manager_provider is None:
            raise ConfigurationError(
                "Failed to get execution_manager provider: "
                "execution_manager is None in container (wiring not called?)"
            )

        logger.info("Using DI container for ExecutionManager creation")
        # The provider returns Any due to dependency injector limitation
        return cast(ExecutionManagerType, execution_manager_provider())

    @classmethod
    def _create_via_direct_instantiation(
        cls,
        api_key: str,
        secret_key: str,
        *,
        paper: bool,
    ) -> ExecutionManagerType:
        """Create ExecutionManager via direct instantiation.

        Args:
            api_key: Alpaca API key (must be non-empty).
            secret_key: Alpaca secret key (must be non-empty).
            paper: Whether to use paper trading mode.

        Returns:
            ExecutionManagerType: Configured ExecutionManager instance.

        Raises:
            ConfigurationError: If module import fails or ExecutionManager class not found.

        """
        logger.debug("Using direct instantiation for ExecutionManager")

        # Use importlib to avoid static import detection (prevents circular imports)
        try:
            execution_manager_module = importlib.import_module(_EXECUTION_MANAGER_MODULE)
        except ImportError as e:
            logger.error(
                "Failed to import ExecutionManager module",
                extra={"module": _EXECUTION_MANAGER_MODULE, "error": str(e)},
            )
            raise ConfigurationError(
                f"Failed to import ExecutionManager module '{_EXECUTION_MANAGER_MODULE}': {e}"
            ) from e

        try:
            execution_manager = execution_manager_module.ExecutionManager
        except AttributeError as e:
            logger.error(
                "ExecutionManager class not found in module",
                extra={"module": _EXECUTION_MANAGER_MODULE, "error": str(e)},
            )
            raise ConfigurationError(
                f"ExecutionManager class not found in module '{_EXECUTION_MANAGER_MODULE}': {e}"
            ) from e

        logger.info(
            "Creating ExecutionManager via direct instantiation",
            extra={"paper_mode": paper},
        )

        return cast(
            ExecutionManagerType,
            execution_manager.create_with_config(
                api_key,
                secret_key,
                paper=paper,
            ),
        )

    @classmethod
    def create_execution_manager(
        cls,
        api_key: str | None = None,
        secret_key: str | None = None,
        *,
        paper: bool | None = None,
    ) -> ExecutionManagerType:
        """Create ExecutionManager using DI or traditional method.

        Creates an ExecutionManager instance either via the DI container
        (if initialized and no credentials provided) or via direct instantiation
        (if credentials are provided).

        Args:
            api_key: Alpaca API key. Required if not using DI container.
            secret_key: Alpaca secret key. Required if not using DI container.
            paper: Whether to use paper trading mode. Defaults to True if not
                specified. Only used for direct instantiation.

        Returns:
            ExecutionManagerType: Configured ExecutionManager instance.

        Raises:
            ConfigurationError: If credentials are missing when not using DI,
                or if DI container initialization fails, or if module import fails.

        Example:
            >>> # Using DI container (preferred)
            >>> ServiceFactory.initialize(container)
            >>> manager = ServiceFactory.create_execution_manager()
            >>>
            >>> # Direct instantiation (backward compatibility)
            >>> manager = ServiceFactory.create_execution_manager(
            ...     api_key="ALPACA_KEY",
            ...     secret_key="ALPACA_SECRET",
            ...     paper=True
            ... )

        """
        # Validate and normalize credentials
        api_key, secret_key = cls._validate_credentials(api_key, secret_key)

        use_di = cls._container is not None and all(x is None for x in [api_key, secret_key, paper])

        logger.info(
            "Creating ExecutionManager",
            extra={
                "use_di": use_di,
                "has_api_key": api_key is not None,
                "has_secret_key": secret_key is not None,
                "paper_mode": paper if paper is not None else True,
            },
        )

        try:
            if use_di:
                return cls._create_via_di_container()

            # Direct instantiation for backward compatibility
            if not api_key or not secret_key:
                logger.error(
                    "Missing required credentials for ExecutionManager",
                    extra={
                        "has_api_key": bool(api_key),
                        "has_secret_key": bool(secret_key),
                    },
                )
                raise ConfigurationError(
                    "api_key and secret_key are required when not using DI container. "
                    "Either initialize ServiceFactory with a DI container or provide credentials."
                )

            # Default to paper trading for safety
            paper = paper if paper is not None else True

            return cls._create_via_direct_instantiation(api_key, secret_key, paper=paper)

        except ConfigurationError:
            # Re-raise ConfigurationError as-is
            raise
        except Exception as e:
            # Wrap unexpected errors with context
            logger.error(
                "Unexpected error creating ExecutionManager",
                extra={"error": str(e), "error_type": type(e).__name__},
                exc_info=True,
            )
            raise ConfigurationError(f"Unexpected error creating ExecutionManager: {e}") from e

    @classmethod
    def get_container(cls) -> ApplicationContainer | None:
        """Get the current DI container.

        Returns the ApplicationContainer instance currently in use by the factory,
        or None if the factory has not been initialized.

        Returns:
            ApplicationContainer | None: The active container, or None if not initialized.

        Thread-safety: Not thread-safe. The container reference could change
        if initialize() is called concurrently.

        Example:
            >>> container = ServiceFactory.get_container()
            >>> if container is not None:
            ...     # Use container
            ...     pass

        """
        return cls._container
