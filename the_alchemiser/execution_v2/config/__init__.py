"""Business Unit: execution | Status: current.

Dependency injection configuration for execution_v2 layer.

This module provides the ExecutionProviders container for lazy initialization
via ApplicationContainer.initialize_execution_providers(). The dynamic import
pattern (via importlib) breaks circular dependencies between shared.config
and execution_v2 modules.
"""

from .execution_providers import ExecutionProviders

__all__: list[str] = [
    "ExecutionProviders",
]
