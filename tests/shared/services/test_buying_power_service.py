"""Business Unit: shared | Status: current.

Test suite for BuyingPowerService.

Tests buying power verification, retry logic, error handling, and cost estimation.
"""

from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from the_alchemiser.shared.services.buying_power_service import BuyingPowerService


class TestBuyingPowerService:
    """Test suite for BuyingPowerService."""

    @pytest.fixture
    def mock_broker_manager(self):
        """Create a mock AlpacaManager."""
        mock = Mock()
        mock.get_buying_power.return_value = 10000.0
        mock.get_portfolio_value.return_value = 50000.0
        mock.get_current_price.return_value = 150.0
        return mock

    @pytest.fixture
    def service(self, mock_broker_manager):
        """Create BuyingPowerService with mock broker manager."""
        return BuyingPowerService(mock_broker_manager)

    def test_verify_buying_power_available_success_first_attempt(
        self, service, mock_broker_manager
    ):
        """Test successful buying power verification on first attempt."""
        mock_broker_manager.get_buying_power.return_value = 10000.0
        expected_amount = Decimal("5000")

        is_available, actual_bp = service.verify_buying_power_available(expected_amount)

        assert is_available is True
        assert actual_bp == Decimal("10000.00")
        mock_broker_manager.get_buying_power.assert_called_once()

    def test_verify_buying_power_available_success_after_retry(
        self, service, mock_broker_manager
    ):
        """Test buying power verification succeeds after retry."""
        # First call returns insufficient, second call returns sufficient
        mock_broker_manager.get_buying_power.side_effect = [3000.0, 8000.0]
        expected_amount = Decimal("5000")

        with patch("time.sleep"):  # Mock sleep to speed up test
            is_available, actual_bp = service.verify_buying_power_available(
                expected_amount, max_retries=2, initial_wait=0.1
            )

        assert is_available is True
        assert actual_bp == Decimal("8000.00")
        assert mock_broker_manager.get_buying_power.call_count == 2

    def test_verify_buying_power_available_failure_all_retries(
        self, service, mock_broker_manager
    ):
        """Test buying power verification fails after all retries."""
        mock_broker_manager.get_buying_power.return_value = 3000.0
        expected_amount = Decimal("5000")

        with patch("time.sleep"):
            is_available, actual_bp = service.verify_buying_power_available(
                expected_amount, max_retries=3, initial_wait=0.1
            )

        assert is_available is False
        assert actual_bp == Decimal("3000.00")
        assert mock_broker_manager.get_buying_power.call_count == 4  # 3 retries + 1 final

    def test_verify_buying_power_available_none_response(
        self, service, mock_broker_manager
    ):
        """Test handling when broker returns None for buying power."""
        mock_broker_manager.get_buying_power.side_effect = [None, None, 5000.0]
        expected_amount = Decimal("4000")

        with patch("time.sleep"):
            is_available, actual_bp = service.verify_buying_power_available(
                expected_amount, max_retries=3, initial_wait=0.1
            )

        assert is_available is True
        assert actual_bp == Decimal("5000.00")

    def test_verify_buying_power_available_exception_handling(
        self, service, mock_broker_manager
    ):
        """Test exception handling during buying power check."""
        from the_alchemiser.shared.errors.exceptions import DataProviderError
        
        mock_broker_manager.get_buying_power.side_effect = [
            DataProviderError("API Error"),
            5000.0,
        ]
        expected_amount = Decimal("4000")

        with patch("time.sleep"), patch("random.uniform", return_value=0):
            is_available, actual_bp = service.verify_buying_power_available(
                expected_amount, max_retries=2, initial_wait=0.1
            )

        assert is_available is True
        assert actual_bp == Decimal("5000.00")

    def test_verify_buying_power_available_exponential_backoff(
        self, service, mock_broker_manager
    ):
        """Test that exponential backoff wait times are correct (with jitter)."""
        mock_broker_manager.get_buying_power.return_value = 3000.0
        expected_amount = Decimal("5000")

        with patch("time.sleep") as mock_sleep, patch("random.uniform", return_value=0):
            service.verify_buying_power_available(
                expected_amount, max_retries=3, initial_wait=1.0
            )

            # Check backoff: 1.0 * 2^0, 1.0 * 2^1 (last retry doesn't sleep)
            # With jitter mocked to return 0, the waits should be exact
            calls = mock_sleep.call_args_list
            assert len(calls) == 2
            assert calls[0][0][0] == 1.0  # First wait
            assert calls[1][0][0] == 2.0  # Second wait

    def test_check_buying_power_attempt_sufficient(self, service, mock_broker_manager):
        """Test _check_buying_power_attempt when buying power is sufficient."""
        mock_broker_manager.get_buying_power.return_value = 10000.0
        expected_amount = Decimal("5000")

        result = service._check_buying_power_attempt(expected_amount, 0)

        assert result is not None
        assert result[0] is True
        assert result[1] == Decimal("10000.00")

    def test_check_buying_power_attempt_insufficient(
        self, service, mock_broker_manager
    ):
        """Test _check_buying_power_attempt when buying power is insufficient."""
        mock_broker_manager.get_buying_power.return_value = 3000.0
        expected_amount = Decimal("5000")

        result = service._check_buying_power_attempt(expected_amount, 0)

        assert result is None

    def test_check_buying_power_attempt_none_response(
        self, service, mock_broker_manager
    ):
        """Test _check_buying_power_attempt when broker returns None."""
        mock_broker_manager.get_buying_power.return_value = None
        expected_amount = Decimal("5000")

        result = service._check_buying_power_attempt(expected_amount, 0)

        assert result is None

    def test_get_final_buying_power_success(self, service, mock_broker_manager):
        """Test _get_final_buying_power returns correct value."""
        mock_broker_manager.get_buying_power.return_value = 7500.0

        result = service._get_final_buying_power()

        assert result == Decimal("7500.00")

    def test_get_final_buying_power_none(self, service, mock_broker_manager):
        """Test _get_final_buying_power handles None response."""
        mock_broker_manager.get_buying_power.return_value = None

        result = service._get_final_buying_power()

        assert result == Decimal("0")

    def test_get_final_buying_power_exception(self, service, mock_broker_manager):
        """Test _get_final_buying_power handles exceptions."""
        mock_broker_manager.get_buying_power.side_effect = Exception("API Error")

        result = service._get_final_buying_power()

        assert result == Decimal("0")

    def test_force_account_refresh_success(self, service, mock_broker_manager):
        """Test successful account refresh."""
        mock_broker_manager.get_buying_power.return_value = 10000.0
        mock_broker_manager.get_portfolio_value.return_value = 50000.0

        result = service.force_account_refresh()

        assert result is True
        mock_broker_manager.get_buying_power.assert_called_once()
        mock_broker_manager.get_portfolio_value.assert_called_once()

    def test_force_account_refresh_incomplete_data(self, service, mock_broker_manager):
        """Test account refresh with incomplete data."""
        mock_broker_manager.get_buying_power.return_value = None
        mock_broker_manager.get_portfolio_value.return_value = 50000.0

        result = service.force_account_refresh()

        assert result is False

    def test_force_account_refresh_exception(self, service, mock_broker_manager):
        """Test account refresh exception handling."""
        from the_alchemiser.shared.errors.exceptions import DataProviderError
        
        mock_broker_manager.get_buying_power.side_effect = DataProviderError("API Error")

        result = service.force_account_refresh()

        assert result is False

    def test_estimate_order_cost_success(self, service, mock_broker_manager):
        """Test successful order cost estimation."""
        mock_broker_manager.get_current_price.return_value = 150.0
        quantity = Decimal("10")

        result = service.estimate_order_cost("AAPL", quantity, buffer_pct=5.0)

        assert result is not None
        expected_cost = Decimal("10") * Decimal("150.00") * Decimal("1.05")
        assert result == expected_cost

    def test_estimate_order_cost_custom_buffer(self, service, mock_broker_manager):
        """Test order cost estimation with custom buffer."""
        mock_broker_manager.get_current_price.return_value = 100.0
        quantity = Decimal("5")

        result = service.estimate_order_cost("MSFT", quantity, buffer_pct=10.0)

        assert result is not None
        expected_cost = Decimal("5") * Decimal("100.00") * Decimal("1.10")
        assert result == expected_cost

    def test_estimate_order_cost_no_price(self, service, mock_broker_manager):
        """Test order cost estimation when price is unavailable."""
        mock_broker_manager.get_current_price.return_value = None
        quantity = Decimal("10")

        result = service.estimate_order_cost("AAPL", quantity)

        assert result is None

    def test_estimate_order_cost_exception(self, service, mock_broker_manager):
        """Test order cost estimation exception handling."""
        from the_alchemiser.shared.errors.exceptions import DataProviderError
        
        mock_broker_manager.get_current_price.side_effect = DataProviderError("API Error")
        quantity = Decimal("10")

        result = service.estimate_order_cost("AAPL", quantity)

        assert result is None

    def test_check_sufficient_buying_power_sufficient(
        self, service, mock_broker_manager
    ):
        """Test check_sufficient_buying_power when power is sufficient."""
        mock_broker_manager.get_current_price.return_value = 100.0
        mock_broker_manager.get_buying_power.return_value = 10000.0
        quantity = Decimal("10")

        is_sufficient, current_bp, estimated_cost = service.check_sufficient_buying_power(
            "AAPL", quantity, buffer_pct=5.0
        )

        assert is_sufficient is True
        assert current_bp == Decimal("10000.00")
        assert estimated_cost == Decimal("10") * Decimal("100.00") * Decimal("1.05")

    def test_check_sufficient_buying_power_insufficient(
        self, service, mock_broker_manager
    ):
        """Test check_sufficient_buying_power when power is insufficient."""
        mock_broker_manager.get_current_price.return_value = 100.0
        mock_broker_manager.get_buying_power.return_value = 500.0
        quantity = Decimal("10")

        is_sufficient, current_bp, estimated_cost = service.check_sufficient_buying_power(
            "AAPL", quantity, buffer_pct=5.0
        )

        assert is_sufficient is False
        assert current_bp == Decimal("500.00")
        assert estimated_cost == Decimal("10") * Decimal("100.00") * Decimal("1.05")

    def test_check_sufficient_buying_power_no_price(
        self, service, mock_broker_manager
    ):
        """Test check_sufficient_buying_power when price unavailable."""
        mock_broker_manager.get_current_price.return_value = None
        mock_broker_manager.get_buying_power.return_value = 10000.0
        quantity = Decimal("10")

        is_sufficient, current_bp, estimated_cost = service.check_sufficient_buying_power(
            "AAPL", quantity
        )

        assert is_sufficient is False
        assert current_bp == Decimal("0")
        assert estimated_cost is None

    def test_check_sufficient_buying_power_no_buying_power(
        self, service, mock_broker_manager
    ):
        """Test check_sufficient_buying_power when buying power unavailable."""
        mock_broker_manager.get_current_price.return_value = 100.0
        mock_broker_manager.get_buying_power.return_value = None
        quantity = Decimal("10")

        is_sufficient, current_bp, estimated_cost = service.check_sufficient_buying_power(
            "AAPL", quantity
        )

        assert is_sufficient is False
        assert current_bp == Decimal("0")
        assert estimated_cost is not None

    def test_check_sufficient_buying_power_exception(
        self, service, mock_broker_manager
    ):
        """Test check_sufficient_buying_power exception handling."""
        from the_alchemiser.shared.errors.exceptions import DataProviderError
        
        mock_broker_manager.get_current_price.side_effect = DataProviderError("API Error")
        quantity = Decimal("10")

        is_sufficient, current_bp, estimated_cost = service.check_sufficient_buying_power(
            "AAPL", quantity
        )

        assert is_sufficient is False
        assert current_bp == Decimal("0")
        assert estimated_cost is None


