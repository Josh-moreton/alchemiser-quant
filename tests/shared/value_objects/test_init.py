"""Business Unit: shared | Status: current.

Tests for value_objects.__init__ module export completeness.
"""

from __future__ import annotations

import pytest


class TestValueObjectsExports:
    """Test that value_objects package exports all expected types."""

    @pytest.mark.unit
    def test_all_types_importable(self):
        """Test that all types in __all__ are importable."""
        from the_alchemiser.shared.value_objects import (
            AccountInfo,
            EnrichedAccountInfo,
            ErrorContext,
            Identifier,
            IndicatorData,
            KLMDecision,
            MarketDataPoint,
            OrderDetails,
            OrderStatusLiteral,
            PortfolioHistoryData,
            PortfolioSnapshot,
            PositionInfo,
            PositionsDict,
            PriceData,
            QuoteData,
            StrategyPnLSummary,
            StrategySignal,
            StrategySignalBase,
            Symbol,
            TradeAnalysis,
        )

        # Verify imports are not None
        assert AccountInfo is not None
        assert EnrichedAccountInfo is not None
        assert ErrorContext is not None
        assert Identifier is not None
        assert IndicatorData is not None
        assert KLMDecision is not None
        assert MarketDataPoint is not None
        assert OrderDetails is not None
        assert OrderStatusLiteral is not None
        assert PortfolioHistoryData is not None
        assert PortfolioSnapshot is not None
        assert PositionInfo is not None
        assert PositionsDict is not None
        assert PriceData is not None
        assert QuoteData is not None
        assert StrategyPnLSummary is not None
        assert StrategySignal is not None
        assert StrategySignalBase is not None
        assert Symbol is not None
        assert TradeAnalysis is not None

    @pytest.mark.unit
    def test_all_list_matches_imports(self):
        """Test that __all__ list matches actual exports."""
        from the_alchemiser.shared import value_objects

        expected_exports = {
            "AccountInfo",
            "EnrichedAccountInfo",
            "ErrorContext",
            "Identifier",
            "IndicatorData",
            "KLMDecision",
            "MarketDataPoint",
            "OrderDetails",
            "OrderStatusLiteral",
            "PortfolioHistoryData",
            "PortfolioSnapshot",
            "PositionInfo",
            "PositionsDict",
            "PriceData",
            "QuoteData",
            "StrategyPnLSummary",
            "StrategySignal",
            "StrategySignalBase",
            "Symbol",
            "TradeAnalysis",
        }

        actual_exports = set(value_objects.__all__)
        assert actual_exports == expected_exports

    @pytest.mark.unit
    def test_symbol_is_frozen_dataclass(self):
        """Test that Symbol is a frozen dataclass."""
        from the_alchemiser.shared.value_objects import Symbol

        symbol = Symbol("AAPL")
        assert symbol.value == "AAPL"

        # Verify it's frozen (immutable)
        with pytest.raises(AttributeError):
            symbol.value = "TSLA"

    @pytest.mark.unit
    def test_identifier_is_frozen_dataclass(self):
        """Test that Identifier is a frozen dataclass."""
        from the_alchemiser.shared.value_objects import Identifier

        # Test generation
        id1 = Identifier.generate()
        id2 = Identifier.generate()

        assert id1.value != id2.value

        # Verify it's frozen (immutable)
        with pytest.raises(AttributeError):
            id1.value = id2.value

    @pytest.mark.unit
    def test_typeddict_types_are_types(self):
        """Test that TypedDict types are properly typed."""
        from the_alchemiser.shared.value_objects import (
            AccountInfo,
            ErrorContext,
            OrderDetails,
            PositionInfo,
        )

        # These should be type objects (classes)
        assert isinstance(AccountInfo, type)
        assert isinstance(ErrorContext, type)
        assert isinstance(OrderDetails, type)
        assert isinstance(PositionInfo, type)

    @pytest.mark.unit
    def test_no_unexpected_exports(self):
        """Test that only expected names are exported via __all__."""
        from the_alchemiser.shared import value_objects

        # Get all public names (not starting with _)
        public_names = {
            name for name in dir(value_objects) if not name.startswith("_")
        }

        # __all__ should be a subset of public names (minus module metadata)
        all_names = set(value_objects.__all__)

        # Verify __all__ names are actually public
        assert all_names.issubset(public_names)

        # Check for common module metadata
        expected_metadata = {"annotations"}  # from __future__ import annotations
        metadata_present = expected_metadata & public_names

        # All __all__ items plus expected metadata should equal public names
        assert all_names | metadata_present == public_names
