"""Business Unit: shared | Status: current.

Tests for error catalog module covering error code mapping and specifications.
"""

import pytest

from the_alchemiser.shared.errors.catalog import (
    ERROR_CATALOG,
    ErrorCode,
    ErrorSpec,
    get_error_spec,
    get_suggested_action,
    map_exception_to_error_code,
)
from the_alchemiser.shared.errors.exceptions import (
    BuyingPowerError,
    ConfigurationError,
    DataProviderError,
    EnvironmentError,
    InsufficientFundsError,
    MarketClosedError,
    MarketDataError,
    NotificationError,
    OrderTimeoutError,
    RateLimitError,
)


class TestErrorCode:
    """Test ErrorCode enum."""

    def test_all_error_codes_exist(self):
        """Test that all error codes are defined."""
        assert ErrorCode.TRD_MARKET_CLOSED.value == "TRD_MARKET_CLOSED"
        assert ErrorCode.TRD_INSUFFICIENT_FUNDS.value == "TRD_INSUFFICIENT_FUNDS"
        assert ErrorCode.TRD_ORDER_TIMEOUT.value == "TRD_ORDER_TIMEOUT"
        assert ErrorCode.TRD_BUYING_POWER.value == "TRD_BUYING_POWER"
        assert ErrorCode.DATA_RATE_LIMIT.value == "DATA_RATE_LIMIT"
        assert ErrorCode.DATA_PROVIDER_FAILURE.value == "DATA_PROVIDER_FAILURE"
        assert ErrorCode.CONF_MISSING_ENV.value == "CONF_MISSING_ENV"
        assert ErrorCode.CONF_INVALID_VALUE.value == "CONF_INVALID_VALUE"
        assert ErrorCode.NOTIF_SMTP_FAILURE.value == "NOTIF_SMTP_FAILURE"


class TestErrorSpec:
    """Test ErrorSpec model."""

    def test_error_spec_frozen(self):
        """Test that ErrorSpec is frozen and immutable."""
        spec = ERROR_CATALOG[ErrorCode.TRD_MARKET_CLOSED]
        with pytest.raises((AttributeError, Exception)):
            spec.category = "modified"  # Should fail due to frozen model

    def test_error_spec_has_required_fields(self):
        """Test that all error specs have required fields."""
        for error_code in ErrorCode:
            spec = ERROR_CATALOG[error_code]
            assert spec.code == error_code
            assert isinstance(spec.category, str)
            assert spec.category in [
                "trading",
                "data",
                "configuration",
                "notification",
            ]
            assert isinstance(spec.default_severity, str)
            assert spec.default_severity in ["low", "medium", "high", "critical"]
            assert isinstance(spec.retryable, bool)
            assert isinstance(spec.message_template, str)
            assert len(spec.message_template) > 0
            assert isinstance(spec.suggested_action, str)
            assert len(spec.suggested_action) > 0


class TestMapExceptionToErrorCode:
    """Test exception to error code mapping."""

    def test_market_closed_error_maps_correctly(self):
        """Test MarketClosedError maps to TRD_MARKET_CLOSED."""
        exc = MarketClosedError("Market is closed")
        result = map_exception_to_error_code(exc)
        assert result == ErrorCode.TRD_MARKET_CLOSED

    def test_insufficient_funds_error_maps_correctly(self):
        """Test InsufficientFundsError maps to TRD_INSUFFICIENT_FUNDS."""
        exc = InsufficientFundsError("Not enough funds")
        result = map_exception_to_error_code(exc)
        assert result == ErrorCode.TRD_INSUFFICIENT_FUNDS

    def test_order_timeout_error_maps_correctly(self):
        """Test OrderTimeoutError maps to TRD_ORDER_TIMEOUT."""
        exc = OrderTimeoutError("Order timed out")
        result = map_exception_to_error_code(exc)
        assert result == ErrorCode.TRD_ORDER_TIMEOUT

    def test_buying_power_error_maps_correctly(self):
        """Test BuyingPowerError maps to TRD_BUYING_POWER."""
        exc = BuyingPowerError("Insufficient buying power")
        result = map_exception_to_error_code(exc)
        assert result == ErrorCode.TRD_BUYING_POWER

    def test_rate_limit_error_maps_correctly(self):
        """Test RateLimitError maps to DATA_RATE_LIMIT."""
        exc = RateLimitError("Rate limit exceeded")
        result = map_exception_to_error_code(exc)
        assert result == ErrorCode.DATA_RATE_LIMIT

    def test_data_provider_error_maps_correctly(self):
        """Test DataProviderError maps to DATA_PROVIDER_FAILURE."""
        exc = DataProviderError("Provider failed")
        result = map_exception_to_error_code(exc)
        assert result == ErrorCode.DATA_PROVIDER_FAILURE

    def test_market_data_error_maps_correctly(self):
        """Test MarketDataError maps to DATA_PROVIDER_FAILURE."""
        exc = MarketDataError("Market data unavailable")
        result = map_exception_to_error_code(exc)
        assert result == ErrorCode.DATA_PROVIDER_FAILURE

    def test_environment_error_maps_correctly(self):
        """Test EnvironmentError maps to CONF_MISSING_ENV."""
        exc = EnvironmentError("ENV_VAR not set")
        result = map_exception_to_error_code(exc)
        assert result == ErrorCode.CONF_MISSING_ENV

    def test_configuration_error_maps_correctly(self):
        """Test ConfigurationError maps to CONF_INVALID_VALUE."""
        exc = ConfigurationError("Invalid config")
        result = map_exception_to_error_code(exc)
        assert result == ErrorCode.CONF_INVALID_VALUE

    def test_notification_error_maps_correctly(self):
        """Test NotificationError maps to NOTIF_SMTP_FAILURE."""
        exc = NotificationError("Email failed")
        result = map_exception_to_error_code(exc)
        assert result == ErrorCode.NOTIF_SMTP_FAILURE

    def test_unknown_exception_returns_none(self):
        """Test that unknown exceptions return None."""
        exc = ValueError("Some generic error")
        result = map_exception_to_error_code(exc)
        assert result is None

    def test_standard_exception_returns_none(self):
        """Test that standard exceptions return None."""
        exc = Exception("Generic exception")
        result = map_exception_to_error_code(exc)
        assert result is None


