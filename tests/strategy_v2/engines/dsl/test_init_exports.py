#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

Test DSL package public API exports.

Verifies that the public API surface of the DSL engine package is complete
and correctly exported through __init__.py.
"""


class TestDslPackageExports:
    """Test DSL package __init__.py exports."""

    def test_all_exports_available(self) -> None:
        """Test that all symbols in __all__ are importable from package root."""
        from the_alchemiser.strategy_v2.engines import dsl

        # Verify __all__ is defined
        assert hasattr(dsl, "__all__")
        assert isinstance(dsl.__all__, list)
        assert len(dsl.__all__) == 8

        # Verify all symbols in __all__ are actually exported
        for symbol in dsl.__all__:
            assert hasattr(dsl, symbol), f"Symbol {symbol} not found in package exports"

    def test_engine_classes_importable(self) -> None:
        """Test that core engine classes can be imported from package root."""
        from the_alchemiser.strategy_v2.engines.dsl import (
            DslEngine,
            DslEvaluator,
            DslStrategyEngine,
        )

        # Verify classes are actually classes
        assert isinstance(DslEngine, type)
        assert isinstance(DslEvaluator, type)
        assert isinstance(DslStrategyEngine, type)

    def test_parser_importable(self) -> None:
        """Test that parser class can be imported from package root."""
        from the_alchemiser.strategy_v2.engines.dsl import SexprParser

        # Verify it's a class
        assert isinstance(SexprParser, type)

    def test_service_importable(self) -> None:
        """Test that indicator service can be imported from package root."""
        from the_alchemiser.strategy_v2.engines.dsl import IndicatorService

        # Verify it's a class
        assert isinstance(IndicatorService, type)

    def test_exceptions_importable(self) -> None:
        """Test that all exception classes can be imported from package root."""
        from the_alchemiser.strategy_v2.engines.dsl import (
            DslEngineError,
            DslEvaluationError,
            SexprParseError,
        )

        # Verify they are exception classes
        assert issubclass(DslEngineError, Exception)
        assert issubclass(DslEvaluationError, Exception)
        assert issubclass(SexprParseError, Exception)

    def test_all_matches_imports(self) -> None:
        """Test that __all__ list matches actual imported symbols."""
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

        actual_exports = set(dsl.__all__)

        assert actual_exports == expected_exports, (
            f"__all__ mismatch. "
            f"Expected: {expected_exports}, "
            f"Got: {actual_exports}, "
            f"Missing: {expected_exports - actual_exports}, "
            f"Extra: {actual_exports - expected_exports}"
        )

    def test_no_private_exports(self) -> None:
        """Test that __all__ does not export any private symbols."""
        from the_alchemiser.strategy_v2.engines import dsl

        for symbol in dsl.__all__:
            assert not symbol.startswith("_"), f"Private symbol {symbol} should not be exported"

    def test_alphabetical_order(self) -> None:
        """Test that __all__ exports are in alphabetical order for consistency."""
        from the_alchemiser.strategy_v2.engines import dsl

        sorted_exports = sorted(dsl.__all__)
        assert dsl.__all__ == sorted_exports, (
            f"__all__ should be in alphabetical order. "
            f"Expected: {sorted_exports}, "
            f"Got: {dsl.__all__}"
        )
