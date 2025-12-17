"""Business Unit: trade_aggregator | Status: current.

Unit tests for TradeAggregator Lambda handler and service.

Tests the trade aggregation logic using atomic counters with DynamoDB.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest


class TestTradeAggregatorLambdaHandler:
    """Tests for trade_aggregator Lambda handler."""

    @pytest.fixture
    def trade_executed_event(self) -> dict[str, Any]:
        """Create a sample TradeExecuted EventBridge event."""
        return {
            "version": "0",
            "id": str(uuid4()),
            "detail-type": "TradeExecuted",
            "source": "alchemiser.execution",
            "time": "2025-01-01T00:00:00Z",
            "region": "us-east-1",
            "detail": {
                "correlation_id": "test-correlation-id",
                "run_id": "test-run-id",
                "plan_id": "test-plan-id",
                "event_id": "test-event-id",
                "timestamp": "2025-01-01T00:00:00Z",
                "source_module": "execution_v2",
                "source_component": "ExecutionService",
                "order": {
                    "symbol": "AAPL",
                    "qty": 10,
                    "side": "buy",
                    "order_type": "market",
                },
                "result": {
                    "order_id": "order-123",
                    "status": "filled",
                    "filled_qty": 10,
                    "filled_avg_price": 150.50,
                    "filled_value": 1505.00,
                },
                "success": True,
            },
        }

    @pytest.fixture
    def unknown_event(self) -> dict[str, Any]:
        """Create an unknown event type for testing ignore logic."""
        return {
            "version": "0",
            "id": str(uuid4()),
            "detail-type": "SomeOtherEvent",
            "source": "alchemiser.other",
            "time": "2025-01-01T00:00:00Z",
            "region": "us-east-1",
            "detail": {
                "correlation_id": "test-correlation-id",
                "run_id": "test-run-id",
            },
        }

    def test_ignores_unknown_event_type(self, unknown_event: dict[str, Any]) -> None:
        """Test that unknown event types return skipped response."""
        from the_alchemiser.trade_aggregator.lambda_handler import lambda_handler

        result = lambda_handler(unknown_event, None)

        # Handler returns skip for non-TradeExecuted events
        assert result["statusCode"] == 200
        # The body contains skip status
        assert "skipped" in str(result.get("body", "")).lower() or "status" in result

    @patch("the_alchemiser.trade_aggregator.lambda_handler.TradeAggregatorService")
    def test_handler_with_trade_executed(
        self, mock_service_class: MagicMock, trade_executed_event: dict[str, Any]
    ) -> None:
        """Test that TradeExecuted events are processed correctly."""
        from the_alchemiser.trade_aggregator.lambda_handler import lambda_handler

        # Mock service methods
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.record_trade_completed.return_value = (2, 3)  # 2 of 3 done

        result = lambda_handler(trade_executed_event, None)

        # Should succeed
        assert result["statusCode"] == 200


class TestTradeAggregatorService:
    """Tests for TradeAggregatorService."""

    def test_aggregate_trade_results_success(self) -> None:
        """Test aggregation of successful trade results."""
        from the_alchemiser.trade_aggregator.services import TradeAggregatorService

        service = TradeAggregatorService.__new__(TradeAggregatorService)
        service._client = MagicMock()
        service._table_name = "test-table"

        run_metadata = {
            "run_id": "test-run",
            "total_trades": 3,
            "succeeded_trades": 2,
            "failed_trades": 1,
        }

        trade_results = [
            {
                "trade_id": "trade-1",
                "symbol": "AAPL",
                "action": "buy",
                "status": "COMPLETED",
                "trade_amount": Decimal("1500.00"),
            },
            {
                "trade_id": "trade-2",
                "symbol": "MSFT",
                "action": "buy",
                "status": "COMPLETED",
                "trade_amount": Decimal("2000.00"),
            },
            {
                "trade_id": "trade-3",
                "symbol": "GOOG",
                "action": "buy",
                "status": "FAILED",
                "trade_amount": Decimal("0"),
            },
        ]

        aggregated = service.aggregate_trade_results(run_metadata, trade_results)

        assert aggregated["execution_summary"]["total_trades"] == 3
        assert aggregated["execution_summary"]["succeeded"] == 2
        assert aggregated["execution_summary"]["failed"] == 1
        assert "GOOG" in aggregated["failed_symbols"]
        assert len(aggregated["orders_executed"]) == 3

    def test_aggregate_trade_results_all_success(self) -> None:
        """Test aggregation when all trades succeed."""
        from the_alchemiser.trade_aggregator.services import TradeAggregatorService

        service = TradeAggregatorService.__new__(TradeAggregatorService)
        service._client = MagicMock()
        service._table_name = "test-table"

        run_metadata = {
            "run_id": "test-run",
            "total_trades": 1,
            "succeeded_trades": 1,
            "failed_trades": 0,
        }

        trade_results = [
            {
                "trade_id": "trade-1",
                "symbol": "AAPL",
                "action": "buy",
                "status": "COMPLETED",
                "trade_amount": Decimal("1500.00"),
            },
        ]

        aggregated = service.aggregate_trade_results(run_metadata, trade_results)

        assert aggregated["execution_summary"]["total_trades"] == 1
        assert aggregated["execution_summary"]["succeeded"] == 1
        assert aggregated["execution_summary"]["failed"] == 0
        assert aggregated["failed_symbols"] == []


class TestTradeAggregatorConfig:
    """Tests for TradeAggregatorSettings."""

    def test_config_from_environment(self) -> None:
        """Test settings load from environment."""
        import os

        from the_alchemiser.trade_aggregator.config import TradeAggregatorSettings

        with patch.dict(
            os.environ,
            {
                "EXECUTION_RUNS_TABLE_NAME": "test-execution-runs",
            },
        ):
            settings = TradeAggregatorSettings.from_environment()

        assert settings.execution_runs_table_name == "test-execution-runs"

    def test_config_raises_without_required_env(self) -> None:
        """Test settings raises when required env var is missing."""
        import os

        from the_alchemiser.trade_aggregator.config import TradeAggregatorSettings

        with patch.dict(os.environ, {"EXECUTION_RUNS_TABLE_NAME": ""}, clear=False):
            with pytest.raises(ValueError, match="EXECUTION_RUNS_TABLE_NAME"):
                TradeAggregatorSettings.from_environment()
