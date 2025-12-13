"""Business Unit: coordinator_v2 | Status: current.

Unit tests for AggregationSessionService.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from the_alchemiser.coordinator_v2.services.aggregation_session_service import (
    AggregationSessionService,
)


class TestAggregationSessionService:
    """Tests for AggregationSessionService."""

    @pytest.fixture
    def mock_dynamodb_client(self) -> MagicMock:
        """Create a mock DynamoDB client."""
        mock = MagicMock()
        # Add exceptions attribute for ConditionalCheckFailedException
        mock.exceptions = MagicMock()
        mock.exceptions.ConditionalCheckFailedException = type(
            "ConditionalCheckFailedException", (Exception,), {}
        )
        return mock

    @pytest.fixture
    def session_service(
        self, mock_dynamodb_client: MagicMock
    ) -> AggregationSessionService:
        """Create an AggregationSessionService with mocked client."""
        with patch("boto3.client", return_value=mock_dynamodb_client):
            service = AggregationSessionService(table_name="test-table")
            service._client = mock_dynamodb_client
            return service

    def test_create_session(
        self,
        session_service: AggregationSessionService,
        mock_dynamodb_client: MagicMock,
    ) -> None:
        """Test creating a new aggregation session."""
        session_id = "test-session-123"
        correlation_id = "corr-456"
        strategy_configs = [
            ("strategy1.clj", 0.6),
            ("strategy2.clj", 0.4),
        ]

        result = session_service.create_session(
            session_id=session_id,
            correlation_id=correlation_id,
            strategy_configs=strategy_configs,
            timeout_seconds=300,
        )

        # Verify DynamoDB put_item was called
        mock_dynamodb_client.put_item.assert_called_once()
        call_kwargs = mock_dynamodb_client.put_item.call_args.kwargs

        assert call_kwargs["TableName"] == "test-table"
        item = call_kwargs["Item"]
        assert item["PK"]["S"] == f"SESSION#{session_id}"
        assert item["SK"]["S"] == "METADATA"
        assert item["session_id"]["S"] == session_id
        assert item["correlation_id"]["S"] == correlation_id
        assert item["total_strategies"]["N"] == "2"
        assert item["completed_strategies"]["N"] == "0"
        assert item["status"]["S"] == "PENDING"

        # Verify return value
        assert result["session_id"] == session_id
        assert result["correlation_id"] == correlation_id
        assert result["total_strategies"] == 2
        assert result["completed_strategies"] == 0
        assert result["status"] == "PENDING"

    def test_store_partial_signal_success(
        self,
        session_service: AggregationSessionService,
        mock_dynamodb_client: MagicMock,
    ) -> None:
        """Test storing a partial signal successfully."""
        # Mock update_item to return new count
        mock_dynamodb_client.update_item.return_value = {
            "Attributes": {"completed_strategies": {"N": "1"}}
        }

        session_id = "test-session"
        dsl_file = "strategy1.clj"
        allocation = Decimal("0.6")
        consolidated_portfolio = {"AAPL": "0.3", "MSFT": "0.3"}
        signals_data = {"strategy1": {"symbols": ["AAPL", "MSFT"]}}

        result = session_service.store_partial_signal(
            session_id=session_id,
            dsl_file=dsl_file,
            allocation=allocation,
            consolidated_portfolio=consolidated_portfolio,
            signals_data=signals_data,
            signal_count=2,
        )

        assert result == 1
        mock_dynamodb_client.put_item.assert_called_once()
        mock_dynamodb_client.update_item.assert_called_once()

    def test_store_partial_signal_duplicate(
        self,
        session_service: AggregationSessionService,
        mock_dynamodb_client: MagicMock,
    ) -> None:
        """Test that duplicate signals are ignored (idempotent)."""
        # Simulate conditional check failure (duplicate)
        mock_dynamodb_client.put_item.side_effect = (
            mock_dynamodb_client.exceptions.ConditionalCheckFailedException()
        )
        # Mock get_session for fallback
        mock_dynamodb_client.get_item.return_value = {
            "Item": {
                "session_id": {"S": "test-session"},
                "correlation_id": {"S": "corr-123"},
                "total_strategies": {"N": "2"},
                "completed_strategies": {"N": "1"},
                "status": {"S": "PENDING"},
                "created_at": {"S": "2024-01-01T00:00:00+00:00"},
                "timeout_at": {"S": "2024-01-01T00:05:00+00:00"},
            }
        }

        session_id = "test-session"
        dsl_file = "strategy1.clj"

        result = session_service.store_partial_signal(
            session_id=session_id,
            dsl_file=dsl_file,
            allocation=Decimal("0.6"),
            consolidated_portfolio={},
            signals_data={},
            signal_count=0,
        )

        # Should return existing count
        assert result == 1
        mock_dynamodb_client.put_item.assert_called_once()
        # update_item should NOT be called for duplicates
        mock_dynamodb_client.update_item.assert_not_called()

    def test_get_session_found(
        self,
        session_service: AggregationSessionService,
        mock_dynamodb_client: MagicMock,
    ) -> None:
        """Test getting an existing session."""
        mock_dynamodb_client.get_item.return_value = {
            "Item": {
                "PK": {"S": "SESSION#test-123"},
                "SK": {"S": "METADATA"},
                "session_id": {"S": "test-123"},
                "correlation_id": {"S": "corr-456"},
                "total_strategies": {"N": "2"},
                "completed_strategies": {"N": "1"},
                "status": {"S": "PENDING"},
                "created_at": {"S": "2024-01-01T00:00:00+00:00"},
                "timeout_at": {"S": "2024-01-01T00:05:00+00:00"},
            }
        }

        result = session_service.get_session("test-123")

        assert result is not None
        assert result["session_id"] == "test-123"
        assert result["total_strategies"] == 2
        assert result["completed_strategies"] == 1

    def test_get_session_not_found(
        self,
        session_service: AggregationSessionService,
        mock_dynamodb_client: MagicMock,
    ) -> None:
        """Test getting a non-existent session."""
        mock_dynamodb_client.get_item.return_value = {}

        result = session_service.get_session("nonexistent")

        assert result is None

    def test_get_all_partial_signals(
        self,
        session_service: AggregationSessionService,
        mock_dynamodb_client: MagicMock,
    ) -> None:
        """Test retrieving all partial signals for a session."""
        mock_dynamodb_client.query.return_value = {
            "Items": [
                {
                    "PK": {"S": "SESSION#test-123"},
                    "SK": {"S": "STRATEGY#strategy1.clj"},
                    "dsl_file": {"S": "strategy1.clj"},
                    "allocation": {"N": "0.6"},
                    "signal_count": {"N": "2"},
                    "completed_at": {"S": "2024-01-01T00:00:00+00:00"},
                    "consolidated_portfolio": {"S": '{"target_allocations": {"AAPL": "0.3"}}'},
                    "signals_data": {"S": "{}"},
                },
                {
                    "PK": {"S": "SESSION#test-123"},
                    "SK": {"S": "STRATEGY#strategy2.clj"},
                    "dsl_file": {"S": "strategy2.clj"},
                    "allocation": {"N": "0.4"},
                    "signal_count": {"N": "1"},
                    "completed_at": {"S": "2024-01-01T00:01:00+00:00"},
                    "consolidated_portfolio": {"S": '{"target_allocations": {"MSFT": "0.2"}}'},
                    "signals_data": {"S": "{}"},
                },
            ]
        }

        result = session_service.get_all_partial_signals("test-123")

        assert len(result) == 2
        assert result[0]["dsl_file"] == "strategy1.clj"
        assert result[1]["dsl_file"] == "strategy2.clj"
        assert result[0]["allocation"] == Decimal("0.6")
        assert result[0]["consolidated_portfolio"]["target_allocations"]["AAPL"] == "0.3"

    def test_update_session_status(
        self,
        session_service: AggregationSessionService,
        mock_dynamodb_client: MagicMock,
    ) -> None:
        """Test updating session status."""
        session_service.update_session_status("test-123", "COMPLETED")

        mock_dynamodb_client.update_item.assert_called_once()
        call_kwargs = mock_dynamodb_client.update_item.call_args.kwargs

        assert call_kwargs["TableName"] == "test-table"
        assert call_kwargs["Key"]["PK"]["S"] == "SESSION#test-123"
        assert call_kwargs["Key"]["SK"]["S"] == "METADATA"
        assert ":status" in call_kwargs["ExpressionAttributeValues"]
        assert call_kwargs["ExpressionAttributeValues"][":status"]["S"] == "COMPLETED"
