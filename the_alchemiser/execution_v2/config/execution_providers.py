"""Business Unit: execution | Status: current.

Execution service providers for dependency injection.
"""

from __future__ import annotations

from dependency_injector import containers, providers

from the_alchemiser.execution_v2.core.execution_manager import ExecutionManager
from the_alchemiser.execution_v2.core.smart_execution_strategy import ExecutionConfig


class ExecutionProviders(containers.DeclarativeContainer):
    """Providers for execution layer components."""

    # Dependencies
    infrastructure = providers.DependenciesContainer()
    config = providers.DependenciesContainer()

    # V2 execution manager
    execution_manager = providers.Factory(
        ExecutionManager,
        alpaca_manager=infrastructure.alpaca_manager,
        execution_config=providers.Factory(ExecutionConfig),
        enable_smart_execution=providers.Factory(
            lambda exec_settings: exec_settings.enable_smart_execution,
            exec_settings=config.execution,
        ),
        enable_trade_ledger=providers.Factory(
            lambda exec_settings: exec_settings.enable_trade_ledger,
            exec_settings=config.execution,
        ),
    )
