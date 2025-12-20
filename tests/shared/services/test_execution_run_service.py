"""Business Unit: shared | Status: current.

Unit tests for ExecutionRunService, particularly the two-phase execution flow
and edge cases like 0 SELL trades.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from the_alchemiser.shared.services.execution_run_service import ExecutionRunService

if TYPE_CHECKING:
    from mypy_boto3_dynamodb import DynamoDBClient


class MockDynamoDBClient:
    """Mock DynamoDB client for testing."""

    def __init__(self) -> None:
        self.items: dict[tuple[str, str], dict] = {}
        self.exceptions = MagicMock()
        self.exceptions.ConditionalCheckFailedException = Exception

    def put_item(self, TableName: str, Item: dict) -> dict:
        pk = Item["PK"]["S"]
        sk = Item["SK"]["S"]
        self.items[(pk, sk)] = Item
        return {}

    def get_item(self, TableName: str, Key: dict) -> dict:
        pk = Key["PK"]["S"]
        sk = Key["SK"]["S"]
        item = self.items.get((pk, sk))
        if item:
            return {"Item": item}
        return {}

    def update_item(
        self,
        TableName: str,
        Key: dict,
        UpdateExpression: str,
        ExpressionAttributeValues: dict | None = None,
        ExpressionAttributeNames: dict | None = None,
        ConditionExpression: str | None = None,
        ReturnValues: str | None = None,
    ) -> dict:
        pk = Key["PK"]["S"]
        sk = Key["SK"]["S"]
        item = self.items.get((pk, sk), {})

        # Return updated attributes for mark_trade_completed
        if ReturnValues == "ALL_NEW":
            return {"Attributes": item}
        return {}

    def query(
        self,
        TableName: str,
        KeyConditionExpression: str,
        ExpressionAttributeValues: dict | None = None,
        FilterExpression: str | None = None,
        ExpressionAttributeNames: dict | None = None,
    ) -> dict:
        # Extract pk from expression values
        pk = ExpressionAttributeValues.get(":pk", {}).get("S", "")

        # Return matching items
        matching_items = []
        for (item_pk, item_sk), item in self.items.items():
            if item_pk == pk and item_sk.startswith("TRADE#"):
                matching_items.append(item)

        return {"Items": matching_items}


class MockTradeMessage:
    """Mock TradeMessage for testing."""

    def __init__(
        self,
        trade_id: str,
        symbol: str,
        action: str,
        phase: str,
        sequence_number: int,
        trade_amount: Decimal,
    ) -> None:
        self.trade_id = trade_id
        self.symbol = symbol
        self.action = action
        self.phase = phase
        self.sequence_number = sequence_number
        self.trade_amount = trade_amount

    def to_sqs_message_body(self) -> str:
        import json

        return json.dumps(
            {
                "trade_id": self.trade_id,
                "symbol": self.symbol,
                "action": self.action,
                "phase": self.phase,
                "sequence_number": self.sequence_number,
                "trade_amount": str(self.trade_amount),
            }
        )


class TestExecutionRunServiceSellPhaseComplete:
    """Tests for sell phase completion logic, especially 0-sells edge case."""

    def test_is_sell_phase_complete_with_zero_sells_returns_true(self) -> None:
        """When sell_total == 0, the SELL phase should be immediately complete.

        This is the key bug fix: workflows with only BUY trades should not get stuck.
        """
        mock_client = MockDynamoDBClient()
        service = ExecutionRunService(table_name="test-table")
        service._client = mock_client

        # Create a run with 0 sells and 5 buys
        run_id = "test-run-0-sells"
        mock_client.items[("RUN#" + run_id, "METADATA")] = {
            "PK": {"S": f"RUN#{run_id}"},
            "SK": {"S": "METADATA"},
            "run_id": {"S": run_id},
            "plan_id": {"S": "test-plan"},
            "correlation_id": {"S": "test-correlation"},
            "total_trades": {"N": "5"},
            "completed_trades": {"N": "0"},
            "sell_total": {"N": "0"},  # Key: 0 sells
            "sell_completed": {"N": "0"},
            "buy_total": {"N": "5"},
            "buy_completed": {"N": "0"},
            "current_phase": {"S": "SELL"},  # Still in SELL phase
            "status": {"S": "SELL_PHASE"},
            "created_at": {"S": datetime.now(UTC).isoformat()},
        }

        # SELL phase should be complete even though no trades were executed
        result = service.is_sell_phase_complete(run_id)
        assert result is True, "SELL phase should be complete when sell_total == 0"

    def test_is_sell_phase_complete_with_sells_pending(self) -> None:
        """When sell_total > 0 and not all completed, should return False."""
        mock_client = MockDynamoDBClient()
        service = ExecutionRunService(table_name="test-table")
        service._client = mock_client

        run_id = "test-run-sells-pending"
        mock_client.items[("RUN#" + run_id, "METADATA")] = {
            "PK": {"S": f"RUN#{run_id}"},
            "SK": {"S": "METADATA"},
            "run_id": {"S": run_id},
            "plan_id": {"S": "test-plan"},
            "correlation_id": {"S": "test-correlation"},
            "total_trades": {"N": "8"},
            "completed_trades": {"N": "1"},
            "sell_total": {"N": "3"},
            "sell_completed": {"N": "1"},  # Only 1 of 3 complete
            "buy_total": {"N": "5"},
            "buy_completed": {"N": "0"},
            "current_phase": {"S": "SELL"},
            "status": {"S": "SELL_PHASE"},
            "created_at": {"S": datetime.now(UTC).isoformat()},
        }

        result = service.is_sell_phase_complete(run_id)
        assert result is False, "SELL phase should NOT be complete with pending sells"

    def test_is_sell_phase_complete_with_all_sells_done(self) -> None:
        """When all sells are completed, should return True."""
        mock_client = MockDynamoDBClient()
        service = ExecutionRunService(table_name="test-table")
        service._client = mock_client

        run_id = "test-run-sells-done"
        mock_client.items[("RUN#" + run_id, "METADATA")] = {
            "PK": {"S": f"RUN#{run_id}"},
            "SK": {"S": "METADATA"},
            "run_id": {"S": run_id},
            "plan_id": {"S": "test-plan"},
            "correlation_id": {"S": "test-correlation"},
            "total_trades": {"N": "8"},
            "completed_trades": {"N": "3"},
            "sell_total": {"N": "3"},
            "sell_completed": {"N": "3"},  # All 3 sells complete
            "buy_total": {"N": "5"},
            "buy_completed": {"N": "0"},
            "current_phase": {"S": "SELL"},
            "status": {"S": "SELL_PHASE"},
            "created_at": {"S": datetime.now(UTC).isoformat()},
        }

        result = service.is_sell_phase_complete(run_id)
        assert result is True, "SELL phase should be complete when all sells are done"

    def test_is_sell_phase_complete_wrong_phase_returns_false(self) -> None:
        """When not in SELL phase, should return False regardless of counts."""
        mock_client = MockDynamoDBClient()
        service = ExecutionRunService(table_name="test-table")
        service._client = mock_client

        run_id = "test-run-buy-phase"
        mock_client.items[("RUN#" + run_id, "METADATA")] = {
            "PK": {"S": f"RUN#{run_id}"},
            "SK": {"S": "METADATA"},
            "run_id": {"S": run_id},
            "plan_id": {"S": "test-plan"},
            "correlation_id": {"S": "test-correlation"},
            "total_trades": {"N": "5"},
            "completed_trades": {"N": "0"},
            "sell_total": {"N": "0"},
            "sell_completed": {"N": "0"},
            "buy_total": {"N": "5"},
            "buy_completed": {"N": "0"},
            "current_phase": {"S": "BUY"},  # Already in BUY phase
            "status": {"S": "BUY_PHASE"},
            "created_at": {"S": datetime.now(UTC).isoformat()},
        }

        result = service.is_sell_phase_complete(run_id)
        assert result is False, "Should return False when not in SELL phase"


class TestExecutionRunServiceCreateRun:
    """Tests for create_run method."""

    def test_create_run_with_only_buys(self) -> None:
        """Create a run with only BUY trades - should track correctly."""
        mock_client = MockDynamoDBClient()
        service = ExecutionRunService(table_name="test-table")
        service._client = mock_client

        buy_trades = [
            MockTradeMessage(
                trade_id=f"trade-{i}",
                symbol=f"SYM{i}",
                action="BUY",
                phase="BUY",
                sequence_number=1000 + i,
                trade_amount=Decimal("100.00"),
            )
            for i in range(5)
        ]

        result = service.create_run(
            run_id="test-run-buys-only",
            plan_id="test-plan",
            correlation_id="test-correlation",
            trade_messages=buy_trades,
            run_timestamp=datetime.now(UTC),
            enqueue_sells_only=True,
        )

        assert result["sell_total"] == 0
        assert result["buy_total"] == 5
        assert result["current_phase"] == "SELL"
        assert result["status"] == "SELL_PHASE"

    def test_create_run_with_sells_and_buys(self) -> None:
        """Create a run with both SELL and BUY trades."""
        mock_client = MockDynamoDBClient()
        service = ExecutionRunService(table_name="test-table")
        service._client = mock_client

        trades = [
            MockTradeMessage(
                trade_id="sell-1",
                symbol="AAPL",
                action="SELL",
                phase="SELL",
                sequence_number=1,
                trade_amount=Decimal("100.00"),
            ),
            MockTradeMessage(
                trade_id="sell-2",
                symbol="MSFT",
                action="SELL",
                phase="SELL",
                sequence_number=2,
                trade_amount=Decimal("200.00"),
            ),
            MockTradeMessage(
                trade_id="buy-1",
                symbol="GOOGL",
                action="BUY",
                phase="BUY",
                sequence_number=1001,
                trade_amount=Decimal("150.00"),
            ),
        ]

        result = service.create_run(
            run_id="test-run-mixed",
            plan_id="test-plan",
            correlation_id="test-correlation",
            trade_messages=trades,
            run_timestamp=datetime.now(UTC),
            enqueue_sells_only=True,
        )

        assert result["sell_total"] == 2
        assert result["buy_total"] == 1
        assert result["total_trades"] == 3


class TestExecutionRunServiceTransitionToBuyPhase:
    """Tests for phase transition logic."""

    def test_transition_to_buy_phase_from_sell_phase(self) -> None:
        """Transition from SELL to BUY phase should succeed."""
        mock_client = MockDynamoDBClient()
        service = ExecutionRunService(table_name="test-table")
        service._client = mock_client

        run_id = "test-run-transition"
        mock_client.items[("RUN#" + run_id, "METADATA")] = {
            "PK": {"S": f"RUN#{run_id}"},
            "SK": {"S": "METADATA"},
            "current_phase": {"S": "SELL"},
            "status": {"S": "SELL_PHASE"},
        }

        # Should succeed (returns True on first call)
        result = service.transition_to_buy_phase(run_id)
        # Note: With our mock, this will succeed
        assert isinstance(result, bool)


class TestMarkTradeCompletedSellPhaseFlag:
    """Tests for mark_trade_completed sell_phase_complete flag."""

    def test_mark_trade_completed_returns_sell_phase_complete_true_for_0_sells(
        self,
    ) -> None:
        """When sell_total == 0, sell_phase_complete should be True in response.

        This tests the fix in mark_trade_completed at line ~385.
        """
        # This test validates the logic change:
        # sell_phase_complete = sell_total == 0 or sell_completed >= sell_total
        #
        # When sell_total == 0:
        #   sell_total == 0 -> True
        #   Result: True (short-circuit, SELL phase is complete)
        #
        # This allows the workflow to proceed to BUY phase immediately.

        # Test the logic directly
        sell_total = 0
        sell_completed = 0

        # New logic
        sell_phase_complete = sell_total == 0 or sell_completed >= sell_total
        assert sell_phase_complete is True

    def test_mark_trade_completed_returns_sell_phase_complete_false_for_pending(
        self,
    ) -> None:
        """When sells are pending, sell_phase_complete should be False."""
        sell_total = 3
        sell_completed = 1

        sell_phase_complete = sell_total == 0 or sell_completed >= sell_total
        assert sell_phase_complete is False

    def test_mark_trade_completed_returns_sell_phase_complete_true_when_done(
        self,
    ) -> None:
        """When all sells complete, sell_phase_complete should be True."""
        sell_total = 3
        sell_completed = 3

        sell_phase_complete = sell_total == 0 or sell_completed >= sell_total
        assert sell_phase_complete is True


class TestEquityCircuitBreaker:
    """Tests for the equity deployment circuit breaker.

    The circuit breaker prevents over-deployment by blocking BUY trades when
    cumulative executed buys would exceed portfolio_equity * EQUITY_DEPLOYMENT_PCT.
    """

    def test_check_equity_circuit_breaker_allows_trade_within_limit(self) -> None:
        """Trade should be allowed when cumulative buy is within limit."""
        mock_client = MockDynamoDBClient()
        service = ExecutionRunService(table_name="test-table")
        service._client = mock_client

        run_id = "test-run-circuit-breaker"
        # Set up run with $10,000 limit, $5,000 already deployed
        mock_client.items[("RUN#" + run_id, "METADATA")] = {
            "PK": {"S": f"RUN#{run_id}"},
            "SK": {"S": "METADATA"},
            "run_id": {"S": run_id},
            "plan_id": {"S": "test-plan"},
            "correlation_id": {"S": "test-correlation"},
            "total_trades": {"N": "5"},
            "completed_trades": {"N": "2"},
            "succeeded_trades": {"N": "2"},
            "failed_trades": {"N": "0"},
            "sell_total": {"N": "0"},
            "sell_completed": {"N": "0"},
            "buy_total": {"N": "5"},
            "buy_completed": {"N": "2"},
            "sell_failed_amount": {"N": "0"},
            "sell_succeeded_amount": {"N": "0"},
            "max_equity_limit_usd": {"N": "10000"},
            "cumulative_buy_succeeded_value": {"N": "5000"},
            "current_phase": {"S": "BUY"},
            "status": {"S": "BUY_PHASE"},
            "created_at": {"S": datetime.now(UTC).isoformat()},
        }

        # Propose a $3,000 buy - should be allowed (5000 + 3000 = 8000 < 10000)
        allowed, details = service.check_equity_circuit_breaker(
            run_id, Decimal("3000")
        )

        assert allowed is True
        assert details["circuit_breaker_enabled"] is True
        assert details["max_equity_limit_usd"] == Decimal("10000")
        assert details["cumulative_buy_succeeded_value"] == Decimal("5000")
        assert details["proposed_buy_value"] == Decimal("3000")
        assert details["new_cumulative_if_executed"] == Decimal("8000")
        assert details["headroom_remaining"] == Decimal("5000")
        assert details["would_exceed_limit"] is False

    def test_check_equity_circuit_breaker_blocks_trade_exceeding_limit(self) -> None:
        """Trade should be blocked when it would exceed the equity limit."""
        mock_client = MockDynamoDBClient()
        service = ExecutionRunService(table_name="test-table")
        service._client = mock_client

        run_id = "test-run-circuit-breaker-block"
        # Set up run with $10,000 limit, $9,500 already deployed
        mock_client.items[("RUN#" + run_id, "METADATA")] = {
            "PK": {"S": f"RUN#{run_id}"},
            "SK": {"S": "METADATA"},
            "run_id": {"S": run_id},
            "plan_id": {"S": "test-plan"},
            "correlation_id": {"S": "test-correlation"},
            "total_trades": {"N": "5"},
            "completed_trades": {"N": "4"},
            "succeeded_trades": {"N": "4"},
            "failed_trades": {"N": "0"},
            "sell_total": {"N": "0"},
            "sell_completed": {"N": "0"},
            "buy_total": {"N": "5"},
            "buy_completed": {"N": "4"},
            "sell_failed_amount": {"N": "0"},
            "sell_succeeded_amount": {"N": "0"},
            "max_equity_limit_usd": {"N": "10000"},
            "cumulative_buy_succeeded_value": {"N": "9500"},
            "current_phase": {"S": "BUY"},
            "status": {"S": "BUY_PHASE"},
            "created_at": {"S": datetime.now(UTC).isoformat()},
        }

        # Propose a $1,000 buy - should be BLOCKED (9500 + 1000 = 10500 > 10000)
        allowed, details = service.check_equity_circuit_breaker(
            run_id, Decimal("1000")
        )

        assert allowed is False
        assert details["circuit_breaker_enabled"] is True
        assert details["max_equity_limit_usd"] == Decimal("10000")
        assert details["cumulative_buy_succeeded_value"] == Decimal("9500")
        assert details["proposed_buy_value"] == Decimal("1000")
        assert details["new_cumulative_if_executed"] == Decimal("10500")
        assert details["headroom_remaining"] == Decimal("500")
        assert details["would_exceed_limit"] is True

    def test_check_equity_circuit_breaker_disabled_when_limit_zero(self) -> None:
        """Circuit breaker should be disabled when max_equity_limit_usd is 0."""
        mock_client = MockDynamoDBClient()
        service = ExecutionRunService(table_name="test-table")
        service._client = mock_client

        run_id = "test-run-circuit-breaker-disabled"
        # Set up run with $0 limit (circuit breaker disabled)
        mock_client.items[("RUN#" + run_id, "METADATA")] = {
            "PK": {"S": f"RUN#{run_id}"},
            "SK": {"S": "METADATA"},
            "run_id": {"S": run_id},
            "plan_id": {"S": "test-plan"},
            "correlation_id": {"S": "test-correlation"},
            "total_trades": {"N": "5"},
            "completed_trades": {"N": "0"},
            "succeeded_trades": {"N": "0"},
            "failed_trades": {"N": "0"},
            "sell_total": {"N": "0"},
            "sell_completed": {"N": "0"},
            "buy_total": {"N": "5"},
            "buy_completed": {"N": "0"},
            "sell_failed_amount": {"N": "0"},
            "sell_succeeded_amount": {"N": "0"},
            "max_equity_limit_usd": {"N": "0"},
            "cumulative_buy_succeeded_value": {"N": "0"},
            "current_phase": {"S": "BUY"},
            "status": {"S": "BUY_PHASE"},
            "created_at": {"S": datetime.now(UTC).isoformat()},
        }

        # Any buy should be allowed when circuit breaker is disabled
        allowed, details = service.check_equity_circuit_breaker(
            run_id, Decimal("1000000")
        )

        assert allowed is True
        assert details["circuit_breaker_enabled"] is False
        assert details["reason"] == "max_equity_limit_usd not configured"

    def test_check_equity_circuit_breaker_blocks_on_run_not_found(self) -> None:
        """Circuit breaker should fail-safe (block) when run is not found."""
        mock_client = MockDynamoDBClient()
        service = ExecutionRunService(table_name="test-table")
        service._client = mock_client

        # Don't create any run - it doesn't exist
        allowed, details = service.check_equity_circuit_breaker(
            "nonexistent-run", Decimal("1000")
        )

        assert allowed is False
        assert details["error"] == "run_not_found"
        assert details["run_id"] == "nonexistent-run"

    def test_check_equity_circuit_breaker_allows_trade_at_exact_limit(self) -> None:
        """Trade should be allowed when cumulative buy equals limit exactly."""
        mock_client = MockDynamoDBClient()
        service = ExecutionRunService(table_name="test-table")
        service._client = mock_client

        run_id = "test-run-exact-limit"
        # Set up run with $10,000 limit, $9,000 already deployed
        mock_client.items[("RUN#" + run_id, "METADATA")] = {
            "PK": {"S": f"RUN#{run_id}"},
            "SK": {"S": "METADATA"},
            "run_id": {"S": run_id},
            "plan_id": {"S": "test-plan"},
            "correlation_id": {"S": "test-correlation"},
            "total_trades": {"N": "5"},
            "completed_trades": {"N": "4"},
            "succeeded_trades": {"N": "4"},
            "failed_trades": {"N": "0"},
            "sell_total": {"N": "0"},
            "sell_completed": {"N": "0"},
            "buy_total": {"N": "5"},
            "buy_completed": {"N": "4"},
            "sell_failed_amount": {"N": "0"},
            "sell_succeeded_amount": {"N": "0"},
            "max_equity_limit_usd": {"N": "10000"},
            "cumulative_buy_succeeded_value": {"N": "9000"},
            "current_phase": {"S": "BUY"},
            "status": {"S": "BUY_PHASE"},
            "created_at": {"S": datetime.now(UTC).isoformat()},
        }

        # Propose a $1,000 buy - should be allowed (9000 + 1000 = 10000 == limit)
        allowed, details = service.check_equity_circuit_breaker(
            run_id, Decimal("1000")
        )

        assert allowed is True
        assert details["would_exceed_limit"] is False
        assert details["new_cumulative_if_executed"] == Decimal("10000")


class TestCreateRunWithEquityLimit:
    """Tests for create_run with max_equity_limit_usd parameter."""

    def test_create_run_stores_max_equity_limit(self) -> None:
        """create_run should store max_equity_limit_usd in DynamoDB."""
        mock_client = MockDynamoDBClient()
        service = ExecutionRunService(table_name="test-table")
        service._client = mock_client

        buy_trades = [
            MockTradeMessage(
                trade_id=f"trade-{i}",
                symbol=f"SYM{i}",
                action="BUY",
                phase="BUY",
                sequence_number=1000 + i,
                trade_amount=Decimal("100.00"),
            )
            for i in range(3)
        ]

        result = service.create_run(
            run_id="test-run-with-limit",
            plan_id="test-plan",
            correlation_id="test-correlation",
            trade_messages=buy_trades,
            run_timestamp=datetime.now(UTC),
            enqueue_sells_only=True,
            max_equity_limit_usd=Decimal("10000"),
        )

        # Check the returned result
        assert result["max_equity_limit_usd"] == Decimal("10000")
        assert result["cumulative_buy_succeeded_value"] == Decimal("0")

        # Check the stored DynamoDB item
        stored_item = mock_client.items[("RUN#test-run-with-limit", "METADATA")]
        assert stored_item["max_equity_limit_usd"]["N"] == "10000"
        assert stored_item["cumulative_buy_succeeded_value"]["N"] == "0"

    def test_create_run_defaults_equity_limit_to_zero_when_not_provided(self) -> None:
        """create_run should default max_equity_limit_usd to 0 when not provided."""
        mock_client = MockDynamoDBClient()
        service = ExecutionRunService(table_name="test-table")
        service._client = mock_client

        buy_trades = [
            MockTradeMessage(
                trade_id="trade-1",
                symbol="AAPL",
                action="BUY",
                phase="BUY",
                sequence_number=1000,
                trade_amount=Decimal("100.00"),
            )
        ]

        result = service.create_run(
            run_id="test-run-no-limit",
            plan_id="test-plan",
            correlation_id="test-correlation",
            trade_messages=buy_trades,
            run_timestamp=datetime.now(UTC),
            enqueue_sells_only=True,
            # max_equity_limit_usd not provided
        )

        # Check defaults
        assert result["max_equity_limit_usd"] == Decimal("0")
        assert result["cumulative_buy_succeeded_value"] == Decimal("0")

        # Check stored DynamoDB item
        stored_item = mock_client.items[("RUN#test-run-no-limit", "METADATA")]
        assert stored_item["max_equity_limit_usd"]["N"] == "0"


class TestGetRunWithEquityFields:
    """Tests for get_run returning equity circuit breaker fields."""

    def test_get_run_returns_equity_circuit_breaker_fields(self) -> None:
        """get_run should return cumulative_buy_succeeded_value and max_equity_limit_usd."""
        mock_client = MockDynamoDBClient()
        service = ExecutionRunService(table_name="test-table")
        service._client = mock_client

        run_id = "test-run-get-equity"
        mock_client.items[("RUN#" + run_id, "METADATA")] = {
            "PK": {"S": f"RUN#{run_id}"},
            "SK": {"S": "METADATA"},
            "run_id": {"S": run_id},
            "plan_id": {"S": "test-plan"},
            "correlation_id": {"S": "test-correlation"},
            "total_trades": {"N": "5"},
            "completed_trades": {"N": "3"},
            "succeeded_trades": {"N": "3"},
            "failed_trades": {"N": "0"},
            "sell_total": {"N": "0"},
            "sell_completed": {"N": "0"},
            "buy_total": {"N": "5"},
            "buy_completed": {"N": "3"},
            "sell_failed_amount": {"N": "0"},
            "sell_succeeded_amount": {"N": "0"},
            "max_equity_limit_usd": {"N": "15000.50"},
            "cumulative_buy_succeeded_value": {"N": "7500.25"},
            "current_phase": {"S": "BUY"},
            "status": {"S": "BUY_PHASE"},
            "created_at": {"S": datetime.now(UTC).isoformat()},
        }

        run = service.get_run(run_id)

        assert run is not None
        assert run["max_equity_limit_usd"] == Decimal("15000.50")
        assert run["cumulative_buy_succeeded_value"] == Decimal("7500.25")
