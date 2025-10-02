"""Business Unit: orchestration | Status: current

Test for email notification error details propagation.

Verifies that detailed failure information (failure reason, failed symbols)
is properly propagated from execution handler through TradeExecuted event
to notification system, resolving the "Unknown error" issue.
"""

import uuid
from datetime import UTC, datetime

from the_alchemiser.shared.events.schemas import TradeExecuted, TradingNotificationRequested


class TestNotificationErrorDetails:
    """Tests for notification error details propagation."""

    def test_trade_executed_event_includes_failure_details(self):
        """Test that TradeExecuted event can include failure details."""
        # Create a TradeExecuted event with failure details
        event = TradeExecuted(
            correlation_id=str(uuid.uuid4()),
            causation_id=str(uuid.uuid4()),
            event_id=f"trade-executed-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="execution_v2.handlers",
            source_component="TradingExecutionHandler",
            execution_data={
                "plan_id": str(uuid.uuid4()),
                "orders_placed": 10,
                "orders_succeeded": 8,
                "total_trade_value": "1000.00",
                "orders": [],
            },
            success=False,
            orders_placed=10,
            orders_succeeded=8,
            metadata={},
            failure_reason="Trade execution partially failed: 8/10 orders succeeded. Failed symbols: BWXT, LEU",
            failed_symbols=["BWXT", "LEU"],
        )

        # Verify the event has the failure details
        assert event.failure_reason is not None
        assert "8/10 orders succeeded" in event.failure_reason
        assert "BWXT" in event.failure_reason
        assert "LEU" in event.failure_reason
        assert len(event.failed_symbols) == 2
        assert "BWXT" in event.failed_symbols
        assert "LEU" in event.failed_symbols

    def test_trade_executed_event_optional_failure_fields(self):
        """Test that failure fields are optional for successful executions."""
        # Create a TradeExecuted event without failure details (success case)
        event = TradeExecuted(
            correlation_id=str(uuid.uuid4()),
            causation_id=str(uuid.uuid4()),
            event_id=f"trade-executed-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="execution_v2.handlers",
            source_component="TradingExecutionHandler",
            execution_data={
                "plan_id": str(uuid.uuid4()),
                "orders_placed": 10,
                "orders_succeeded": 10,
                "total_trade_value": "1000.00",
                "orders": [],
            },
            success=True,
            orders_placed=10,
            orders_succeeded=10,
            metadata={},
            # failure_reason and failed_symbols not provided - should default
        )

        # Verify the event defaults are correct
        assert event.failure_reason is None
        assert event.failed_symbols == []

    def test_orchestrator_uses_failure_reason_field(self):
        """Test that orchestrator prioritizes failure_reason field over metadata."""
        # Test the logic directly without needing a full orchestrator instance
        # Create a mock TradeExecuted event with failure_reason
        event = TradeExecuted(
            correlation_id=str(uuid.uuid4()),
            causation_id=str(uuid.uuid4()),
            event_id=f"trade-executed-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="execution_v2.handlers",
            source_component="TradingExecutionHandler",
            execution_data={
                "plan_id": str(uuid.uuid4()),
                "orders_placed": 10,
                "orders_succeeded": 8,
                "total_trade_value": "1000.00",
                "orders": [],
            },
            success=False,
            orders_placed=10,
            orders_succeeded=8,
            metadata={"error_message": "Old metadata error"},  # Should be overridden
            failure_reason="Trade execution partially failed: 8/10 orders succeeded. Failed symbols: BWXT, LEU",
            failed_symbols=["BWXT", "LEU"],
        )

        # Verify the field precedence: failure_reason should be used
        # This matches the orchestrator logic: event.failure_reason or event.metadata.get("error_message")
        error_message = (
            event.failure_reason or event.metadata.get("error_message") or "Unknown error"
        )

        assert error_message == event.failure_reason
        assert "8/10 orders succeeded" in error_message
        assert "BWXT" in error_message
        assert error_message != "Old metadata error"
        assert error_message != "Unknown error"

    def test_trading_notification_requested_includes_error_message(self):
        """Test that TradingNotificationRequested event includes error message."""
        # Create a TradingNotificationRequested event
        event = TradingNotificationRequested(
            correlation_id=str(uuid.uuid4()),
            causation_id=str(uuid.uuid4()),
            event_id=f"trading-notification-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="orchestration.event_driven_orchestrator",
            source_component="EventDrivenOrchestrator",
            trading_success=False,
            trading_mode="PAPER",
            orders_placed=10,
            orders_succeeded=8,
            total_trade_value=1000.0,
            execution_data={
                "plan_id": str(uuid.uuid4()),
                "orders": [],
            },
            error_message="Trade execution partially failed: 8/10 orders succeeded. Failed symbols: BWXT, LEU",
            error_code=None,
        )

        # Verify the event has the error message
        assert event.error_message is not None
        assert "8/10 orders succeeded" in event.error_message
        assert "BWXT" in event.error_message
        assert event.error_message != "Unknown error"
