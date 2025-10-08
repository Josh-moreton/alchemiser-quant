#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Tests for shared.schemas.market_data module.

Validates correctness of Result-based schemas for market data operations.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from the_alchemiser.shared.schemas.market_data import (
    MarketStatusResult,
    MultiSymbolQuotesResult,
    PriceHistoryResult,
    PriceResult,
    SpreadAnalysisResult,
)


class TestPriceResult:
    """Tests for PriceResult schema."""

    def test_price_result_is_frozen(self) -> None:
        """Test that PriceResult is immutable."""
        result = PriceResult(success=True, symbol="AAPL", price=Decimal("150.0"))
        with pytest.raises(Exception):  # Pydantic raises ValidationError on frozen
            result.price = Decimal("160.0")  # type: ignore

    def test_price_result_success(self) -> None:
        """Test successful price result."""
        result = PriceResult(success=True, symbol="AAPL", price=Decimal("150.50"))
        assert result.success is True
        assert result.is_success is True
        assert result.symbol == "AAPL"
        assert result.price == Decimal("150.50")
        assert result.error is None

    def test_price_result_failure(self) -> None:
        """Test failed price result."""
        result = PriceResult(success=False, error="Market closed")
        assert result.success is False
        assert result.is_success is False
        assert result.symbol is None
        assert result.price is None
        assert result.error == "Market closed"

    def test_price_result_validates_assignment(self) -> None:
        """Test that validate_assignment is enabled."""
        result = PriceResult(success=True, symbol="AAPL", price=Decimal("150.0"))
        # Should not allow reassignment due to frozen config
        with pytest.raises(Exception):
            result.symbol = "GOOGL"  # type: ignore

    def test_price_result_strict_mode(self) -> None:
        """Test that strict mode validates types."""
        # Strict mode should reject wrong types
        with pytest.raises(Exception):
            PriceResult(success=True, symbol="AAPL", price="150.0")  # type: ignore


class TestPriceHistoryResult:
    """Tests for PriceHistoryResult schema."""

    def test_price_history_result_success(self) -> None:
        """Test successful price history result."""
        data = [
            {"timestamp": "2024-01-01", "price": "150.0"},
            {"timestamp": "2024-01-02", "price": "151.0"},
        ]
        result = PriceHistoryResult(
            success=True,
            symbol="AAPL",
            timeframe="1Day",
            limit=2,
            data=data,
        )
        assert result.success is True
        assert result.symbol == "AAPL"
        assert result.timeframe == "1Day"
        assert result.limit == 2
        assert result.data == data
        assert result.error is None

    def test_price_history_result_failure(self) -> None:
        """Test failed price history result."""
        result = PriceHistoryResult(success=False, error="Invalid timeframe")
        assert result.success is False
        assert result.symbol is None
        assert result.timeframe is None
        assert result.limit is None
        assert result.data is None
        assert result.error == "Invalid timeframe"

    def test_price_history_result_is_frozen(self) -> None:
        """Test that PriceHistoryResult is immutable."""
        result = PriceHistoryResult(success=True, symbol="AAPL", timeframe="1Day")
        with pytest.raises(Exception):
            result.timeframe = "1Hour"  # type: ignore


class TestSpreadAnalysisResult:
    """Tests for SpreadAnalysisResult schema."""

    def test_spread_analysis_result_success(self) -> None:
        """Test successful spread analysis result."""
        analysis = {
            "bid": "149.50",
            "ask": "150.00",
            "spread": "0.50",
            "spread_bps": 33,
        }
        result = SpreadAnalysisResult(
            success=True,
            symbol="AAPL",
            spread_analysis=analysis,
        )
        assert result.success is True
        assert result.symbol == "AAPL"
        assert result.spread_analysis == analysis
        assert result.error is None

    def test_spread_analysis_result_failure(self) -> None:
        """Test failed spread analysis result."""
        result = SpreadAnalysisResult(success=False, error="No quote data available")
        assert result.success is False
        assert result.symbol is None
        assert result.spread_analysis is None
        assert result.error == "No quote data available"

    def test_spread_analysis_result_is_frozen(self) -> None:
        """Test that SpreadAnalysisResult is immutable."""
        result = SpreadAnalysisResult(success=True, symbol="AAPL")
        with pytest.raises(Exception):
            result.symbol = "GOOGL"  # type: ignore


class TestMarketStatusResult:
    """Tests for MarketStatusResult schema."""

    def test_market_status_result_open(self) -> None:
        """Test market open status."""
        result = MarketStatusResult(success=True, market_open=True)
        assert result.success is True
        assert result.market_open is True
        assert result.error is None

    def test_market_status_result_closed(self) -> None:
        """Test market closed status."""
        result = MarketStatusResult(success=True, market_open=False)
        assert result.success is True
        assert result.market_open is False
        assert result.error is None

    def test_market_status_result_failure(self) -> None:
        """Test failed market status result."""
        result = MarketStatusResult(success=False, error="API unavailable")
        assert result.success is False
        assert result.market_open is None
        assert result.error == "API unavailable"

    def test_market_status_result_is_frozen(self) -> None:
        """Test that MarketStatusResult is immutable."""
        result = MarketStatusResult(success=True, market_open=True)
        with pytest.raises(Exception):
            result.market_open = False  # type: ignore


