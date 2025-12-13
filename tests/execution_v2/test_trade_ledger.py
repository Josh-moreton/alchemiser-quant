"""Business Unit: execution | Status: current.

Tests for trade ledger service.
"""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import MagicMock

from the_alchemiser.execution_v2.models.execution_result import OrderResult
from the_alchemiser.execution_v2.services.trade_ledger import TradeLedgerService
from the_alchemiser.shared.schemas.rebalance_plan import (
    RebalancePlan,
    RebalancePlanItem,
)
from the_alchemiser.shared.types.market_data import QuoteModel


class TestTradeLedgerService:
    """Test suite for TradeLedgerService."""

    def test_record_filled_order_success(self):
        """Test recording a successful filled order."""
        service = TradeLedgerService()

        order_result = OrderResult(
            symbol="AAPL",
            action="BUY",
            trade_amount=Decimal("1000.00"),
            shares=Decimal("10"),
            price=Decimal("100.00"),
            order_id="order-123",
            success=True,
            error_message=None,
            timestamp=datetime.now(UTC),
            order_type="MARKET",  # Default to MARKET for tests
            filled_at=datetime.now(UTC),  # Set filled_at for successful order
        )

        entry = service.record_filled_order(
            order_result=order_result,
            correlation_id="corr-123",
            rebalance_plan=None,
            quote_at_fill=None,
        )

        assert entry is not None
        assert entry.order_id == "order-123"
        assert entry.symbol == "AAPL"
        assert entry.direction == "BUY"
        assert entry.filled_qty == Decimal("10")
        assert entry.fill_price == Decimal("100.00")
        assert entry.order_type == "MARKET"
        assert service.total_entries == 1

    def test_record_filled_order_with_quote(self):
        """Test recording a filled order with market quote."""
        service = TradeLedgerService()

        order_result = OrderResult(
            symbol="TSLA",
            action="SELL",
            trade_amount=Decimal("2500.00"),
            shares=Decimal("10"),
            price=Decimal("250.00"),
            order_id="order-456",
            success=True,
            error_message=None,
            timestamp=datetime.now(UTC),
            order_type="MARKET",  # Default to MARKET for tests
            filled_at=datetime.now(UTC),  # Set filled_at for successful order
        )

        quote = QuoteModel(
            symbol="TSLA",
            bid_price=Decimal("249.50"),
            ask_price=Decimal("250.50"),
            bid_size=Decimal("100"),
            ask_size=Decimal("100"),
            timestamp=datetime.now(UTC),
        )

        entry = service.record_filled_order(
            order_result=order_result,
            correlation_id="corr-456",
            rebalance_plan=None,
            quote_at_fill=quote,
        )

        assert entry is not None
        assert entry.bid_at_fill == Decimal("249.50")
        assert entry.ask_at_fill == Decimal("250.50")

    def test_record_filled_order_with_strategy_attribution(self):
        """Test recording a filled order with strategy attribution."""
        service = TradeLedgerService()

        # Create rebalance plan with strategy attribution in metadata
        plan = RebalancePlan(
            correlation_id="corr-789",
            causation_id="cause-789",
            timestamp=datetime.now(UTC),
            plan_id="plan-789",
            items=[
                RebalancePlanItem(
                    symbol="NVDA",
                    current_weight=Decimal("0.0"),
                    target_weight=Decimal("0.5"),
                    weight_diff=Decimal("0.5"),
                    target_value=Decimal("5000"),
                    current_value=Decimal("0"),
                    trade_amount=Decimal("5000"),
                    action="BUY",
                    priority=1,
                )
            ],
            total_portfolio_value=Decimal("10000"),
            total_trade_value=Decimal("5000"),
            metadata={
                "strategy_attribution": {
                    "NVDA": {
                        "momentum_strategy": 0.6,
                        "mean_reversion_strategy": 0.4,
                    }
                }
            },
        )

        order_result = OrderResult(
            symbol="NVDA",
            action="BUY",
            trade_amount=Decimal("5000.00"),
            shares=Decimal("10"),
            price=Decimal("500.00"),
            order_id="order-789",
            success=True,
            error_message=None,
            timestamp=datetime.now(UTC),
            order_type="MARKET",  # Default to MARKET for tests
            filled_at=datetime.now(UTC),  # Set filled_at for successful order
        )

        entry = service.record_filled_order(
            order_result=order_result,
            correlation_id="corr-789",
            rebalance_plan=plan,
            quote_at_fill=None,
        )

        assert entry is not None
        assert len(entry.strategy_names) == 2
        assert "momentum_strategy" in entry.strategy_names
        assert "mean_reversion_strategy" in entry.strategy_names
        assert entry.strategy_weights is not None
        assert entry.strategy_weights["momentum_strategy"] == Decimal("0.6")
        assert entry.strategy_weights["mean_reversion_strategy"] == Decimal("0.4")

    def test_record_filled_order_with_plan_id(self):
        """Test recording a filled order with plan_id from rebalance plan."""
        service = TradeLedgerService()

        # Create rebalance plan with plan_id
        plan = RebalancePlan(
            correlation_id="corr-plan",
            causation_id="cause-plan",
            timestamp=datetime.now(UTC),
            plan_id="portfolio_v2_abc123_1702468800",
            items=[
                RebalancePlanItem(
                    symbol="AAPL",
                    current_weight=Decimal("0.0"),
                    target_weight=Decimal("0.5"),
                    weight_diff=Decimal("0.5"),
                    target_value=Decimal("5000"),
                    current_value=Decimal("0"),
                    trade_amount=Decimal("5000"),
                    action="BUY",
                    priority=1,
                )
            ],
            total_portfolio_value=Decimal("10000"),
            total_trade_value=Decimal("5000"),
        )

        order_result = OrderResult(
            symbol="AAPL",
            action="BUY",
            trade_amount=Decimal("5000.00"),
            shares=Decimal("50"),
            price=Decimal("100.00"),
            order_id="order-plan",
            success=True,
            error_message=None,
            timestamp=datetime.now(UTC),
            order_type="MARKET",
            filled_at=datetime.now(UTC),
        )

        entry = service.record_filled_order(
            order_result=order_result,
            correlation_id="corr-plan",
            rebalance_plan=plan,
            quote_at_fill=None,
        )

        assert entry is not None
        assert entry.plan_id == "portfolio_v2_abc123_1702468800"
        assert entry.order_id == "order-plan"
        assert entry.symbol == "AAPL"

    def test_record_filled_order_without_plan(self):
        """Test recording a filled order without rebalance plan has None plan_id."""
        service = TradeLedgerService()

        order_result = OrderResult(
            symbol="TSLA",
            action="BUY",
            trade_amount=Decimal("1000.00"),
            shares=Decimal("10"),
            price=Decimal("100.00"),
            order_id="order-no-plan",
            success=True,
            error_message=None,
            timestamp=datetime.now(UTC),
            order_type="MARKET",
            filled_at=datetime.now(UTC),
        )

        entry = service.record_filled_order(
            order_result=order_result,
            correlation_id="corr-no-plan",
            rebalance_plan=None,  # No plan provided
            quote_at_fill=None,
        )

        assert entry is not None
        assert entry.plan_id is None
        assert entry.order_id == "order-no-plan"

    def test_skip_recording_unsuccessful_order(self):
        """Test that unsuccessful orders are not recorded."""
        service = TradeLedgerService()

        order_result = OrderResult(
            symbol="FAIL",
            action="BUY",
            trade_amount=Decimal("0"),
            shares=Decimal("10"),
            price=None,
            order_id=None,
            success=False,
            error_message="Order failed",
            timestamp=datetime.now(UTC),
            order_type="MARKET",  # Default to MARKET for tests
            filled_at=None,  # Not filled for unsuccessful order
        )

        entry = service.record_filled_order(
            order_result=order_result,
            correlation_id="corr-fail",
            rebalance_plan=None,
            quote_at_fill=None,
        )

        assert entry is None
        assert service.total_entries == 0

    def test_get_entries_for_symbol(self):
        """Test filtering entries by symbol."""
        service = TradeLedgerService()

        # Record multiple orders
        for symbol in ["AAPL", "TSLA", "AAPL"]:
            order_result = OrderResult(
                symbol=symbol,
                action="BUY",
                trade_amount=Decimal("1000.00"),
                shares=Decimal("10"),
                price=Decimal("100.00"),
                order_id=f"order-{symbol}",
                success=True,
                error_message=None,
                timestamp=datetime.now(UTC),
                order_type="MARKET",  # Default to MARKET for tests
                filled_at=datetime.now(UTC),  # Set filled_at for successful order
            )
            service.record_filled_order(
                order_result=order_result,
                correlation_id="corr-test",
                rebalance_plan=None,
                quote_at_fill=None,
            )

        aapl_entries = service.get_entries_for_symbol("AAPL")
        assert len(aapl_entries) == 2
        assert all(entry.symbol == "AAPL" for entry in aapl_entries)

        tsla_entries = service.get_entries_for_symbol("TSLA")
        assert len(tsla_entries) == 1
        assert tsla_entries[0].symbol == "TSLA"

    def test_get_entries_for_strategy(self):
        """Test filtering entries by strategy."""
        service = TradeLedgerService()

        # Create plan with strategy attribution
        plan = RebalancePlan(
            correlation_id="corr-strategy",
            causation_id="cause-strategy",
            timestamp=datetime.now(UTC),
            plan_id="plan-strategy",
            items=[
                RebalancePlanItem(
                    symbol="TEST",
                    current_weight=Decimal("0.0"),
                    target_weight=Decimal("0.5"),
                    weight_diff=Decimal("0.5"),
                    target_value=Decimal("5000"),
                    current_value=Decimal("0"),
                    trade_amount=Decimal("5000"),
                    action="BUY",
                    priority=1,
                )
            ],
            total_portfolio_value=Decimal("10000"),
            total_trade_value=Decimal("5000"),
            metadata={
                "strategy_attribution": {
                    "TEST": {
                        "strategy_a": 1.0,
                    }
                }
            },
        )

        order_result = OrderResult(
            symbol="TEST",
            action="BUY",
            trade_amount=Decimal("5000.00"),
            shares=Decimal("50"),
            price=Decimal("100.00"),
            order_id="order-strategy",
            success=True,
            error_message=None,
            timestamp=datetime.now(UTC),
            order_type="MARKET",  # Default to MARKET for tests
            filled_at=datetime.now(UTC),  # Set filled_at for successful order
        )

        service.record_filled_order(
            order_result=order_result,
            correlation_id="corr-strategy",
            rebalance_plan=plan,
            quote_at_fill=None,
        )

        strategy_a_entries = service.get_entries_for_strategy("strategy_a")
        assert len(strategy_a_entries) == 1
        assert strategy_a_entries[0].symbol == "TEST"

        strategy_b_entries = service.get_entries_for_strategy("strategy_b")
        assert len(strategy_b_entries) == 0

    def test_get_ledger(self):
        """Test getting the complete ledger."""
        service = TradeLedgerService()

        # Record a few orders
        for i in range(3):
            order_result = OrderResult(
                symbol=f"SYM{i}",
                action="BUY",
                trade_amount=Decimal("1000.00"),
                shares=Decimal("10"),
                price=Decimal("100.00"),
                order_id=f"order-{i}",
                success=True,
                error_message=None,
                timestamp=datetime.now(UTC),
                order_type="MARKET",  # Default to MARKET for tests
                filled_at=datetime.now(UTC),  # Set filled_at for successful order
            )
            service.record_filled_order(
                order_result=order_result,
                correlation_id=f"corr-{i}",
                rebalance_plan=None,
                quote_at_fill=None,
            )

        ledger = service.get_ledger()
        assert ledger.total_entries == 3
        assert len(ledger.entries) == 3
        assert ledger.total_buy_value == Decimal("3000.00")
        assert ledger.total_sell_value == Decimal("0")

    def test_skip_recording_zero_quantity_order(self):
        """Test that orders with zero quantity are not recorded."""
        service = TradeLedgerService()

        order_result = OrderResult(
            symbol="ZERO",
            action="BUY",
            trade_amount=Decimal("0"),
            shares=Decimal("0"),  # Zero quantity
            price=Decimal("100.00"),
            order_id="order-zero",
            success=True,
            error_message=None,
            timestamp=datetime.now(UTC),
        )

        entry = service.record_filled_order(
            order_result=order_result,
            correlation_id="corr-zero",
            rebalance_plan=None,
            quote_at_fill=None,
        )

        assert entry is None
        assert service.total_entries == 0

    def test_symbol_normalization_lowercase(self):
        """Test that lowercase symbols are normalized to uppercase."""
        service = TradeLedgerService()

        order_result = OrderResult(
            symbol="aapl",  # Lowercase
            action="BUY",
            trade_amount=Decimal("1000.00"),
            shares=Decimal("10"),
            price=Decimal("100.00"),
            order_id="order-lower",
            success=True,
            error_message=None,
            timestamp=datetime.now(UTC),
        )

        entry = service.record_filled_order(
            order_result=order_result,
            correlation_id="corr-lower",
            rebalance_plan=None,
            quote_at_fill=None,
        )

        assert entry is not None
        assert entry.symbol == "AAPL"  # Should be uppercase

    def test_strategy_weights_validation_invalid_sum(self):
        """Test that strategy weights not summing to ~1.0 are rejected."""
        service = TradeLedgerService()

        # Create plan with invalid strategy weights (sum != 1.0)
        plan = RebalancePlan(
            correlation_id="corr-invalid-weights",
            causation_id="cause-invalid",
            timestamp=datetime.now(UTC),
            plan_id="plan-invalid",
            items=[
                RebalancePlanItem(
                    symbol="TEST",
                    current_weight=Decimal("0.0"),
                    target_weight=Decimal("0.5"),
                    weight_diff=Decimal("0.5"),
                    target_value=Decimal("5000"),
                    current_value=Decimal("0"),
                    trade_amount=Decimal("5000"),
                    action="BUY",
                    priority=1,
                )
            ],
            total_portfolio_value=Decimal("10000"),
            total_trade_value=Decimal("5000"),
            metadata={
                "strategy_attribution": {
                    "TEST": {
                        "strategy_a": 0.3,  # Only sums to 0.3, not 1.0
                    }
                }
            },
        )

        order_result = OrderResult(
            symbol="TEST",
            action="BUY",
            trade_amount=Decimal("5000.00"),
            shares=Decimal("50"),
            price=Decimal("100.00"),
            order_id="order-invalid-weights",
            success=True,
            error_message=None,
            timestamp=datetime.now(UTC),
        )

        # This should fail during TradeLedgerEntry creation due to weight validation
        entry = service.record_filled_order(
            order_result=order_result,
            correlation_id="corr-invalid-weights",
            rebalance_plan=plan,
            quote_at_fill=None,
        )

        # Entry should be None because validation failed
        assert entry is None
        assert service.total_entries == 0

    def test_quote_data_capture_integration(self):
        """Test that quote data is properly captured when available."""
        service = TradeLedgerService()

        # Create quote with bid/ask spread
        quote = QuoteModel(
            symbol="QUOTE",
            bid_price=Decimal("99.50"),
            ask_price=Decimal("100.50"),
            bid_size=Decimal("100"),
            ask_size=Decimal("100"),
            timestamp=datetime.now(UTC),
        )

        order_result = OrderResult(
            symbol="QUOTE",
            action="BUY",
            trade_amount=Decimal("1000.00"),
            shares=Decimal("10"),
            price=Decimal("100.00"),
            order_id="order-quote",
            success=True,
            error_message=None,
            timestamp=datetime.now(UTC),
        )

        entry = service.record_filled_order(
            order_result=order_result,
            correlation_id="corr-quote",
            rebalance_plan=None,
            quote_at_fill=quote,
        )

        assert entry is not None
        assert entry.bid_at_fill == Decimal("99.50")
        assert entry.ask_at_fill == Decimal("100.50")
        # Spread should be 1.00 (100.50 - 99.50)
        assert entry.ask_at_fill - entry.bid_at_fill == Decimal("1.00")

    def test_quote_data_none_handled_gracefully(self):
        """Test that None quote data is handled gracefully."""
        service = TradeLedgerService()

        order_result = OrderResult(
            symbol="NOQUOTE",
            action="SELL",
            trade_amount=Decimal("2000.00"),
            shares=Decimal("20"),
            price=Decimal("100.00"),
            order_id="order-noquote",
            success=True,
            error_message=None,
            timestamp=datetime.now(UTC),
        )

        entry = service.record_filled_order(
            order_result=order_result,
            correlation_id="corr-noquote",
            rebalance_plan=None,
            quote_at_fill=None,  # No quote available
        )

        assert entry is not None
        assert entry.bid_at_fill is None
        assert entry.ask_at_fill is None
        assert entry.symbol == "NOQUOTE"
        assert entry.fill_price == Decimal("100.00")

    def test_order_type_extraction_from_order_result(self):
        """Test that order_type is properly extracted from OrderResult."""
        service = TradeLedgerService()

        # Test LIMIT order type
        order_result = OrderResult(
            symbol="LIMIT_TEST",
            action="BUY",
            trade_amount=Decimal("1000.00"),
            shares=Decimal("10"),
            price=Decimal("100.00"),
            order_id="order-limit",
            success=True,
            error_message=None,
            timestamp=datetime.now(UTC),
            order_type="LIMIT",  # LIMIT order type
            filled_at=datetime.now(UTC),
        )

        entry = service.record_filled_order(
            order_result=order_result,
            correlation_id="corr-limit",
            rebalance_plan=None,
            quote_at_fill=None,
        )

        assert entry is not None
        assert entry.order_type == "LIMIT"
        assert entry.symbol == "LIMIT_TEST"

    def test_order_type_market_from_order_result(self):
        """Test that MARKET order_type is properly extracted from OrderResult."""
        service = TradeLedgerService()

        # Test MARKET order type
        order_result = OrderResult(
            symbol="MRKT",  # Shortened to fit max_length=10
            action="SELL",
            trade_amount=Decimal("2000.00"),
            shares=Decimal("20"),
            price=Decimal("100.00"),
            order_id="order-market",
            success=True,
            error_message=None,
            timestamp=datetime.now(UTC),
            order_type="MARKET",  # MARKET order type
            filled_at=datetime.now(UTC),
        )

        entry = service.record_filled_order(
            order_result=order_result,
            correlation_id="corr-market",
            rebalance_plan=None,
            quote_at_fill=None,
        )

        assert entry is not None
        assert entry.order_type == "MARKET"
        assert entry.symbol == "MRKT"

    def test_filled_at_timestamp_extraction(self):
        """Test that filled_at timestamp is used when available."""
        service = TradeLedgerService()

        placement_time = datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC)
        fill_time = datetime(2024, 1, 1, 10, 0, 5, tzinfo=UTC)  # 5 seconds later

        order_result = OrderResult(
            symbol="FILLTIME",  # Shortened to fit max_length=10
            action="BUY",
            trade_amount=Decimal("1000.00"),
            shares=Decimal("10"),
            price=Decimal("100.00"),
            order_id="order-filltime",
            success=True,
            error_message=None,
            timestamp=placement_time,  # Order placement time
            order_type="LIMIT",
            filled_at=fill_time,  # Actual fill time (later)
        )

        entry = service.record_filled_order(
            order_result=order_result,
            correlation_id="corr-filltime",
            rebalance_plan=None,
            quote_at_fill=None,
        )

        assert entry is not None
        assert entry.fill_timestamp == fill_time  # Should use filled_at, not timestamp
        assert entry.fill_timestamp != placement_time

    def test_filled_at_fallback_to_timestamp(self):
        """Test that timestamp is used as fallback when filled_at is None."""
        service = TradeLedgerService()

        placement_time = datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC)

        order_result = OrderResult(
            symbol="FALLBACK",  # Shortened to fit max_length=10
            action="BUY",
            trade_amount=Decimal("1000.00"),
            shares=Decimal("10"),
            price=Decimal("100.00"),
            order_id="order-fallback",
            success=True,
            error_message=None,
            timestamp=placement_time,
            order_type="MARKET",
            filled_at=None,  # No filled_at available
        )

        entry = service.record_filled_order(
            order_result=order_result,
            correlation_id="corr-fallback",
            rebalance_plan=None,
            quote_at_fill=None,
        )

        assert entry is not None
        assert entry.fill_timestamp == placement_time  # Should fall back to timestamp


