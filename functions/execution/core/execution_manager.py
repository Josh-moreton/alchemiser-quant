"""Business Unit: execution | Status: current.

Execution manager that coordinates Executor with AlpacaManager.

This module provides a thin coordination layer that:
- Delegates execution to Executor
- Manages async/sync boundary via asyncio.run()
- Provides factory method for easy instantiation

Key responsibilities:
- Initialize Executor with AlpacaManager and optional ExecutionConfig
- Execute rebalance plans synchronously (wraps async Executor)
- Expose smart execution capabilities from Executor
"""

from __future__ import annotations

import asyncio
import threading
from typing import TYPE_CHECKING

from core.executor import Executor
from core.smart_execution_strategy import ExecutionConfig
from models.execution_result import (
    ExecutionResult,
)
from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
from the_alchemiser.shared.errors import (
    ConfigurationError,
    ExecutionManagerError,
    TradingClientError,
    ValidationError,
)
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlan

if TYPE_CHECKING:
    from logging import Logger

logger: Logger = get_logger(__name__)


class ExecutionManager:
    """Execution manager that delegates to Executor with smart execution capabilities.

    This class provides a synchronous interface to the async Executor,
    handling the asyncio event loop management and coordination with AlpacaManager.

    Attributes:
        alpaca_manager: Alpaca broker manager instance
        executor: Underlying async executor for order placement
        enable_smart_execution: Whether smart execution is available (from Executor)

    """

    def __init__(
        self,
        alpaca_manager: AlpacaManager,
        execution_config: ExecutionConfig | None = None,
    ) -> None:
        """Initialize the execution manager.

        Args:
            alpaca_manager: The Alpaca broker manager
            execution_config: Configuration for smart execution strategies

        Raises:
            ValidationError: If alpaca_manager is None
            ExecutionManagerError: If Executor initialization fails

        """
        if alpaca_manager is None:
            raise ValidationError("alpaca_manager cannot be None", field_name="alpaca_manager")

        self.alpaca_manager = alpaca_manager

        # Delegate all execution (and smart execution setup) to Executor
        try:
            self.executor = Executor(
                alpaca_manager=alpaca_manager,
                execution_config=execution_config,
            )
            self.enable_smart_execution = self.executor.enable_smart_execution
        except (ValidationError, ConfigurationError) as e:
            # Configuration or validation errors during executor initialization
            logger.error(
                "Failed to initialize Executor due to configuration error",
                extra={"error": str(e), "error_type": type(e).__name__},
            )
            raise ExecutionManagerError(
                f"Executor initialization failed: {e}", operation="initialization"
            ) from e
        except Exception as e:
            # Unexpected errors during executor initialization
            logger.error(
                "Failed to initialize Executor due to unexpected error",
                exc_info=True,
                extra={"error": str(e), "error_type": type(e).__name__},
            )
            raise ExecutionManagerError(
                f"Executor initialization failed: {e}", operation="initialization"
            ) from e

    def execute_rebalance_plan(self, plan: RebalancePlan) -> ExecutionResult:
        """Execute rebalance plan using executor.

        This method provides a synchronous interface to the async executor,
        managing the asyncio event loop and coordination with AlpacaManager.

        Args:
            plan: RebalancePlan to execute

        Returns:
            ExecutionResult with execution results

        Raises:
            ValidationError: If plan is None or invalid
            ExecutionManagerError: If async execution fails
            ConnectionError: If broker connection fails

        """
        if plan is None:
            raise ValidationError("plan cannot be None", field_name="plan")

        correlation_id = plan.correlation_id
        logger.info(
            "Starting execution of rebalance plan",
            extra={
                "plan_id": plan.plan_id,
                "correlation_id": correlation_id,
                "causation_id": plan.causation_id,
                "num_items": len(plan.items),
                "module": "execution_v2",
            },
        )

        # Initialize TradingStream asynchronously in background - don't block on connection
        # This starts the WebSocket connection process early without waiting for completion
        # Note: This optimization may be removed if it causes issues
        stream_init_event = threading.Event()
        stream_init_error: Exception | None = None

        def start_trading_stream_async() -> None:
            """Start TradingStream in background without blocking main execution.

            Sets stream_init_event when complete (success or failure).
            Stores any exception in stream_init_error for later inspection.
            """
            nonlocal stream_init_error
            try:
                logger.debug(
                    "Starting TradingStream initialization in background",
                    extra={"correlation_id": correlation_id},
                )
                # Note: Accessing package-private method - should be made public in AlpacaManager
                # or this initialization should be handled by Executor
                self.alpaca_manager._ensure_trading_stream()
                logger.debug(
                    "TradingStream initialization completed",
                    extra={"correlation_id": correlation_id},
                )
            except (OSError, TimeoutError, ConnectionError) as e:
                # Network-related errors that shouldn't stop execution
                stream_init_error = e
                logger.warning(
                    "TradingStream background initialization failed (non-critical network error)",
                    extra={
                        "correlation_id": correlation_id,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                )
            except (TradingClientError, ConfigurationError) as e:
                # Trading client or configuration errors - log but don't crash
                stream_init_error = e
                logger.warning(
                    "TradingStream initialization failed (non-critical client error)",
                    extra={
                        "correlation_id": correlation_id,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                )
            except Exception as e:
                # Unexpected errors - log but don't crash
                stream_init_error = e
                logger.error(
                    "Unexpected error in TradingStream initialization",
                    exc_info=True,
                    extra={
                        "correlation_id": correlation_id,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                )
            finally:
                stream_init_event.set()

        # Start TradingStream initialization in a separate thread so it doesn't block execution
        stream_init_thread = threading.Thread(
            target=start_trading_stream_async, name="TradingStreamInit", daemon=True
        )
        stream_init_thread.start()
        logger.debug(
            "TradingStream initialization started in background",
            extra={"correlation_id": correlation_id},
        )

        # Execute the rebalance plan via async executor
        # We use asyncio.run() to create a new event loop for this execution
        try:
            result = asyncio.run(self.executor.execute_rebalance_plan(plan))
        except (ValidationError, ExecutionManagerError) as e:
            # Known execution errors - log and reraise
            logger.error(
                "Execution failed with known error",
                extra={
                    "correlation_id": correlation_id,
                    "plan_id": plan.plan_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )
            raise
        except Exception as e:
            # Unexpected errors during execution - log and reraise
            logger.error(
                "Execution failed with unexpected error",
                exc_info=True,
                extra={
                    "correlation_id": correlation_id,
                    "plan_id": plan.plan_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )
            raise

        logger.info(
            "Execution completed",
            extra={
                "correlation_id": correlation_id,
                "plan_id": plan.plan_id,
                "success": result.success,
                "orders_placed": result.orders_placed,
                "orders_succeeded": result.orders_succeeded,
                "status": (
                    result.status.value if hasattr(result.status, "value") else str(result.status)
                ),
            },
        )

        # Optional: Wait for stream initialization to complete (with timeout)
        # This ensures any errors are logged before returning
        if not stream_init_event.wait(timeout=2.0):
            logger.debug(
                "TradingStream initialization still in progress after execution",
                extra={"correlation_id": correlation_id},
            )

        return result

    def shutdown(self) -> None:
        """Shutdown the execution manager and cleanup resources.

        This ensures proper cleanup of the underlying executor,
        including stopping the real-time pricing service WebSocket connection.
        """
        try:
            if hasattr(self, "executor") and self.executor:
                self.executor.shutdown()
                logger.debug("ExecutionManager: Executor shutdown completed")
        except (AttributeError, RuntimeError) as e:
            # Expected errors during shutdown (resource cleanup issues)
            logger.warning(
                f"ExecutionManager: Error during shutdown (non-critical): {e}",
                extra={"error_type": type(e).__name__},
            )
        except Exception as e:
            # Unexpected errors during shutdown - log but don't crash
            logger.warning(
                f"ExecutionManager: Unexpected error during shutdown: {e}",
                extra={"error_type": type(e).__name__},
            )

    @classmethod
    def create_with_config(
        cls,
        api_key: str,
        secret_key: str,
        *,
        paper: bool = True,
        execution_config: ExecutionConfig | None = None,
    ) -> ExecutionManager:
        """Create ExecutionManager with config and smart execution options.

        Factory method for convenient instantiation with credentials.

        Args:
            api_key: Alpaca API key (non-empty)
            secret_key: Alpaca secret key (non-empty)
            paper: Whether to use paper trading
            execution_config: Configuration for smart execution strategies

        Returns:
            ExecutionManager instance with configured smart execution

        Raises:
            ValidationError: If api_key or secret_key is empty or None

        """
        if not api_key or not api_key.strip():
            raise ValidationError("api_key cannot be empty", field_name="api_key")
        if not secret_key or not secret_key.strip():
            raise ValidationError("secret_key cannot be empty", field_name="secret_key")

        try:
            alpaca_manager = AlpacaManager(
                api_key=api_key.strip(),
                secret_key=secret_key.strip(),
                paper=paper,
            )
            return cls(
                alpaca_manager=alpaca_manager,
                execution_config=execution_config,
            )
        except (ValidationError, ConfigurationError, TradingClientError) as e:
            # Known errors during manager creation
            logger.error(
                "Failed to create ExecutionManager due to known error",
                extra={"error": str(e), "error_type": type(e).__name__, "paper": paper},
            )
            raise ExecutionManagerError(
                f"Failed to create ExecutionManager: {e}", operation="creation"
            ) from e
        except Exception as e:
            # Unexpected errors during manager creation
            logger.error(
                "Failed to create ExecutionManager due to unexpected error",
                exc_info=True,
                extra={"error": str(e), "error_type": type(e).__name__, "paper": paper},
            )
            raise ExecutionManagerError(
                f"Failed to create ExecutionManager: {e}", operation="creation"
            ) from e
