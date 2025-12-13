"""Business Unit: coordinator_v2 | Status: current.

Unit tests for StrategyInvoker.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from the_alchemiser.coordinator_v2.services.strategy_invoker import StrategyInvoker


class TestStrategyInvoker:
    """Tests for StrategyInvoker service."""

    @pytest.fixture
    def mock_lambda_client(self) -> MagicMock:
        """Create a mock Lambda client."""
        return MagicMock()

    @pytest.fixture
    def invoker(self, mock_lambda_client: MagicMock) -> StrategyInvoker:
        """Create a StrategyInvoker with mocked client."""
        with patch("boto3.client", return_value=mock_lambda_client):
            invoker = StrategyInvoker(function_name="TestStrategyLambda")
            invoker._client = mock_lambda_client
            return invoker

    def test_invoke_for_strategy(
        self,
        invoker: StrategyInvoker,
        mock_lambda_client: MagicMock,
    ) -> None:
        """Test invoking Lambda for a single strategy."""
        mock_lambda_client.invoke.return_value = {
            "StatusCode": 202,
            "ResponseMetadata": {"RequestId": "req-123"},
        }

        request_id = invoker.invoke_for_strategy(
            session_id="session-123",
            correlation_id="corr-456",
            dsl_file="strategy1.clj",
            allocation=0.6,
            strategy_number=1,
            total_strategies=2,
        )

        # Verify Lambda invocation
        mock_lambda_client.invoke.assert_called_once()
        call_kwargs = mock_lambda_client.invoke.call_args.kwargs

        assert call_kwargs["FunctionName"] == "TestStrategyLambda"
        assert call_kwargs["InvocationType"] == "Event"  # Async invocation

        # Verify payload
        payload = json.loads(call_kwargs["Payload"])
        assert payload["session_id"] == "session-123"
        assert payload["correlation_id"] == "corr-456"
        assert payload["dsl_file"] == "strategy1.clj"
        assert payload["allocation"] == 0.6
        assert payload["strategy_number"] == 1
        assert payload["total_strategies"] == 2

        assert request_id == "req-123"

    def test_invoke_all_strategies(
        self,
        invoker: StrategyInvoker,
        mock_lambda_client: MagicMock,
    ) -> None:
        """Test invoking Lambda for all strategies."""
        # Each call returns different request ID
        mock_lambda_client.invoke.side_effect = [
            {"StatusCode": 202, "ResponseMetadata": {"RequestId": "req-1"}},
            {"StatusCode": 202, "ResponseMetadata": {"RequestId": "req-2"}},
            {"StatusCode": 202, "ResponseMetadata": {"RequestId": "req-3"}},
        ]

        strategy_configs = [
            ("strategy1.clj", 0.5),
            ("strategy2.clj", 0.3),
            ("strategy3.clj", 0.2),
        ]

        request_ids = invoker.invoke_all_strategies(
            session_id="session-abc",
            correlation_id="corr-xyz",
            strategy_configs=strategy_configs,
        )

        assert len(request_ids) == 3
        assert request_ids == ["req-1", "req-2", "req-3"]

        # Verify all strategies were invoked
        assert mock_lambda_client.invoke.call_count == 3

        # Check payload of first call
        first_call = mock_lambda_client.invoke.call_args_list[0]
        payload = json.loads(first_call.kwargs["Payload"])
        assert payload["dsl_file"] == "strategy1.clj"
        assert payload["allocation"] == 0.5
        assert payload["strategy_number"] == 1
        assert payload["total_strategies"] == 3

        # Check payload of last call
        last_call = mock_lambda_client.invoke.call_args_list[2]
        payload = json.loads(last_call.kwargs["Payload"])
        assert payload["dsl_file"] == "strategy3.clj"
        assert payload["allocation"] == 0.2
        assert payload["strategy_number"] == 3
        assert payload["total_strategies"] == 3

    def test_invoke_strategy_handles_error(
        self,
        invoker: StrategyInvoker,
        mock_lambda_client: MagicMock,
    ) -> None:
        """Test that invocation errors are propagated."""
        mock_lambda_client.invoke.side_effect = ClientError(
            {"Error": {"Code": "ServiceException", "Message": "Service unavailable"}},
            "Invoke",
        )

        with pytest.raises(ClientError):
            invoker.invoke_for_strategy(
                session_id="session-123",
                correlation_id="corr-456",
                dsl_file="strategy1.clj",
                allocation=0.6,
                strategy_number=1,
                total_strategies=1,
            )

    def test_invoke_empty_strategies_list(
        self,
        invoker: StrategyInvoker,
        mock_lambda_client: MagicMock,
    ) -> None:
        """Test invoking with empty strategies list."""
        request_ids = invoker.invoke_all_strategies(
            session_id="session-empty",
            correlation_id="corr-empty",
            strategy_configs=[],
        )

        assert request_ids == []
        mock_lambda_client.invoke.assert_not_called()
