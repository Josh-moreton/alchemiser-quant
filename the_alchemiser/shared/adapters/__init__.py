"""Business Unit: shared | Status: current.

Adapter functions for converting between internal objects and DTOs.
"""

from __future__ import annotations

# Strategy adapters
from the_alchemiser.shared.adapters.strategy_adapters import (
    batch_strategy_signals_to_dtos,
    dto_to_strategy_signal_context,
    strategy_signal_to_dto,
    validate_signal_conversion,
)

# Portfolio adapters  
from the_alchemiser.shared.adapters.portfolio_adapters import (
    batch_positions_to_dtos,
    dto_to_portfolio_context,
    portfolio_state_to_dto,
    position_to_dto,
)

# Execution adapters
from the_alchemiser.shared.adapters.execution_adapters import (
    batch_order_requests_to_contexts,
    create_execution_report_dto,
    order_request_to_context,
    order_result_to_executed_order_dto,
    rebalance_plan_to_order_requests,
)

__all__ = [
    # Strategy adapters
    "batch_strategy_signals_to_dtos",
    "dto_to_strategy_signal_context", 
    "strategy_signal_to_dto",
    "validate_signal_conversion",
    # Portfolio adapters
    "batch_positions_to_dtos",
    "dto_to_portfolio_context",
    "portfolio_state_to_dto",
    "position_to_dto",
    # Execution adapters
    "batch_order_requests_to_contexts",
    "create_execution_report_dto",
    "order_request_to_context",
    "order_result_to_executed_order_dto",
    "rebalance_plan_to_order_requests",
]