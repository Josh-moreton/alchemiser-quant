"""Business Unit: execution | Status: current.

Tests for trade ledger service.
"""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from the_alchemiser.execution_v2.models.execution_result import OrderResult
from the_alchemiser.execution_v2.services.trade_ledger import TradeLedgerService
from the_alchemiser.shared.schemas.rebalance_plan import (
    RebalancePlan,
    RebalancePlanItem,
)
from the_alchemiser.shared.types.quote import QuoteModel


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
            ts=datetime.now(UTC),
            bid=Decimal("249.50"),
            ask=Decimal("250.50"),
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

    def test_persist_to_s3_success(self):
        """Test successful S3 persistence."""
        service = TradeLedgerService()

        # Mock S3 client directly on the service instance
        mock_s3_client = MagicMock()
        service._s3_client = mock_s3_client

        # Override settings for test
        service._settings.trade_ledger.enabled = True
        service._settings.trade_ledger.bucket_name = "test-bucket"

        # Record an order
        order_result = OrderResult(
            symbol="TEST",
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
        service.record_filled_order(
            order_result=order_result,
            correlation_id="test-corr-123",
            rebalance_plan=None,
            quote_at_fill=None,
        )

        # Persist to S3
        result = service.persist_to_s3(correlation_id="test-corr-123")

        assert result is True
        mock_s3_client.put_object.assert_called_once()
        call_kwargs = mock_s3_client.put_object.call_args[1]
        assert call_kwargs["Bucket"] == "test-bucket"
        assert "trade-ledgers/" in call_kwargs["Key"]
        assert call_kwargs["ContentType"] == "application/json"

    def test_persist_to_s3_disabled(self):
        """Test that S3 persistence can be disabled."""
        service = TradeLedgerService()
        service._settings.trade_ledger.enabled = False

        result = service.persist_to_s3(correlation_id="test-corr")
        assert result is False

    def test_persist_to_s3_no_entries(self):
        """Test S3 persistence with no entries."""
        service = TradeLedgerService()
        service._settings.trade_ledger.enabled = True
        service._settings.trade_ledger.bucket_name = "test-bucket"

        result = service.persist_to_s3(correlation_id="test-corr")
        assert result is True  # Returns True but doesn't actually persist