class TestGetErrorSpec:
    """Test get_error_spec function."""

    def test_get_error_spec_returns_correct_spec(self):
        """Test that get_error_spec returns the correct specification."""
        spec = get_error_spec(ErrorCode.TRD_MARKET_CLOSED)
        assert spec.code == ErrorCode.TRD_MARKET_CLOSED
        assert spec.category == "trading"
        assert spec.default_severity == "medium"
        assert spec.retryable is True

    def test_get_error_spec_for_all_codes(self):
        """Test that get_error_spec works for all error codes."""
        for error_code in ErrorCode:
            spec = get_error_spec(error_code)
            assert spec.code == error_code
            assert isinstance(spec, ErrorSpec)


class TestGetSuggestedAction:
    """Test get_suggested_action function."""

    def test_get_suggested_action_returns_string(self):
        """Test that get_suggested_action returns a non-empty string."""
        action = get_suggested_action(ErrorCode.TRD_MARKET_CLOSED)
        assert isinstance(action, str)
        assert len(action) > 0
        assert action == "Wait for market open or check trading hours"

    def test_get_suggested_action_for_trading_errors(self):
        """Test suggested actions for trading errors."""
        action = get_suggested_action(ErrorCode.TRD_INSUFFICIENT_FUNDS)
        assert "balance" in action.lower() or "funds" in action.lower()

    def test_get_suggested_action_for_data_errors(self):
        """Test suggested actions for data errors."""
        action = get_suggested_action(ErrorCode.DATA_RATE_LIMIT)
        assert "rate limit" in action.lower() or "wait" in action.lower()

    def test_get_suggested_action_for_config_errors(self):
        """Test suggested actions for configuration errors."""
        action = get_suggested_action(ErrorCode.CONF_MISSING_ENV)
        assert "environment" in action.lower() or "variable" in action.lower()

    def test_get_suggested_action_for_all_codes(self):
        """Test that all error codes have meaningful suggested actions."""
        for error_code in ErrorCode:
            action = get_suggested_action(error_code)
            assert isinstance(action, str)
            assert len(action) > 10  # Should be a meaningful message


class TestErrorCatalogCompleteness:
    """Test that the error catalog is complete and consistent."""

    def test_all_error_codes_in_catalog(self):
        """Test that all ErrorCode enum values are in the catalog."""
        for error_code in ErrorCode:
            assert error_code in ERROR_CATALOG, f"Missing catalog entry for {error_code}"

    def test_catalog_only_contains_valid_error_codes(self):
        """Test that catalog only contains valid ErrorCode values."""
        for error_code in ERROR_CATALOG.keys():
            assert isinstance(error_code, ErrorCode)

    def test_retryable_errors_have_appropriate_severity(self):
        """Test that retryable errors generally have lower severity than non-retryable."""
        # This is a soft guideline - critical non-retryable errors should be rare
        non_retryable_critical = [
            spec
            for spec in ERROR_CATALOG.values()
            if not spec.retryable and spec.default_severity == "critical"
        ]
        # Should have at least one non-retryable critical error (config issues)
        assert len(non_retryable_critical) >= 1
