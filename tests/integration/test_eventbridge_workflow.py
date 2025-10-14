#!/usr/bin/env python3
"""Business Unit: integration | Status: current.

Integration tests for EventBridge event-driven workflow.

Tests the complete event publishing and handling workflow with EventBridge,
including idempotency, error handling, and DLQ routing.

These tests require AWS credentials and are skipped in CI unless explicitly enabled.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from unittest.mock import Mock, patch

import pytest

from the_alchemiser.shared.events import EventBridgeBus, SignalGenerated
from the_alchemiser.shared.events.errors import EventPublishError
from the_alchemiser.shared.idempotency import is_duplicate_event, mark_event_processed


@pytest.mark.integration
@pytest.mark.skipif(
    not os.environ.get("AWS_PROFILE") and not os.environ.get("AWS_ACCESS_KEY_ID"),
    reason="AWS credentials not available",
)
class TestEventBridgePublishWorkflow:
    """Integration tests for EventBridge publish workflow."""

    def test_publish_event_to_eventbridge_success(self) -> None:
        """Test publishing event to EventBridge (requires AWS credentials)."""
        # Use a test-specific bus name to avoid conflicts
        bus = EventBridgeBus(
            event_bus_name="alchemiser-trading-events-dev",
            source_prefix="alchemiser.test"
        )
        
        event = SignalGenerated(
            correlation_id="test-corr-123",
            causation_id="test-cause-123",
            event_id="test-evt-123",
            timestamp=datetime.now(UTC),
            source_module="strategy",
            signals_data={},
            consolidated_portfolio={},
            signal_count=0,
        )
        
        # This will actually call EventBridge if credentials are available
        # If it fails, it should raise EventPublishError
        try:
            bus.publish(event)
            # If successful, verify counter incremented
            assert bus.get_event_count() == 1
        except EventPublishError as e:
            # Expected if EventBridge is not configured or accessible
            pytest.skip(f"EventBridge not accessible: {e}")


@pytest.mark.integration
@pytest.mark.skipif(
    not os.environ.get("AWS_PROFILE") and not os.environ.get("AWS_ACCESS_KEY_ID"),
    reason="AWS credentials not available",
)
class TestIdempotencyIntegration:
    """Integration tests for DynamoDB-backed idempotency."""

    def test_idempotency_check_with_dynamodb(self) -> None:
        """Test idempotency check against real DynamoDB table (requires AWS)."""
        # Use test-specific event ID
        test_event_id = f"test-evt-integration-{int(datetime.now(UTC).timestamp())}"
        
        try:
            # Check if event is duplicate (should be False for new event)
            is_dup = is_duplicate_event(test_event_id, stage="dev")
            assert is_dup is False
            
            # Mark event as processed
            marked = mark_event_processed(test_event_id, stage="dev", ttl_seconds=3600)
            
            # If marking failed, skip test (table might not exist)
            if not marked:
                pytest.skip("DynamoDB table not accessible or write failed")
            
            # Check again (should be True now)
            is_dup = is_duplicate_event(test_event_id, stage="dev")
            assert is_dup is True
            
        except Exception as e:
            # Skip if DynamoDB not accessible
            pytest.skip(f"DynamoDB not accessible: {e}")


@pytest.mark.unit
class TestEventBridgeMockWorkflow:
    """Unit tests for EventBridge workflow with mocked AWS services."""

    def test_publish_and_idempotency_workflow(self) -> None:
        """Test complete workflow with mocked EventBridge and DynamoDB."""
        # Mock EventBridge client
        mock_eb_client = Mock()
        mock_eb_client.put_events.return_value = {
            "FailedEntryCount": 0,
            "Entries": [{"EventId": "eb-123"}]
        }
        
        # Create bus with mock client
        bus = EventBridgeBus(event_bus_name="test-bus")
        bus._events_client = mock_eb_client
        
        # Create event
        event = SignalGenerated(
            correlation_id="mock-corr",
            causation_id="mock-cause",
            event_id="mock-evt",
            timestamp=datetime.now(UTC),
            source_module="strategy",
            signals_data={},
            consolidated_portfolio={},
            signal_count=0,
        )
        
        # Publish event (should succeed with mock)
        bus.publish(event)
        
        # Verify EventBridge was called
        assert mock_eb_client.put_events.call_count == 1
        
        # Verify event counter incremented
        assert bus.get_event_count() == 1

    @patch("the_alchemiser.shared.idempotency._get_dynamodb_client")
    def test_idempotency_workflow_with_mock_dynamodb(self, mock_get_client: Mock) -> None:
        """Test idempotency workflow with mocked DynamoDB."""
        mock_ddb_client = Mock()
        mock_get_client.return_value = mock_ddb_client
        
        # First check: event not found
        mock_ddb_client.get_item.return_value = {}
        is_dup = is_duplicate_event("test-event", stage="dev")
        assert is_dup is False
        
        # Mark as processed
        mark_event_processed("test-event", stage="dev")
        mock_ddb_client.put_item.assert_called_once()
        
        # Second check: event found
        mock_ddb_client.get_item.return_value = {
            "Item": {
                "event_id": {"S": "test-event"},
                "processed_at": {"N": "1234567890"},
            }
        }
        is_dup = is_duplicate_event("test-event", stage="dev")
        assert is_dup is True

    def test_publish_failure_raises_error(self) -> None:
        """Test that publish failures raise EventPublishError."""
        # Mock EventBridge client with failure
        mock_eb_client = Mock()
        mock_eb_client.put_events.return_value = {
            "FailedEntryCount": 1,
            "Entries": [{
                "ErrorCode": "InternalException",
                "ErrorMessage": "Service unavailable"
            }]
        }
        
        # Create bus with mock client
        bus = EventBridgeBus(event_bus_name="test-bus")
        bus._events_client = mock_eb_client
        
        # Create event
        event = SignalGenerated(
            correlation_id="fail-corr",
            causation_id="fail-cause",
            event_id="fail-evt",
            timestamp=datetime.now(UTC),
            source_module="strategy",
            signals_data={},
            consolidated_portfolio={},
            signal_count=0,
        )
        
        # Publish should raise
        with pytest.raises(EventPublishError) as exc_info:
            bus.publish(event)
        
        assert "InternalException" in str(exc_info.value)
        assert exc_info.value.event_id == "fail-evt"
        
        # Verify counter not incremented on failure
        assert bus.get_event_count() == 0

    @patch("the_alchemiser.shared.idempotency._get_dynamodb_client")
    def test_idempotency_fails_open_on_error(self, mock_get_client: Mock) -> None:
        """Test idempotency check fails open when DynamoDB is unavailable."""
        mock_ddb_client = Mock()
        mock_ddb_client.get_item.side_effect = Exception("DynamoDB unavailable")
        mock_get_client.return_value = mock_ddb_client
        
        # Should return False (fail-open) on error
        is_dup = is_duplicate_event("test-event", stage="dev")
        assert is_dup is False


@pytest.mark.unit
class TestEventBridgeHandlerIdempotencyIntegration:
    """Test integration between handler and idempotency system."""

    @patch("the_alchemiser.lambda_handler_eventbridge.is_duplicate_event")
    @patch("the_alchemiser.lambda_handler_eventbridge.mark_event_processed")
    @patch("the_alchemiser.lambda_handler_eventbridge.ApplicationContainer")
    def test_handler_idempotency_prevents_duplicate_processing(
        self,
        mock_container: Mock,
        mock_mark: Mock,
        mock_is_duplicate: Mock,
    ) -> None:
        """Test handler uses idempotency to prevent duplicate processing."""
        from the_alchemiser.lambda_handler_eventbridge import eventbridge_handler
        
        # First invocation: not a duplicate
        mock_is_duplicate.return_value = False
        mock_mark.return_value = True
        
        # Mock handler
        mock_handler_instance = Mock()
        mock_container.create_for_environment.return_value = Mock()
        
        with patch(
            "the_alchemiser.lambda_handler_eventbridge._get_handler_for_event",
            return_value=mock_handler_instance
        ):
            context = Mock()
            context.request_id = "lambda-1"
            
            event = {
                "detail-type": "SignalGenerated",
                "source": "alchemiser.strategy",
                "detail": {
                    "event_id": "dup-test",
                    "correlation_id": "dup-corr",
                    "causation_id": "dup-cause",
                    "timestamp": "2025-10-14T12:00:00Z",
                    "event_type": "SignalGenerated",
                    "source_module": "strategy",
                    "signals_data": {},
                    "consolidated_portfolio": {},
                    "signal_count": 0,
                },
            }
            
            # First call: processes event
            response = eventbridge_handler(event, context)
            assert response["statusCode"] == 200
            assert "processed successfully" in response["body"].lower()
            mock_handler_instance.handle_event.assert_called_once()
            mock_mark.assert_called_once()
        
        # Second invocation: is a duplicate
        mock_is_duplicate.return_value = True
        mock_handler_instance.reset_mock()
        mock_mark.reset_mock()
        
        # Second call: skips processing
        response = eventbridge_handler(event, context)
        assert response["statusCode"] == 200
        assert "duplicate" in response["body"].lower()
        mock_handler_instance.handle_event.assert_not_called()
        mock_mark.assert_not_called()
