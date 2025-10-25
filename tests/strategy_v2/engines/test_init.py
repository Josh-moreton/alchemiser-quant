"""Business Unit: strategy | Status: current

Unit tests for strategy_v2/engines/__init__.py.

Tests module structure, documentation, and accessibility patterns.
"""


class TestEnginesInit:
    """Test strategy_v2/engines __init__.py module structure."""

    def test_module_docstring_exists(self):
        """Test that the module has proper docstring."""
        from the_alchemiser.strategy_v2 import engines

        assert engines.__doc__ is not None
        assert "Business Unit: strategy" in engines.__doc__
        assert "Status: current" in engines.__doc__

    def test_all_exports_defined(self):
        """Test that __all__ is defined and is empty (submodule pattern)."""
        from the_alchemiser.strategy_v2 import engines

        assert hasattr(engines, "__all__")
        assert isinstance(engines.__all__, list)
        # Empty __all__ is intentional - engines are accessed via submodules
        assert engines.__all__ == []

    def test_dsl_submodule_accessible(self):
        """Test that dsl submodule can be imported."""
        from the_alchemiser.strategy_v2.engines import dsl

        assert dsl is not None
        # Verify dsl has expected exports
        assert hasattr(dsl, "DslEngine")
        assert hasattr(dsl, "DslStrategyEngine")
        assert hasattr(dsl, "DslEvaluator")

    def test_dsl_submodule_has_all_exports(self):
        """Test that dsl submodule exports match __all__."""
        from the_alchemiser.strategy_v2.engines import dsl

        expected_exports = {
            "DslEngine",
            "DslEngineError",
            "DslEvaluationError",
            "DslEvaluator",
            "DslStrategyEngine",
            "IndicatorService",
            "SexprParseError",
            "SexprParser",
        }
        assert set(dsl.__all__) == expected_exports

    def test_dsl_classes_importable_from_submodule(self):
        """Test that DSL classes can be imported from dsl submodule."""
        from the_alchemiser.strategy_v2.engines.dsl import (
            DslEngine,
            DslEngineError,
            DslEvaluationError,
            DslEvaluator,
            DslStrategyEngine,
            IndicatorService,
            SexprParseError,
            SexprParser,
        )

        # Verify they are classes/types
        assert DslEngine is not None
        assert DslEngineError is not None
        assert DslEvaluationError is not None
        assert DslEvaluator is not None
        assert DslStrategyEngine is not None
        assert IndicatorService is not None
        assert SexprParseError is not None
        assert SexprParser is not None

    def test_repeated_submodule_imports_return_same_object(self):
        """Test that repeated submodule imports return the same module object."""
        from the_alchemiser.strategy_v2.engines import dsl as dsl1
        from the_alchemiser.strategy_v2.engines import dsl as dsl2

        assert dsl1 is dsl2

    def test_module_is_a_package(self):
        """Test that engines is a package (has __path__)."""
        from the_alchemiser.strategy_v2 import engines

        assert hasattr(engines, "__path__")
        assert engines.__path__ is not None

    def test_module_has_correct_name(self):
        """Test that engines module has correct __name__."""
        from the_alchemiser.strategy_v2 import engines

        assert engines.__name__ == "the_alchemiser.strategy_v2.engines"

    def test_module_file_location(self):
        """Test that engines module __file__ points to correct location."""
        from the_alchemiser.strategy_v2 import engines

        assert engines.__file__ is not None
        assert "__init__.py" in engines.__file__
        assert "strategy_v2/engines" in engines.__file__
