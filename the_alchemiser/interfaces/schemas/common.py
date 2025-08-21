"""
Common DTOs for application layer and interface boundaries.

This module provides Pydantic v2 DTOs for common data structures used across
the application layer, replacing loose dataclasses and dict usage with
strongly typed, validated structures.

Key Features:
- Pydantic v2 BaseModel with strict validation
- Type safety for execution results and summaries
- Comprehensive field validation and normalization
- Immutable DTOs for consistent data flow
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from the_alchemiser.domain.registry import StrategyType
from the_alchemiser.domain.types import AccountInfo, OrderDetails, StrategySignal


class MultiStrategyExecutionResultDTO(BaseModel):
    """
    DTO for multi-strategy execution results.

    Provides an immutable, validated container for multi-strategy execution
    outcomes, replacing the dataclass version with enhanced type safety
    and validation capabilities.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    # Core execution status
    success: bool

    # Strategy data
    strategy_signals: dict[StrategyType, StrategySignal]
    consolidated_portfolio: dict[str, float]

    # Order execution results
    orders_executed: list[OrderDetails]

    # Account state tracking
    account_info_before: AccountInfo
    account_info_after: AccountInfo

    # Summary and state (keeping as Any for now to maintain compatibility)
    # TODO: Define specific structured types for these fields
    execution_summary: dict[str, Any]
    final_portfolio_state: dict[str, Any] | None = None
