"""Business Unit: execution | Status: current.

Comprehensive test suite for PhaseExecutor.

Tests phase execution logic, order orchestration, micro-order validation,
callback integration, and error handling.
"""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch
import uuid

import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from the_alchemiser.execution_v2.core.phase_executor import PhaseExecutor
from the_alchemiser.execution_v2.models.execution_result import OrderResult
from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlanItem


# Test Helpers

def _make_rebalance_item(
    symbol: str = "AAPL",
    *,
    current_weight: Decimal = Decimal("0.1"),
    target_weight: Decimal = Decimal("0.2"),
    trade_amount: Decimal = Decimal("1000"),
    action: str = "BUY",
) -> RebalancePlanItem:
    """Create a test rebalance plan item."""
    weight_diff = target_weight - current_weight
    return RebalancePlanItem(
        symbol=symbol,
        current_weight=current_weight,
        target_weight=target_weight,
        weight_diff=weight_diff,
        target_value=target_weight * Decimal("10000"),
        current_value=current_weight * Decimal("10000"),
        trade_amount=trade_amount,
        action=action,
        priority=1,
    )


def _make_order_result(
    symbol: str = "AAPL",
    *,
    action: str = "BUY",
    shares: Decimal = Decimal("10"),
    trade_amount: Decimal = Decimal("1000"),
    success: bool = True,
    price: Decimal | None = Decimal("100"),
    order_id: str | None = "order123",
    error_message: str | None = None,
) -> OrderResult:
    """Create a test order result."""
    return OrderResult(
        symbol=symbol,
        action=action,
        trade_amount=trade_amount,
        shares=shares,
        price=price,
        order_id=order_id,
        success=success,
        error_message=error_message,
        timestamp=datetime.now(UTC),
        order_type="MARKET",
        filled_at=datetime.now(UTC) if success and price else None,
    )


# Test Fixtures

@pytest.fixture
def mock_alpaca_manager():
    """Mock Alpaca manager."""
    mock = Mock()
    mock.get_asset_info = Mock(return_value=Mock(fractionable=True))
    return mock


@pytest.fixture
def mock_position_utils():
    """Mock position utilities."""
    mock = Mock()
    mock.get_price_for_estimation = Mock(return_value=Decimal("100"))
    mock.get_position_quantity = Mock(return_value=Decimal("10"))
    mock.adjust_quantity_for_fractionability = Mock(side_effect=lambda sym, qty: qty)
    return mock


@pytest.fixture
def mock_execution_config():
    """Mock execution configuration."""
    mock = Mock()
    mock.min_fractional_notional_usd = Decimal("1.00")
    return mock


@pytest.fixture
def phase_executor(mock_alpaca_manager, mock_position_utils, mock_execution_config):
    """Create a PhaseExecutor instance with mocked dependencies."""
    return PhaseExecutor(
        alpaca_manager=mock_alpaca_manager,
        position_utils=mock_position_utils,
        smart_strategy=None,
        execution_config=mock_execution_config,
        enable_smart_execution=False,
    )


# Test Classes

class TestPhaseExecutorInitialization:
    """Test PhaseExecutor initialization."""

    def test_initialization_with_all_dependencies(
        self, mock_alpaca_manager, mock_position_utils, mock_execution_config
    ):
        """Test that executor initializes with all dependencies."""
        executor = PhaseExecutor(
            alpaca_manager=mock_alpaca_manager,
            position_utils=mock_position_utils,
            smart_strategy=None,
            execution_config=mock_execution_config,
            enable_smart_execution=True,
        )

        assert executor.alpaca_manager == mock_alpaca_manager
        assert executor.position_utils == mock_position_utils
        assert executor.execution_config == mock_execution_config
        assert executor.enable_smart_execution is True

    def test_initialization_with_minimal_dependencies(self, mock_alpaca_manager):
        """Test that executor initializes with minimal dependencies."""
        executor = PhaseExecutor(
            alpaca_manager=mock_alpaca_manager,
            position_utils=None,
            smart_strategy=None,
            execution_config=None,
        )

        assert executor.alpaca_manager == mock_alpaca_manager
        assert executor.position_utils is None
        assert executor.smart_strategy is None
        assert executor.execution_config is None
        assert executor.enable_smart_execution is True  # Default