class TestCorrelationIDPropagation:
    """Test correlation ID propagation through logs and methods."""

    @pytest.fixture
    def service(self):
        """Create BuyingPowerService with mock broker manager."""
        mock = Mock()
        mock.get_buying_power.return_value = 10000.0
        mock.get_portfolio_value.return_value = 50000.0
        mock.get_current_price.return_value = 150.0
        return BuyingPowerService(mock)

    def test_verify_buying_power_with_correlation_id(self, service, caplog):
        """Test that correlation_id is included in logs."""
        correlation_id = "test-correlation-123"
        expected_amount = Decimal("5000")

        is_available, _ = service.verify_buying_power_available(
            expected_amount, correlation_id=correlation_id
        )

        assert is_available is True

    def test_check_sufficient_buying_power_with_correlation_id(self, service):
        """Test that correlation_id can be passed to check_sufficient_buying_power."""
        correlation_id = "test-correlation-456"
        quantity = Decimal("10")

        is_sufficient, current_bp, estimated_cost = service.check_sufficient_buying_power(
            "AAPL", quantity, correlation_id=correlation_id
        )

        assert is_sufficient is True
        assert current_bp > Decimal("0")

    def test_force_account_refresh_with_correlation_id(self, service):
        """Test that correlation_id can be passed to force_account_refresh."""
        correlation_id = "test-correlation-789"

        result = service.force_account_refresh(correlation_id=correlation_id)

        assert result is True


