"""Business Unit: shared | Status: current.

Integration tests for signal persistence lifecycle.

Tests the complete flow: Signal Generation → Trade Execution → Lifecycle Updates.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from the_alchemiser.shared.repositories.dynamodb_trade_ledger_repository import (
    DynamoDBTradeLedgerRepository,
)
from the_alchemiser.shared.schemas.strategy_signal import StrategySignal
from the_alchemiser.shared.schemas.trade_ledger import SignalLedgerEntry, TradeLedgerEntry


class TestSignalPersistenceLifecycle:
    """Integration tests for complete signal persistence lifecycle."""

    @pytest.fixture
    def mock_dynamodb_table(self):
        """Create a mock DynamoDB table."""
        mock_table = MagicMock()
        mock_table.put_item = MagicMock()
        mock_table.get_item = MagicMock()
        mock_table.query = MagicMock()
        mock_table.update_item = MagicMock()
        return mock_table

    @pytest.fixture
    def repository(self, mock_dynamodb_table: MagicMock) -> MagicMock:
        """Create repository with mocked DynamoDB."""
        repo = MagicMock(spec=DynamoDBTradeLedgerRepository)
        repo._table = mock_dynamodb_table

        # Bind all methods
        repo.put_signal = DynamoDBTradeLedgerRepository.put_signal.__get__(repo)
        repo.put_trade = DynamoDBTradeLedgerRepository.put_trade.__get__(repo)
        repo.query_signals_by_correlation = (
            DynamoDBTradeLedgerRepository.query_signals_by_correlation.__get__(repo)
        )
        repo.query_signals_by_strategy = (
            DynamoDBTradeLedgerRepository.query_signals_by_strategy.__get__(repo)
        )
        repo.update_signal_lifecycle = (
            DynamoDBTradeLedgerRepository.update_signal_lifecycle.__get__(repo)
        )
        repo.query_signals_by_state = DynamoDBTradeLedgerRepository.query_signals_by_state.__get__(
            repo
        )
        repo.compute_signal_execution_rate = (
            DynamoDBTradeLedgerRepository.compute_signal_execution_rate.__get__(repo)
        )
        repo._write_strategy_links = DynamoDBTradeLedgerRepository._write_strategy_links.__get__(
            repo
        )

        return repo

    def test_signal_to_trade_complete_lifecycle(self, repository, mock_dynamodb_table):
        """Test complete signal lifecycle: GENERATED → EXECUTED."""
        correlation_id = "corr-test-123"
        signal_id = "sig-test-456"
        order_id = "order-789"

        # Step 1: Create and persist signal with GENERATED state
        signal = SignalLedgerEntry(
            signal_id=signal_id,
            correlation_id=correlation_id,
            causation_id=correlation_id,
            timestamp=datetime(2025, 1, 15, 14, 0, 0, tzinfo=UTC),
            strategy_name="Nuclear",
            data_source="dsl_engine:Nuclear",
            symbol="TQQQ",
            action="BUY",
            target_allocation=Decimal("0.5"),
            reasoning="Strong momentum",
            lifecycle_state="GENERATED",
            signal_dto={"symbol": "TQQQ", "action": "BUY"},
            created_at=datetime.now(UTC),
        )

        repository.put_signal(signal, "ledger-123")

        # Verify signal was persisted with GENERATED state
        signal_call = mock_dynamodb_table.put_item.call_args_list[0]
        signal_item = signal_call.kwargs["Item"]
        assert signal_item["signal_id"] == signal_id
        assert signal_item["lifecycle_state"] == "GENERATED"
        assert signal_item["executed_trade_ids"] == []
        assert signal_item["GSI4PK"] == "STATE#GENERATED"

        # Step 2: Execute trade for the signal
        trade = TradeLedgerEntry(
            order_id=order_id,
            correlation_id=correlation_id,
            symbol="TQQQ",
            direction="BUY",
            filled_qty=Decimal("10"),
            fill_price=Decimal("50.0"),
            fill_timestamp=datetime(2025, 1, 15, 14, 5, 0, tzinfo=UTC),
            order_type="MARKET",
            strategy_names=["Nuclear"],
        )

        repository.put_trade(trade, "ledger-123")

        # Step 3: Query signals to update lifecycle (simulating TradeLedgerService)
        # Mock query_signals_by_correlation to return our signal
        mock_dynamodb_table.get_item.return_value = {
            "Item": {
                "PK": f"SIGNAL#{signal_id}",
                "SK": "METADATA",
                "signal_id": signal_id,
                "timestamp": "2025-01-15T14:00:00+00:00",
                "lifecycle_state": "GENERATED",
                "executed_trade_ids": [],
            }
        }

        # Update signal to EXECUTED with trade ID
        repository.update_signal_lifecycle(signal_id, "EXECUTED", [order_id])

        # Verify update was called
        update_call = mock_dynamodb_table.update_item.call_args
        assert update_call.kwargs["Key"] == {"PK": f"SIGNAL#{signal_id}", "SK": "METADATA"}
        assert update_call.kwargs["ExpressionAttributeValues"][":state"] == "EXECUTED"
        assert update_call.kwargs["ExpressionAttributeValues"][":trade_ids"] == [order_id]

    def test_signal_ignored_when_no_trade_executed(self, repository, mock_dynamodb_table):
        """Test signal marked as IGNORED when no trade executes."""
        correlation_id = "corr-test-456"
        signal_id = "sig-test-789"

        # Step 1: Create signal with GENERATED state
        signal = SignalLedgerEntry(
            signal_id=signal_id,
            correlation_id=correlation_id,
            causation_id=correlation_id,
            timestamp=datetime(2025, 1, 15, 14, 0, 0, tzinfo=UTC),
            strategy_name="Nuclear",
            data_source="dsl_engine:Nuclear",
            symbol="SPY",
            action="SELL",
            target_allocation=Decimal("0.3"),
            reasoning="Exit position",
            lifecycle_state="GENERATED",
            signal_dto={"symbol": "SPY", "action": "SELL"},
            created_at=datetime.now(UTC),
        )

        repository.put_signal(signal, "ledger-123")

        # Step 2: Workflow completes without executing trade
        # Mock get_item for signal lifecycle update
        mock_dynamodb_table.get_item.return_value = {
            "Item": {
                "PK": f"SIGNAL#{signal_id}",
                "SK": "METADATA",
                "signal_id": signal_id,
                "timestamp": "2025-01-15T14:00:00+00:00",
                "lifecycle_state": "GENERATED",
            }
        }

        # Mark signal as IGNORED
        repository.update_signal_lifecycle(signal_id, "IGNORED", None)

        # Verify update was called with IGNORED state
        update_call = mock_dynamodb_table.update_item.call_args
        assert update_call.kwargs["ExpressionAttributeValues"][":state"] == "IGNORED"

    def test_multiple_signals_with_mixed_outcomes(self, repository, mock_dynamodb_table):
        """Test workflow with multiple signals having different outcomes."""
        correlation_id = "corr-test-mixed"

        # Create 3 signals for the same workflow
        signals = [
            SignalLedgerEntry(
                signal_id="sig-1",
                correlation_id=correlation_id,
                causation_id=correlation_id,
                timestamp=datetime.now(UTC),
                strategy_name="Nuclear",
                data_source="dsl_engine:Nuclear",
                symbol="TQQQ",
                action="BUY",
                target_allocation=Decimal("0.4"),
                reasoning="Buy signal",
                lifecycle_state="GENERATED",
                signal_dto={"symbol": "TQQQ"},
                created_at=datetime.now(UTC),
            ),
            SignalLedgerEntry(
                signal_id="sig-2",
                correlation_id=correlation_id,
                causation_id=correlation_id,
                timestamp=datetime.now(UTC),
                strategy_name="Nuclear",
                data_source="dsl_engine:Nuclear",
                symbol="SOXL",
                action="BUY",
                target_allocation=Decimal("0.3"),
                reasoning="Buy signal",
                lifecycle_state="GENERATED",
                signal_dto={"symbol": "SOXL"},
                created_at=datetime.now(UTC),
            ),
            SignalLedgerEntry(
                signal_id="sig-3",
                correlation_id=correlation_id,
                causation_id=correlation_id,
                timestamp=datetime.now(UTC),
                strategy_name="Nuclear",
                data_source="dsl_engine:Nuclear",
                symbol="SPY",
                action="SELL",
                target_allocation=Decimal("0.3"),
                reasoning="Sell signal",
                lifecycle_state="GENERATED",
                signal_dto={"symbol": "SPY"},
                created_at=datetime.now(UTC),
            ),
        ]

        # Persist all signals
        for signal in signals:
            repository.put_signal(signal, "ledger-123")

        # Execute trades for sig-1 and sig-2 only (sig-3 is ignored)
        for idx, (signal_id, symbol) in enumerate([("sig-1", "TQQQ"), ("sig-2", "SOXL")], 1):
            mock_dynamodb_table.get_item.return_value = {
                "Item": {
                    "PK": f"SIGNAL#{signal_id}",
                    "SK": "METADATA",
                    "signal_id": signal_id,
                    "timestamp": datetime.now(UTC).isoformat(),
                    "lifecycle_state": "GENERATED",
                }
            }
            repository.update_signal_lifecycle(signal_id, "EXECUTED", [f"order-{idx}"])

        # Mark sig-3 as IGNORED
        mock_dynamodb_table.get_item.return_value = {
            "Item": {
                "PK": "SIGNAL#sig-3",
                "SK": "METADATA",
                "signal_id": "sig-3",
                "timestamp": datetime.now(UTC).isoformat(),
                "lifecycle_state": "GENERATED",
            }
        }
        repository.update_signal_lifecycle("sig-3", "IGNORED", None)

        # Verify all updates were made
        assert mock_dynamodb_table.update_item.call_count == 3

    def test_signal_execution_rate_calculation(self, repository, mock_dynamodb_table):
        """Test computation of signal execution rate for a strategy."""
        strategy_name = "Nuclear"

        # Mock query results: 3 EXECUTED, 2 IGNORED signals
        mock_dynamodb_table.query.return_value = {
            "Items": [
                {"signal_id": "sig-1", "lifecycle_state": "EXECUTED", "symbol": "TQQQ"},
                {"signal_id": "sig-2", "lifecycle_state": "EXECUTED", "symbol": "SOXL"},
                {"signal_id": "sig-3", "lifecycle_state": "EXECUTED", "symbol": "TECL"},
                {"signal_id": "sig-4", "lifecycle_state": "IGNORED", "symbol": "SPY"},
                {"signal_id": "sig-5", "lifecycle_state": "IGNORED", "symbol": "QQQ"},
            ]
        }

        metrics = repository.compute_signal_execution_rate(strategy_name)

        assert metrics["strategy_name"] == strategy_name
        assert metrics["total_signals"] == 5
        assert metrics["executed_signals"] == 3
        assert metrics["ignored_signals"] == 2
        assert metrics["execution_rate"] == Decimal("0.6")  # 3/5 = 0.6

    def test_signal_to_trade_attribution_query(self, repository, mock_dynamodb_table):
        """Test querying signals by correlation_id to find trade attribution."""
        correlation_id = "corr-attribution-test"

        # Mock query to return signals with different states
        mock_dynamodb_table.query.return_value = {
            "Items": [
                {
                    "signal_id": "sig-1",
                    "correlation_id": correlation_id,
                    "symbol": "TQQQ",
                    "action": "BUY",
                    "lifecycle_state": "EXECUTED",
                    "executed_trade_ids": ["order-1"],
                },
                {
                    "signal_id": "sig-2",
                    "correlation_id": correlation_id,
                    "symbol": "SPY",
                    "action": "SELL",
                    "lifecycle_state": "IGNORED",
                    "executed_trade_ids": [],
                },
            ]
        }

        signals = repository.query_signals_by_correlation(correlation_id)

        # Verify we can trace trade attribution
        assert len(signals) == 2
        executed_signal = next(s for s in signals if s["lifecycle_state"] == "EXECUTED")
        assert executed_signal["executed_trade_ids"] == ["order-1"]
        assert executed_signal["symbol"] == "TQQQ"

        ignored_signal = next(s for s in signals if s["lifecycle_state"] == "IGNORED")
        assert ignored_signal["executed_trade_ids"] == []
        assert ignored_signal["symbol"] == "SPY"

    def test_atomic_append_prevents_race_conditions(self, repository, mock_dynamodb_table):
        """Test that atomic append prevents race conditions in concurrent trade updates.

        This test verifies that the list_append operation is used, which ensures
        that multiple trades updating the same signal concurrently will not lose
        trade IDs due to read-modify-write races.
        """
        signal_id = "sig-concurrent-test"

        # Mock get_item to return a signal with existing trade
        mock_dynamodb_table.get_item.return_value = {
            "Item": {
                "PK": f"SIGNAL#{signal_id}",
                "SK": "METADATA",
                "signal_id": signal_id,
                "timestamp": "2025-01-15T14:00:00+00:00",
                "lifecycle_state": "GENERATED",
                "executed_trade_ids": ["order-existing"],
            }
        }

        # Simulate concurrent update - append new trade ID
        repository.update_signal_lifecycle(signal_id, "EXECUTED", ["order-new"])

        # Verify update_item was called with list_append
        update_call = mock_dynamodb_table.update_item.call_args
        assert update_call is not None

        # Verify the UpdateExpression uses list_append for atomic operation
        update_expr = update_call.kwargs["UpdateExpression"]
        assert "list_append" in update_expr
        assert "if_not_exists(executed_trade_ids" in update_expr

        # Verify the expression values include empty list for initialization
        expr_values = update_call.kwargs["ExpressionAttributeValues"]
        assert ":empty_list" in expr_values
        assert expr_values[":empty_list"] == []
        assert expr_values[":trade_ids"] == ["order-new"]
