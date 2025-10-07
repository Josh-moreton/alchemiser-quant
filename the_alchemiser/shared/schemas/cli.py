#!/usr/bin/env python3
"""Business Unit: utilities; Status: current.

CLI-related DTOs for The Alchemiser Trading System.

This module contains Pydantic models for CLI interface boundaries.
Migrated from TypedDict to Pydantic for runtime validation and consistent
serialization. These handle user interaction, command processing, and display formatting.
"""

from __future__ import annotations

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
    """
    
    model_config = ConfigDict(strict=True, frozen=True)
    
    verbose: bool = Field(default=False, description="Enable verbose output")
    quiet: bool = Field(default=False, description="Suppress non-essential output")
    live: bool = Field(default=False, description="Enable live trading mode")
    force: bool = Field(default=False, description="Force operation without confirmation")
    no_header: bool = Field(default=False, description="Suppress header output")


class CLICommandResult(BaseModel):
    """Result of CLI command execution.
    
    Standard response format for all CLI commands.
    """
    
    model_config = ConfigDict(strict=True, frozen=True)
    
    success: bool = Field(description="Whether command succeeded")
    message: str = Field(description="Human-readable result message")
    exit_code: int = Field(description="Shell exit code", ge=0, le=255)


# CLI Display Types
class CLISignalData(BaseModel):
    """Strategy signal data for CLI display.
    
    Aggregates strategy signals and technical indicators for terminal display.
    """
    
    model_config = ConfigDict(strict=True, frozen=True)
    
    strategy_type: str = Field(description="Strategy identifier")
    signals: dict[str, StrategySignal] = Field(
        default_factory=dict,
        description="Symbol-to-signal mapping"
    )
    indicators: dict[str, dict[str, float]] = Field(
        default_factory=dict,
        description="Symbol-to-indicators mapping"
    )


class CLIAccountDisplay(BaseModel):
    """Account information formatted for CLI display.
    
    Contains account state, positions, and mode for terminal rendering.
    """
    
    model_config = ConfigDict(strict=True, frozen=True)
    
    account_info: AccountInfo = Field(description="Current account information")
    positions: dict[str, PositionInfo] = Field(
        default_factory=dict,
        description="Symbol-to-position mapping"
    )
    mode: Literal["live", "paper"] = Field(description="Trading mode")


class CLIPortfolioData(BaseModel):
    """Portfolio allocation data for CLI display.
    
    Contains position allocation details for terminal display.
    """
    
    model_config = ConfigDict(strict=True, frozen=True)
    
    symbol: str = Field(description="Asset symbol")
    allocation_percentage: float = Field(
        description="Target allocation percentage",
        ge=0.0,
        le=100.0
    )
    current_value: float = Field(description="Current position value")
    target_value: float = Field(description="Target position value")


class CLIOrderDisplay(BaseModel):
    """Order information formatted for CLI display.
    
    Contains order details with display formatting for terminal output.
    """
    
    model_config = ConfigDict(strict=True, frozen=True)
    
    order_details: OrderDetails = Field(description="Order details")
    display_style: str = Field(description="Display style/format")
    formatted_amount: str = Field(description="Human-formatted amount string")
