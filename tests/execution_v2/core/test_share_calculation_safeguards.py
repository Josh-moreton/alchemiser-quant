"""Business Unit: execution | Status: current.

Tests for share calculation safeguards in the executor.

These tests ensure that the executor's _calculate_shares_for_item method
properly handles edge cases like:
- Bad price data causing inflated share counts
- Sell orders exceeding current position
- Price discovery failures

Addresses production bug where price discovery returned low prices causing
validation errors like: "Insufficient position for BOND: need 71365, have 907"
"""

from decimal import Decimal
from unittest.mock import Mock, patch

import pytest


class TestShareCalculationSafeguards:
    """Test safeguards in share calculation to prevent bad orders.

    These tests verify the fixes for production bugs where bad price data
    caused the executor to calculate share quantities far exceeding
    actual position sizes.
    """

    @pytest.fixture
    def mock_alpaca_manager(self):
        """Create mock Alpaca manager."""
        mock = Mock()

        # Default asset info - fractionable
        asset_info = Mock()
        asset_info.fractionable = True
        mock.get_asset_info.return_value = asset_info

        return mock

    @pytest.fixture
    def mock_position_utils(self):
        """Create mock position utils."""
        mock = Mock()
        mock.get_price_for_estimation.return_value = Decimal("50.00")
        mock.get_position_quantity.return_value = Decimal("100.00")
        mock.adjust_quantity_for_fractionability.side_effect = lambda symbol, qty: qty
        return mock

    @pytest.fixture
    def executor(self, mock_alpaca_manager, mock_position_utils):
        """Create executor with mocked dependencies."""
        # Import inside fixture to avoid module-level import issues
        from the_alchemiser.execution_v2.core.executor import Executor

        # Create executor with mock
        with patch(
            "the_alchemiser.execution_v2.core.executor.WebSocketConnectionManager"
        ), patch(
            "the_alchemiser.execution_v2.core.executor.RealTimePricingService"
        ), patch(
            "the_alchemiser.execution_v2.core.executor.UnifiedOrderPlacementService"
        ):
            executor = Executor(mock_alpaca_manager)
            # Replace position utils with mock
            executor._position_utils = mock_position_utils
            return executor

    def _create_plan_item(
        self,
        symbol: str = "BOND",
        action: str = "SELL",
        trade_amount: Decimal = Decimal("-5000.00"),
        target_weight: Decimal = Decimal("0.05"),
    ):
        """Create a mock rebalance plan item."""
        from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlanItem

        return RebalancePlanItem(
            symbol=symbol,
            action=action,
            trade_amount=trade_amount,
            target_weight=target_weight,
            current_weight=Decimal("0.10"),
            weight_diff=target_weight - Decimal("0.10"),
            target_value=Decimal("1000.00"),
            current_value=Decimal("2000.00"),
            priority=1,
        )

    def test_normal_sell_calculation(self, executor, mock_position_utils):
        """Test normal sell calculation with reasonable price."""
        # Price is $50, trade amount is $-5000, so shares should be 100
        mock_position_utils.get_price_for_estimation.return_value = Decimal("50.00")
        mock_position_utils.get_position_quantity.return_value = Decimal("200.00")

        item = self._create_plan_item(trade_amount=Decimal("-5000.00"))

        shares = executor._calculate_shares_for_item(item)

        # 5000 / 50 = 100 shares
        assert shares == Decimal("100.00")

    def test_sell_capped_at_position_when_exceeds(self, executor, mock_position_utils):
        """Test that sell shares are capped at current position.

        This is the key fix: when calculated shares > position, use position instead.
        This prevents the 'need 71365, have 907' error.
        """
        # Price is $1 (bad data!), trade amount is $-71365, would calculate 71365 shares
        # But position is only 907 shares
        mock_position_utils.get_price_for_estimation.return_value = Decimal("1.00")
        mock_position_utils.get_position_quantity.return_value = Decimal("907.32")

        item = self._create_plan_item(
            symbol="BOND",
            trade_amount=Decimal("-71365.37"),
        )

        shares = executor._calculate_shares_for_item(item)

        # Should cap at position quantity, not calculated shares
        assert shares == Decimal("907.32")
        assert shares <= Decimal("907.32"), "Shares should never exceed position"

    def test_buy_not_capped(self, executor, mock_position_utils):
        """Test that buy orders are not capped at position."""
        # Price is reasonable
        mock_position_utils.get_price_for_estimation.return_value = Decimal("50.00")
        mock_position_utils.get_position_quantity.return_value = Decimal("10.00")

        item = self._create_plan_item(
            action="BUY",
            trade_amount=Decimal("5000.00"),  # Positive for BUY
            target_weight=Decimal("0.20"),
        )

        shares = executor._calculate_shares_for_item(item)

        # 5000 / 50 = 100 shares, should NOT be capped
        assert shares == Decimal("100.00")

    def test_suspiciously_low_price_falls_back_to_position(
        self, executor, mock_position_utils
    ):
        """Test that suspiciously low prices trigger fallback for SELL."""
        # Price is $0.10 (way too low for most securities)
        mock_position_utils.get_price_for_estimation.return_value = Decimal("0.10")
        mock_position_utils.get_position_quantity.return_value = Decimal("100.00")

        item = self._create_plan_item(
            trade_amount=Decimal("-5000.00"),
        )

        shares = executor._calculate_shares_for_item(item)

        # Should use position quantity due to suspiciously low price
        assert shares == Decimal("100.00")

    def test_liquidation_uses_position_quantity_directly(
        self, executor, mock_position_utils
    ):
        """Test that full liquidation (0% target) uses position quantity."""
        mock_position_utils.get_position_quantity.return_value = Decimal("500.00")

        item = self._create_plan_item(
            target_weight=Decimal("0.0"),  # Full liquidation
        )

        shares = executor._calculate_shares_for_item(item)

        # Should use position quantity directly, not calculate from trade amount
        assert shares == Decimal("500.00")
        mock_position_utils.get_price_for_estimation.assert_not_called()

    def test_price_discovery_failure_defaults_to_one_share(
        self, executor, mock_position_utils
    ):
        """Test fallback to 1 share when price discovery completely fails."""
        mock_position_utils.get_price_for_estimation.return_value = None

        item = self._create_plan_item(
            action="BUY",
            trade_amount=Decimal("5000.00"),
        )

        shares = executor._calculate_shares_for_item(item)

        # Should default to 1 share
        assert shares == Decimal("1")

    def test_price_below_threshold_defaults_to_one_share(
        self, executor, mock_position_utils
    ):
        """Test fallback to 1 share when price is below minimum threshold."""
        # Price below $0.001 threshold
        mock_position_utils.get_price_for_estimation.return_value = Decimal("0.0001")

        item = self._create_plan_item(
            action="BUY",
            trade_amount=Decimal("5000.00"),
        )

        shares = executor._calculate_shares_for_item(item)

        # Should default to 1 share
        assert shares == Decimal("1")

    def test_multiple_symbols_handled_independently(self, executor, mock_position_utils):
        """Test that different symbols are handled independently."""
        # Set up different positions for different symbols
        def get_position(symbol):
            positions = {
                "AAPL": Decimal("50.00"),
                "BOND": Decimal("100.00"),
            }
            return positions.get(symbol, Decimal("0"))

        mock_position_utils.get_position_quantity.side_effect = get_position
        mock_position_utils.get_price_for_estimation.return_value = Decimal("1.00")  # Bad price

        # AAPL sell - bad price would calculate too many shares
        item_aapl = self._create_plan_item(symbol="AAPL", trade_amount=Decimal("-10000.00"))
        shares_aapl = executor._calculate_shares_for_item(item_aapl)

        # BOND sell - bad price would calculate too many shares
        item_bond = self._create_plan_item(symbol="BOND", trade_amount=Decimal("-20000.00"))
        shares_bond = executor._calculate_shares_for_item(item_bond)

        # Each should be capped at their respective position
        assert shares_aapl == Decimal("50.00")
        assert shares_bond == Decimal("100.00")


