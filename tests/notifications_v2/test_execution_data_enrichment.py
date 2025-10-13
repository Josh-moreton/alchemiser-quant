"""Business Unit: notifications | Status: current.

Tests for execution data enrichment in email notifications.

Verifies that execution data is properly passed from events to email templates
to ensure emails contain complete trading information.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from the_alchemiser.notifications_v2.service import _ExecutionResultAdapter
from the_alchemiser.shared.events.schemas import TradingNotificationRequested


class TestExecutionDataEnrichment:
    """Test execution data extraction and enrichment for email notifications."""

    def test_adapter_extracts_orders_executed_from_execution_data(self) -> None:
        """Test that adapter extracts orders_executed from event execution_data."""
        orders_executed = [
            {
                "symbol": "SPY",
                "side": "buy",
                "qty": 10.0,
                "status": "filled",
                "filled_avg_price": 450.25,
            },
            {
                "symbol": "BND",
                "side": "sell",
                "qty": 5.0,
                "status": "filled",
                "filled_avg_price": 75.50,
            },
        ]

        event = TradingNotificationRequested(
            correlation_id="test-123",
            causation_id="test-cause-123",
            event_id="test-event-123",
            timestamp=datetime.now(UTC),
            source_module="test",
            source_component="test",
            trading_success=True,
            trading_mode="PAPER",
            orders_placed=2,
            orders_succeeded=2,
            total_trade_value=Decimal("5000.00"),
            execution_data={"orders_executed": orders_executed},
        )

        adapter = _ExecutionResultAdapter(event)

        assert adapter.orders_executed == orders_executed
        assert len(adapter.orders_executed) == 2
        assert adapter.orders_executed[0]["symbol"] == "SPY"
        assert adapter.orders_executed[1]["symbol"] == "BND"

    def test_adapter_extracts_strategy_signals_from_execution_data(self) -> None:
        """Test that adapter extracts strategy_signals from event execution_data."""
        strategy_signals = {
            "Nuclear": {"signal": "bullish", "confidence": 0.85},
            "Phoenix": {"signal": "neutral", "confidence": 0.60},
        }

        event = TradingNotificationRequested(
            correlation_id="test-123",
            causation_id="test-cause-123",
            event_id="test-event-123",
            timestamp=datetime.now(UTC),
            source_module="test",
            source_component="test",
            trading_success=True,
            trading_mode="PAPER",
            orders_placed=0,
            orders_succeeded=0,
            total_trade_value=Decimal("0.00"),
            execution_data={"strategy_signals": strategy_signals},
        )

        adapter = _ExecutionResultAdapter(event)

        assert adapter.strategy_signals == strategy_signals
        assert "Nuclear" in adapter.strategy_signals
        assert adapter.strategy_signals["Nuclear"]["signal"] == "bullish"

    def test_adapter_extracts_consolidated_portfolio_from_execution_data(self) -> None:
        """Test that adapter extracts consolidated_portfolio from event execution_data."""
        consolidated_portfolio = {
            "SPY": 0.6,
            "BND": 0.3,
            "GLD": 0.1,
        }

        event = TradingNotificationRequested(
            correlation_id="test-123",
            causation_id="test-cause-123",
            event_id="test-event-123",
            timestamp=datetime.now(UTC),
            source_module="test",
            source_component="test",
            trading_success=True,
            trading_mode="PAPER",
            orders_placed=0,
            orders_succeeded=0,
            total_trade_value=Decimal("0.00"),
            execution_data={"consolidated_portfolio": consolidated_portfolio},
        )

        adapter = _ExecutionResultAdapter(event)

        assert adapter.consolidated_portfolio == consolidated_portfolio
        assert adapter.consolidated_portfolio["SPY"] == 0.6
        assert adapter.consolidated_portfolio["BND"] == 0.3
        assert adapter.consolidated_portfolio["GLD"] == 0.1

    def test_adapter_extracts_execution_summary_from_execution_data(self) -> None:
        """Test that adapter extracts execution_summary from event execution_data."""
        execution_summary = {
            "orders_placed": 3,
            "orders_succeeded": 2,
            "consolidated_portfolio": {"SPY": 0.5, "BND": 0.5},
        }

        event = TradingNotificationRequested(
            correlation_id="test-123",
            causation_id="test-cause-123",
            event_id="test-event-123",
            timestamp=datetime.now(UTC),
            source_module="test",
            source_component="test",
            trading_success=True,
            trading_mode="PAPER",
            orders_placed=3,
            orders_succeeded=2,
            total_trade_value=Decimal("1000.00"),
            execution_data={"execution_summary": execution_summary},
        )

        adapter = _ExecutionResultAdapter(event)

        assert adapter.execution_summary == execution_summary
        assert adapter.execution_summary["orders_placed"] == 3
        assert adapter.execution_summary["orders_succeeded"] == 2

    def test_adapter_handles_empty_execution_data_gracefully(self) -> None:
        """Test that adapter handles empty execution_data without errors."""
        event = TradingNotificationRequested(
            correlation_id="test-123",
            causation_id="test-cause-123",
            event_id="test-event-123",
            timestamp=datetime.now(UTC),
            source_module="test",
            source_component="test",
            trading_success=True,
            trading_mode="PAPER",
            orders_placed=0,
            orders_succeeded=0,
            total_trade_value=Decimal("0.00"),
            execution_data={},
        )

        adapter = _ExecutionResultAdapter(event)

        # Should default to empty collections, not None or raise errors
        assert adapter.orders_executed == []
        assert adapter.strategy_signals == {}
        assert adapter.consolidated_portfolio == {}
        assert adapter.execution_summary == {}

    def test_adapter_handles_missing_keys_in_execution_data_gracefully(self) -> None:
        """Test that adapter handles missing keys in execution_data without errors."""
        # execution_data with only some keys present
        event = TradingNotificationRequested(
            correlation_id="test-123",
            causation_id="test-cause-123",
            event_id="test-event-123",
            timestamp=datetime.now(UTC),
            source_module="test",
            source_component="test",
            trading_success=True,
            trading_mode="PAPER",
            orders_placed=0,
            orders_succeeded=0,
            total_trade_value=Decimal("0.00"),
            execution_data={"some_other_key": "some_value"},
        )

        adapter = _ExecutionResultAdapter(event)

        # Should default to empty collections for missing keys
        assert adapter.orders_executed == []
        assert adapter.strategy_signals == {}
        assert adapter.consolidated_portfolio == {}
        assert adapter.execution_summary == {}

    def test_adapter_extracts_complete_execution_context(self) -> None:
        """Test that adapter extracts all execution context fields together."""
        execution_data = {
            "orders_executed": [{"symbol": "SPY", "side": "buy", "qty": 10.0, "status": "filled"}],
            "strategy_signals": {"Nuclear": {"signal": "bullish"}},
            "consolidated_portfolio": {"SPY": 0.6, "BND": 0.4},
            "execution_summary": {
                "orders_placed": 1,
                "orders_succeeded": 1,
                "consolidated_portfolio": {"SPY": 0.6, "BND": 0.4},
            },
        }

        event = TradingNotificationRequested(
            correlation_id="test-123",
            causation_id="test-cause-123",
            event_id="test-event-123",
            timestamp=datetime.now(UTC),
            source_module="test",
            source_component="test",
            trading_success=True,
            trading_mode="PAPER",
            orders_placed=1,
            orders_succeeded=1,
            total_trade_value=Decimal("1000.00"),
            execution_data=execution_data,
        )

        adapter = _ExecutionResultAdapter(event)

        # Verify all fields are extracted
        assert len(adapter.orders_executed) == 1
        assert "Nuclear" in adapter.strategy_signals
        assert "SPY" in adapter.consolidated_portfolio
        assert adapter.execution_summary["orders_placed"] == 1
        assert adapter.success is True
        assert adapter.correlation_id == "test-123"