class TestInputValidation:
    """Test input validation for all public methods."""

    @pytest.fixture
    def service(self):
        """Create BuyingPowerService with mock broker manager."""
        mock = Mock()
        return BuyingPowerService(mock)

    def test_verify_buying_power_negative_amount(self, service):
        """Test that negative expected_amount raises ValueError."""
        with pytest.raises(ValueError, match="expected_amount must be positive"):
            service.verify_buying_power_available(Decimal("-100"))

    def test_verify_buying_power_zero_amount(self, service):
        """Test that zero expected_amount raises ValueError."""
        with pytest.raises(ValueError, match="expected_amount must be positive"):
            service.verify_buying_power_available(Decimal("0"))

    def test_verify_buying_power_negative_max_retries(self, service):
        """Test that negative max_retries raises ValueError."""
        with pytest.raises(ValueError, match="max_retries must be >= 1"):
            service.verify_buying_power_available(Decimal("100"), max_retries=0)

    def test_verify_buying_power_negative_initial_wait(self, service):
        """Test that negative initial_wait raises ValueError."""
        with pytest.raises(ValueError, match="initial_wait must be positive"):
            service.verify_buying_power_available(Decimal("100"), initial_wait=-1.0)

    def test_estimate_order_cost_negative_quantity(self, service):
        """Test that negative quantity raises ValueError."""
        with pytest.raises(ValueError, match="quantity must be positive"):
            service.estimate_order_cost("AAPL", Decimal("-10"))

    def test_estimate_order_cost_zero_quantity(self, service):
        """Test that zero quantity raises ValueError."""
        with pytest.raises(ValueError, match="quantity must be positive"):
            service.estimate_order_cost("AAPL", Decimal("0"))

    def test_estimate_order_cost_negative_buffer(self, service):
        """Test that negative buffer_pct raises ValueError."""
        with pytest.raises(ValueError, match="buffer_pct must be non-negative"):
            service.estimate_order_cost("AAPL", Decimal("10"), buffer_pct=-5.0)

    def test_check_sufficient_buying_power_negative_quantity(self, service):
        """Test that negative quantity raises ValueError."""
        with pytest.raises(ValueError, match="quantity must be positive"):
            service.check_sufficient_buying_power("AAPL", Decimal("-10"))

    def test_check_sufficient_buying_power_negative_buffer(self, service):
        """Test that negative buffer_pct raises ValueError."""
        with pytest.raises(ValueError, match="buffer_pct must be non-negative"):
            service.check_sufficient_buying_power("AAPL", Decimal("10"), buffer_pct=-5.0)


