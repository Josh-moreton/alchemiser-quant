"""Business Unit: execution | Status: current

Test market order executor functionality.

Tests market order placement, validation, error handling without broker dependencies.
"""

import uuid
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from the_alchemiser.execution_v2.core.market_order_executor import MarketOrderExecutor
from the_alchemiser.execution_v2.utils.execution_validator import OrderValidationResult
from the_alchemiser.shared.schemas.execution_report import ExecutedOrder


def _make_executed_order(
    symbol: str = "AAPL",
    *,
    filled_qty: Decimal = Decimal("10"),
    filled_avg_price: Decimal = Decimal("150.00"),
    order_id: str | None = None,
    status: str = "filled",
) -> Mock:
    """Create a mock executed order."""
    order = Mock(spec=ExecutedOrder)
    order.id = order_id or str(uuid.uuid4())
    order.filled_qty = filled_qty
    order.filled_avg_price = filled_avg_price
    order.status = status
    order.symbol = symbol
    return order


class TestMarketOrderExecutor:
    """Test market order executor functionality."""

    @pytest.fixture
    def mock_alpaca_manager(self):
        """Mock Alpaca manager."""
        mock = Mock()
        mock.get_buying_power.return_value = Decimal("10000.00")
        mock.get_current_price.return_value = Decimal("150.00")
        return mock

    @pytest.fixture
    def mock_validator(self):
        """Mock execution validator."""
        mock = Mock()
        # Default to valid
        mock.validate_order.return_value = OrderValidationResult(
            is_valid=True, adjusted_quantity=None, error_message=None, warnings=()
        )
        return mock

    @pytest.fixture
    def mock_buying_power_service(self):
        """Mock buying power service."""
        mock = Mock()
        mock.verify_buying_power_available.return_value = (True, Decimal("10000.00"))
        mock.estimate_order_cost.return_value = Decimal("1500.00")
        return mock

    @pytest.fixture
    def executor(self, mock_alpaca_manager, mock_validator, mock_buying_power_service):
        """Create market order executor."""
        return MarketOrderExecutor(
            alpaca_manager=mock_alpaca_manager,
            validator=mock_validator,
            buying_power_service=mock_buying_power_service,
        )

    def test_initialization(self, mock_alpaca_manager, mock_validator, mock_buying_power_service):
        """Test executor initializes with required dependencies."""
        executor = MarketOrderExecutor(
            alpaca_manager=mock_alpaca_manager,
            validator=mock_validator,
            buying_power_service=mock_buying_power_service,
        )

        assert executor.alpaca_manager is mock_alpaca_manager
        assert executor.validator is mock_validator
        assert executor.buying_power_service is mock_buying_power_service

    def test_execute_market_order_success_buy(self, executor, mock_alpaca_manager):
        """Test successful buy market order execution."""
        executed_order = _make_executed_order(
            "AAPL", filled_qty=Decimal("10"), filled_avg_price=Decimal("150.00")
        )
        mock_alpaca_manager.place_market_order.return_value = executed_order

        result = executor.execute_market_order("AAPL", "buy", Decimal("10"))

        assert result.success is True
        assert result.symbol == "AAPL"
        assert result.action == "BUY"
        assert result.shares == Decimal("10")
        assert result.price == Decimal("150.00")
        assert result.trade_amount == Decimal("10") * Decimal("150.00")
        assert result.order_id == executed_order.id

    def test_execute_market_order_success_sell(self, executor, mock_alpaca_manager):
        """Test successful sell market order execution."""
        executed_order = _make_executed_order(
            "MSFT", filled_qty=Decimal("5"), filled_avg_price=Decimal("300.00")
        )
        mock_alpaca_manager.place_market_order.return_value = executed_order

        result = executor.execute_market_order("MSFT", "sell", Decimal("5"))

        assert result.success is True
        assert result.symbol == "MSFT"
        assert result.action == "SELL"
        assert result.shares == Decimal("5")
        assert result.price == Decimal("300.00")
        assert result.order_id == executed_order.id

    def test_execute_market_order_validation_failure(self, executor, mock_validator):
        """Test market order with validation failure."""
        mock_validator.validate_order.return_value = OrderValidationResult(
            is_valid=False,
            adjusted_quantity=None,
            error_message="Insufficient shares for sell",
            warnings=(),
        )

        result = executor.execute_market_order("AAPL", "sell", Decimal("100"))

        assert result.success is False
        assert result.error_message == "Insufficient shares for sell"
        assert result.trade_amount == Decimal("0")
        assert result.order_id is None

    def test_execute_market_order_with_quantity_adjustment(
        self, executor, mock_validator, mock_alpaca_manager
    ):
        """Test market order with quantity adjustment from validator."""
        # Validator adjusts quantity from 10.5 to 10 (non-fractionable)
        mock_validator.validate_order.return_value = OrderValidationResult(
            is_valid=True,
            adjusted_quantity=Decimal("10"),
            error_message=None,
            warnings=("Quantity adjusted to whole shares",),
        )
        executed_order = _make_executed_order(
            "AAPL", filled_qty=Decimal("10"), filled_avg_price=Decimal("150.00")
        )
        mock_alpaca_manager.place_market_order.return_value = executed_order

        result = executor.execute_market_order("AAPL", "buy", Decimal("10.5"))

        assert result.success is True
        assert result.shares == Decimal("10")  # Adjusted quantity used
        # Verify broker was called with adjusted quantity
        mock_alpaca_manager.place_market_order.assert_called_once_with("AAPL", "buy", Decimal("10"))

    def test_execute_market_order_buying_power_check_buy(
        self, executor, mock_buying_power_service, mock_alpaca_manager
    ):
        """Test buying power verification for buy orders."""
        executed_order = _make_executed_order("AAPL")
        mock_alpaca_manager.place_market_order.return_value = executed_order
        mock_alpaca_manager.get_current_price.return_value = Decimal("150.00")
        mock_buying_power_service.verify_buying_power_available.return_value = (
            True,
            Decimal("10000.00"),
        )

        result = executor.execute_market_order("AAPL", "buy", Decimal("10"))

        assert result.success is True
        # Verify buying power was checked for buy
        assert mock_buying_power_service.verify_buying_power_available.called
        assert mock_alpaca_manager.get_current_price.called

    def test_execute_market_order_no_buying_power_check_sell(
        self, executor, mock_buying_power_service, mock_alpaca_manager
    ):
        """Test no buying power check for sell orders."""
        executed_order = _make_executed_order("AAPL")
        mock_alpaca_manager.place_market_order.return_value = executed_order

        result = executor.execute_market_order("AAPL", "sell", Decimal("10"))

        assert result.success is True
        # Verify buying power was NOT checked for sell
        assert not mock_buying_power_service.verify_buying_power_available.called

    def test_execute_market_order_broker_exception(self, executor, mock_alpaca_manager):
        """Test handling broker exception during order placement."""
        mock_alpaca_manager.place_market_order.side_effect = RuntimeError(
            "Broker connection failed"
        )

        result = executor.execute_market_order("AAPL", "buy", Decimal("10"))

        assert result.success is False
        assert "Broker connection failed" in result.error_message
        assert result.trade_amount == Decimal("0")
        assert result.order_id is None

    def test_execute_market_order_zero_quantity(self, executor, mock_validator):
        """Test market order with zero quantity."""
        mock_validator.validate_order.return_value = OrderValidationResult(
            is_valid=False,
            adjusted_quantity=None,
            error_message="Quantity must be greater than zero",
            warnings=(),
        )

        result = executor.execute_market_order("AAPL", "buy", Decimal("0"))

        assert result.success is False
        assert result.error_message == "Quantity must be greater than zero"

    def test_execute_market_order_negative_quantity(self, executor, mock_validator):
        """Test market order with negative quantity."""
        mock_validator.validate_order.return_value = OrderValidationResult(
            is_valid=False,
            adjusted_quantity=None,
            error_message="Quantity cannot be negative",
            warnings=(),
        )

        result = executor.execute_market_order("AAPL", "buy", Decimal("-5"))

        assert result.success is False
        assert "negative" in result.error_message.lower()

    def test_execute_market_order_partial_fill(self, executor, mock_alpaca_manager):
        """Test market order with partial fill."""
        # Order for 10 shares but only 7 filled
        executed_order = _make_executed_order(
            "AAPL", filled_qty=Decimal("7"), filled_avg_price=Decimal("150.00")
        )
        mock_alpaca_manager.place_market_order.return_value = executed_order

        result = executor.execute_market_order("AAPL", "buy", Decimal("10"))

        # Should still succeed but with actual filled quantity
        assert result.success is True
        assert result.trade_amount == Decimal("7") * Decimal("150.00")

    def test_execute_market_order_no_price_available(self, executor, mock_alpaca_manager):
        """Test market order when fill price is not available."""
        executed_order = _make_executed_order("AAPL")
        executed_order.filled_avg_price = None  # No price data
        mock_alpaca_manager.place_market_order.return_value = executed_order

        result = executor.execute_market_order("AAPL", "buy", Decimal("10"))

        assert result.success is True
        assert result.price is None
        assert result.trade_amount == Decimal("0")  # No trade amount without price

    def test_execute_market_order_with_warnings(
        self, executor, mock_validator, mock_alpaca_manager
    ):
        """Test market order execution with validation warnings."""
        mock_validator.validate_order.return_value = OrderValidationResult(
            is_valid=True,
            adjusted_quantity=None,
            error_message=None,
            warnings=(
                "Market volatility detected",
                "Large order size relative to volume",
            ),
        )
        executed_order = _make_executed_order("AAPL")
        mock_alpaca_manager.place_market_order.return_value = executed_order

        with patch("the_alchemiser.execution_v2.core.market_order_executor.logger") as mock_logger:
            result = executor.execute_market_order("AAPL", "buy", Decimal("10"))

            assert result.success is True
            # Verify warnings were logged
            assert mock_logger.warning.call_count >= 2

    def test_execute_market_order_decimal_precision(self, executor, mock_alpaca_manager):
        """Test that Decimal precision is maintained throughout execution."""
        # Use precise Decimal values
        executed_order = _make_executed_order(
            "AAPL",
            filled_qty=Decimal("10.123456"),
            filled_avg_price=Decimal("150.789012"),
        )
        mock_alpaca_manager.place_market_order.return_value = executed_order

        result = executor.execute_market_order("AAPL", "buy", Decimal("10.123456"))

        # Verify Decimal types are preserved
        assert isinstance(result.shares, Decimal)
        assert isinstance(result.price, Decimal)
        assert isinstance(result.trade_amount, Decimal)
        # Verify precision is maintained (not converted to float)
        expected_amount = Decimal("10.123456") * Decimal("150.789012")
        # Use Decimal comparison
        assert abs(result.trade_amount - expected_amount) < Decimal("0.000001")

    def test_execute_market_order_insufficient_buying_power(
        self, executor, mock_buying_power_service, mock_alpaca_manager
    ):
        """Test market order fails when insufficient buying power."""
        # Buying power service indicates insufficient funds
        mock_alpaca_manager.get_current_price.return_value = Decimal("150.00")
        mock_buying_power_service.verify_buying_power_available.return_value = (
            False,
            Decimal("100.00"),
        )

        # Should catch exception and return failed order result
        result = executor.execute_market_order("AAPL", "buy", Decimal("10"))

        assert result.success is False
        assert "Insufficient buying power" in result.error_message

    def test_execute_market_order_case_insensitive_side(self, executor, mock_alpaca_manager):
        """Test that order side is case-insensitive."""
        executed_order = _make_executed_order("AAPL")
        mock_alpaca_manager.place_market_order.return_value = executed_order

        # Test various cases
        for side_input in ["buy", "BUY", "Buy"]:
            result = executor.execute_market_order("AAPL", side_input, Decimal("10"))
            assert result.success is True
            assert result.action == "BUY"  # Normalized to uppercase

        for side_input in ["sell", "SELL", "Sell"]:
            result = executor.execute_market_order("AAPL", side_input, Decimal("10"))
            assert result.success is True
            assert result.action == "SELL"  # Normalized to uppercase

    def test_execute_market_order_with_correlation_id(self, executor, mock_alpaca_manager):
        """Test that correlation_id is propagated through order execution."""
        executed_order = _make_executed_order("AAPL")
        mock_alpaca_manager.place_market_order.return_value = executed_order

        with patch(
            "the_alchemiser.execution_v2.core.market_order_executor.log_order_flow"
        ) as mock_log_order_flow:
            result = executor.execute_market_order(
                "AAPL", "buy", Decimal("10"), correlation_id="test-correlation-123"
            )

            assert result.success is True
            # Verify log_order_flow was called with correlation_id
            mock_log_order_flow.assert_called_once()
            call_kwargs = mock_log_order_flow.call_args[1]
            assert call_kwargs.get("correlation_id") == "test-correlation-123"