class TestMultiSymbolQuotesResult:
    """Tests for MultiSymbolQuotesResult schema."""

    def test_multi_symbol_quotes_result_success(self) -> None:
        """Test successful multi-symbol quotes result."""
        quotes = {
            "AAPL": Decimal("150.00"),
            "GOOGL": Decimal("2800.00"),
            "MSFT": Decimal("380.00"),
        }
        symbols = ["AAPL", "GOOGL", "MSFT"]
        result = MultiSymbolQuotesResult(
            success=True,
            quotes=quotes,
            symbols=symbols,
        )
        assert result.success is True
        assert result.quotes == quotes
        assert result.symbols == symbols
        assert result.error is None

    def test_multi_symbol_quotes_result_failure(self) -> None:
        """Test failed multi-symbol quotes result."""
        result = MultiSymbolQuotesResult(success=False, error="Rate limit exceeded")
        assert result.success is False
        assert result.quotes is None
        assert result.symbols is None
        assert result.error == "Rate limit exceeded"

    def test_multi_symbol_quotes_result_is_frozen(self) -> None:
        """Test that MultiSymbolQuotesResult is immutable."""
        quotes = {"AAPL": Decimal("150.00")}
        result = MultiSymbolQuotesResult(success=True, quotes=quotes)
        with pytest.raises(Exception):
            result.quotes = {}  # type: ignore

    def test_multi_symbol_quotes_result_decimal_preservation(self) -> None:
        """Test that Decimal precision is preserved."""
        quotes = {
            "AAPL": Decimal("150.123456"),
            "GOOGL": Decimal("2800.987654"),
        }
        result = MultiSymbolQuotesResult(success=True, quotes=quotes)
        assert result.quotes is not None
        assert result.quotes["AAPL"] == Decimal("150.123456")
        assert result.quotes["GOOGL"] == Decimal("2800.987654")


class TestBackwardCompatibility:
    """Tests for backward compatibility aliases."""

    def test_price_dto_alias(self) -> None:
        """Test PriceDTO alias exists and works."""
        from the_alchemiser.shared.schemas.market_data import PriceDTO

        result = PriceDTO(success=True, symbol="AAPL", price=Decimal("150.0"))
        assert isinstance(result, PriceResult)

    def test_price_history_dto_alias(self) -> None:
        """Test PriceHistoryDTO alias exists and works."""
        from the_alchemiser.shared.schemas.market_data import PriceHistoryDTO

        result = PriceHistoryDTO(success=True, symbol="AAPL")
        assert isinstance(result, PriceHistoryResult)

    def test_spread_analysis_dto_alias(self) -> None:
        """Test SpreadAnalysisDTO alias exists and works."""
        from the_alchemiser.shared.schemas.market_data import SpreadAnalysisDTO

        result = SpreadAnalysisDTO(success=True, symbol="AAPL")
        assert isinstance(result, SpreadAnalysisResult)

    def test_market_status_dto_alias(self) -> None:
        """Test MarketStatusDTO alias exists and works."""
        from the_alchemiser.shared.schemas.market_data import MarketStatusDTO

        result = MarketStatusDTO(success=True, market_open=True)
        assert isinstance(result, MarketStatusResult)

    def test_multi_symbol_quotes_dto_alias(self) -> None:
        """Test MultiSymbolQuotesDTO alias exists and works."""
        from the_alchemiser.shared.schemas.market_data import MultiSymbolQuotesDTO

        result = MultiSymbolQuotesDTO(success=True)
        assert isinstance(result, MultiSymbolQuotesResult)


class TestStrictValidation:
    """Tests demonstrating strict validation behavior."""

    def test_strict_mode_validates_types(self) -> None:
        """Test that strict mode validates field types."""
        # Strict mode validates types at runtime
        result = PriceResult(
            success=True,
            symbol="AAPL",
            price=Decimal("150.0"),
        )
        assert result.price == Decimal("150.0")

    def test_frozen_prevents_modification(self) -> None:
        """Test that frozen config prevents all field modifications."""
        result = PriceResult(success=True, symbol="AAPL", price=Decimal("150.0"))
        with pytest.raises(Exception):
            result.success = False  # type: ignore
        with pytest.raises(Exception):
            result.symbol = "GOOGL"  # type: ignore
        with pytest.raises(Exception):
            result.price = Decimal("200.0")  # type: ignore
        with pytest.raises(Exception):
            result.error = "Some error"  # type: ignore
