"""Business Unit: portfolio | Status: current.

Test correlation_id and causation_id propagation in AlpacaDataAdapter.

Tests that correlation and causation IDs are properly propagated through
all adapter methods for distributed tracing support.
"""

from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from the_alchemiser.portfolio_v2.adapters.alpaca_data_adapter import (
    AlpacaDataAdapter,
)
from the_alchemiser.shared.errors.exceptions import DataProviderError


class TestCorrelationIdPropagation:
    """Test that correlation_id and causation_id are propagated in all methods."""

    @pytest.fixture
    def mock_alpaca_manager(self):
        """Create mock Alpaca manager."""
        manager = Mock()
        manager.get_positions.return_value = []
        manager.get_account.return_value = {"cash": "1000.00"}
        manager.get_current_price.return_value = 150.50
        manager.close_all_positions.return_value = []
        return manager

    @pytest.fixture
    def data_adapter(self, mock_alpaca_manager):
        """Create data adapter with mock manager."""
        return AlpacaDataAdapter(mock_alpaca_manager)

    @patch("the_alchemiser.portfolio_v2.adapters.alpaca_data_adapter.logger")
    def test_get_positions_logs_correlation_id(
        self, mock_logger, data_adapter, mock_alpaca_manager
    ):
        """Test that get_positions includes correlation_id in logs."""
        correlation_id = "test-corr-123"
        causation_id = "test-cause-456"

        data_adapter.get_positions(
            correlation_id=correlation_id, causation_id=causation_id
        )

        # Check debug log calls include correlation_id
        assert mock_logger.debug.called
        for call in mock_logger.debug.call_args_list:
            kwargs = call[1]
            assert kwargs.get("correlation_id") == correlation_id
            assert kwargs.get("causation_id") == causation_id

    @patch("the_alchemiser.portfolio_v2.adapters.alpaca_data_adapter.logger")
    def test_get_current_prices_logs_correlation_id(
        self, mock_logger, data_adapter, mock_alpaca_manager
    ):
        """Test that get_current_prices includes correlation_id in logs."""
        correlation_id = "test-corr-789"
        causation_id = "test-cause-012"

        data_adapter.get_current_prices(
            ["AAPL"], correlation_id=correlation_id, causation_id=causation_id
        )

        # Check debug log calls include correlation_id
        assert mock_logger.debug.called
        for call in mock_logger.debug.call_args_list:
            kwargs = call[1]
            assert kwargs.get("correlation_id") == correlation_id
            assert kwargs.get("causation_id") == causation_id

    @patch("the_alchemiser.portfolio_v2.adapters.alpaca_data_adapter.logger")
    def test_get_account_cash_logs_correlation_id(
        self, mock_logger, data_adapter, mock_alpaca_manager
    ):
        """Test that get_account_cash includes correlation_id in logs."""
        correlation_id = "test-corr-345"
        causation_id = "test-cause-678"

        data_adapter.get_account_cash(
            correlation_id=correlation_id, causation_id=causation_id
        )

        # Check debug log calls include correlation_id
        assert mock_logger.debug.called
        for call in mock_logger.debug.call_args_list:
            kwargs = call[1]
            assert kwargs.get("correlation_id") == correlation_id
            assert kwargs.get("causation_id") == causation_id

    @patch("the_alchemiser.portfolio_v2.adapters.alpaca_data_adapter.logger")
    def test_liquidate_all_positions_logs_correlation_id(
        self, mock_logger, data_adapter, mock_alpaca_manager
    ):
        """Test that liquidate_all_positions includes correlation_id in logs."""
        correlation_id = "test-corr-901"
        causation_id = "test-cause-234"

        data_adapter.liquidate_all_positions(
            correlation_id=correlation_id, causation_id=causation_id
        )

        # Check warning log includes correlation_id
        assert mock_logger.warning.called
        for call in mock_logger.warning.call_args_list:
            kwargs = call[1]
            assert kwargs.get("correlation_id") == correlation_id
            assert kwargs.get("causation_id") == causation_id

    @patch("the_alchemiser.portfolio_v2.adapters.alpaca_data_adapter.logger")
    def test_error_logs_include_correlation_id(
        self, mock_logger, data_adapter, mock_alpaca_manager
    ):
        """Test that error logs include correlation_id for traceability."""
        correlation_id = "test-corr-567"
        causation_id = "test-cause-890"

        # Cause an error by making get_positions fail
        mock_alpaca_manager.get_positions.side_effect = AttributeError("Test error")

        with pytest.raises(DataProviderError):
            data_adapter.get_positions(
                correlation_id=correlation_id, causation_id=causation_id
            )

        # Check error log includes correlation_id
        assert mock_logger.error.called
        error_call = mock_logger.error.call_args
        kwargs = error_call[1]
        assert kwargs.get("correlation_id") == correlation_id
        assert kwargs.get("causation_id") == causation_id
        assert kwargs.get("error_type") == "AttributeError"