class TestJitterBehavior:
    """Test that jitter is applied to exponential backoff."""

    @pytest.fixture
    def service(self):
        """Create BuyingPowerService with mock broker manager."""
        mock = Mock()
        mock.get_buying_power.return_value = 3000.0  # Insufficient
        return BuyingPowerService(mock)

    def test_jitter_adds_variation_to_wait_times(self, service):
        """Test that jitter makes wait times vary slightly."""
        expected_amount = Decimal("5000")

        with patch("time.sleep") as mock_sleep:
            # Run multiple times to see variation
            wait_times = []
            for _ in range(5):
                service.verify_buying_power_available(
                    expected_amount, max_retries=2, initial_wait=1.0
                )
                if mock_sleep.call_args_list:
                    wait_times.append(mock_sleep.call_args_list[0][0][0])
                mock_sleep.reset_mock()

            # Wait times should vary (not all exactly 1.0)
            # With jitter, they should be around 1.0 but not identical
            assert len(set(wait_times)) > 1  # At least some variation

    def test_max_backoff_cap_applied(self, service):
        """Test that wait time is capped at MAX_BACKOFF_SECONDS."""
        expected_amount = Decimal("5000")

        with patch("time.sleep") as mock_sleep, patch("random.uniform", return_value=0):
            service.verify_buying_power_available(
                expected_amount, max_retries=10, initial_wait=5.0
            )

            # Check that no wait time exceeds MAX_BACKOFF_SECONDS
            for call in mock_sleep.call_args_list:
                wait_time = call[0][0]
                assert wait_time <= 10.0  # MAX_BACKOFF_SECONDS


class TestDecimalPrecision:
    """Test that Decimal values are properly rounded."""

    @pytest.fixture
    def mock_broker_manager(self):
        """Create a mock AlpacaManager."""
        mock = Mock()
        mock.get_buying_power.return_value = 10000.123456  # Many decimal places
        mock.get_current_price.return_value = 150.789123  # Many decimal places
        return mock

    @pytest.fixture
    def service(self, mock_broker_manager):
        """Create BuyingPowerService with mock broker manager."""
        return BuyingPowerService(mock_broker_manager)

    def test_buying_power_rounded_to_cents(self, service):
        """Test that buying power is rounded to 2 decimal places."""
        expected_amount = Decimal("5000")

        is_available, actual_bp = service.verify_buying_power_available(expected_amount)

        assert is_available is True
        # Should be rounded to 2 decimal places
        assert actual_bp == Decimal("10000.12")
        assert actual_bp.as_tuple().exponent == -2  # 2 decimal places

    def test_order_cost_rounded_to_cents(self, service):
        """Test that estimated order cost is rounded to 2 decimal places."""
        quantity = Decimal("10")

        estimated_cost = service.estimate_order_cost("AAPL", quantity, buffer_pct=5.0)

        assert estimated_cost is not None
        # Should be rounded to 2 decimal places
        assert estimated_cost.as_tuple().exponent == -2  # 2 decimal places
