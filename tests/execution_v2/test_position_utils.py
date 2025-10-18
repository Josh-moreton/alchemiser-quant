"""Business Unit: execution | Status: current

Test position utilities functionality.

Tests position management, pricing, and subscription operations without broker dependencies.
"""

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import Mock

import pytest

from the_alchemiser.execution_v2.utils.position_utils import PositionUtils
from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlan, RebalancePlanItem


def _make_rebalance_plan_item(
    symbol: str = "AAPL",
    *,
    action: str = "BUY",
    trade_amount: Decimal = Decimal("1000.00"),
) -> RebalancePlanItem:
    """Create a test rebalance plan item."""
    return RebalancePlanItem(
        symbol=symbol,
        action=action,
        trade_amount=trade_amount,
        target_weight=Decimal("0.5"),
        current_weight=Decimal("0.3"),
        weight_diff=Decimal("0.2"),
        target_value=Decimal("5000.00"),
        current_value=Decimal("3000.00"),
        priority=1,
    )


def _make_rebalance_plan(items: list[RebalancePlanItem]) -> RebalancePlan:
    """Create a test rebalance plan."""
    return RebalancePlan(
        plan_id=f"plan-{uuid.uuid4()}",
        items=items,
        total_trade_value=sum(abs(item.trade_amount) for item in items),
        total_portfolio_value=Decimal("10000.00"),
        correlation_id=f"corr-{uuid.uuid4()}",
        causation_id=f"cause-{uuid.uuid4()}",
        timestamp=datetime.now(UTC),
    )