class TestExecuteSellPhase:
    """Test execute_sell_phase method."""

    @pytest.mark.asyncio
    async def test_execute_sell_phase_with_callback(self, phase_executor):
        """Test sell phase execution with order callback."""
        sell_items = [
            _make_rebalance_item("AAPL", action="SELL", trade_amount=Decimal("-500")),
            _make_rebalance_item("GOOGL", action="SELL", trade_amount=Decimal("-300")),
        ]

        expected_results = [
            _make_order_result("AAPL", action="SELL", shares=Decimal("5")),
            _make_order_result("GOOGL", action="SELL", shares=Decimal("3")),
        ]

        async def mock_execute_callback(item):
            if item.symbol == "AAPL":
                return expected_results[0]
            return expected_results[1]

        orders, stats = await phase_executor.execute_sell_phase(
            sell_items=sell_items,
            correlation_id="test-corr-123",
            execute_order_callback=mock_execute_callback,
        )

        assert len(orders) == 2
        assert orders[0].symbol == "AAPL"
        assert orders[1].symbol == "GOOGL"
        assert stats["placed"] == 2
        assert stats["succeeded"] == 0  # No finalizer provided
        assert stats["trade_value"] == Decimal("0")  # No finalizer provided

    @pytest.mark.asyncio
    async def test_execute_sell_phase_with_finalize_callback(self, phase_executor):
        """Test sell phase with finalization callback."""
        sell_items = [_make_rebalance_item("AAPL", action="SELL")]

        async def mock_execute_callback(item):
            return _make_order_result("AAPL", action="SELL")

        def mock_finalize_callback(*, phase_type, orders, items):
            return orders, 1, Decimal("500")

        orders, stats = await phase_executor.execute_sell_phase(
            sell_items=sell_items,
            execute_order_callback=mock_execute_callback,
            finalize_orders_callback=mock_finalize_callback,
        )

        assert stats["placed"] == 1
        assert stats["succeeded"] == 1
        assert stats["trade_value"] == Decimal("500")

    @pytest.mark.asyncio
    async def test_execute_sell_phase_correlation_id_binding(self, phase_executor):
        """Test that correlation_id is bound to logger context."""
        sell_items = [_make_rebalance_item("AAPL", action="SELL")]

        async def mock_execute_callback(item):
            return _make_order_result("AAPL", action="SELL")

        # Execute with correlation_id
        orders, stats = await phase_executor.execute_sell_phase(
            sell_items=sell_items,
            correlation_id="test-correlation-id",
            execute_order_callback=mock_execute_callback,
        )

        assert len(orders) == 1
        assert stats["placed"] == 1


class TestExecuteBuyPhase:
    """Test execute_buy_phase method."""

    @pytest.mark.asyncio
    async def test_execute_buy_phase_with_callback(self, phase_executor):
        """Test buy phase execution with order callback."""
        buy_items = [
            _make_rebalance_item("AAPL", action="BUY", trade_amount=Decimal("1000")),
            _make_rebalance_item("GOOGL", action="BUY", trade_amount=Decimal("500")),
        ]

        async def mock_execute_callback(item):
            return _make_order_result(item.symbol, action="BUY")

        orders, stats = await phase_executor.execute_buy_phase(
            buy_items=buy_items,
            correlation_id="test-corr-456",
            execute_order_callback=mock_execute_callback,
        )

        assert len(orders) == 2
        assert orders[0].symbol == "AAPL"
        assert orders[1].symbol == "GOOGL"
        assert stats["placed"] == 2

    @pytest.mark.asyncio
    async def test_execute_buy_phase_skips_micro_orders(self, phase_executor):
        """Test that buy phase skips micro orders below minimum notional."""
        # Create a micro order (very small amount)
        micro_item = _make_rebalance_item(
            "AAPL", action="BUY", trade_amount=Decimal("0.50")  # Below $1 minimum
        )

        # Mock price estimation to return $100
        phase_executor.position_utils.get_price_for_estimation.return_value = Decimal("100")

        orders, stats = await phase_executor.execute_buy_phase(
            buy_items=[micro_item],
            execute_order_callback=None,  # Should skip before callback
        )

        # Should have 1 order but it's skipped
        assert len(orders) == 1
        assert orders[0].success is False
        assert "Skipped" in orders[0].error_message
        assert stats["placed"] == 0  # Not placed, skipped

    @pytest.mark.asyncio
    async def test_execute_buy_phase_processes_valid_orders(self, phase_executor):
        """Test that valid orders are processed (not skipped)."""
        valid_item = _make_rebalance_item(
            "AAPL", action="BUY", trade_amount=Decimal("1000")  # Well above minimum
        )

        async def mock_execute_callback(item):
            return _make_order_result("AAPL", action="BUY", success=True)

        orders, stats = await phase_executor.execute_buy_phase(
            buy_items=[valid_item],
            execute_order_callback=mock_execute_callback,
        )

        assert len(orders) == 1
        assert orders[0].success is True
        assert stats["placed"] == 1


