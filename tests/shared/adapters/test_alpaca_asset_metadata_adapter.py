"""Business Unit: shared | Status: current.

Test suite for AlpacaAssetMetadataAdapter.

Tests adapter implementation for asset metadata retrieval from AlpacaManager.
"""

from unittest.mock import Mock

import pytest

from the_alchemiser.shared.adapters.alpaca_asset_metadata_adapter import (
    FRACTIONAL_SIGNIFICANCE_THRESHOLD,
    AlpacaAssetMetadataAdapter,
)
from the_alchemiser.shared.errors.exceptions import DataProviderError, RateLimitError
from the_alchemiser.shared.value_objects.symbol import Symbol


class TestAlpacaAssetMetadataAdapter:
    """Test suite for AlpacaAssetMetadataAdapter."""

    @pytest.fixture
    def mock_alpaca_manager(self):
        """Create mock AlpacaManager."""
        mock = Mock()
        return mock

    @pytest.fixture
    def adapter(self, mock_alpaca_manager):
        """Create adapter with mock AlpacaManager."""
        return AlpacaAssetMetadataAdapter(mock_alpaca_manager)

    def test_is_fractionable_true(self, adapter, mock_alpaca_manager):
        """Test is_fractionable returns True for fractionable asset."""
        mock_alpaca_manager.is_fractionable.return_value = True
        symbol = Symbol("AAPL")

        result = adapter.is_fractionable(symbol)

        assert result is True
        mock_alpaca_manager.is_fractionable.assert_called_once_with("AAPL")

    def test_is_fractionable_false(self, adapter, mock_alpaca_manager):
        """Test is_fractionable returns False for non-fractionable asset."""
        mock_alpaca_manager.is_fractionable.return_value = False
        symbol = Symbol("MSFT")

        result = adapter.is_fractionable(symbol)

        assert result is False
        mock_alpaca_manager.is_fractionable.assert_called_once_with("MSFT")

    def test_get_asset_class_stock(self, adapter, mock_alpaca_manager):
        """Test get_asset_class returns stock class."""
        mock_asset_info = Mock()
        mock_asset_info.asset_class = "us_equity"
        mock_alpaca_manager.get_asset_info.return_value = mock_asset_info
        symbol = Symbol("AAPL")

        result = adapter.get_asset_class(symbol)

        assert result == "us_equity"
        mock_alpaca_manager.get_asset_info.assert_called_once_with("AAPL")

    def test_get_asset_class_etf(self, adapter, mock_alpaca_manager):
        """Test get_asset_class returns ETF class."""
        mock_asset_info = Mock()
        mock_asset_info.asset_class = "us_equity"
        mock_alpaca_manager.get_asset_info.return_value = mock_asset_info
        symbol = Symbol("SPY")

        result = adapter.get_asset_class(symbol)

        assert result == "us_equity"
        mock_alpaca_manager.get_asset_info.assert_called_once_with("SPY")

    def test_get_asset_class_crypto(self, adapter, mock_alpaca_manager):
        """Test get_asset_class returns crypto class."""
        mock_asset_info = Mock()
        mock_asset_info.asset_class = "crypto"
        mock_alpaca_manager.get_asset_info.return_value = mock_asset_info
        symbol = Symbol("BTC")

        result = adapter.get_asset_class(symbol)

        assert result == "crypto"

    def test_get_asset_class_unknown_no_info(self, adapter, mock_alpaca_manager):
        """Test get_asset_class returns unknown when asset info is None."""
        mock_alpaca_manager.get_asset_info.return_value = None
        symbol = Symbol("UNKN")

        result = adapter.get_asset_class(symbol)

        assert result == "unknown"

    def test_get_asset_class_unknown_no_class(self, adapter, mock_alpaca_manager):
        """Test get_asset_class returns unknown when asset_class is None."""
        mock_asset_info = Mock()
        mock_asset_info.asset_class = None
        mock_alpaca_manager.get_asset_info.return_value = mock_asset_info
        symbol = Symbol("UNKN")

        result = adapter.get_asset_class(symbol)

        assert result == "unknown"

    def test_should_use_notional_order_non_fractionable(self, adapter, mock_alpaca_manager):
        """Test should_use_notional_order for non-fractionable asset."""
        mock_alpaca_manager.is_fractionable.return_value = False
        symbol = Symbol("BERKB")

        result = adapter.should_use_notional_order(symbol, 10.0)

        assert result is True

    def test_should_use_notional_order_small_quantity(self, adapter, mock_alpaca_manager):
        """Test should_use_notional_order for quantity < 1."""
        mock_alpaca_manager.is_fractionable.return_value = True
        symbol = Symbol("AAPL")

        result = adapter.should_use_notional_order(symbol, 0.5)

        assert result is True

    def test_should_use_notional_order_significant_fraction(self, adapter, mock_alpaca_manager):
        """Test should_use_notional_order for quantity with significant fraction."""
        mock_alpaca_manager.is_fractionable.return_value = True
        symbol = Symbol("AAPL")

        # Quantity with fractional part > 0.1
        result = adapter.should_use_notional_order(symbol, 10.5)

        assert result is True

    def test_should_use_notional_order_false_whole_number(self, adapter, mock_alpaca_manager):
        """Test should_use_notional_order returns False for whole number."""
        mock_alpaca_manager.is_fractionable.return_value = True
        symbol = Symbol("AAPL")

        result = adapter.should_use_notional_order(symbol, 10.0)

        assert result is False

    def test_should_use_notional_order_false_small_fraction(self, adapter, mock_alpaca_manager):
        """Test should_use_notional_order returns False for small fraction."""
        mock_alpaca_manager.is_fractionable.return_value = True
        symbol = Symbol("AAPL")

        # Quantity with fractional part < 0.1
        result = adapter.should_use_notional_order(symbol, 10.05)

        assert result is False

    def test_should_use_notional_order_boundary_case_exactly_one(
        self, adapter, mock_alpaca_manager
    ):
        """Test should_use_notional_order boundary case with exactly 1 share."""
        mock_alpaca_manager.is_fractionable.return_value = True
        symbol = Symbol("AAPL")

        result = adapter.should_use_notional_order(symbol, 1.0)

        assert result is False

    def test_should_use_notional_order_boundary_case_just_below_one(
        self, adapter, mock_alpaca_manager
    ):
        """Test should_use_notional_order boundary case just below 1 share."""
        mock_alpaca_manager.is_fractionable.return_value = True
        symbol = Symbol("AAPL")

        result = adapter.should_use_notional_order(symbol, 0.99)

        assert result is True

    def test_should_use_notional_order_boundary_case_fraction_threshold(
        self, adapter, mock_alpaca_manager
    ):
        """Test should_use_notional_order at fractional threshold of 0.1."""
        mock_alpaca_manager.is_fractionable.return_value = True
        symbol = Symbol("AAPL")

        # Exactly at threshold (> 0.1)
        result1 = adapter.should_use_notional_order(symbol, 10.11)
        assert result1 is True

        # Just below threshold (<= 0.1)
        result2 = adapter.should_use_notional_order(
            symbol, 10.0 + FRACTIONAL_SIGNIFICANCE_THRESHOLD
        )
        assert result2 is False

    def test_should_use_notional_order_negative_quantity(self, adapter, mock_alpaca_manager):
        """Test should_use_notional_order rejects negative quantity."""
        symbol = Symbol("AAPL")

        with pytest.raises(ValueError, match="quantity must be > 0"):
            adapter.should_use_notional_order(symbol, -1.0)

    def test_should_use_notional_order_zero_quantity(self, adapter, mock_alpaca_manager):
        """Test should_use_notional_order rejects zero quantity."""
        symbol = Symbol("AAPL")

        with pytest.raises(ValueError, match="quantity must be > 0"):
            adapter.should_use_notional_order(symbol, 0.0)

    def test_get_asset_class_handles_rate_limit(self, adapter, mock_alpaca_manager):
        """Test get_asset_class re-raises RateLimitError."""
        mock_alpaca_manager.get_asset_info.side_effect = RateLimitError("Rate limit exceeded")
        symbol = Symbol("AAPL")

        with pytest.raises(RateLimitError):
            adapter.get_asset_class(symbol)

    def test_get_asset_class_handles_data_provider_error(self, adapter, mock_alpaca_manager):
        """Test get_asset_class returns unknown for DataProviderError."""
        mock_alpaca_manager.get_asset_info.side_effect = DataProviderError("Asset not found")
        symbol = Symbol("UNKN")

        result = adapter.get_asset_class(symbol)

        assert result == "unknown"

    def test_get_asset_class_handles_unexpected_error(self, adapter, mock_alpaca_manager):
        """Test get_asset_class returns unknown for unexpected exceptions."""
        mock_alpaca_manager.get_asset_info.side_effect = RuntimeError("Unexpected error")
        symbol = Symbol("UNKN")

        result = adapter.get_asset_class(symbol)

        assert result == "unknown"

    def test_correlation_id_passed_to_constructor(self, mock_alpaca_manager):
        """Test correlation_id is stored when provided."""
        correlation_id = "test-correlation-123"
        adapter = AlpacaAssetMetadataAdapter(mock_alpaca_manager, correlation_id)

        assert adapter._correlation_id == correlation_id

    def test_correlation_id_optional(self, mock_alpaca_manager):
        """Test correlation_id is optional."""
        adapter = AlpacaAssetMetadataAdapter(mock_alpaca_manager)

        assert adapter._correlation_id is None