class TestPositionUtils:
    """Test position utilities."""

    @pytest.fixture
    def mock_alpaca_manager(self):
        """Mock Alpaca manager."""
        mock = Mock()
        mock.get_current_price.return_value = Decimal("150.00")

        # Mock asset info for fractionability
        asset_info = Mock()
        asset_info.fractionable = True
        mock.get_asset_info.return_value = asset_info

        # Mock position
        position = Mock()
        position.qty = Decimal("10")
        mock.get_position.return_value = position

        return mock

    @pytest.fixture
    def mock_pricing_service(self):
        """Mock real-time pricing service."""
        mock = Mock()

        # Mock quote data
        quote = Mock()
        quote.bid_price = 149.50
        quote.ask_price = 150.50
        mock.get_quote_data.return_value = quote

        # Mock subscription
        mock.subscribe_symbols_bulk.return_value = {"AAPL": True, "MSFT": True}

        return mock

    @pytest.fixture
    def position_utils(self, mock_alpaca_manager, mock_pricing_service):
        """Create position utils."""
        return PositionUtils(
            alpaca_manager=mock_alpaca_manager,
            pricing_service=mock_pricing_service,
            enable_smart_execution=True,
        )

    @pytest.fixture
    def position_utils_no_smart(self, mock_alpaca_manager):
        """Create position utils without smart execution."""
        return PositionUtils(
            alpaca_manager=mock_alpaca_manager,
            pricing_service=None,
            enable_smart_execution=False,
        )

    def test_initialization(self, mock_alpaca_manager, mock_pricing_service):
        """Test position utils initializes with required dependencies."""
        utils = PositionUtils(
            alpaca_manager=mock_alpaca_manager,
            pricing_service=mock_pricing_service,
            enable_smart_execution=True,
        )

        assert utils.alpaca_manager is mock_alpaca_manager
        assert utils.pricing_service is mock_pricing_service
        assert utils.enable_smart_execution is True

    def test_extract_all_symbols_single_action(self, position_utils):
        """Test extracting symbols from plan with single action type."""
        items = [
            _make_rebalance_plan_item("AAPL", action="BUY"),
            _make_rebalance_plan_item("MSFT", action="BUY"),
            _make_rebalance_plan_item("GOOGL", action="BUY"),
        ]
        plan = _make_rebalance_plan(items)

        symbols = position_utils.extract_all_symbols(plan)

        assert len(symbols) == 3
        assert "AAPL" in symbols
        assert "MSFT" in symbols
        assert "GOOGL" in symbols
        # Should be sorted
        assert symbols == sorted(symbols)

    def test_extract_all_symbols_mixed_actions(self, position_utils):
        """Test extracting symbols with buy and sell actions."""
        items = [
            _make_rebalance_plan_item("AAPL", action="BUY"),
            _make_rebalance_plan_item("MSFT", action="SELL"),
            _make_rebalance_plan_item("GOOGL", action="BUY"),
        ]
        plan = _make_rebalance_plan(items)

        symbols = position_utils.extract_all_symbols(plan)

        assert len(symbols) == 3
        assert set(symbols) == {"AAPL", "GOOGL", "MSFT"}

    def test_extract_all_symbols_duplicates_removed(self, position_utils):
        """Test duplicate symbols are removed."""
        items = [
            _make_rebalance_plan_item("AAPL", action="BUY"),
            _make_rebalance_plan_item("AAPL", action="SELL"),  # Duplicate
        ]
        plan = _make_rebalance_plan(items)

        symbols = position_utils.extract_all_symbols(plan)

        assert len(symbols) == 1
        assert symbols == ["AAPL"]

    def test_extract_all_symbols_ignores_hold(self, position_utils):
        """Test HOLD actions are ignored."""
        items = [
            _make_rebalance_plan_item("AAPL", action="BUY"),
            _make_rebalance_plan_item("MSFT", action="HOLD"),
            _make_rebalance_plan_item("GOOGL", action="SELL"),
        ]
        plan = _make_rebalance_plan(items)

        symbols = position_utils.extract_all_symbols(plan)

        # HOLD should be filtered out
        assert len(symbols) == 2
        assert "MSFT" not in symbols

    def test_bulk_subscribe_symbols_success(self, position_utils, mock_pricing_service):
        """Test bulk subscription to symbols."""
        symbols = ["AAPL", "MSFT", "GOOGL"]

        result = position_utils.bulk_subscribe_symbols(symbols)

        assert mock_pricing_service.subscribe_symbols_bulk.called
        call_args = mock_pricing_service.subscribe_symbols_bulk.call_args
        assert call_args[0][0] == symbols  # First positional arg
        assert "priority" in call_args[1]  # Keyword arg

    def test_bulk_subscribe_symbols_disabled_smart_execution(self, position_utils_no_smart):
        """Test bulk subscription skipped when smart execution disabled."""
        symbols = ["AAPL", "MSFT"]

        result = position_utils_no_smart.bulk_subscribe_symbols(symbols)

        assert result == {}

    def test_bulk_subscribe_symbols_empty_list(self, position_utils):
        """Test bulk subscription with empty symbol list."""
        result = position_utils.bulk_subscribe_symbols([])

        assert result == {}

    def test_cleanup_subscriptions(self, position_utils, mock_pricing_service):
        """Test cleanup of symbol subscriptions."""
        symbols = ["AAPL", "MSFT"]

        position_utils.cleanup_subscriptions(symbols)

        # Should call unsubscribe for each symbol
        assert mock_pricing_service.unsubscribe_symbol.call_count == 2

    def test_cleanup_subscriptions_with_exception(self, position_utils, mock_pricing_service):
        """Test cleanup handles exceptions gracefully."""
        mock_pricing_service.unsubscribe_symbol.side_effect = RuntimeError("Unsubscribe failed")
        symbols = ["AAPL"]

        # Should not raise exception
        position_utils.cleanup_subscriptions(symbols)

    def test_get_price_for_estimation_real_time(self, position_utils, mock_pricing_service):
        """Test getting price from real-time service."""
        price = position_utils.get_price_for_estimation("AAPL")

        assert price == Decimal("150.00")  # Mid price of 149.50 and 150.50
        mock_pricing_service.get_quote_data.assert_called_once_with("AAPL")

    def test_get_price_for_estimation_fallback_static(
        self, position_utils, mock_pricing_service, mock_alpaca_manager
    ):
        """Test fallback to static price when real-time unavailable."""
        mock_pricing_service.get_quote_data.return_value = None
        mock_alpaca_manager.get_current_price.return_value = Decimal("145.00")

        price = position_utils.get_price_for_estimation("AAPL")

        assert price == Decimal("145.00")
        mock_alpaca_manager.get_current_price.assert_called_once_with("AAPL")

    def test_get_price_for_estimation_no_pricing_service(
        self, position_utils_no_smart, mock_alpaca_manager
    ):
        """Test price estimation without real-time pricing service."""
        mock_alpaca_manager.get_current_price.return_value = Decimal("150.00")

        price = position_utils_no_smart.get_price_for_estimation("AAPL")

        assert price == Decimal("150.00")
        # Should go directly to static price
        mock_alpaca_manager.get_current_price.assert_called_once()

    def test_get_price_for_estimation_invalid_prices(self, position_utils, mock_pricing_service):
        """Test handling of invalid quote prices."""
        quote = Mock()
        quote.bid_price = 0  # Invalid
        quote.ask_price = 0  # Invalid
        mock_pricing_service.get_quote_data.return_value = quote

        # Should fall back to static price
        price = position_utils.get_price_for_estimation("AAPL")

        # Will use static fallback
        assert price is not None

    def test_adjust_quantity_for_fractionability_fractional(
        self, position_utils, mock_alpaca_manager
    ):
        """Test quantity adjustment for fractional shares."""
        asset_info = Mock()
        asset_info.fractionable = True
        mock_alpaca_manager.get_asset_info.return_value = asset_info

        adjusted = position_utils.adjust_quantity_for_fractionability(
            "AAPL", Decimal("10.123456789")
        )

        # Should keep fractional but limit to 6 decimal places
        assert adjusted == Decimal("10.123457")
        assert isinstance(adjusted, Decimal)

    def test_adjust_quantity_for_fractionability_whole_shares(
        self, position_utils, mock_alpaca_manager
    ):
        """Test quantity adjustment for whole shares only."""
        asset_info = Mock()
        asset_info.fractionable = False
        mock_alpaca_manager.get_asset_info.return_value = asset_info

        adjusted = position_utils.adjust_quantity_for_fractionability("AAPL", Decimal("10.75"))

        # Should round down to whole shares
        assert adjusted == Decimal("10")
        assert isinstance(adjusted, Decimal)

    def test_adjust_quantity_for_fractionability_float_input(
        self, position_utils, mock_alpaca_manager
    ):
        """Test quantity adjustment handles float input."""
        asset_info = Mock()
        asset_info.fractionable = False
        mock_alpaca_manager.get_asset_info.return_value = asset_info

        # Pass float instead of Decimal
        adjusted = position_utils.adjust_quantity_for_fractionability("AAPL", 10.75)

        assert adjusted == Decimal("10")
        assert isinstance(adjusted, Decimal)

    def test_adjust_quantity_for_fractionability_error_handling(
        self, position_utils, mock_alpaca_manager
    ):
        """Test quantity adjustment with asset info error."""
        mock_alpaca_manager.get_asset_info.side_effect = RuntimeError("Asset not found")

        # Should default to whole shares on error
        adjusted = position_utils.adjust_quantity_for_fractionability("UNKNOWN", Decimal("10.75"))

        assert adjusted == Decimal("10")

    def test_get_position_quantity_existing_position(self, position_utils, mock_alpaca_manager):
        """Test getting quantity for existing position."""
        position = Mock()
        position.qty = Decimal("25.5")
        mock_alpaca_manager.get_position.return_value = position

        quantity = position_utils.get_position_quantity("AAPL")

        assert quantity == Decimal("25.5")
        assert isinstance(quantity, Decimal)

    def test_get_position_quantity_no_position(self, position_utils, mock_alpaca_manager):
        """Test getting quantity when no position exists."""
        mock_alpaca_manager.get_position.return_value = None

        quantity = position_utils.get_position_quantity("AAPL")

        assert quantity == Decimal("0")

    def test_get_position_quantity_string_qty(self, position_utils, mock_alpaca_manager):
        """Test getting position quantity when broker returns string."""
        position = Mock()
        position.qty = "15.25"  # String instead of Decimal
        mock_alpaca_manager.get_position.return_value = position

        quantity = position_utils.get_position_quantity("AAPL")

        assert quantity == Decimal("15.25")
        assert isinstance(quantity, Decimal)

    def test_get_position_quantity_exception_handling(self, position_utils, mock_alpaca_manager):
        """Test position quantity handles exceptions."""
        mock_alpaca_manager.get_position.side_effect = RuntimeError("API error")

        quantity = position_utils.get_position_quantity("AAPL")

        assert quantity == Decimal("0")

    def test_decimal_precision_throughout(self, position_utils, mock_alpaca_manager):
        """Test that Decimal precision is maintained throughout operations."""
        # Test with very precise Decimal values
        precise_qty = Decimal("10.123456789012345")

        # Fractional asset
        asset_info = Mock()
        asset_info.fractionable = True
        mock_alpaca_manager.get_asset_info.return_value = asset_info

        adjusted = position_utils.adjust_quantity_for_fractionability("AAPL", precise_qty)

        # Should maintain precision (limited to 6 decimals)
        assert isinstance(adjusted, Decimal)
        # No float conversion
        assert str(adjusted) == "10.123457"


