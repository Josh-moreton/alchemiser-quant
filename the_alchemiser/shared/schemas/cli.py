#!/usr/bin/env python3
"""Business Unit: shared; Status: current.

CLI-related DTOs for The Alchemiser Trading System.

This module contains Pydantic models for CLI interface boundaries.
Migrated from TypedDict to Pydantic for runtime validation and consistent
serialization. These handle user interaction, command processing, and display formatting.

⚠️ IMPORTANT:
CLIPortfolioData uses Decimal for all monetary values and percentages to maintain
consistency with domain models and prevent float precision issues. Convert to string
for final display formatting only.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from the_alchemiser.shared.value_objects.core_types import (
    AccountInfo,
    OrderDetails,
    PositionInfo,
    StrategySignal,
)


# CLI Command Types
class CLIOptions(BaseModel):
    """CLI command options.

    Configuration flags for CLI command execution.
    
    Schema version: 1.0
    """

    model_config = ConfigDict(strict=True, frozen=True)

    schema_version: str = Field(default="1.0", description="Schema version for compatibility tracking")
    verbose: bool = Field(default=False, description="Enable verbose output")
    quiet: bool = Field(default=False, description="Suppress non-essential output")
    live: bool = Field(default=False, description="Enable live trading mode")
    force: bool = Field(default=False, description="Force operation without confirmation")
    no_header: bool = Field(default=False, description="Suppress header output")


class CLICommandResult(BaseModel):
    """Result of CLI command execution.

    Standard response format for all CLI commands.
    
    Schema version: 1.0
    """

    model_config = ConfigDict(strict=True, frozen=True)

    schema_version: str = Field(default="1.0", description="Schema version for compatibility tracking")
    success: bool = Field(description="Whether command succeeded")
    message: str = Field(description="Human-readable result message")
    exit_code: int = Field(description="Shell exit code", ge=0, le=255)


# CLI Display Types
class CLISignalData(BaseModel):
    """Strategy signal data for CLI display.

    Aggregates strategy signals and technical indicators for terminal display.
    
    Schema version: 1.0
    
    Note: Indicator values use float for display purposes. These are derived
    from technical analysis and do not require Decimal precision.
    """

    model_config = ConfigDict(strict=True, frozen=True)

    schema_version: str = Field(default="1.0", description="Schema version for compatibility tracking")
    strategy_type: str = Field(description="Strategy identifier")
    signals: dict[str, StrategySignal] = Field(
        default_factory=dict, description="Symbol-to-signal mapping"
    )
    indicators: dict[str, dict[str, float]] = Field(
        default_factory=dict, description="Symbol-to-indicators mapping (display values)"
    )


class CLIAccountDisplay(BaseModel):
    """Account information formatted for CLI display.

    Contains account state, positions, and mode for terminal rendering.
    
    Schema version: 1.0
    """

    model_config = ConfigDict(strict=True, frozen=True)

    schema_version: str = Field(default="1.0", description="Schema version for compatibility tracking")
    account_info: AccountInfo = Field(description="Current account information")
    positions: dict[str, PositionInfo] = Field(
        default_factory=dict, description="Symbol-to-position mapping"
    )
    mode: Literal["live", "paper"] = Field(description="Trading mode")


class CLIPortfolioData(BaseModel):
    """Portfolio allocation data for CLI display.

    Contains position allocation details for terminal display.
    
    Schema version: 1.0
    
    ⚠️ IMPORTANT:
    All monetary values and percentages use Decimal for precision consistency
    with domain models. Convert to float/string only at final display formatting.
    """

    model_config = ConfigDict(strict=True, frozen=True)

    schema_version: str = Field(default="1.0", description="Schema version for compatibility tracking")
    symbol: str = Field(description="Asset symbol")
    allocation_percentage: Decimal = Field(
        description="Target allocation percentage (0-100 as Decimal)", ge=0, le=100
    )
    current_value: Decimal = Field(description="Current position value in USD (Decimal for precision)")
    target_value: Decimal = Field(description="Target position value in USD (Decimal for precision)")


class CLIOrderDisplay(BaseModel):
    """Order information formatted for CLI display.

    Contains order details with display formatting for terminal output.
    
    Schema version: 1.0
    """

    model_config = ConfigDict(strict=True, frozen=True)

    schema_version: str = Field(default="1.0", description="Schema version for compatibility tracking")
    order_details: OrderDetails = Field(description="Order details")
    display_style: str = Field(description="Display style/format")
    formatted_amount: str = Field(description="Human-formatted amount string")
