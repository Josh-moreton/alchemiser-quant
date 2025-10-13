"""Business Unit: execution | Status: current.

Tests for execution_v2.handlers.__init__ module exports.

Validates that the handlers __init__ module correctly exports the expected
public API and maintains proper module structure.
"""

from __future__ import annotations


def test_handlers_module_exports() -> None:
    """Test that handlers module exports expected components."""
    from the_alchemiser.execution_v2 import handlers

    # Verify __all__ attribute exists and contains expected exports
    assert hasattr(handlers, "__all__")
    assert "TradingExecutionHandler" in handlers.__all__

    # Verify the handler class is accessible
    assert hasattr(handlers, "TradingExecutionHandler")


def test_trading_execution_handler_import() -> None:
    """Test that TradingExecutionHandler can be imported directly."""
    from the_alchemiser.execution_v2.handlers import TradingExecutionHandler

    # Verify it's a class
    assert isinstance(TradingExecutionHandler, type)

    # Verify the class has expected methods
    assert hasattr(TradingExecutionHandler, "handle_event")
    assert hasattr(TradingExecutionHandler, "can_handle")


def test_handlers_module_structure() -> None:
    """Test that handlers module has proper structure and documentation."""
    from the_alchemiser.execution_v2 import handlers

    # Verify module docstring exists
    assert handlers.__doc__ is not None
    assert len(handlers.__doc__) > 0

    # Verify business unit identifier in docstring
    assert "Business Unit: execution" in handlers.__doc__
    assert "Status: current" in handlers.__doc__

    # Verify module purpose is documented
    assert "handlers" in handlers.__doc__.lower()
