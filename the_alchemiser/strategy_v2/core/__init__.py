#!/usr/bin/env python3
"""Business Unit: strategy | Status: current

Core strategy orchestration and registry components.

Provides the main orchestration logic for running strategies and
mapping strategy names to their implementations.
"""

from __future__ import annotations

from .factory import create_orchestrator, create_orchestrator_with_adapter
from .orchestrator import SingleStrategyOrchestrator
from .registry import get_strategy, list_strategies, register_strategy

__all__ = [
    "SingleStrategyOrchestrator",
    "create_orchestrator",
    "create_orchestrator_with_adapter",
    "get_strategy",
    "list_strategies",
    "register_strategy",
]
