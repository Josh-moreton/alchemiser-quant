#!/usr/bin/env python3
"""
CLI-related DTOs for The Alchemiser Trading System.

This module contains Pydantic v2 DTOs for CLI interface boundaries,
moved from domain/types.py as part of the Pydantic migration.
These handle user interaction, command processing, and display formatting.
"""

from typing import Literal, TypedDict

from the_alchemiser.domain.types import AccountInfo, OrderDetails, PositionInfo, StrategySignal


# CLI Command Types
class CLIOptions(TypedDict):
    """CLI command options."""

    verbose: bool
    quiet: bool
    live: bool
    ignore_market_hours: bool
    force: bool
    no_header: bool


class CLICommandResult(TypedDict):
    """Result of CLI command execution."""

    success: bool
    message: str
    exit_code: int


# CLI Display Types
class CLISignalData(TypedDict):
    """Strategy signal data for CLI display."""

    strategy_type: str
    signals: dict[str, StrategySignal]
    indicators: dict[str, dict[str, float]]


class CLIAccountDisplay(TypedDict):
    """Account information formatted for CLI display."""

    account_info: AccountInfo
    positions: dict[str, PositionInfo]
    mode: Literal["live", "paper"]


class CLIPortfolioData(TypedDict):
    """Portfolio allocation data for CLI display."""

    symbol: str
    allocation_percentage: float
    current_value: float
    target_value: float


class CLIOrderDisplay(TypedDict):
    """Order information formatted for CLI display."""

    order_details: OrderDetails
    display_style: str
    formatted_amount: str