class TestInputValidation:
    """Test input validation in AlpacaDataAdapter."""

    @pytest.fixture
    def mock_alpaca_manager(self):
        """Create mock Alpaca manager."""
        manager = Mock()
        manager.get_current_price.return_value = 150.50
        return manager

    @pytest.fixture
    def data_adapter(self, mock_alpaca_manager):
        """Create data adapter with mock manager."""
        return AlpacaDataAdapter(mock_alpaca_manager)

    def test_init_with_none_raises_type_error(self):
        """Test that initializing with None alpaca_manager raises TypeError."""
        with pytest.raises(TypeError, match="alpaca_manager cannot be None"):
            AlpacaDataAdapter(None)  # type: ignore

    def test_get_current_prices_filters_empty_strings(
        self, data_adapter, mock_alpaca_manager
    ):
        """Test that empty strings are filtered from symbols list."""
        result = data_adapter.get_current_prices(["", "  ", "AAPL", ""])

        # Should only call get_current_price for valid symbol
        assert mock_alpaca_manager.get_current_price.call_count == 1
        mock_alpaca_manager.get_current_price.assert_called_with("AAPL")
        assert "AAPL" in result

    def test_get_current_prices_returns_empty_for_all_invalid(
        self, data_adapter, mock_alpaca_manager
    ):
        """Test that all invalid symbols returns empty dict."""
        result = data_adapter.get_current_prices(["", "  ", None])  # type: ignore

        # Should not call get_current_price at all
        assert mock_alpaca_manager.get_current_price.call_count == 0
        assert result == {}


class TestSpecificExceptions:
    """Test that specific exceptions are raised instead of generic ones."""

    @pytest.fixture
    def mock_alpaca_manager(self):
        """Create mock Alpaca manager."""
        return Mock()

    @pytest.fixture
    def data_adapter(self, mock_alpaca_manager):
        """Create data adapter with mock manager."""
        return AlpacaDataAdapter(mock_alpaca_manager)

    def test_get_positions_raises_data_provider_error(
        self, data_adapter, mock_alpaca_manager
    ):
        """Test that get_positions raises DataProviderError on failure."""
        mock_alpaca_manager.get_positions.side_effect = ValueError("Test error")

        with pytest.raises(DataProviderError) as exc_info:
            data_adapter.get_positions()

        assert "Failed to retrieve positions" in str(exc_info.value)
        assert exc_info.value.context["operation"] == "get_positions"

    def test_get_current_prices_raises_data_provider_error_on_invalid_price(
        self, data_adapter, mock_alpaca_manager
    ):
        """Test that invalid price raises DataProviderError."""
        mock_alpaca_manager.get_current_price.return_value = None

        with pytest.raises(DataProviderError) as exc_info:
            data_adapter.get_current_prices(["AAPL"])

        assert "Invalid price" in str(exc_info.value)
        assert exc_info.value.context["symbol"] == "AAPL"

    def test_get_current_prices_raises_data_provider_error_on_zero_price(
        self, data_adapter, mock_alpaca_manager
    ):
        """Test that zero price raises DataProviderError."""
        mock_alpaca_manager.get_current_price.return_value = 0

        with pytest.raises(DataProviderError) as exc_info:
            data_adapter.get_current_prices(["AAPL"])

        assert "Invalid price" in str(exc_info.value)

    def test_get_current_prices_raises_data_provider_error_on_negative_price(
        self, data_adapter, mock_alpaca_manager
    ):
        """Test that negative price raises DataProviderError."""
        mock_alpaca_manager.get_current_price.return_value = -10.50

        with pytest.raises(DataProviderError) as exc_info:
            data_adapter.get_current_prices(["AAPL"])

        assert "Invalid price" in str(exc_info.value)

    def test_get_account_cash_raises_data_provider_error_on_missing_account(
        self, data_adapter, mock_alpaca_manager
    ):
        """Test that missing account raises DataProviderError."""
        mock_alpaca_manager.get_account.return_value = None

        with pytest.raises(DataProviderError) as exc_info:
            data_adapter.get_account_cash()

        assert "Account information unavailable" in str(exc_info.value)
        assert exc_info.value.context["operation"] == "get_account_cash"

    def test_get_account_cash_raises_data_provider_error_on_missing_cash(
        self, data_adapter, mock_alpaca_manager
    ):
        """Test that missing cash field raises DataProviderError."""
        mock_alpaca_manager.get_account.return_value = {"other_field": "value"}

        with pytest.raises(DataProviderError) as exc_info:
            data_adapter.get_account_cash()

        assert "Cash information not available" in str(exc_info.value)
        assert "available_keys" in exc_info.value.context


