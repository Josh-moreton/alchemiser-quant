#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Strategy type enumeration for inter-module communication.
"""

from __future__ import annotations

from enum import Enum


class StrategyType(Enum):
    """Enumeration of available trading strategies."""

    NUCLEAR = "NUCLEAR"
    TECL = "TECL"
    KLM = "KLM"
    ALL = "ALL"
