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
        assert actual_bp == Decimal("10000.0")
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
        assert actual_bp == Decimal("8000.0")
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
        assert actual_bp == Decimal("3000.0")
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
        assert actual_bp == Decimal("5000.0")

    def test_verify_buying_power_available_exception_handling(
        self, service, mock_broker_manager
    ):
        """Test exception handling during buying power check."""
        mock_broker_manager.get_buying_power.side_effect = [
            Exception("API Error"),
            5000.0,
        ]
        expected_amount = Decimal("4000")

        with patch("time.sleep"):
            is_available, actual_bp = service.verify_buying_power_available(
                expected_amount, max_retries=2, initial_wait=0.1
            )

        assert is_available is True
        assert actual_bp == Decimal("5000.0")

    def test_verify_buying_power_available_exponential_backoff(
        self, service, mock_broker_manager
    ):
        """Test that exponential backoff wait times are correct."""
        mock_broker_manager.get_buying_power.return_value = 3000.0
        expected_amount = Decimal("5000")

        with patch("time.sleep") as mock_sleep:
            service.verify_buying_power_available(
                expected_amount, max_retries=3, initial_wait=1.0
            )

            # Check backoff: 1.0 * 2^0, 1.0 * 2^1 (last retry doesn't sleep)
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
        assert result[1] == Decimal("10000.0")

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

        assert result == Decimal("7500.0")

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
        mock_broker_manager.get_buying_power.side_effect = Exception("API Error")

        result = service.force_account_refresh()

        assert result is False

    def test_estimate_order_cost_success(self, service, mock_broker_manager):
        """Test successful order cost estimation."""
        mock_broker_manager.get_current_price.return_value = 150.0
        quantity = Decimal("10")

        result = service.estimate_order_cost("AAPL", quantity, buffer_pct=5.0)

        assert result is not None
        expected_cost = Decimal("10") * Decimal("150.0") * Decimal("1.05")
        assert result == expected_cost

    def test_estimate_order_cost_custom_buffer(self, service, mock_broker_manager):
        """Test order cost estimation with custom buffer."""
        mock_broker_manager.get_current_price.return_value = 100.0
        quantity = Decimal("5")

        result = service.estimate_order_cost("MSFT", quantity, buffer_pct=10.0)

        assert result is not None
        expected_cost = Decimal("5") * Decimal("100.0") * Decimal("1.10")
        assert result == expected_cost

    def test_estimate_order_cost_no_price(self, service, mock_broker_manager):
        """Test order cost estimation when price is unavailable."""
        mock_broker_manager.get_current_price.return_value = None
        quantity = Decimal("10")

        result = service.estimate_order_cost("AAPL", quantity)

        assert result is None

    def test_estimate_order_cost_exception(self, service, mock_broker_manager):
        """Test order cost estimation exception handling."""
        mock_broker_manager.get_current_price.side_effect = Exception("API Error")
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
        assert current_bp == Decimal("10000.0")
        assert estimated_cost == Decimal("10") * Decimal("100.0") * Decimal("1.05")

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
        assert current_bp == Decimal("500.0")
        assert estimated_cost == Decimal("10") * Decimal("100.0") * Decimal("1.05")

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
        mock_broker_manager.get_current_price.side_effect = Exception("API Error")
        quantity = Decimal("10")

        is_sufficient, current_bp, estimated_cost = service.check_sufficient_buying_power(
            "AAPL", quantity
        )

        assert is_sufficient is False
        assert current_bp == Decimal("0")
        assert estimated_cost is None
