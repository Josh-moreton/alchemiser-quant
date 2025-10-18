"""Business Unit: execution | Status: current.

Comprehensive test suite for smart execution strategy utility functions.

This module provides unit tests and property-based tests for the utility
functions used in the smart execution strategy, ensuring correctness of
price adjustments, validations, and timing checks.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock

from hypothesis import given
from hypothesis import strategies as st

from the_alchemiser.execution_v2.core.smart_execution_strategy.utils import (
    calculate_price_adjustment,
    ensure_minimum_price,
    fetch_price_for_notional_check,
    is_order_completed,
    is_remaining_quantity_too_small,
    quantize_price_safely,
    should_consider_repeg,
    should_escalate_order,
    validate_repeg_price_with_history,
)
from the_alchemiser.shared.types.market_data import QuoteModel


class TestCalculatePriceAdjustment:
    """Test price adjustment calculations."""

    def test_fifty_percent_adjustment_upward(self):
        """Test 50% adjustment moving price upward."""
        original = Decimal("100.00")
        target = Decimal("110.00")
        result = calculate_price_adjustment(original, target)
        expected = Decimal("105.00")  # 50% of the way from 100 to 110
        assert result == expected

    def test_fifty_percent_adjustment_downward(self):
        """Test 50% adjustment moving price downward."""
        original = Decimal("110.00")
        target = Decimal("100.00")
        result = calculate_price_adjustment(original, target)
        expected = Decimal("105.00")  # 50% of the way from 110 to 100
        assert result == expected

    def test_custom_adjustment_factor_25_percent(self):
        """Test custom 25% adjustment factor."""
        original = Decimal("100.00")
        target = Decimal("200.00")
        result = calculate_price_adjustment(original, target, Decimal("0.25"))
        expected = Decimal("125.00")  # 25% of the way from 100 to 200
        assert result == expected

    def test_custom_adjustment_factor_75_percent(self):
        """Test custom 75% adjustment factor."""
        original = Decimal("100.00")
        target = Decimal("200.00")
        result = calculate_price_adjustment(original, target, Decimal("0.75"))
        expected = Decimal("175.00")  # 75% of the way from 100 to 200
        assert result == expected

    def test_zero_adjustment_factor(self):
        """Test that zero adjustment factor returns original price."""
        original = Decimal("100.00")
        target = Decimal("200.00")
        result = calculate_price_adjustment(original, target, Decimal("0"))
        assert result == original

    def test_full_adjustment_factor(self):
        """Test that 1.0 adjustment factor reaches target price."""
        original = Decimal("100.00")
        target = Decimal("150.00")
        result = calculate_price_adjustment(original, target, Decimal("1"))
        assert result == target

    def test_same_original_and_target(self):
        """Test adjustment when original and target are the same."""
        price = Decimal("100.00")
        result = calculate_price_adjustment(price, price)
        assert result == price

    @given(
        original=st.decimals(
            min_value=Decimal("0.01"),
            max_value=Decimal("10000"),
            places=2,
        ),
        target=st.decimals(
            min_value=Decimal("0.01"),
            max_value=Decimal("10000"),
            places=2,
        ),
        factor=st.decimals(
            min_value=Decimal("0"),
            max_value=Decimal("1"),
            places=2,
        ),
    )
    def test_adjustment_properties(self, original, target, factor):
        """Property test: result should be between original and target."""
        result = calculate_price_adjustment(original, target, factor)

        # Result should be between original and target (inclusive)
        min_price = min(original, target)
        max_price = max(original, target)
        assert min_price <= result <= max_price


class TestValidateRepegPriceWithHistory:
    """Test repeg price validation against price history."""

    def test_new_price_not_in_history_returns_unchanged(self):
        """Test that new unique price is returned unchanged."""
        new_price = Decimal("100.00")
        price_history = [Decimal("99.00"), Decimal("101.00")]
        quote = QuoteModel(
            symbol="AAPL",
            bid_price=99.50,
            ask_price=100.50,
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )

        result = validate_repeg_price_with_history(new_price, price_history, "BUY", quote)
        assert result == new_price

    def test_empty_history_returns_unchanged(self):
        """Test that price is returned unchanged when history is empty."""
        new_price = Decimal("100.00")
        quote = QuoteModel(
            symbol="AAPL",
            bid_price=99.50,
            ask_price=100.50,
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )

        result = validate_repeg_price_with_history(new_price, [], "BUY", quote)
        assert result == new_price

    def test_none_history_returns_unchanged(self):
        """Test that price is returned unchanged when history is None."""
        new_price = Decimal("100.00")
        quote = QuoteModel(
            symbol="AAPL",
            bid_price=99.50,
            ask_price=100.50,
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )

        result = validate_repeg_price_with_history(new_price, None, "BUY", quote)
        assert result == new_price

    def test_buy_duplicate_price_increases_by_min_improvement(self):
        """Test that duplicate buy price is increased by minimum improvement."""
        new_price = Decimal("100.00")
        price_history = [Decimal("99.00"), Decimal("100.00")]
        quote = QuoteModel(
            symbol="AAPL",
            bid_price=99.50,
            ask_price=100.50,
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )

        result = validate_repeg_price_with_history(
            new_price, price_history, "BUY", quote, min_improvement=Decimal("0.01")
        )
        expected = Decimal("100.01")  # Increased by 0.01
        assert result == expected

    def test_sell_duplicate_price_decreases_by_min_improvement(self):
        """Test that duplicate sell price is decreased by minimum improvement."""
        new_price = Decimal("100.00")
        price_history = [Decimal("100.00"), Decimal("101.00")]
        quote = QuoteModel(
            symbol="AAPL",
            bid_price=99.50,
            ask_price=100.50,
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )

        result = validate_repeg_price_with_history(
            new_price, price_history, "SELL", quote, min_improvement=Decimal("0.01")
        )
        expected = Decimal("99.99")  # Decreased by 0.01
        assert result == expected

    def test_custom_min_improvement(self):
        """Test validation with custom minimum improvement value."""
        new_price = Decimal("100.00")
        price_history = [Decimal("100.00")]
        quote = QuoteModel(
            symbol="AAPL",
            bid_price=99.50,
            ask_price=100.50,
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )

        result = validate_repeg_price_with_history(
            new_price, price_history, "BUY", quote, min_improvement=Decimal("0.05")
        )
        expected = Decimal("100.05")  # Increased by 0.05
        assert result == expected

    def test_case_insensitive_side(self):
        """Test that side parameter is case-insensitive."""
        new_price = Decimal("100.00")
        price_history = [Decimal("100.00")]
        quote = QuoteModel(
            symbol="AAPL",
            bid_price=99.50,
            ask_price=100.50,
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )

        result_upper = validate_repeg_price_with_history(new_price, price_history, "BUY", quote)
        result_lower = validate_repeg_price_with_history(new_price, price_history, "buy", quote)
        assert result_upper == result_lower == Decimal("100.01")


class TestShouldEscalateOrder:
    """Test order escalation logic."""

    def test_escalate_when_count_equals_max(self):
        """Test escalation when repeg count equals maximum."""
        assert should_escalate_order(3, 3) is True

    def test_escalate_when_count_exceeds_max(self):
        """Test escalation when repeg count exceeds maximum."""
        assert should_escalate_order(5, 3) is True

    def test_no_escalate_when_count_below_max(self):
        """Test no escalation when count is below maximum."""
        assert should_escalate_order(2, 3) is False

    def test_no_escalate_at_zero(self):
        """Test no escalation at zero repegs."""
        assert should_escalate_order(0, 3) is False

    def test_edge_case_max_zero(self):
        """Test edge case where max repegs is zero."""
        assert should_escalate_order(0, 0) is True
        assert should_escalate_order(1, 0) is True


class TestShouldConsiderRepeg:
    """Test repeg timing checks."""

    def test_should_repeg_after_wait_period(self):
        """Test that repeg is considered after wait period elapses."""
        placement_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        current_time = datetime(2024, 1, 1, 12, 1, 0, tzinfo=UTC)  # 60 seconds later
        wait_seconds = 30.0

        assert should_consider_repeg(placement_time, current_time, wait_seconds) is True

    def test_should_not_repeg_before_wait_period(self):
        """Test that repeg is not considered before wait period."""
        placement_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        current_time = datetime(2024, 1, 1, 12, 0, 15, tzinfo=UTC)  # 15 seconds later
        wait_seconds = 30.0

        assert should_consider_repeg(placement_time, current_time, wait_seconds) is False

    def test_should_repeg_exactly_at_wait_period(self):
        """Test repeg consideration exactly at wait period boundary."""
        placement_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        current_time = datetime(2024, 1, 1, 12, 0, 30, tzinfo=UTC)  # Exactly 30 seconds
        wait_seconds = 30.0

        assert should_consider_repeg(placement_time, current_time, wait_seconds) is True

    def test_zero_wait_seconds(self):
        """Test with zero wait seconds."""
        placement_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        current_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)  # Same time
        wait_seconds = 0.0

        assert should_consider_repeg(placement_time, current_time, wait_seconds) is True

    def test_fractional_seconds(self):
        """Test with fractional wait seconds."""
        placement_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        current_time = placement_time + timedelta(seconds=1.5)
        wait_seconds = 1.0

        assert should_consider_repeg(placement_time, current_time, wait_seconds) is True


class TestIsOrderCompleted:
    """Test order completion status checks."""

    def test_filled_status_is_completed(self):
        """Test that FILLED status is recognized as completed."""
        assert is_order_completed("FILLED") is True

    def test_canceled_status_is_completed(self):
        """Test that CANCELED status is recognized as completed."""
        assert is_order_completed("CANCELED") is True

    def test_rejected_status_is_completed(self):
        """Test that REJECTED status is recognized as completed."""
        assert is_order_completed("REJECTED") is True

    def test_expired_status_is_completed(self):
        """Test that EXPIRED status is recognized as completed."""
        assert is_order_completed("EXPIRED") is True

    def test_new_status_is_not_completed(self):
        """Test that NEW status is not completed."""
        assert is_order_completed("NEW") is False

    def test_partially_filled_status_is_not_completed(self):
        """Test that PARTIALLY_FILLED status is not completed."""
        assert is_order_completed("PARTIALLY_FILLED") is False

    def test_pending_status_is_not_completed(self):
        """Test that PENDING status is not completed."""
        assert is_order_completed("PENDING") is False

    def test_unknown_status_is_not_completed(self):
        """Test that unknown status is not completed."""
        assert is_order_completed("UNKNOWN") is False


class TestQuantizePriceSafely:
    """Test safe price quantization."""

    def test_quantize_to_cent_precision(self):
        """Test quantization to cent precision."""
        price = Decimal("100.123456")
        result = quantize_price_safely(price)
        assert result == Decimal("100.12")

    def test_quantize_rounds_half_even(self):
        """Test that quantization uses ROUND_HALF_EVEN (banker's rounding)."""
        # 0.125 rounds to 0.12 (even)
        assert quantize_price_safely(Decimal("0.125")) == Decimal("0.12")
        # 0.135 rounds to 0.14 (even)
        assert quantize_price_safely(Decimal("0.135")) == Decimal("0.14")

    def test_quantize_already_precise(self):
        """Test quantization of already precise values."""
        price = Decimal("100.00")
        result = quantize_price_safely(price)
        assert result == Decimal("100.00")

    def test_quantize_single_decimal(self):
        """Test quantization of single decimal place."""
        price = Decimal("100.1")
        result = quantize_price_safely(price)
        assert result == Decimal("100.10")

    @given(
        price=st.decimals(
            min_value=Decimal("0.001"),
            max_value=Decimal("100000"),
            places=6,
        )
    )
    def test_quantize_properties(self, price):
        """Property test: quantized price has at most 2 decimal places."""
        result = quantize_price_safely(price)
        # Check that result has at most 2 decimal places
        assert result == result.quantize(Decimal("0.01"))


class TestEnsureMinimumPrice:
    """Test minimum price enforcement."""

    def test_valid_price_above_minimum(self):
        """Test that valid price above minimum is unchanged."""
        price = Decimal("100.00")
        result = ensure_minimum_price(price)
        assert result == Decimal("100.00")

    def test_valid_price_at_minimum(self):
        """Test that price at minimum is unchanged."""
        price = Decimal("0.01")
        result = ensure_minimum_price(price)
        assert result == Decimal("0.01")

    def test_zero_price_returns_minimum(self):
        """Test that zero price returns minimum."""
        price = Decimal("0.00")
        result = ensure_minimum_price(price)
        assert result == Decimal("0.01")

    def test_negative_price_returns_minimum(self):
        """Test that negative price returns minimum."""
        price = Decimal("-10.00")
        result = ensure_minimum_price(price)
        assert result == Decimal("0.01")

    def test_custom_minimum_price(self):
        """Test with custom minimum price."""
        price = Decimal("0.05")
        result = ensure_minimum_price(price, min_price=Decimal("0.10"))
        assert result == Decimal("0.10")

    def test_price_below_custom_minimum(self):
        """Test that price below custom minimum is raised."""
        price = Decimal("0.03")
        result = ensure_minimum_price(price, min_price=Decimal("0.05"))
        assert result == Decimal("0.05")


class TestFetchPriceForNotionalCheck:
    """Test price fetching for notional value calculations."""

    def test_fetch_buy_price_from_quote_provider(self):
        """Test fetching ask price for BUY orders from quote provider."""
        quote = QuoteModel(
            symbol="AAPL",
            bid_price=100.00,
            ask_price=100.50,
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )

        quote_provider = Mock()
        quote_provider.get_quote_with_validation.return_value = (quote, False)

        alpaca_manager = Mock()

        result = fetch_price_for_notional_check("AAPL", "BUY", quote_provider, alpaca_manager)

        assert result == Decimal("100.50")  # Ask price for BUY
        quote_provider.get_quote_with_validation.assert_called_once_with("AAPL")
        alpaca_manager.get_current_price.assert_not_called()

    def test_fetch_sell_price_from_quote_provider(self):
        """Test fetching bid price for SELL orders from quote provider."""
        quote = QuoteModel(
            symbol="AAPL",
            bid_price=100.00,
            ask_price=100.50,
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )

        quote_provider = Mock()
        quote_provider.get_quote_with_validation.return_value = (quote, False)

        alpaca_manager = Mock()

        result = fetch_price_for_notional_check("AAPL", "SELL", quote_provider, alpaca_manager)

        assert result == Decimal("100.00")  # Bid price for SELL
        quote_provider.get_quote_with_validation.assert_called_once_with("AAPL")

    def test_fallback_to_alpaca_when_quote_unavailable(self):
        """Test fallback to Alpaca REST API when quote is unavailable."""
        quote_provider = Mock()
        quote_provider.get_quote_with_validation.return_value = None

        alpaca_manager = Mock()
        alpaca_manager.get_current_price.return_value = 99.75

        result = fetch_price_for_notional_check("AAPL", "BUY", quote_provider, alpaca_manager)

        assert result == Decimal("99.75")
        alpaca_manager.get_current_price.assert_called_once_with("AAPL")

    def test_returns_none_when_all_sources_fail(self):
        """Test returns None when both quote provider and Alpaca fail."""
        quote_provider = Mock()
        quote_provider.get_quote_with_validation.return_value = None

        alpaca_manager = Mock()
        alpaca_manager.get_current_price.return_value = None

        result = fetch_price_for_notional_check("AAPL", "BUY", quote_provider, alpaca_manager)

        assert result is None

    def test_handles_exception_gracefully(self):
        """Test that exceptions are handled gracefully."""
        quote_provider = Mock()
        quote_provider.get_quote_with_validation.side_effect = Exception("API error")

        alpaca_manager = Mock()

        result = fetch_price_for_notional_check("AAPL", "BUY", quote_provider, alpaca_manager)

        assert result is None

    def test_case_insensitive_side_buy(self):
        """Test that side parameter is case-insensitive for BUY."""
        quote = QuoteModel(
            symbol="AAPL",
            bid_price=100.00,
            ask_price=100.50,
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )

        quote_provider = Mock()
        quote_provider.get_quote_with_validation.return_value = (quote, False)

        alpaca_manager = Mock()

        result_upper = fetch_price_for_notional_check("AAPL", "BUY", quote_provider, alpaca_manager)
        result_lower = fetch_price_for_notional_check("AAPL", "buy", quote_provider, alpaca_manager)

        assert result_upper == result_lower == Decimal("100.50")


class TestIsRemainingQuantityTooSmall:
    """Test remaining quantity validation."""

    def test_fractionable_asset_below_minimum_notional(self):
        """Test fractionable asset with notional below minimum."""
        remaining_qty = Decimal("0.1")
        price = Decimal("5.00")  # Notional = 0.50
        min_notional = Decimal("1.00")

        asset_info = Mock()
        asset_info.fractionable = True

        result = is_remaining_quantity_too_small(remaining_qty, asset_info, price, min_notional)

        assert result is True  # 0.50 < 1.00

    def test_fractionable_asset_above_minimum_notional(self):
        """Test fractionable asset with notional above minimum."""
        remaining_qty = Decimal("0.5")
        price = Decimal("5.00")  # Notional = 2.50
        min_notional = Decimal("1.00")

        asset_info = Mock()
        asset_info.fractionable = True

        result = is_remaining_quantity_too_small(remaining_qty, asset_info, price, min_notional)

        assert result is False  # 2.50 > 1.00

    def test_non_fractionable_rounds_to_zero(self):
        """Test non-fractionable asset that rounds to zero."""
        remaining_qty = Decimal("0.4")  # Rounds to 0
        price = Decimal("100.00")
        min_notional = Decimal("1.00")

        asset_info = Mock()
        asset_info.fractionable = False

        result = is_remaining_quantity_too_small(remaining_qty, asset_info, price, min_notional)

        assert result is True  # 0.4 rounds to 0

    def test_non_fractionable_rounds_to_one(self):
        """Test non-fractionable asset that rounds to one."""
        remaining_qty = Decimal("0.6")  # Rounds to 1
        price = Decimal("100.00")
        min_notional = Decimal("1.00")

        asset_info = Mock()
        asset_info.fractionable = False

        result = is_remaining_quantity_too_small(remaining_qty, asset_info, price, min_notional)

        assert result is False  # 0.6 rounds to 1

    def test_none_asset_info_with_small_quantity(self):
        """Test None asset_info with quantity that rounds to zero."""
        remaining_qty = Decimal("0.3")
        price = Decimal("100.00")
        min_notional = Decimal("1.00")

        result = is_remaining_quantity_too_small(remaining_qty, None, price, min_notional)

        assert result is True  # Treated as non-fractionable, 0.3 rounds to 0

    def test_none_asset_info_with_adequate_quantity(self):
        """Test None asset_info with adequate quantity."""
        remaining_qty = Decimal("1.0")
        price = Decimal("100.00")
        min_notional = Decimal("1.00")

        result = is_remaining_quantity_too_small(remaining_qty, None, price, min_notional)

        assert result is False

    def test_fractionable_with_none_price(self):
        """Test fractionable asset when price is None."""
        remaining_qty = Decimal("0.1")
        price = None
        min_notional = Decimal("1.00")

        asset_info = Mock()
        asset_info.fractionable = True

        result = is_remaining_quantity_too_small(remaining_qty, asset_info, price, min_notional)

        assert result is False  # Cannot calculate notional, so assume ok

    def test_edge_case_exactly_minimum_notional(self):
        """Test edge case where notional exactly equals minimum."""
        remaining_qty = Decimal("0.2")
        price = Decimal("5.00")  # Notional = 1.00
        min_notional = Decimal("1.00")

        asset_info = Mock()
        asset_info.fractionable = True

        result = is_remaining_quantity_too_small(remaining_qty, asset_info, price, min_notional)

        assert result is False  # 1.00 >= 1.00
