#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Tests for MarketDataPort protocol.

Verifies protocol structure and that implementations satisfy the contract.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from the_alchemiser.shared.types.market_data import BarModel
from the_alchemiser.shared.types.market_data_port import MarketDataPort
from the_alchemiser.shared.types.quote import QuoteModel
from the_alchemiser.shared.value_objects.symbol import Symbol


@pytest.mark.unit
class TestMarketDataPortProtocol:
    """Test MarketDataPort protocol structure."""

    def test_protocol_is_runtime_checkable(self):
        """Test that MarketDataPort is runtime checkable."""
        # This test verifies @runtime_checkable decorator is present

        class MockPort:
            def get_bars(self, symbol: Symbol, period: str, timeframe: str) -> list[BarModel]:
                return []

            def get_latest_quote(self, symbol: Symbol) -> QuoteModel | None:
                return None

            def get_mid_price(self, symbol: Symbol) -> float | None:
                return None

        mock = MockPort()
        assert isinstance(mock, MarketDataPort)

    def test_protocol_requires_all_methods(self):
        """Test that classes missing methods don't satisfy protocol."""

        class IncompletePort:
            def get_bars(self, symbol: Symbol, period: str, timeframe: str) -> list[BarModel]:
                return []

            # Missing get_latest_quote and get_mid_price

        incomplete = IncompletePort()
        # Should not satisfy protocol (missing 2 methods)
        assert not isinstance(incomplete, MarketDataPort)

    def test_protocol_method_signatures(self):
        """Test that protocol has expected method signatures."""
        # Verify methods exist and are callable
        assert hasattr(MarketDataPort, "get_bars")
        assert hasattr(MarketDataPort, "get_latest_quote")
        assert hasattr(MarketDataPort, "get_mid_price")

        # Verify they're protocol methods (not implemented)

        # Protocol methods should not have implementation
        assert not hasattr(MarketDataPort.get_bars, "__func__")


@pytest.mark.unit
class TestMarketDataPortImplementation:
    """Test a concrete implementation of MarketDataPort."""

    @pytest.fixture
    def mock_port(self):
        """Create a mock implementation of MarketDataPort."""

        class MockMarketDataPort:
            """Mock implementation for testing."""

            def __init__(self):
                self.bars_calls = []
                self.quote_calls = []
                self.mid_price_calls = []

            def get_bars(self, symbol: Symbol, period: str, timeframe: str) -> list[BarModel]:
                """Mock get_bars returning test data."""
                self.bars_calls.append((symbol, period, timeframe))

                # Return mock bar data
                return [
                    BarModel(
                        symbol=str(symbol),
                        timestamp=datetime(2025, 1, 1, tzinfo=UTC),
                        open=100.0,
                        high=105.0,
                        low=99.0,
                        close=103.0,
                        volume=1000000,
                    )
                ]

            def get_latest_quote(self, symbol: Symbol) -> QuoteModel | None:
                """Mock get_latest_quote returning test quote."""
                self.quote_calls.append(symbol)
                return QuoteModel(
                    ts=datetime(2025, 1, 1, tzinfo=UTC),
                    bid=Decimal("100.50"),
                    ask=Decimal("100.55"),
                )

            def get_mid_price(self, symbol: Symbol) -> float | None:
                """Mock get_mid_price returning test mid price."""
                self.mid_price_calls.append(symbol)
                return 100.525

        return MockMarketDataPort()

    def test_get_bars_returns_list(self, mock_port):
        """Test get_bars returns list of BarModel."""
        symbol = Symbol("AAPL")
        bars = mock_port.get_bars(symbol, period="1Y", timeframe="1Day")

        assert isinstance(bars, list)
        assert len(bars) == 1
        assert isinstance(bars[0], BarModel)
        assert bars[0].symbol == "AAPL"

    def test_get_bars_accepts_symbol_object(self, mock_port):
        """Test get_bars accepts Symbol value object."""
        symbol = Symbol("TSLA")
        bars = mock_port.get_bars(symbol, period="6M", timeframe="1Hour")

        # Verify Symbol was passed through
        assert mock_port.bars_calls[0][0] == symbol
        assert mock_port.bars_calls[0][1] == "6M"
        assert mock_port.bars_calls[0][2] == "1Hour"

    def test_get_latest_quote_returns_quote_or_none(self, mock_port):
        """Test get_latest_quote returns QuoteModel or None."""
        symbol = Symbol("AAPL")
        quote = mock_port.get_latest_quote(symbol)

        assert quote is not None
        assert isinstance(quote, QuoteModel)
        assert quote.bid > 0
        assert quote.ask > quote.bid

    def test_get_mid_price_returns_float_or_none(self, mock_port):
        """Test get_mid_price returns float or None."""
        symbol = Symbol("AAPL")
        mid = mock_port.get_mid_price(symbol)

        assert mid is not None
        assert isinstance(mid, float)
        assert mid > 0

    def test_implementation_satisfies_protocol(self, mock_port):
        """Test that mock implementation satisfies MarketDataPort protocol."""
        assert isinstance(mock_port, MarketDataPort)

    def test_empty_bars_list_is_valid(self):
        """Test that returning empty list for get_bars is valid."""

        class EmptyPort:
            def get_bars(self, symbol: Symbol, period: str, timeframe: str) -> list[BarModel]:
                return []  # No data available

            def get_latest_quote(self, symbol: Symbol) -> QuoteModel | None:
                return None

            def get_mid_price(self, symbol: Symbol) -> float | None:
                return None

        port = EmptyPort()
        assert isinstance(port, MarketDataPort)

        bars = port.get_bars(Symbol("AAPL"), "1Y", "1Day")
        assert bars == []  # Empty list is valid response


@pytest.mark.unit
class TestMarketDataPortTypes:
    """Test type annotations and contracts."""

    def test_get_bars_return_type(self):
        """Test get_bars returns list not None."""

        class StrictPort:
            def get_bars(self, symbol: Symbol, period: str, timeframe: str) -> list[BarModel]:
                # Must return list, never None
                return []

            def get_latest_quote(self, symbol: Symbol) -> QuoteModel | None:
                return None

            def get_mid_price(self, symbol: Symbol) -> float | None:
                return None

        port = StrictPort()
        bars = port.get_bars(Symbol("TEST"), "1Y", "1Day")
        assert isinstance(bars, list)  # Always list, never None

    def test_get_latest_quote_can_return_none(self):
        """Test get_latest_quote returning None is valid."""

        class NonePort:
            def get_bars(self, symbol: Symbol, period: str, timeframe: str) -> list[BarModel]:
                return []

            def get_latest_quote(self, symbol: Symbol) -> QuoteModel | None:
                return None  # No quote available

            def get_mid_price(self, symbol: Symbol) -> float | None:
                return None

        port = NonePort()
        quote = port.get_latest_quote(Symbol("TEST"))
        assert quote is None  # None is valid return value

    def test_get_mid_price_can_return_none(self):
        """Test get_mid_price returning None is valid."""

        class NoMidPort:
            def get_bars(self, symbol: Symbol, period: str, timeframe: str) -> list[BarModel]:
                return []

            def get_latest_quote(self, symbol: Symbol) -> QuoteModel | None:
                return None

            def get_mid_price(self, symbol: Symbol) -> float | None:
                return None  # No mid price available

        port = NoMidPort()
        mid = port.get_mid_price(Symbol("TEST"))
        assert mid is None  # None is valid return value