class TestTradeLedgerInvalidQuoteHandling:
    """Test handling of invalid quote data (zero or negative prices)."""

    def test_zero_ask_price_filtered_out(self):
        """Test that zero ask_price is filtered out and doesn't cause validation error."""
        from the_alchemiser.shared.types.market_data import QuoteModel

        service = TradeLedgerService()

        # Create quote with zero ask_price (invalid)
        quote = QuoteModel(
            symbol="GE",
            bid_price=Decimal("100.00"),
            ask_price=Decimal("0.0"),  # Invalid - should be filtered
            bid_size=Decimal("100"),
            ask_size=Decimal("0"),
            timestamp=datetime.now(UTC),
        )

        order_result = OrderResult(
            symbol="GE",
            action="BUY",
            trade_amount=Decimal("1000.00"),
            shares=Decimal("10"),
            price=Decimal("100.50"),
            order_id="order-zero-ask",
            success=True,
            error_message=None,
            timestamp=datetime.now(UTC),
            order_type="MARKET",
            filled_at=datetime.now(UTC),
        )

        # Should not raise validation error
        entry = service.record_filled_order(
            order_result=order_result,
            correlation_id="corr-zero-ask",
            rebalance_plan=None,
            quote_at_fill=quote,
        )

        assert entry is not None
        assert entry.bid_at_fill == Decimal("100.00")  # Valid bid preserved
        assert entry.ask_at_fill is None  # Invalid ask filtered out

    def test_zero_bid_price_filtered_out(self):
        """Test that zero bid_price is filtered out."""
        from the_alchemiser.shared.types.market_data import QuoteModel

        service = TradeLedgerService()

        # Create quote with zero bid_price (invalid)
        quote = QuoteModel(
            symbol="KOLD",
            bid_price=Decimal("0.0"),  # Invalid - should be filtered
            ask_price=Decimal("50.50"),
            bid_size=Decimal("0"),
            ask_size=Decimal("100"),
            timestamp=datetime.now(UTC),
        )

        order_result = OrderResult(
            symbol="KOLD",
            action="SELL",
            trade_amount=Decimal("500.00"),
            shares=Decimal("10"),
            price=Decimal("50.00"),
            order_id="order-zero-bid",
            success=True,
            error_message=None,
            timestamp=datetime.now(UTC),
            order_type="MARKET",
            filled_at=datetime.now(UTC),
        )

        # Should not raise validation error
        entry = service.record_filled_order(
            order_result=order_result,
            correlation_id="corr-zero-bid",
            rebalance_plan=None,
            quote_at_fill=quote,
        )

        assert entry is not None
        assert entry.bid_at_fill is None  # Invalid bid filtered out
        assert entry.ask_at_fill == Decimal("50.50")  # Valid ask preserved

    def test_both_prices_zero_filtered_out(self):
        """Test that both zero prices are filtered out completely."""
        from the_alchemiser.shared.types.market_data import QuoteModel

        service = TradeLedgerService()

        # Create quote with both prices zero (completely invalid)
        quote = QuoteModel(
            symbol="BADQUOTE",
            bid_price=Decimal("0.0"),  # Invalid
            ask_price=Decimal("0.0"),  # Invalid
            bid_size=Decimal("0"),
            ask_size=Decimal("0"),
            timestamp=datetime.now(UTC),
        )

        order_result = OrderResult(
            symbol="BADQUOTE",
            action="BUY",
            trade_amount=Decimal("1000.00"),
            shares=Decimal("10"),
            price=Decimal("100.00"),
            order_id="order-bad-quote",
            success=True,
            error_message=None,
            timestamp=datetime.now(UTC),
            order_type="MARKET",
            filled_at=datetime.now(UTC),
        )

        # Should not raise validation error
        entry = service.record_filled_order(
            order_result=order_result,
            correlation_id="corr-bad-quote",
            rebalance_plan=None,
            quote_at_fill=quote,
        )

        assert entry is not None
        assert entry.bid_at_fill is None  # Both filtered out
        assert entry.ask_at_fill is None
        assert entry.fill_price == Decimal("100.00")  # Core data still recorded

    def test_negative_prices_filtered_out(self):
        """Test that negative prices are filtered out (edge case)."""
        from the_alchemiser.shared.types.market_data import QuoteModel

        service = TradeLedgerService()

        # Create quote with negative prices (shouldn't happen but defensive)
        quote = QuoteModel(
            symbol="NEGATIVE",
            bid_price=Decimal("-10.00"),  # Invalid
            ask_price=Decimal("-5.00"),  # Invalid
            bid_size=Decimal("100"),
            ask_size=Decimal("100"),
            timestamp=datetime.now(UTC),
        )

        order_result = OrderResult(
            symbol="NEGATIVE",
            action="BUY",
            trade_amount=Decimal("1000.00"),
            shares=Decimal("10"),
            price=Decimal("100.00"),
            order_id="order-negative",
            success=True,
            error_message=None,
            timestamp=datetime.now(UTC),
            order_type="MARKET",
            filled_at=datetime.now(UTC),
        )

        # Should not raise validation error
        entry = service.record_filled_order(
            order_result=order_result,
            correlation_id="corr-negative",
            rebalance_plan=None,
            quote_at_fill=quote,
        )

        assert entry is not None
        assert entry.bid_at_fill is None  # Negative filtered out
        assert entry.ask_at_fill is None  # Negative filtered out
