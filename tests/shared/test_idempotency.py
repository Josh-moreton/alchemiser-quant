#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Unit tests for idempotency functionality.

Tests DynamoDB-backed event deduplication for Lambda handlers.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from the_alchemiser.shared.idempotency import (
    is_duplicate_event,
    mark_event_processed,
)


class TestIsDuplicateEvent:
    """Test is_duplicate_event function."""

    @patch("the_alchemiser.shared.idempotency._get_dynamodb_client")
    def test_event_not_duplicate_when_not_found(self, mock_get_client: Mock) -> None:
        """Test returns False when event not in table."""
        mock_client = MagicMock()
        mock_client.get_item.return_value = {}  # No "Item" key
        mock_get_client.return_value = mock_client
        
        result = is_duplicate_event("evt-123", stage="dev")
        
        assert result is False
        mock_client.get_item.assert_called_once()

    @patch("the_alchemiser.shared.idempotency._get_dynamodb_client")
    def test_event_is_duplicate_when_found(self, mock_get_client: Mock) -> None:
        """Test returns True when event exists in table."""
        mock_client = MagicMock()
        mock_client.get_item.return_value = {
            "Item": {
                "event_id": {"S": "evt-123"},
                "processed_at": {"N": "1234567890"},
            }
        }
        mock_get_client.return_value = mock_client
        
        result = is_duplicate_event("evt-123", stage="dev")
        
        assert result is True
        mock_client.get_item.assert_called_once()

    @patch("the_alchemiser.shared.idempotency._get_dynamodb_client")
    def test_uses_custom_table_name(self, mock_get_client: Mock) -> None:
        """Test uses provided table_name parameter."""
        mock_client = MagicMock()
        mock_client.get_item.return_value = {}
        mock_get_client.return_value = mock_client
        
        is_duplicate_event("evt-123", table_name="custom-table")
        
        call_args = mock_client.get_item.call_args
        assert call_args[1]["TableName"] == "custom-table"

    @patch("the_alchemiser.shared.idempotency._get_dynamodb_client")
    def test_uses_consistent_read(self, mock_get_client: Mock) -> None:
        """Test uses consistent read for strong consistency."""
        mock_client = MagicMock()
        mock_client.get_item.return_value = {}
        mock_get_client.return_value = mock_client
        
        is_duplicate_event("evt-123", stage="dev")
        
        call_args = mock_client.get_item.call_args
        assert call_args[1]["ConsistentRead"] is True

    @patch("the_alchemiser.shared.idempotency._get_dynamodb_client")
    def test_returns_false_on_error_fail_open(self, mock_get_client: Mock) -> None:
        """Test returns False (fail-open) when DynamoDB error occurs."""
        mock_client = MagicMock()
        mock_client.get_item.side_effect = Exception("DynamoDB unavailable")
        mock_get_client.return_value = mock_client
        
        result = is_duplicate_event("evt-123", stage="dev")
        
        assert result is False

    def test_returns_false_for_empty_event_id(self) -> None:
        """Test returns False when event_id is empty."""
        result = is_duplicate_event("", stage="dev")
        
        assert result is False

    @patch("the_alchemiser.shared.idempotency._get_dynamodb_client")
    def test_constructs_correct_key(self, mock_get_client: Mock) -> None:
        """Test constructs correct DynamoDB key."""
        mock_client = MagicMock()
        mock_client.get_item.return_value = {}
        mock_get_client.return_value = mock_client
        
        is_duplicate_event("evt-456", stage="dev")
        
        call_args = mock_client.get_item.call_args
        assert call_args[1]["Key"] == {"event_id": {"S": "evt-456"}}


class TestMarkEventProcessed:
    """Test mark_event_processed function."""

    @patch("the_alchemiser.shared.idempotency._get_dynamodb_client")
    @patch("time.time")
    def test_marks_event_successfully(
        self, mock_time: Mock, mock_get_client: Mock
    ) -> None:
        """Test successfully writes event to table."""
        mock_time.return_value = 1000000000
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        result = mark_event_processed("evt-123", stage="dev", ttl_seconds=3600)
        
        assert result is True
        mock_client.put_item.assert_called_once()

    @patch("the_alchemiser.shared.idempotency._get_dynamodb_client")
    def test_uses_custom_table_name(self, mock_get_client: Mock) -> None:
        """Test uses provided table_name parameter."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        mark_event_processed("evt-123", table_name="custom-table")
        
        call_args = mock_client.put_item.call_args
        assert call_args[1]["TableName"] == "custom-table"

    @patch("the_alchemiser.shared.idempotency._get_dynamodb_client")
    @patch("time.time")
    def test_sets_ttl_correctly(self, mock_time: Mock, mock_get_client: Mock) -> None:
        """Test sets TTL expiration correctly."""
        mock_time.return_value = 1000000000
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        mark_event_processed("evt-123", stage="dev", ttl_seconds=7200)
        
        call_args = mock_client.put_item.call_args
        item = call_args[1]["Item"]
        assert item["ttl"]["N"] == str(1000000000 + 7200)

    @patch("the_alchemiser.shared.idempotency._get_dynamodb_client")
    @patch("time.time")
    def test_stores_processed_timestamp(
        self, mock_time: Mock, mock_get_client: Mock
    ) -> None:
        """Test stores current timestamp in processed_at."""
        mock_time.return_value = 1234567890
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        mark_event_processed("evt-123", stage="dev")
        
        call_args = mock_client.put_item.call_args
        item = call_args[1]["Item"]
        assert item["processed_at"]["N"] == "1234567890"

    @patch("the_alchemiser.shared.idempotency._get_dynamodb_client")
    def test_returns_false_on_error(self, mock_get_client: Mock) -> None:
        """Test returns False when DynamoDB write fails."""
        mock_client = MagicMock()
        mock_client.put_item.side_effect = Exception("Write failed")
        mock_get_client.return_value = mock_client
        
        result = mark_event_processed("evt-123", stage="dev")
        
        assert result is False

    def test_returns_false_for_empty_event_id(self) -> None:
        """Test returns False when event_id is empty."""
        result = mark_event_processed("", stage="dev")
        
        assert result is False

    @patch("the_alchemiser.shared.idempotency._get_dynamodb_client")
    def test_constructs_correct_item(self, mock_get_client: Mock) -> None:
        """Test constructs correct DynamoDB item structure."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        mark_event_processed("evt-789", stage="dev")
        
        call_args = mock_client.put_item.call_args
        item = call_args[1]["Item"]
        assert "event_id" in item
        assert item["event_id"]["S"] == "evt-789"
        assert "processed_at" in item
        assert "ttl" in item
