"""Business Unit: order execution/placement | Status: current.

Bootstrap helper for Execution context Lambda handlers.

Provides dependency injection and initialization for Execution context use cases
while keeping AWS Lambda specifics isolated from application logic.
"""

from __future__ import annotations

import logging

from the_alchemiser.execution.application.use_cases.execute_plan import ExecutePlanUseCase
from the_alchemiser.execution.infrastructure.adapters.event_bus_execution_report_publisher_adapter import (
    EventBusExecutionReportPublisherAdapter,
)
from the_alchemiser.infrastructure.config import Settings, load_settings
from the_alchemiser.shared_kernel.exceptions.base_exceptions import ConfigurationError

logger = logging.getLogger(__name__)


class ExecutionBootstrapContext:
    """Dependency bundle for Execution Lambda handlers."""
    
    def __init__(
        self,
        execute_plan_use_case: ExecutePlanUseCase,
        config: Settings,
    ) -> None:
        self.execute_plan_use_case = execute_plan_use_case
        self.config = config


def bootstrap_execution_context() -> ExecutionBootstrapContext:
    """Bootstrap Execution context dependencies for Lambda execution.
    
    Constructs all required ports, adapters, and use cases while pulling
    configuration from environment variables.
    
    Returns:
        ExecutionBootstrapContext with initialized dependencies
        
    Raises:
        ConfigurationError: If required configuration is missing or invalid
    """
    logger.info("Bootstrapping Execution context for Lambda execution")
    
    try:
        # Load configuration from environment
        config = load_settings()
        
        # Create execution report publisher (using EventBus)
        execution_report_publisher = EventBusExecutionReportPublisherAdapter()
        
        # Create use case
        execute_plan_use_case = ExecutePlanUseCase(
            execution_report_publisher=execution_report_publisher
        )
        
        logger.info("Execution context bootstrap completed successfully")
        
        return ExecutionBootstrapContext(
            execute_plan_use_case=execute_plan_use_case,
            config=config,
        )
        
    except Exception as e:
        logger.error(f"Failed to bootstrap Execution context: {e}", exc_info=True)
        raise ConfigurationError(f"Execution context bootstrap failed: {e}") from e