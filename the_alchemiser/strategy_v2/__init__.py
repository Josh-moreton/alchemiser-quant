#!/usr/bin/env python3
"""Business Unit: strategy | Status: current

Strategy_v2 module for signal generation and indicator calculation.

This module provides a clean, boundary-enforcing strategy system that:
- Consumes market data via shared Alpaca capabilities
- Outputs pure strategy signal DTOs (StrategyAllocationDTO)
- Maintains strict separation from portfolio and execution concerns

Public API:
- SingleStrategyOrchestrator: Main entry point for running strategies
- get_strategy: Registry access for strategy engines
- StrategyContext: Input context for strategy execution
"""

from __future__ import annotations

# Core imports
from .core.orchestrator import SingleStrategyOrchestrator
from .core.registry import get_strategy, list_strategies, register_strategy
from .models.context import StrategyContext

# Public API exports
__all__ = [
    # Core components
    "StrategyContext",
    "SingleStrategyOrchestrator",
    "get_strategy",
    "list_strategies",
    "register_strategy",
]

# Version for compatibility tracking
__version__ = "2.0.0"
