#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Stub entry point for The Alchemiser Trading System.

Trading execution happens via Lambda functions (strategy_v2, portfolio_v2,
execution_v2, notifications_v2). This module exists only for backwards
compatibility with tooling that expects a main() function.
"""

from __future__ import annotations

__all__ = ["main"]


def main(argv: list[str] | None = None) -> bool:
    """Stub entry point - trading runs via Lambda functions.

    Args:
        argv: Command line arguments (unused)

    Returns:
        False - local execution is not supported

    """
    return False
