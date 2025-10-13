"""Business Unit: execution | Status: current.

Test suite for pricing validation and input checking.

This module tests the new validation features added to the pricing calculator
including input validation, correlation_id propagation, and config validation.
"""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from the_alchemiser.execution_v2.core.smart_execution_strategy.models import ExecutionConfig
from the_alchemiser.execution_v2.core.smart_execution_strategy.pricing import PricingCalculator
from the_alchemiser.shared.errors.exceptions import ValidationError
from the_alchemiser.shared.types.market_data import QuoteModel


class TestConfigValidation:
    """Test ExecutionConfig validation in PricingCalculator."""

    def test_valid_config_accepted(self):
        """Test that valid config is accepted."""
        config = ExecutionConfig()
        calculator = PricingCalculator(config)
        assert calculator.config == config

    def test_negative_bid_offset_rejected(self):
        """Test that negative bid_anchor_offset_cents is rejected."""
        config = ExecutionConfig(bid_anchor_offset_cents=Decimal("-0.01"))
        with pytest.raises(ValidationError, match="bid_anchor_offset_cents must be positive"):
            PricingCalculator(config)

    def test_negative_ask_offset_rejected(self):
        """Test that negative ask_anchor_offset_cents is rejected."""
        config = ExecutionConfig(ask_anchor_offset_cents=Decimal("-0.01"))
        with pytest.raises(ValidationError, match="ask_anchor_offset_cents must be positive"):
            PricingCalculator(config)

    def test_negative_min_bid_ask_size_rejected(self):
        """Test that negative min_bid_ask_size is rejected."""
        config = ExecutionConfig(min_bid_ask_size=Decimal("-10"))
        with pytest.raises(ValidationError, match="min_bid_ask_size must be positive"):
            PricingCalculator(config)

    def test_negative_max_spread_rejected(self):
        """Test that negative max_spread_percent is rejected."""
        config = ExecutionConfig(max_spread_percent=Decimal("-0.50"))
        with pytest.raises(ValidationError, match="max_spread_percent must be positive"):
            PricingCalculator(config)

    def test_zero_bid_offset_rejected(self):
        """Test that zero bid_anchor_offset_cents is rejected."""
        config = ExecutionConfig(bid_anchor_offset_cents=Decimal("0.00"))
        with pytest.raises(ValidationError, match="bid_anchor_offset_cents must be positive"):
            PricingCalculator(config)


class TestSideParameterValidation:
    """Test side parameter validation."""

    @pytest.fixture
    def pricing_calculator(self):
        """Create pricing calculator with default config."""
        return PricingCalculator(ExecutionConfig())

    @pytest.fixture
    def valid_quote(self):
        """Create valid quote for testing."""
        return QuoteModel(
            symbol="AAPL",
            bid_price=100.00,
            ask_price=100.50,
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )

    def test_buy_side_accepted(self, pricing_calculator, valid_quote):
        """Test that 'BUY' side is accepted."""
        price, _ = pricing_calculator.calculate_simple_inside_spread_price(
            valid_quote, "BUY"
        )
        assert price > 0

    def test_sell_side_accepted(self, pricing_calculator, valid_quote):
        """Test that 'SELL' side is accepted."""
        price, _ = pricing_calculator.calculate_simple_inside_spread_price(
            valid_quote, "SELL"
        )
        assert price > 0

    def test_lowercase_buy_accepted(self, pricing_calculator, valid_quote):
        """Test that lowercase 'buy' is accepted."""
        price, _ = pricing_calculator.calculate_simple_inside_spread_price(
            valid_quote, "buy"
        )
        assert price > 0

    def test_lowercase_sell_accepted(self, pricing_calculator, valid_quote):
        """Test that lowercase 'sell' is accepted."""
        price, _ = pricing_calculator.calculate_simple_inside_spread_price(
            valid_quote, "sell"
        )
        assert price > 0

    def test_invalid_side_rejected(self, pricing_calculator, valid_quote):
        """Test that invalid side parameter is rejected."""
        with pytest.raises(ValidationError, match="Invalid side parameter.*Must be 'BUY' or 'SELL'"):
            pricing_calculator.calculate_simple_inside_spread_price(
                valid_quote, "INVALID"
            )

    def test_empty_side_rejected(self, pricing_calculator, valid_quote):
        """Test that empty side parameter is rejected."""
        with pytest.raises(ValidationError, match="Invalid side parameter.*Must be 'BUY' or 'SELL'"):
            pricing_calculator.calculate_simple_inside_spread_price(
                valid_quote, ""
            )


