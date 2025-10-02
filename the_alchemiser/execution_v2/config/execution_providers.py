"""Business Unit: execution | Status: current.

Execution service providers for dependency injection.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from dependency_injector import containers, providers

from the_alchemiser.execution_v2.core.execution_manager import ExecutionManager
from the_alchemiser.execution_v2.core.smart_execution_strategy import ExecutionConfig


def _create_execution_config_from_settings(execution_settings: Any) -> ExecutionConfig:
    """Create ExecutionConfig from ExecutionSettings.

    Args:
        execution_settings: ExecutionSettings from global config

    Returns:
        ExecutionConfig with settings applied

    """
    config = ExecutionConfig()
    
    # Apply market-on-exhaust settings from global config
    if hasattr(execution_settings, "market_on_exhaust_enabled"):
        config.market_on_exhaust_enabled = execution_settings.market_on_exhaust_enabled
    if hasattr(execution_settings, "market_on_exhaust_max_notional_usd"):
        max_notional = execution_settings.market_on_exhaust_max_notional_usd
        if max_notional is not None:
            config.market_on_exhaust_max_notional_usd = Decimal(str(max_notional))
    
    return config


class ExecutionProviders(containers.DeclarativeContainer):
    """Providers for execution layer components."""

    # Dependencies
    infrastructure = providers.DependenciesContainer()
    config = providers.DependenciesContainer()

    # V2 execution manager
    execution_manager = providers.Factory(
        ExecutionManager,
        alpaca_manager=infrastructure.alpaca_manager,
        execution_config=providers.Factory(
            _create_execution_config_from_settings,
            execution_settings=config.execution,
        ),
    )