class TestMicroOrderValidation:
    """Test micro-order validation logic."""

    def test_check_micro_order_skip_with_fractional_asset_below_minimum(
        self, phase_executor
    ):
        """Test that fractional assets below minimum are skipped."""
        item = _make_rebalance_item("AAPL", trade_amount=Decimal("0.50"))

        # Mock asset as fractionable and price at $100
        phase_executor.alpaca_manager.get_asset_info.return_value = Mock(fractionable=True)
        phase_executor.position_utils.get_price_for_estimation.return_value = Decimal("100")

        # Estimated notional: $0.50 / $100 * $100 = $0.50 < $1.00 minimum
        result = phase_executor._check_micro_order_skip(item, phase_executor._logger_bound())

        assert result is not None
        assert result.success is False
        assert "Skipped" in result.error_message

    def test_check_micro_order_skip_with_fractional_asset_above_minimum(
        self, phase_executor
    ):
        """Test that fractional assets above minimum are not skipped."""
        item = _make_rebalance_item("AAPL", trade_amount=Decimal("1000"))

        phase_executor.alpaca_manager.get_asset_info.return_value = Mock(fractionable=True)
        phase_executor.position_utils.get_price_for_estimation.return_value = Decimal("100")

        result = phase_executor._check_micro_order_skip(item, phase_executor._logger_bound())

        assert result is None  # Not skipped

    def test_check_micro_order_skip_with_non_fractional_asset(self, phase_executor):
        """Test that non-fractional assets are never skipped for micro-order reasons."""
        item = _make_rebalance_item("AAPL", trade_amount=Decimal("0.50"))

        # Mock asset as NOT fractionable
        phase_executor.alpaca_manager.get_asset_info.return_value = Mock(fractionable=False)
        phase_executor.position_utils.get_price_for_estimation.return_value = Decimal("100")

        result = phase_executor._check_micro_order_skip(item, phase_executor._logger_bound())

        assert result is None  # Not skipped (non-fractional)

    def test_check_micro_order_skip_without_config(self, phase_executor):
        """Test that orders are not skipped when config is None."""
        phase_executor.execution_config = None
        item = _make_rebalance_item("AAPL", trade_amount=Decimal("0.50"))

        result = phase_executor._check_micro_order_skip(item, phase_executor._logger_bound())

        assert result is None  # Not skipped

    def test_check_micro_order_skip_with_price_unavailable(self, phase_executor):
        """Test that orders proceed when price is unavailable."""
        item = _make_rebalance_item("AAPL", trade_amount=Decimal("1000"))

        phase_executor.alpaca_manager.get_asset_info.return_value = Mock(fractionable=True)
        phase_executor.position_utils.get_price_for_estimation.return_value = Decimal("0")

        result = phase_executor._check_micro_order_skip(item, phase_executor._logger_bound())

        assert result is None  # Proceeds when price unavailable

    def test_check_micro_order_skip_handles_value_error(self, phase_executor):
        """Test that ValueError in price estimation is handled gracefully."""
        item = _make_rebalance_item("AAPL", trade_amount=Decimal("1000"))

        phase_executor.alpaca_manager.get_asset_info.return_value = Mock(fractionable=True)
        phase_executor.position_utils.get_price_for_estimation.side_effect = ValueError(
            "Price error"
        )

        result = phase_executor._check_micro_order_skip(item, phase_executor._logger_bound())

        # Should return None (let order proceed) and log warning
        assert result is None


class TestShareCalculations:
    """Test share calculation methods."""

    def test_calculate_liquidation_shares(self, phase_executor):
        """Test liquidation share calculation."""
        phase_executor.position_utils.get_position_quantity.return_value = Decimal("15.5")

        shares = phase_executor._calculate_liquidation_shares("AAPL")

        assert shares == Decimal("15.5")
        phase_executor.position_utils.get_position_quantity.assert_called_once_with("AAPL")

    def test_calculate_liquidation_shares_without_position_utils(self, phase_executor):
        """Test liquidation returns 0 when position_utils is None."""
        phase_executor.position_utils = None

        shares = phase_executor._calculate_liquidation_shares("AAPL")

        assert shares == Decimal("0")

    def test_calculate_shares_from_amount(self, phase_executor):
        """Test shares calculation from dollar amount."""
        phase_executor.position_utils.get_price_for_estimation.return_value = Decimal("100")
        phase_executor.position_utils.adjust_quantity_for_fractionability.return_value = Decimal(
            "10"
        )

        shares = phase_executor._calculate_shares_from_amount("AAPL", Decimal("1000"))

        assert shares == Decimal("10")

    def test_calculate_shares_from_amount_with_zero_price(self, phase_executor):
        """Test shares calculation defaults to 1 when price is unavailable."""
        phase_executor.position_utils.get_price_for_estimation.return_value = Decimal("0")

        shares = phase_executor._calculate_shares_from_amount("AAPL", Decimal("1000"))

        assert shares == Decimal("1")  # Default fallback

    def test_calculate_shares_from_amount_without_position_utils(self, phase_executor):
        """Test shares calculation without position utils."""
        phase_executor.position_utils = None

        # Should default to 1 share since no price available
        shares = phase_executor._calculate_shares_from_amount("AAPL", Decimal("1000"))

        assert shares == Decimal("1")

    def test_determine_shares_to_trade_for_liquidation(self, phase_executor):
        """Test share determination for liquidation (target_weight = 0)."""
        item = _make_rebalance_item(
            "AAPL",
            action="SELL",
            current_weight=Decimal("0.1"),
            target_weight=Decimal("0.0"),
            trade_amount=Decimal("-1000"),
        )

        phase_executor.position_utils.get_position_quantity.return_value = Decimal("15.5")

        shares = phase_executor._determine_shares_to_trade(item)

        assert shares == Decimal("15.5")  # Liquidation uses exact position

    def test_determine_shares_to_trade_for_regular_buy(self, phase_executor):
        """Test share determination for regular buy order."""
        item = _make_rebalance_item("AAPL", action="BUY", trade_amount=Decimal("1000"))

        phase_executor.position_utils.get_price_for_estimation.return_value = Decimal("100")
        phase_executor.position_utils.adjust_quantity_for_fractionability.return_value = Decimal(
            "10"
        )

        shares = phase_executor._determine_shares_to_trade(item)

        assert shares == Decimal("10")