class TestFractionalLiquidationEdgeCase:
    """Test edge cases for liquidating fractional positions of non-fractionable assets.

    This test class specifically addresses the bug where EDZ (non-fractionable) had
    0.3 shares in the position but liquidation rounded down to 0 shares, causing
    order placement failure.
    """

    @pytest.fixture
    def mock_alpaca_manager(self):
        """Mock Alpaca manager."""
        return Mock()

    @pytest.fixture
    def position_utils(self, mock_alpaca_manager):
        """Create position utils without pricing service (not needed for these tests)."""
        return PositionUtils(
            alpaca_manager=mock_alpaca_manager,
            pricing_service=None,
            enable_smart_execution=False,
        )

    def test_liquidation_preserves_fractional_quantity_for_non_fractionable(
        self, position_utils, mock_alpaca_manager
    ):
        """Test that liquidation does NOT round down fractional positions.

        This is the EDZ bug fix: even for non-fractionable assets, we must sell
        the exact position quantity during liquidation, not apply rounding rules.
        """
        # Setup: EDZ is non-fractionable but has 0.3 shares in position
        asset_info = Mock()
        asset_info.fractionable = False  # EDZ does not support fractional BUYS
        mock_alpaca_manager.get_asset_info.return_value = asset_info

        position = Mock()
        position.qty = Decimal("0.3")  # The exact EDZ position from the bug
        mock_alpaca_manager.get_position.return_value = position

        # Act: Get position quantity (as used in liquidation)
        # NOTE: For liquidation, we should NOT call adjust_quantity_for_fractionability
        # as that would round down to 0
        quantity = position_utils.get_position_quantity("EDZ")

        # Assert: Must preserve exact fractional quantity for liquidation
        assert quantity == Decimal("0.3"), (
            "Liquidation must sell exact position (0.3 shares) even for "
            "non-fractionable assets like EDZ"
        )

    def test_fractionability_adjustment_does_round_for_new_purchases(
        self, position_utils, mock_alpaca_manager
    ):
        """Test that fractionability rules DO apply to new purchases.

        This confirms that the rounding logic still works correctly for NEW
        BUY orders, just not for liquidations.
        """
        # Setup: Non-fractionable asset
        asset_info = Mock()
        asset_info.fractionable = False
        mock_alpaca_manager.get_asset_info.return_value = asset_info

        # Act: Adjust quantity for a NEW purchase (not liquidation)
        adjusted = position_utils.adjust_quantity_for_fractionability("EDZ", Decimal("0.3"))

        # Assert: NEW purchases should round down to whole shares
        assert adjusted == Decimal("0"), (
            "New purchases of non-fractionable assets should round down to whole shares (0.3 → 0)"
        )

    def test_liquidation_various_fractional_amounts(self, position_utils, mock_alpaca_manager):
        """Test liquidation preserves various fractional position amounts."""
        asset_info = Mock()
        asset_info.fractionable = False
        mock_alpaca_manager.get_asset_info.return_value = asset_info

        test_cases = [
            Decimal("0.1"),
            Decimal("0.3"),  # The EDZ case
            Decimal("0.5"),
            Decimal("0.9"),
            Decimal("1.3"),  # Also has whole share
            Decimal("2.7"),
        ]

        for qty in test_cases:
            position = Mock()
            position.qty = qty
            mock_alpaca_manager.get_position.return_value = position

            quantity = position_utils.get_position_quantity("EDZ")

            assert quantity == qty, f"Liquidation must preserve exact quantity {qty}, not round it"
