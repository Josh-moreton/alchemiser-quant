"""Business Unit: strategy | Status: current.

Unit tests for operators module __init__.py.

Tests public API exports and module attribute access patterns.
"""

import inspect

import pytest


@pytest.mark.unit
@pytest.mark.dsl
class TestOperatorsInit:
    """Test operators __init__.py exports and attributes."""

    def test_import_register_portfolio_operators(self) -> None:
        """Test that register_portfolio_operators can be imported."""
        from the_alchemiser.strategy_v2.engines.dsl.operators import (
            register_portfolio_operators,
        )

        assert register_portfolio_operators is not None
        assert callable(register_portfolio_operators)

    def test_import_register_selection_operators(self) -> None:
        """Test that register_selection_operators can be imported."""
        from the_alchemiser.strategy_v2.engines.dsl.operators import (
            register_selection_operators,
        )

        assert register_selection_operators is not None
        assert callable(register_selection_operators)

    def test_import_register_comparison_operators(self) -> None:
        """Test that register_comparison_operators can be imported."""
        from the_alchemiser.strategy_v2.engines.dsl.operators import (
            register_comparison_operators,
        )

        assert register_comparison_operators is not None
        assert callable(register_comparison_operators)

    def test_import_register_control_flow_operators(self) -> None:
        """Test that register_control_flow_operators can be imported."""
        from the_alchemiser.strategy_v2.engines.dsl.operators import (
            register_control_flow_operators,
        )

        assert register_control_flow_operators is not None
        assert callable(register_control_flow_operators)

    def test_import_register_indicator_operators(self) -> None:
        """Test that register_indicator_operators can be imported."""
        from the_alchemiser.strategy_v2.engines.dsl.operators import (
            register_indicator_operators,
        )

        assert register_indicator_operators is not None
        assert callable(register_indicator_operators)

    def test_all_contains_expected_exports(self) -> None:
        """Test __all__ contains expected public API."""
        from the_alchemiser.strategy_v2.engines.dsl import operators

        assert "register_portfolio_operators" in operators.__all__
        assert "register_selection_operators" in operators.__all__
        assert "register_comparison_operators" in operators.__all__
        assert "register_control_flow_operators" in operators.__all__
        assert "register_indicator_operators" in operators.__all__

    def test_all_has_correct_count(self) -> None:
        """Test __all__ has the correct number of exports."""
        from the_alchemiser.strategy_v2.engines.dsl import operators

        assert len(operators.__all__) == 5

    def test_module_docstring_exists(self) -> None:
        """Test that the module has proper docstring."""
        from the_alchemiser.strategy_v2.engines.dsl import operators

        assert operators.__doc__ is not None
        assert "Business Unit: strategy" in operators.__doc__
        assert "Status: current" in operators.__doc__

    def test_register_functions_signature(self) -> None:
        """Test that all register functions have correct signatures."""
        from the_alchemiser.strategy_v2.engines.dsl.operators import (
            register_comparison_operators,
            register_control_flow_operators,
            register_indicator_operators,
            register_portfolio_operators,
            register_selection_operators,
        )

        # All register functions should accept a dispatcher parameter
        for func in [
            register_portfolio_operators,
            register_selection_operators,
            register_comparison_operators,
            register_control_flow_operators,
            register_indicator_operators,
        ]:
            sig = inspect.signature(func)
            params = list(sig.parameters.keys())
            assert len(params) == 1, f"{func.__name__} should have exactly 1 parameter"
            assert (
                params[0] == "dispatcher"
            ), f"{func.__name__} should have 'dispatcher' parameter"