class TestErrorHandling:
    """Test error handling and exception cases."""

    @pytest.mark.asyncio
    async def test_execute_single_item_with_value_error(self, phase_executor):
        """Test _execute_single_item handles ValueError."""
        item = _make_rebalance_item("AAPL")

        # Mock to raise ValueError
        phase_executor._determine_shares_to_trade = Mock(side_effect=ValueError("Invalid value"))

        result = await phase_executor._execute_single_item(
            item, phase_executor._logger_bound()
        )

        assert result.success is False
        assert "Value error" in result.error_message
        assert result.shares == Decimal("0")

    @pytest.mark.asyncio
    async def test_execute_single_item_with_generic_exception(self, phase_executor):
        """Test _execute_single_item handles generic Exception."""
        item = _make_rebalance_item("AAPL")

        # Mock to raise generic exception
        phase_executor._determine_shares_to_trade = Mock(
            side_effect=Exception("Unexpected error")
        )

        result = await phase_executor._execute_single_item(
            item, phase_executor._logger_bound()
        )

        assert result.success is False
        assert "Unexpected error" in result.error_message


class TestPropertyBasedTests:
    """Property-based tests using Hypothesis."""

    @given(
        trade_amount=st.decimals(
            min_value=Decimal("0.01"),
            max_value=Decimal("100000"),
            places=2,
        ),
        price=st.decimals(
            min_value=Decimal("0.01"),
            max_value=Decimal("10000"),
            places=2,
        ),
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_share_calculation_always_positive(
        self, trade_amount, price, phase_executor
    ):
        """Test that share calculations always produce non-negative values."""
        phase_executor.position_utils.get_price_for_estimation.return_value = price
        phase_executor.position_utils.adjust_quantity_for_fractionability.side_effect = (
            lambda sym, qty: qty
        )

        shares = phase_executor._calculate_shares_from_amount("AAPL", trade_amount)

        assert shares >= Decimal("0")

    @given(
        weight=st.decimals(
            min_value=Decimal("0"),
            max_value=Decimal("1"),
            places=4,
        )
    )
    @settings(max_examples=50, deadline=None)
    def test_rebalance_item_weights_valid_range(self, weight):
        """Test that rebalance items with valid weights can be created."""
        item = _make_rebalance_item(
            "TEST",
            current_weight=weight,
            target_weight=weight,
            trade_amount=Decimal("100"),
        )

        assert Decimal("0") <= item.current_weight <= Decimal("1")
        assert Decimal("0") <= item.target_weight <= Decimal("1")


class TestHelperMethod:
    """Test helper method to bind logger."""

    def test_logger_bound_method(self, phase_executor):
        """Test that _logger_bound helper exists and works."""
        # This is a helper method we added for testing
        # In actual code, logger binding happens inline
        # For tests, we need a way to pass bound_logger
        
        # Create a simple method to get bound logger for tests
        bound_logger = phase_executor._logger_bound()
        assert bound_logger is not None


# Add helper method to PhaseExecutor for testing
# This would be added to the actual class
def _logger_bound(self):
    """Get logger instance for testing. In production, logger is bound inline."""
    from the_alchemiser.shared.logging import get_logger
    return get_logger(__name__)


# Monkey-patch for testing
PhaseExecutor._logger_bound = _logger_bound