class TestQuoteDataValidation:
    """Test quote data validation."""

    @pytest.fixture
    def pricing_calculator(self):
        """Create pricing calculator with default config."""
        return PricingCalculator(ExecutionConfig())

    def test_empty_symbol_rejected(self, pricing_calculator):
        """Test that empty symbol is rejected."""
        quote = QuoteModel(
            symbol="",
            bid_price=100.00,
            ask_price=100.50,
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )
        with pytest.raises(ValidationError, match="Quote symbol cannot be empty"):
            pricing_calculator.calculate_simple_inside_spread_price(quote, "BUY")

    def test_negative_bid_price_rejected(self, pricing_calculator):
        """Test that negative bid price is rejected."""
        quote = QuoteModel(
            symbol="AAPL",
            bid_price=-100.00,
            ask_price=100.50,
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )
        with pytest.raises(ValidationError, match="Quote prices cannot be negative"):
            pricing_calculator.calculate_simple_inside_spread_price(quote, "BUY")

    def test_negative_ask_price_rejected(self, pricing_calculator):
        """Test that negative ask price is rejected."""
        quote = QuoteModel(
            symbol="AAPL",
            bid_price=100.00,
            ask_price=-100.50,
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )
        with pytest.raises(ValidationError, match="Quote prices cannot be negative"):
            pricing_calculator.calculate_simple_inside_spread_price(quote, "BUY")

    def test_both_zero_prices_rejected(self, pricing_calculator):
        """Test that both zero bid and ask is rejected."""
        quote = QuoteModel(
            symbol="AAPL",
            bid_price=0.00,
            ask_price=0.00,
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )
        with pytest.raises(ValidationError, match="has zero bid and ask prices"):
            pricing_calculator.calculate_simple_inside_spread_price(quote, "BUY")

    def test_zero_bid_with_valid_ask_accepted(self, pricing_calculator):
        """Test that zero bid with valid ask is accepted (warning logged)."""
        quote = QuoteModel(
            symbol="AAPL",
            bid_price=0.00,
            ask_price=100.50,
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )
        # Should not raise error, quote might be stale
        price, _ = pricing_calculator.calculate_simple_inside_spread_price(quote, "BUY")
        assert price > 0

    def test_inverted_quote_logged_warning(self, pricing_calculator):
        """Test that inverted quote logs warning but is accepted."""
        quote = QuoteModel(
            symbol="AAPL",
            bid_price=100.50,
            ask_price=100.00,
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )
        # Should not raise error, just log warning
        price, _ = pricing_calculator.calculate_simple_inside_spread_price(quote, "BUY")
        assert price > 0


class TestCorrelationIdPropagation:
    """Test correlation_id propagation in logging."""

    @pytest.fixture
    def pricing_calculator(self):
        """Create pricing calculator with default config."""
        return PricingCalculator(ExecutionConfig())

    @pytest.fixture
    def valid_quote(self):
        """Create valid quote for testing."""
        return QuoteModel(
            symbol="AAPL",
            bid_price=100.00,
            ask_price=100.50,
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )

    def test_liquidity_aware_price_with_correlation_id(self, pricing_calculator, valid_quote):
        """Test correlation_id in liquidity-aware pricing."""
        correlation_id = "test-correlation-123"
        price, metadata = pricing_calculator.calculate_liquidity_aware_price(
            valid_quote, "BUY", 50.0, correlation_id=correlation_id
        )
        assert price > 0
        assert metadata is not None

    def test_simple_price_with_correlation_id(self, pricing_calculator, valid_quote):
        """Test correlation_id in simple pricing."""
        correlation_id = "test-correlation-456"
        price, metadata = pricing_calculator.calculate_simple_inside_spread_price(
            valid_quote, "BUY", correlation_id=correlation_id
        )
        assert price > 0
        assert metadata["used_fallback"] is True

    def test_repeg_price_with_correlation_id(self, pricing_calculator, valid_quote):
        """Test correlation_id in repeg pricing."""
        correlation_id = "test-correlation-789"
        original_price = Decimal("100.25")
        new_price = pricing_calculator.calculate_repeg_price(
            valid_quote, "BUY", original_price, correlation_id=correlation_id
        )
        assert new_price is not None
        assert new_price > 0


class TestZeroVolumeHandling:
    """Test handling of zero volume scenarios."""

    @pytest.fixture
    def pricing_calculator(self):
        """Create pricing calculator with default config."""
        return PricingCalculator(ExecutionConfig())

    def test_zero_volume_in_liquidity_aware_pricing(self, pricing_calculator):
        """Test that zero volume is handled gracefully."""
        quote = QuoteModel(
            symbol="AAPL",
            bid_price=100.00,
            ask_price=100.50,
            bid_size=0.0,  # Zero volume
            ask_size=0.0,  # Zero volume
            timestamp=datetime.now(UTC),
        )
        # Should not crash, should log warning
        price, metadata = pricing_calculator.calculate_liquidity_aware_price(
            quote, "BUY", 50.0
        )
        assert price > 0
        # Volume ratio should be 0 when volume is 0
        assert metadata["volume_ratio"] == 0.0


class TestRepegPriceWithValidation:
    """Test repeg price calculation with new validation."""

    @pytest.fixture
    def pricing_calculator(self):
        """Create pricing calculator with default config."""
        return PricingCalculator(ExecutionConfig())

    @pytest.fixture
    def valid_quote(self):
        """Create valid quote for testing."""
        return QuoteModel(
            symbol="AAPL",
            bid_price=100.00,
            ask_price=100.50,
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )

    def test_repeg_with_invalid_side_rejected(self, pricing_calculator, valid_quote):
        """Test that repeg with invalid side is rejected."""
        with pytest.raises(ValidationError, match="Invalid side parameter"):
            pricing_calculator.calculate_repeg_price(
                valid_quote, "INVALID", Decimal("100.25")
            )

    def test_repeg_with_invalid_quote_rejected(self, pricing_calculator):
        """Test that repeg with invalid quote is rejected."""
        quote = QuoteModel(
            symbol="AAPL",
            bid_price=-100.00,  # Negative price
            ask_price=100.50,
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )
        with pytest.raises(ValidationError, match="Quote prices cannot be negative"):
            pricing_calculator.calculate_repeg_price(
                quote, "BUY", Decimal("100.25")
            )

    def test_repeg_with_valid_inputs(self, pricing_calculator, valid_quote):
        """Test that repeg with valid inputs succeeds."""
        new_price = pricing_calculator.calculate_repeg_price(
            valid_quote, "BUY", Decimal("100.25")
        )
        assert new_price is not None
        assert new_price > 0
