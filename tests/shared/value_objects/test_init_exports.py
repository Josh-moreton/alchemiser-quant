"""Business Unit: shared | Status: current.

Test suite for value_objects package __init__.py exports.

Validates that all expected types are properly exported and importable,
preventing regression of missing exports (like the Identifier issue).
"""

from __future__ import annotations


class TestValueObjectsExports:
    """Test that value_objects package exports all expected types."""

    def test_all_exports_are_importable(self):
        """Test that all items in __all__ can be imported."""
        from the_alchemiser.shared import value_objects

        # Get the __all__ list
        all_exports = getattr(value_objects, "__all__", [])

        # Verify __all__ exists and is not empty
        assert all_exports, "value_objects.__all__ should not be empty"

        # Verify each item in __all__ is actually accessible
        for export_name in all_exports:
            assert hasattr(value_objects, export_name), (
                f"'{export_name}' is in __all__ but not accessible from value_objects"
            )

    def test_expected_types_are_exported(self):
        """Test that specific expected types are in __all__."""
        from the_alchemiser.shared.value_objects import __all__

        # Value objects (immutable)
        assert "Symbol" in __all__, "Symbol should be exported"
        assert "Identifier" in __all__, "Identifier should be exported"

        # Account types
        assert "AccountInfo" in __all__, "AccountInfo should be exported"
        assert "EnrichedAccountInfo" in __all__, "EnrichedAccountInfo should be exported"

        # Position types
        assert "PositionInfo" in __all__, "PositionInfo should be exported"
        assert "PositionsDict" in __all__, "PositionsDict should be exported"
        assert "PortfolioSnapshot" in __all__, "PortfolioSnapshot should be exported"

        # Order types
        assert "OrderDetails" in __all__, "OrderDetails should be exported"
        assert "OrderStatusLiteral" in __all__, "OrderStatusLiteral should be exported"

        # Strategy types
        assert "StrategySignal" in __all__, "StrategySignal should be exported"
        assert "StrategySignalBase" in __all__, "StrategySignalBase should be exported"
        assert "StrategyPnLSummary" in __all__, "StrategyPnLSummary should be exported"

        # Market data types
        assert "MarketDataPoint" in __all__, "MarketDataPoint should be exported"
        assert "IndicatorData" in __all__, "IndicatorData should be exported"
        assert "PriceData" in __all__, "PriceData should be exported"
        assert "QuoteData" in __all__, "QuoteData should be exported"

        # Analytics types
        assert "TradeAnalysis" in __all__, "TradeAnalysis should be exported"

        # Error types
        assert "ErrorContext" in __all__, "ErrorContext should be exported"

        # KLM types
        assert "KLMDecision" in __all__, "KLMDecision should be exported"

        # P&L types
        assert "PortfolioHistoryData" in __all__, "PortfolioHistoryData should be exported"

    def test_symbol_import_works(self):
        """Test Symbol can be imported and instantiated."""
        from the_alchemiser.shared.value_objects import Symbol

        symbol = Symbol("AAPL")
        assert symbol.value == "AAPL"
        assert str(symbol) == "AAPL"

    def test_identifier_import_works(self):
        """Test Identifier can be imported and instantiated."""
        from the_alchemiser.shared.value_objects import Identifier

        # Generate a new identifier
        identifier = Identifier.generate()
        assert identifier.value is not None

        # Create from string
        test_uuid = "12345678-1234-5678-1234-567812345678"
        identifier2 = Identifier.from_string(test_uuid)
        assert str(identifier2.value) == test_uuid

    def test_account_info_import_works(self):
        """Test AccountInfo TypedDict can be imported."""
        from the_alchemiser.shared.value_objects import AccountInfo

        # TypedDict can be used as a type hint
        account: AccountInfo = {
            "account_id": "test123",
            "equity": "10000.00",
            "cash": "5000.00",
            "buying_power": "10000.00",
            "day_trades_remaining": 3,
            "portfolio_value": "10000.00",
            "last_equity": "9500.00",
            "daytrading_buying_power": "10000.00",
            "regt_buying_power": "10000.00",
            "status": "ACTIVE",
        }

        assert account["account_id"] == "test123"
        assert account["status"] == "ACTIVE"

    def test_no_unexpected_exports(self):
        """Test that __all__ doesn't contain unexpected items."""
        from the_alchemiser.shared.value_objects import __all__

        # Define expected exports (should match the actual __all__ list)
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

        actual_exports = set(__all__)

        # Check for unexpected exports
        unexpected = actual_exports - expected_exports
        assert not unexpected, f"Unexpected exports found: {unexpected}"

        # Check for missing exports
        missing = expected_exports - actual_exports
        assert not missing, f"Expected exports missing: {missing}"

    def test_all_list_is_sorted(self):
        """Test that __all__ list is alphabetically sorted for maintainability."""
        from the_alchemiser.shared.value_objects import __all__

        sorted_all = sorted(__all__)
        assert __all__ == sorted_all, (
            f"__all__ should be sorted alphabetically.\nExpected: {sorted_all}\nActual: {__all__}"
        )


class TestValueObjectsUsagePatterns:
    """Test common usage patterns for value objects."""

    def test_error_handler_can_import_identifier(self):
        """Test the usage pattern from error_handler.py works."""
        # This was the original bug - Identifier was used but not exported
        from the_alchemiser.shared.value_objects import Identifier

        # Should be able to use it
        correlation_id = Identifier.generate()
        assert correlation_id is not None
        assert hasattr(correlation_id, "value")

    def test_multiple_imports_work(self):
        """Test importing multiple types at once."""
        from the_alchemiser.shared.value_objects import (
            AccountInfo,
            Identifier,
            PositionInfo,
            Symbol,
        )

        # All should be accessible
        assert AccountInfo is not None
        assert Identifier is not None
        assert PositionInfo is not None
        assert Symbol is not None

    def test_wildcard_import_matches_all(self):
        """Test that wildcard import respects __all__."""
        import the_alchemiser.shared.value_objects as vo_module

        # Get what would be imported with wildcard
        all_exports = vo_module.__all__

        # Verify each is accessible
        for export_name in all_exports:
            assert hasattr(vo_module, export_name), (
                f"Export '{export_name}' in __all__ but not accessible"
            )
