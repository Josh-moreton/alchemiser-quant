"""Business Unit: execution | Status: current.

Unit tests for the BUY phase guard safeguard.

Tests verify that:
1. BUY phase is blocked when SELL failures exceed dollar threshold
2. BUY phase proceeds when SELL failures are within threshold
3. SELL retry logic works for transient failures
4. WorkflowFailed event is emitted when BUY phase is blocked
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from the_alchemiser.execution_v2.core.smart_execution_strategy import ExecutionConfig
from the_alchemiser.execution_v2.handlers.single_trade_handler import SingleTradeHandler


class TestBuyPhaseGuard:
    """Test suite for BUY phase guard that prevents over-deployment."""

    @pytest.fixture
    def mock_container(self) -> MagicMock:
        """Create mock application container."""
        container = MagicMock()
        container.services.event_bus.return_value = MagicMock()
        container.infrastructure.alpaca_manager.return_value = MagicMock()
        return container

    @pytest.fixture
    def mock_run_service(self) -> MagicMock:
        """Create mock execution run service."""
        return MagicMock()

    @pytest.fixture
    def handler(self, mock_container: MagicMock, mock_run_service: MagicMock) -> SingleTradeHandler:
        """Create handler with mocked dependencies."""
        return SingleTradeHandler(
            container=mock_container,
            run_service=mock_run_service,
        )

    def test_buy_phase_blocked_when_sell_failures_exceed_threshold(
        self,
        handler: SingleTradeHandler,
        mock_run_service: MagicMock,
    ) -> None:
        """BUY phase should be BLOCKED when sell_failed_amount > threshold."""
        # Arrange: SELL failures exceed threshold ($600 > $500 default threshold)
        completion_result: dict[str, Any] = {
            "current_phase": "SELL",
            "sell_phase_complete": True,
            "sell_completed": 3,
            "sell_total": 3,
            "buy_total": 5,
            "sell_failed_amount": Decimal("600.00"),  # Above $500 threshold
            "sell_succeeded_amount": Decimal("1400.00"),
        }
        run_id = "test-run-123"
        correlation_id = "test-corr-456"

        # Act
        handler._check_and_trigger_buy_phase(
            run_id=run_id,
            correlation_id=correlation_id,
            completion_result=completion_result,
        )

        # Assert: Run marked as FAILED, transition_to_buy_phase NOT called
        mock_run_service.update_run_status.assert_called_once_with(run_id, "FAILED")
        mock_run_service.transition_to_buy_phase.assert_not_called()
        mock_run_service.get_pending_buy_trades.assert_not_called()

    def test_buy_phase_proceeds_when_sell_failures_within_threshold(
        self,
        handler: SingleTradeHandler,
        mock_run_service: MagicMock,
    ) -> None:
        """BUY phase should PROCEED when sell_failed_amount <= threshold."""
        # Arrange: SELL failures within threshold ($200 < $500 default threshold)
        completion_result: dict[str, Any] = {
            "current_phase": "SELL",
            "sell_phase_complete": True,
            "sell_completed": 3,
            "sell_total": 3,
            "buy_total": 5,
            "sell_failed_amount": Decimal("200.00"),  # Below $500 threshold
            "sell_succeeded_amount": Decimal("1800.00"),
        }
        run_id = "test-run-123"
        correlation_id = "test-corr-456"

        # Configure mock to allow transition
        mock_run_service.transition_to_buy_phase.return_value = True
        mock_run_service.get_pending_buy_trades.return_value = [
            {"trade_id": "buy-1", "message_body": "{}"},
        ]

        # Act
        with patch("boto3.client") as mock_boto:
            mock_sqs = MagicMock()
            mock_boto.return_value = mock_sqs
            with patch.dict("os.environ", {"EXECUTION_FIFO_QUEUE_URL": "https://sqs.test"}):
                handler._check_and_trigger_buy_phase(
                    run_id=run_id,
                    correlation_id=correlation_id,
                    completion_result=completion_result,
                )

        # Assert: Transition called, run NOT marked as FAILED
        mock_run_service.transition_to_buy_phase.assert_called_once_with(run_id)
        mock_run_service.update_run_status.assert_not_called()

    def test_buy_phase_proceeds_when_no_sell_failures(
        self,
        handler: SingleTradeHandler,
        mock_run_service: MagicMock,
    ) -> None:
        """BUY phase should PROCEED when there are no SELL failures."""
        # Arrange: No SELL failures at all
        completion_result: dict[str, Any] = {
            "current_phase": "SELL",
            "sell_phase_complete": True,
            "sell_completed": 3,
            "sell_total": 3,
            "buy_total": 5,
            "sell_failed_amount": Decimal("0.00"),  # No failures
            "sell_succeeded_amount": Decimal("2000.00"),
        }
        run_id = "test-run-123"
        correlation_id = "test-corr-456"

        mock_run_service.transition_to_buy_phase.return_value = True
        mock_run_service.get_pending_buy_trades.return_value = []

        # Act
        handler._check_and_trigger_buy_phase(
            run_id=run_id,
            correlation_id=correlation_id,
            completion_result=completion_result,
        )

        # Assert: Transition called
        mock_run_service.transition_to_buy_phase.assert_called_once_with(run_id)
        mock_run_service.update_run_status.assert_not_called()

    def test_buy_phase_not_triggered_when_sell_phase_incomplete(
        self,
        handler: SingleTradeHandler,
        mock_run_service: MagicMock,
    ) -> None:
        """BUY phase should NOT trigger when SELL phase is incomplete."""
        # Arrange: SELL phase not complete yet
        completion_result: dict[str, Any] = {
            "current_phase": "SELL",
            "sell_phase_complete": False,  # Not complete
            "sell_completed": 2,
            "sell_total": 3,
            "buy_total": 5,
            "sell_failed_amount": Decimal("0.00"),
            "sell_succeeded_amount": Decimal("1000.00"),
        }
        run_id = "test-run-123"
        correlation_id = "test-corr-456"

        # Act
        handler._check_and_trigger_buy_phase(
            run_id=run_id,
            correlation_id=correlation_id,
            completion_result=completion_result,
        )

        # Assert: Nothing should happen
        mock_run_service.transition_to_buy_phase.assert_not_called()
        mock_run_service.update_run_status.assert_not_called()

    def test_buy_phase_not_triggered_when_no_buy_trades(
        self,
        handler: SingleTradeHandler,
        mock_run_service: MagicMock,
    ) -> None:
        """BUY phase should NOT trigger when there are no BUY trades."""
        # Arrange: No BUY trades
        completion_result: dict[str, Any] = {
            "current_phase": "SELL",
            "sell_phase_complete": True,
            "sell_completed": 3,
            "sell_total": 3,
            "buy_total": 0,  # No BUY trades
            "sell_failed_amount": Decimal("0.00"),
            "sell_succeeded_amount": Decimal("2000.00"),
        }
        run_id = "test-run-123"
        correlation_id = "test-corr-456"

        # Act
        handler._check_and_trigger_buy_phase(
            run_id=run_id,
            correlation_id=correlation_id,
            completion_result=completion_result,
        )

        # Assert: Nothing should happen
        mock_run_service.transition_to_buy_phase.assert_not_called()
        mock_run_service.update_run_status.assert_not_called()

    def test_workflow_failed_event_emitted_when_buy_blocked(
        self,
        handler: SingleTradeHandler,
        mock_run_service: MagicMock,
        mock_container: MagicMock,
    ) -> None:
        """WorkflowFailed event should be emitted when BUY phase is blocked."""
        # Arrange: SELL failures exceed threshold
        completion_result: dict[str, Any] = {
            "current_phase": "SELL",
            "sell_phase_complete": True,
            "sell_completed": 3,
            "sell_total": 3,
            "buy_total": 5,
            "sell_failed_amount": Decimal("1000.00"),  # Above threshold
            "sell_succeeded_amount": Decimal("1000.00"),
        }
        run_id = "test-run-123"
        correlation_id = "test-corr-456"

        mock_event_bus = mock_container.services.event_bus.return_value

        # Act
        with patch(
            "the_alchemiser.execution_v2.handlers.single_trade_handler.publish_to_eventbridge"
        ) as mock_publish:
            handler._check_and_trigger_buy_phase(
                run_id=run_id,
                correlation_id=correlation_id,
                completion_result=completion_result,
            )

            # Assert: Event published
            mock_event_bus.publish.assert_called_once()
            mock_publish.assert_called_once()

            # Verify the event is a WorkflowFailed with correct details
            published_event = mock_event_bus.publish.call_args[0][0]
            assert published_event.workflow_type == "TradingExecution"
            assert "BUY phase blocked" in published_event.failure_reason
            assert published_event.failure_step == "SELL_PHASE_GUARD"
            assert published_event.error_details["sell_failed_amount"] == "1000.00"


class TestExecutionConfigThreshold:
    """Test the configuration for sell failure threshold."""

    def test_default_threshold_is_500(self) -> None:
        """Default sell_failure_threshold_usd should be $500."""
        config = ExecutionConfig()
        assert config.sell_failure_threshold_usd == Decimal("500.00")

    def test_default_max_sell_retries_is_2(self) -> None:
        """Default max_sell_retries should be 2."""
        config = ExecutionConfig()
        assert config.max_sell_retries == 2

    def test_default_sell_retry_delay_is_5(self) -> None:
        """Default sell_retry_delay_seconds should be 5."""
        config = ExecutionConfig()
        assert config.sell_retry_delay_seconds == 5


class TestSellPhaseAmountTracking:
    """Test dollar amount tracking in ExecutionRunService."""

    @pytest.fixture
    def mock_dynamodb_client(self) -> MagicMock:
        """Create mock DynamoDB client."""
        return MagicMock()

    def test_mark_trade_completed_updates_sell_failed_amount(
        self, mock_dynamodb_client: MagicMock
    ) -> None:
        """Failed SELL trade should increment sell_failed_amount."""
        from the_alchemiser.shared.services.execution_run_service import (
            ExecutionRunService,
        )

        # Arrange
        with patch("boto3.client", return_value=mock_dynamodb_client):
            service = ExecutionRunService(table_name="test-table")

        # Configure mock response
        mock_dynamodb_client.update_item.return_value = {
            "Attributes": {
                "completed_trades": {"N": "1"},
                "total_trades": {"N": "3"},
                "sell_completed": {"N": "1"},
                "sell_total": {"N": "2"},
                "buy_completed": {"N": "0"},
                "buy_total": {"N": "1"},
                "current_phase": {"S": "SELL"},
                "sell_failed_amount": {"N": "500.00"},
                "sell_succeeded_amount": {"N": "0"},
            }
        }

        # Act
        result = service.mark_trade_completed(
            run_id="test-run",
            trade_id="test-trade",
            success=False,
            phase="SELL",
            trade_amount=Decimal("500.00"),
        )

        # Assert: sell_failed_amount is in result
        assert result["sell_failed_amount"] == Decimal("500.00")

        # Verify the update expression included sell_failed_amount
        update_calls = mock_dynamodb_client.update_item.call_args_list
        # Second call is the metadata update
        metadata_call = update_calls[1]
        update_expr = metadata_call.kwargs.get("UpdateExpression", "")
        assert "sell_failed_amount" in update_expr

    def test_mark_trade_completed_updates_sell_succeeded_amount(
        self, mock_dynamodb_client: MagicMock
    ) -> None:
        """Successful SELL trade should increment sell_succeeded_amount."""
        from the_alchemiser.shared.services.execution_run_service import (
            ExecutionRunService,
        )

        # Arrange
        with patch("boto3.client", return_value=mock_dynamodb_client):
            service = ExecutionRunService(table_name="test-table")

        # Configure mock response
        mock_dynamodb_client.update_item.return_value = {
            "Attributes": {
                "completed_trades": {"N": "1"},
                "total_trades": {"N": "3"},
                "sell_completed": {"N": "1"},
                "sell_total": {"N": "2"},
                "buy_completed": {"N": "0"},
                "buy_total": {"N": "1"},
                "current_phase": {"S": "SELL"},
                "sell_failed_amount": {"N": "0"},
                "sell_succeeded_amount": {"N": "1000.00"},
            }
        }

        # Act
        result = service.mark_trade_completed(
            run_id="test-run",
            trade_id="test-trade",
            success=True,
            phase="SELL",
            trade_amount=Decimal("1000.00"),
        )

        # Assert: sell_succeeded_amount is in result
        assert result["sell_succeeded_amount"] == Decimal("1000.00")

        # Verify the update expression included sell_succeeded_amount
        update_calls = mock_dynamodb_client.update_item.call_args_list
        metadata_call = update_calls[1]
        update_expr = metadata_call.kwargs.get("UpdateExpression", "")
        assert "sell_succeeded_amount" in update_expr