class TestStructuredLogging:
    """Test that structured logging is used (no f-strings)."""

    @pytest.fixture
    def mock_alpaca_manager(self):
        """Create mock Alpaca manager."""
        manager = Mock()
        manager.get_positions.return_value = [Mock(symbol="AAPL", qty="10", qty_available="10")]
        manager.get_account.return_value = {"cash": "1000.00"}
        manager.get_current_price.return_value = 150.50
        return manager

    @pytest.fixture
    def data_adapter(self, mock_alpaca_manager):
        """Create data adapter with mock manager."""
        return AlpacaDataAdapter(mock_alpaca_manager)

    @patch("the_alchemiser.portfolio_v2.adapters.alpaca_data_adapter.logger")
    def test_get_positions_uses_structured_logging(
        self, mock_logger, data_adapter, mock_alpaca_manager
    ):
        """Test that get_positions uses structured logging parameters."""
        data_adapter.get_positions()

        # Check that debug calls use keyword arguments, not f-strings
        assert mock_logger.debug.called
        for call in mock_logger.debug.call_args_list:
            args, kwargs = call
            # First arg should be plain string (not f-string with formatting)
            assert isinstance(args[0], str)
            # Should have structured parameters
            assert "action" in kwargs
            assert "module" in kwargs

    @patch("the_alchemiser.portfolio_v2.adapters.alpaca_data_adapter.logger")
    def test_get_current_prices_uses_structured_logging(
        self, mock_logger, data_adapter, mock_alpaca_manager
    ):
        """Test that get_current_prices uses structured logging parameters."""
        data_adapter.get_current_prices(["AAPL"])

        # Check that debug calls use keyword arguments
        assert mock_logger.debug.called
        for call in mock_logger.debug.call_args_list:
            args, kwargs = call
            assert isinstance(args[0], str)
            assert "action" in kwargs
            assert "symbols" in kwargs or "symbol_count" in kwargs

    @patch("the_alchemiser.portfolio_v2.adapters.alpaca_data_adapter.logger")
    def test_get_account_cash_uses_structured_logging(
        self, mock_logger, data_adapter, mock_alpaca_manager
    ):
        """Test that get_account_cash uses structured logging parameters."""
        data_adapter.get_account_cash()

        # Check that debug calls use keyword arguments
        assert mock_logger.debug.called
        for call in mock_logger.debug.call_args_list:
            args, kwargs = call
            assert isinstance(args[0], str)
            assert "action" in kwargs
            # Cash balance should be in kwargs, not in f-string
            assert "cash_balance_usd" in kwargs
