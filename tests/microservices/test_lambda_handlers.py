"""Tests for microservices Lambda handlers."""

from __future__ import annotations


def test_strategy_handler_exists() -> None:
    """Verify strategy Lambda handler can be imported."""
    from the_alchemiser.strategy_v2.lambda_handler import lambda_handler

    assert callable(lambda_handler)


def test_portfolio_handler_exists() -> None:
    """Verify portfolio Lambda handler can be imported."""
    from the_alchemiser.portfolio_v2.lambda_handler import lambda_handler

    assert callable(lambda_handler)


def test_execution_handler_exists() -> None:
    """Verify execution Lambda handler can be imported."""
    from the_alchemiser.execution_v2.lambda_handler import lambda_handler

    assert callable(lambda_handler)
