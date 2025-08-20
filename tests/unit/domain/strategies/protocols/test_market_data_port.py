"""Unit tests for MarketDataPort protocol."""

from typing import Protocol

import pandas as pd

from the_alchemiser.domain.strategies.protocols.market_data_port import MarketDataPort


# Create a simple implementation for testing protocol compliance
class TestMarketDataImplementation:
    """Test implementation of MarketDataPort for protocol compliance testing."""

    def get_data(
        self, symbol: str, timeframe: str = "1day", period: str = "1y", **kwargs
    ) -> pd.DataFrame:
        return pd.DataFrame({"Close": [100, 101, 102]})

    def get_current_price(self, symbol: str, **kwargs) -> float | None:
        return 150.25

    def get_latest_quote(self, symbol: str, **kwargs) -> tuple[float | None, float | None]:
        return (149.50, 150.00)


class TestMarketDataPort:
    """Test suite for MarketDataPort protocol."""

    def test_protocol_definition(self):
        """Test that MarketDataPort is properly defined as a Protocol."""
        # Check that MarketDataPort is a Protocol
        assert issubclass(MarketDataPort, Protocol)

        # Check required methods are defined
        assert hasattr(MarketDataPort, "get_data")
        assert hasattr(MarketDataPort, "get_current_price")
        assert hasattr(MarketDataPort, "get_latest_quote")

    def test_protocol_compliance_check(self):
        """Test that a proper implementation satisfies the protocol."""
        implementation = TestMarketDataImplementation()

        # This should not raise an error if the implementation is compliant
        assert isinstance(implementation, MarketDataPort)

    def test_protocol_method_signatures(self):
        """Test that protocol methods have the expected signatures."""
        # Test that we can call methods with expected parameters
        implementation = TestMarketDataImplementation()

        # Test get_data method
        result = implementation.get_data("AAPL")
        assert isinstance(result, pd.DataFrame)

        result = implementation.get_data("AAPL", timeframe="1hour", period="6m")
        assert isinstance(result, pd.DataFrame)

        result = implementation.get_data("AAPL", extra_param="test")
        assert isinstance(result, pd.DataFrame)

        # Test get_current_price method
        price = implementation.get_current_price("AAPL")
        assert price is not None

        price = implementation.get_current_price("AAPL", extra_param="test")
        assert price is not None

        # Test get_latest_quote method
        quote = implementation.get_latest_quote("AAPL")
        assert isinstance(quote, tuple)
        assert len(quote) == 2

        quote = implementation.get_latest_quote("AAPL", extra_param="test")
        assert isinstance(quote, tuple)
        assert len(quote) == 2

    def test_incomplete_implementation_fails_protocol_check(self):
        """Test that incomplete implementations don't satisfy the protocol."""

        class IncompleteImplementation:
            def get_data(self, symbol: str, **kwargs) -> pd.DataFrame:
                return pd.DataFrame()

            # Missing get_current_price and get_latest_quote

        implementation = IncompleteImplementation()
        # This should fail the protocol check
        assert not isinstance(implementation, MarketDataPort)

    def test_protocol_return_types(self):
        """Test that protocol methods return expected types."""
        implementation = TestMarketDataImplementation()

        # Test get_data returns DataFrame
        result = implementation.get_data("AAPL")
        assert isinstance(result, pd.DataFrame)

        # Test get_current_price returns float or None
        price = implementation.get_current_price("AAPL")
        assert isinstance(price, float | type(None))

        # Test get_latest_quote returns tuple of float|None
        quote = implementation.get_latest_quote("AAPL")
        assert isinstance(quote, tuple)
        assert len(quote) == 2
        for item in quote:
            assert isinstance(item, float | type(None))

    def test_protocol_with_none_returns(self):
        """Test protocol compliance when methods return None values."""

        class NoneReturningImplementation:
            def get_data(
                self, symbol: str, timeframe: str = "1day", period: str = "1y", **kwargs
            ) -> pd.DataFrame:
                return pd.DataFrame()  # Empty DataFrame

            def get_current_price(self, symbol: str, **kwargs) -> float | None:
                return None  # No price available

            def get_latest_quote(self, symbol: str, **kwargs) -> tuple[float | None, float | None]:
                return (None, None)  # No quote available

        implementation = NoneReturningImplementation()
        assert isinstance(implementation, MarketDataPort)

        # Test that None returns are handled properly
        assert implementation.get_current_price("INVALID") is None
        quote = implementation.get_latest_quote("INVALID")
        assert quote == (None, None)

    def test_protocol_import(self):
        """Test that the protocol can be imported from the correct location."""
        # This test ensures the protocol is properly exported
        from the_alchemiser.domain.strategies.protocols import MarketDataPort as ProtocolsPort
        from the_alchemiser.domain.strategies.protocols.market_data_port import (
            MarketDataPort as ImportedPort,
        )

        # Both imports should refer to the same protocol
        assert ImportedPort is ProtocolsPort
        assert ImportedPort is MarketDataPort
