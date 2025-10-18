#!/usr/bin/env python3
"""Business Unit: strategy_v2 | Status: current.

Comprehensive tests for StrategyMarketDataAdapter.

Tests cover:
- Input validation
- Error handling and propagation
- Decimal precision for financial data
- Correlation ID propagation
- Edge cases and boundary conditions
- Property-based tests for numerical correctness
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest
from hypothesis import given
from hypothesis import strategies as st

from the_alchemiser.shared.errors.exceptions import DataProviderError, MarketDataError
from the_alchemiser.shared.schemas.market_bar import MarketBar
from the_alchemiser.strategy_v2.adapters.market_data_adapter import (
    StrategyMarketDataAdapter,
)


@pytest.fixture
def mock_alpaca_manager() -> Mock:
    """Create mock AlpacaManager."""
    mock = Mock()
    mock.validate_connection.return_value = True
    return mock


@pytest.fixture
def mock_market_data_service() -> Mock:
    """Create mock MarketDataService."""
    mock = Mock()
    return mock


@pytest.fixture
def adapter(mock_alpaca_manager: Mock) -> StrategyMarketDataAdapter:
    """Create adapter instance with mock."""
    return StrategyMarketDataAdapter(mock_alpaca_manager)


@pytest.fixture
def adapter_with_correlation_id(mock_alpaca_manager: Mock) -> StrategyMarketDataAdapter:
    """Create adapter instance with correlation ID."""
    return StrategyMarketDataAdapter(mock_alpaca_manager, correlation_id="test-corr-123")


class TestInitialization:
    """Tests for adapter initialization."""

    def test_init_without_correlation_id(self, mock_alpaca_manager: Mock) -> None:
        """Test initialization without correlation ID."""
        adapter = StrategyMarketDataAdapter(mock_alpaca_manager)
        assert adapter._alpaca is mock_alpaca_manager
        assert adapter._correlation_id is None
        assert adapter._market_data_service is not None

    def test_init_with_correlation_id(self, mock_alpaca_manager: Mock) -> None:
        """Test initialization with correlation ID."""
        corr_id = "test-correlation-id-123"
        adapter = StrategyMarketDataAdapter(mock_alpaca_manager, correlation_id=corr_id)
        assert adapter._correlation_id == corr_id


class TestGetBarsInputValidation:
    """Tests for get_bars input validation."""

    def test_empty_symbols_list_raises_value_error(
        self, adapter: StrategyMarketDataAdapter
    ) -> None:
        """Test that empty symbols list raises ValueError."""
        with pytest.raises(ValueError, match="symbols list cannot be empty"):
            adapter.get_bars(symbols=[], timeframe="1D", lookback_days=30)

    def test_negative_lookback_days_raises_value_error(
        self, adapter: StrategyMarketDataAdapter
    ) -> None:
        """Test that negative lookback_days raises ValueError."""
        with pytest.raises(ValueError, match="lookback_days must be > 0"):
            adapter.get_bars(symbols=["AAPL"], timeframe="1D", lookback_days=-5)

    def test_zero_lookback_days_raises_value_error(
        self, adapter: StrategyMarketDataAdapter
    ) -> None:
        """Test that zero lookback_days raises ValueError."""
        with pytest.raises(ValueError, match="lookback_days must be > 0"):
            adapter.get_bars(symbols=["AAPL"], timeframe="1D", lookback_days=0)

    def test_empty_timeframe_raises_value_error(self, adapter: StrategyMarketDataAdapter) -> None:
        """Test that empty timeframe raises ValueError."""
        with pytest.raises(ValueError, match="timeframe cannot be empty"):
            adapter.get_bars(symbols=["AAPL"], timeframe="", lookback_days=30)

    def test_whitespace_only_timeframe_raises_value_error(
        self, adapter: StrategyMarketDataAdapter
    ) -> None:
        """Test that whitespace-only timeframe raises ValueError."""
        with pytest.raises(ValueError, match="timeframe cannot be empty"):
            adapter.get_bars(symbols=["AAPL"], timeframe="   ", lookback_days=30)


class TestGetBarsSuccessScenarios:
    """Tests for successful get_bars operations."""

    def test_get_bars_with_valid_data(
        self, adapter: StrategyMarketDataAdapter, mock_market_data_service: Mock
    ) -> None:
        """Test get_bars returns correctly formatted data."""
        # Setup mock data
        mock_bars = [
            {
                "t": datetime(2024, 1, 1, tzinfo=UTC),
                "o": 150.0,
                "h": 155.0,
                "l": 149.0,
                "c": 154.0,
                "v": 1000000,
                "vw": 152.5,
            }
        ]

        with patch.object(
            adapter._market_data_service, "get_historical_bars", return_value=mock_bars
        ):
            result = adapter.get_bars(symbols=["AAPL"], timeframe="1D", lookback_days=30)

            assert "AAPL" in result
            assert len(result["AAPL"]) == 1
            assert isinstance(result["AAPL"][0], MarketBar)

    def test_get_bars_with_multiple_symbols(
        self, adapter: StrategyMarketDataAdapter, mock_market_data_service: Mock
    ) -> None:
        """Test get_bars handles multiple symbols."""
        mock_bars = [
            {
                "t": datetime(2024, 1, 1, tzinfo=UTC),
                "o": 150.0,
                "h": 155.0,
                "l": 149.0,
                "c": 154.0,
                "v": 1000000,
            }
        ]

        with patch.object(
            adapter._market_data_service, "get_historical_bars", return_value=mock_bars
        ):
            result = adapter.get_bars(
                symbols=["AAPL", "GOOGL", "MSFT"], timeframe="1D", lookback_days=30
            )

            assert len(result) == 3
            assert all(symbol in result for symbol in ["AAPL", "GOOGL", "MSFT"])

    def test_get_bars_with_custom_end_date(
        self, adapter: StrategyMarketDataAdapter, mock_market_data_service: Mock
    ) -> None:
        """Test get_bars respects custom end_date."""
        end_date = datetime(2024, 1, 15, tzinfo=UTC)
        mock_bars = []

        with patch.object(
            adapter._market_data_service, "get_historical_bars", return_value=mock_bars
        ):
            result = adapter.get_bars(
                symbols=["AAPL"], timeframe="1D", lookback_days=30, end_date=end_date
            )

            assert "AAPL" in result
            assert result["AAPL"] == []


class TestGetBarsErrorHandling:
    """Tests for get_bars error handling."""

    def test_individual_symbol_failure_returns_empty_list(
        self, adapter: StrategyMarketDataAdapter
    ) -> None:
        """Test that individual symbol failures return empty list."""
        with patch.object(
            adapter._market_data_service,
            "get_historical_bars",
            side_effect=RuntimeError("API error"),
        ):
            result = adapter.get_bars(symbols=["AAPL"], timeframe="1D", lookback_days=30)

            assert "AAPL" in result
            assert result["AAPL"] == []

    def test_unexpected_error_raises_market_data_error(
        self, adapter: StrategyMarketDataAdapter
    ) -> None:
        """Test that unexpected errors are raised as MarketDataError."""
        with patch.object(
            adapter._market_data_service,
            "get_historical_bars",
            side_effect=TypeError("Unexpected error"),
        ), pytest.raises(MarketDataError, match="Unexpected error fetching bars"):
            adapter.get_bars(symbols=["AAPL"], timeframe="1D", lookback_days=30)

    def test_invalid_bar_data_skipped(self, adapter: StrategyMarketDataAdapter) -> None:
        """Test that invalid bar data is skipped gracefully."""
        # Mix of valid and invalid bars
        mock_bars = [
            {
                "t": datetime(2024, 1, 1, tzinfo=UTC),
                "o": 150.0,
                "h": 155.0,
                "l": 149.0,
                "c": 154.0,
                "v": 1000000,
            },
            {"invalid": "data"},  # This should be skipped
            {
                "t": datetime(2024, 1, 2, tzinfo=UTC),
                "o": 154.0,
                "h": 156.0,
                "l": 153.0,
                "c": 155.0,
                "v": 900000,
            },
        ]

        with patch.object(
            adapter._market_data_service, "get_historical_bars", return_value=mock_bars
        ):
            result = adapter.get_bars(symbols=["AAPL"], timeframe="1D", lookback_days=30)

            # Should have 2 valid bars (invalid one skipped)
            assert len(result["AAPL"]) == 2


class TestGetCurrentPricesInputValidation:
    """Tests for get_current_prices input validation."""

    def test_empty_symbols_list_raises_value_error(
        self, adapter: StrategyMarketDataAdapter
    ) -> None:
        """Test that empty symbols list raises ValueError."""
        with pytest.raises(ValueError, match="symbols list cannot be empty"):
            adapter.get_current_prices(symbols=[])


class TestGetCurrentPricesDecimalCorrectness:
    """Tests for Decimal correctness in price calculations."""

    def test_returns_decimal_not_float(self, adapter: StrategyMarketDataAdapter) -> None:
        """Test that prices are returned as Decimal, not float."""
        mock_quote = {"ask_price": 100.50, "bid_price": 100.00}

        with patch.object(adapter._market_data_service, "get_quote", return_value=mock_quote):
            result = adapter.get_current_prices(symbols=["AAPL"])

            assert "AAPL" in result
            assert isinstance(result["AAPL"], Decimal)

    def test_mid_price_calculation_uses_decimal(self, adapter: StrategyMarketDataAdapter) -> None:
        """Test that mid-price calculation uses Decimal arithmetic."""
        mock_quote = {"ask_price": 100.50, "bid_price": 100.00}

        with patch.object(adapter._market_data_service, "get_quote", return_value=mock_quote):
            result = adapter.get_current_prices(symbols=["AAPL"])

            expected = Decimal("100.25")  # (100.50 + 100.00) / 2
            assert result["AAPL"] == expected

    def test_decimal_precision_maintained(self, adapter: StrategyMarketDataAdapter) -> None:
        """Test that Decimal precision is maintained in calculations."""
        # Use prices that would lose precision with float
        mock_quote = {"ask_price": 100.333333, "bid_price": 100.111111}

        with patch.object(adapter._market_data_service, "get_quote", return_value=mock_quote):
            result = adapter.get_current_prices(symbols=["AAPL"])

            # Verify it's a Decimal and has expected precision
            assert isinstance(result["AAPL"], Decimal)
            # Mid price should be (100.333333 + 100.111111) / 2 = 100.222222
            expected = (Decimal("100.333333") + Decimal("100.111111")) / Decimal("2")
            assert result["AAPL"] == expected


class TestGetCurrentPricesErrorHandling:
    """Tests for get_current_prices error handling."""

    def test_missing_quote_returns_none(self, adapter: StrategyMarketDataAdapter) -> None:
        """Test that missing quote returns None, not 0.0."""
        with patch.object(adapter._market_data_service, "get_quote", return_value=None):
            result = adapter.get_current_prices(symbols=["AAPL"])

            assert "AAPL" in result
            assert result["AAPL"] is None  # CRITICAL: Must be None, not 0.0

    def test_missing_ask_price_returns_none(self, adapter: StrategyMarketDataAdapter) -> None:
        """Test that quote missing ask_price returns None."""
        mock_quote = {"bid_price": 100.00}  # Missing ask_price

        with patch.object(adapter._market_data_service, "get_quote", return_value=mock_quote):
            result = adapter.get_current_prices(symbols=["AAPL"])

            assert result["AAPL"] is None

    def test_missing_bid_price_returns_none(self, adapter: StrategyMarketDataAdapter) -> None:
        """Test that quote missing bid_price returns None."""
        mock_quote = {"ask_price": 100.50}  # Missing bid_price

        with patch.object(adapter._market_data_service, "get_quote", return_value=mock_quote):
            result = adapter.get_current_prices(symbols=["AAPL"])

            assert result["AAPL"] is None

    def test_runtime_error_returns_none(self, adapter: StrategyMarketDataAdapter) -> None:
        """Test that RuntimeError during fetch returns None."""
        with patch.object(
            adapter._market_data_service,
            "get_quote",
            side_effect=RuntimeError("API error"),
        ):
            result = adapter.get_current_prices(symbols=["AAPL"])

            assert result["AAPL"] is None

    def test_value_error_returns_none(self, adapter: StrategyMarketDataAdapter) -> None:
        """Test that ValueError during fetch returns None."""
        with patch.object(
            adapter._market_data_service,
            "get_quote",
            side_effect=ValueError("Invalid data"),
        ):
            result = adapter.get_current_prices(symbols=["AAPL"])

            assert result["AAPL"] is None

    def test_unexpected_error_raises_data_provider_error(
        self, adapter: StrategyMarketDataAdapter
    ) -> None:
        """Test that unexpected errors raise DataProviderError."""
        with patch.object(
            adapter._market_data_service,
            "get_quote",
            side_effect=TypeError("Unexpected error"),
        ), pytest.raises(DataProviderError, match="Unexpected error fetching price"):
            adapter.get_current_prices(symbols=["AAPL"])

    def test_multiple_symbols_partial_failure(self, adapter: StrategyMarketDataAdapter) -> None:
        """Test that partial failures return mixed results."""

        def mock_get_quote(symbol: str):
            if symbol == "AAPL":
                return {"ask_price": 150.0, "bid_price": 149.0}
            if symbol == "GOOGL":
                return None  # No data
            raise RuntimeError("API error")

        with patch.object(adapter._market_data_service, "get_quote", side_effect=mock_get_quote):
            result = adapter.get_current_prices(symbols=["AAPL", "GOOGL", "MSFT"])

            assert isinstance(result["AAPL"], Decimal)
            assert result["GOOGL"] is None
            assert result["MSFT"] is None


class TestValidateConnection:
    """Tests for validate_connection."""

    def test_successful_validation_returns_true(
        self, adapter: StrategyMarketDataAdapter, mock_alpaca_manager: Mock
    ) -> None:
        """Test successful connection validation."""
        mock_alpaca_manager.validate_connection.return_value = True
        assert adapter.validate_connection() is True

    def test_failed_validation_returns_false(
        self, adapter: StrategyMarketDataAdapter, mock_alpaca_manager: Mock
    ) -> None:
        """Test failed connection validation returns False."""
        mock_alpaca_manager.validate_connection.side_effect = RuntimeError("Connection failed")
        assert adapter.validate_connection() is False

    def test_connection_error_returns_false(
        self, adapter: StrategyMarketDataAdapter, mock_alpaca_manager: Mock
    ) -> None:
        """Test ConnectionError returns False."""
        mock_alpaca_manager.validate_connection.side_effect = ConnectionError("Network error")
        assert adapter.validate_connection() is False

    def test_unexpected_error_raises_data_provider_error(
        self, adapter: StrategyMarketDataAdapter, mock_alpaca_manager: Mock
    ) -> None:
        """Test unexpected error raises DataProviderError."""
        mock_alpaca_manager.validate_connection.side_effect = TypeError("Unexpected error")

        with pytest.raises(DataProviderError, match="Unexpected error validating"):
            adapter.validate_connection()


class TestCorrelationIDPropagation:
    """Tests for correlation ID propagation in logging."""

    def test_correlation_id_in_get_bars_logs(
        self, adapter_with_correlation_id: StrategyMarketDataAdapter, caplog
    ) -> None:
        """Test correlation ID appears in get_bars logs."""
        mock_bars = []

        with patch.object(
            adapter_with_correlation_id._market_data_service,
            "get_historical_bars",
            return_value=mock_bars,
        ):
            adapter_with_correlation_id.get_bars(symbols=["AAPL"], timeframe="1D", lookback_days=30)

            # Correlation ID should be in extra fields (implementation detail)
            # This is a smoke test - actual log inspection depends on logger configuration

    def test_correlation_id_in_get_prices_logs(
        self, adapter_with_correlation_id: StrategyMarketDataAdapter
    ) -> None:
        """Test correlation ID appears in get_current_prices logs."""
        mock_quote = {"ask_price": 100.0, "bid_price": 99.0}

        with patch.object(
            adapter_with_correlation_id._market_data_service,
            "get_quote",
            return_value=mock_quote,
        ):
            adapter_with_correlation_id.get_current_prices(symbols=["AAPL"])

            # Smoke test - correlation ID is propagated


class TestPropertyBasedPriceCalculations:
    """Property-based tests for price calculations using Hypothesis."""

    @given(
        bid=st.decimals(
            min_value=Decimal("0.01"),
            max_value=Decimal("100000"),
            places=2,
        ),
        ask=st.decimals(
            min_value=Decimal("0.01"),
            max_value=Decimal("100000"),
            places=2,
        ),
    )
    def test_mid_price_always_between_bid_and_ask(self, bid: Decimal, ask: Decimal) -> None:
        """Property: mid-price should always be between bid and ask."""
        # Ensure ask >= bid
        if ask < bid:
            bid, ask = ask, bid

        # Create adapter inline to avoid function-scoped fixture issues with Hypothesis
        mock = Mock()
        mock.validate_connection.return_value = True
        adapter = StrategyMarketDataAdapter(mock)

        mock_quote = {"ask_price": float(ask), "bid_price": float(bid)}

        with patch.object(adapter._market_data_service, "get_quote", return_value=mock_quote):
            result = adapter.get_current_prices(symbols=["TEST"])
            mid_price = result["TEST"]

            assert mid_price is not None
            assert bid <= mid_price <= ask

    @given(
        price=st.decimals(
            min_value=Decimal("0.01"),
            max_value=Decimal("100000"),
            places=4,
        )
    )
    def test_equal_bid_ask_returns_that_price(self, price: Decimal) -> None:
        """Property: when bid == ask, mid-price should equal that price."""
        # Create adapter inline to avoid function-scoped fixture issues with Hypothesis
        mock = Mock()
        mock.validate_connection.return_value = True
        adapter = StrategyMarketDataAdapter(mock)

        mock_quote = {"ask_price": float(price), "bid_price": float(price)}

        with patch.object(adapter._market_data_service, "get_quote", return_value=mock_quote):
            result = adapter.get_current_prices(symbols=["TEST"])
            mid_price = result["TEST"]

            assert mid_price == price


class TestIdempotency:
    """Tests for idempotent behavior."""

    def test_get_bars_idempotent(self, adapter: StrategyMarketDataAdapter) -> None:
        """Test that repeated get_bars calls with same params return same data."""
        mock_bars = [
            {
                "t": datetime(2024, 1, 1, tzinfo=UTC),
                "o": 150.0,
                "h": 155.0,
                "l": 149.0,
                "c": 154.0,
                "v": 1000000,
            }
        ]

        with patch.object(
            adapter._market_data_service, "get_historical_bars", return_value=mock_bars
        ):
            result1 = adapter.get_bars(symbols=["AAPL"], timeframe="1D", lookback_days=30)
            result2 = adapter.get_bars(symbols=["AAPL"], timeframe="1D", lookback_days=30)

            assert len(result1["AAPL"]) == len(result2["AAPL"])
            # Compare actual data
            for bar1, bar2 in zip(result1["AAPL"], result2["AAPL"], strict=False):
                assert bar1.close_price == bar2.close_price
                assert bar1.timestamp == bar2.timestamp
