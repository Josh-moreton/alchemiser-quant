#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

DSL operators package for strategy expression evaluation.

Contains modular operator implementations organized by concern:
- portfolio: Portfolio construction operators
- selection: Asset selection operators
- comparison: Comparison and logical operators
- control_flow: Control flow and conditional operators
- indicators: Technical indicator operators

Public API:
    Register functions for operator registration with dispatcher:
    - register_portfolio_operators: Register portfolio construction operators
    - register_selection_operators: Register asset selection operators
    - register_comparison_operators: Register comparison and logical operators
    - register_control_flow_operators: Register control flow operators
    - register_indicator_operators: Register technical indicator operators
"""

from __future__ import annotations

from .comparison import register_comparison_operators
from .control_flow import register_control_flow_operators
from .indicators import register_indicator_operators
from .portfolio import register_portfolio_operators
from .selection import register_selection_operators

__all__ = [
    "register_comparison_operators",
    "register_control_flow_operators",
    "register_indicator_operators",
    "register_portfolio_operators",
    "register_selection_operators",
]