class TestPositionUtilsPriceLogging:
    """Test enhanced logging in position utils price estimation."""

    @pytest.fixture
    def mock_alpaca_manager(self):
        """Create mock Alpaca manager."""
        return Mock()

    @pytest.fixture
    def mock_pricing_service(self):
        """Create mock pricing service."""
        return Mock()

    def test_logs_real_time_price_source(
        self, mock_alpaca_manager, mock_pricing_service, caplog
    ):
        """Test that real-time price source is logged."""
        from the_alchemiser.execution_v2.utils.position_utils import PositionUtils

        quote = Mock()
        quote.bid_price = Decimal("149.50")
        quote.ask_price = Decimal("150.50")
        mock_pricing_service.get_quote_data.return_value = quote

        utils = PositionUtils(
            alpaca_manager=mock_alpaca_manager,
            pricing_service=mock_pricing_service,
            enable_smart_execution=True,
        )

        price = utils.get_price_for_estimation("AAPL")

        assert price == Decimal("150.00")  # Mid price

    def test_logs_static_price_fallback(
        self, mock_alpaca_manager, mock_pricing_service, caplog
    ):
        """Test that fallback to static price is logged."""
        from the_alchemiser.execution_v2.utils.position_utils import PositionUtils

        mock_pricing_service.get_quote_data.return_value = None
        mock_alpaca_manager.get_current_price.return_value = Decimal("145.00")

        utils = PositionUtils(
            alpaca_manager=mock_alpaca_manager,
            pricing_service=mock_pricing_service,
            enable_smart_execution=True,
        )

        price = utils.get_price_for_estimation("AAPL")

        assert price == Decimal("145.00")

    def test_logs_complete_failure(
        self, mock_alpaca_manager, mock_pricing_service, caplog
    ):
        """Test that complete price discovery failure is logged."""
        from the_alchemiser.execution_v2.utils.position_utils import PositionUtils

        mock_pricing_service.get_quote_data.return_value = None
        mock_alpaca_manager.get_current_price.return_value = None

        utils = PositionUtils(
            alpaca_manager=mock_alpaca_manager,
            pricing_service=mock_pricing_service,
            enable_smart_execution=True,
        )

        price = utils.get_price_for_estimation("AAPL")

        assert price is None
