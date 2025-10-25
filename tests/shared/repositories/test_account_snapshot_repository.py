"""Business Unit: shared | Status: current.

Tests for AccountSnapshotRepository.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from the_alchemiser.shared.repositories.account_snapshot_repository import (
    AccountSnapshotRepository,
)
from the_alchemiser.shared.schemas.account_snapshot import (
    AccountSnapshot,
    AlpacaAccountData,
)


class TestAccountSnapshotRepository:
    """Test suite for AccountSnapshotRepository."""

    @pytest.fixture
    def mock_dynamodb_table(self):
        """Create a mock DynamoDB table."""
        mock_table = MagicMock()
        mock_table.put_item = MagicMock()
        mock_table.get_item = MagicMock()
        mock_table.query = MagicMock()
        return mock_table

    @pytest.fixture
    def repository(self, mock_dynamodb_table):
        """Create repository instance with mocked DynamoDB."""
        # Create a mock that avoids actual boto3 import
        repo = MagicMock(spec=AccountSnapshotRepository)
        repo._table = mock_dynamodb_table

        # Bind the actual methods to the mock
        repo.put_snapshot = AccountSnapshotRepository.put_snapshot.__get__(repo)
        repo.get_snapshot = AccountSnapshotRepository.get_snapshot.__get__(repo)
        repo.get_latest_snapshot = AccountSnapshotRepository.get_latest_snapshot.__get__(repo)
        repo.query_snapshots_by_date_range = (
            AccountSnapshotRepository.query_snapshots_by_date_range.__get__(repo)
        )
        repo.query_snapshots_by_correlation = (
            AccountSnapshotRepository.query_snapshots_by_correlation.__get__(repo)
        )
        repo._serialize_nested_data = AccountSnapshotRepository._serialize_nested_data.__get__(repo)
        repo._convert_decimals_to_strings = (
            AccountSnapshotRepository._convert_decimals_to_strings.__get__(repo)
        )
        repo._deserialize_snapshot = AccountSnapshotRepository._deserialize_snapshot.__get__(repo)
        repo._convert_strings_to_decimals = (
            AccountSnapshotRepository._convert_strings_to_decimals.__get__(repo)
        )

        return repo

    @pytest.fixture
    def sample_snapshot(self):
        """Create a sample account snapshot."""
        account_data = AlpacaAccountData(
            account_id="test-account-123",
            status="ACTIVE",
            buying_power=Decimal("10000.00"),
            cash=Decimal("5000.00"),
            equity=Decimal("15000.00"),
            portfolio_value=Decimal("15000.00"),
        )

        ledger_summary = InternalLedgerSummary(
            ledger_id="ledger-123",
            total_trades=5,
            total_buy_value=Decimal("3000.00"),
            total_sell_value=Decimal("3100.00"),
            strategies_active=["nuclear"],
            strategy_performance={},
        )

        created_at = datetime(2025, 1, 15, 14, 30, 0, tzinfo=UTC)
        period_start = datetime(2025, 1, 15, 0, 0, 0, tzinfo=UTC)
        period_end = datetime(2025, 1, 15, 23, 59, 59, tzinfo=UTC)

        snapshot_data = {
            "snapshot_id": "snap-123",
            "snapshot_version": "1.0",
            "account_id": "test-account-123",
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "correlation_id": "corr-456",
            "created_at": created_at.isoformat(),
            "alpaca_account": account_data.model_dump(),
            "alpaca_positions": [],
            "alpaca_orders": [],
            "internal_ledger": ledger_summary.model_dump(),
        }

        checksum = AccountSnapshot.calculate_checksum(snapshot_data)

        return AccountSnapshot(
            snapshot_id="snap-123",
            snapshot_version="1.0",
            account_id="test-account-123",
            period_start=period_start,
            period_end=period_end,
            correlation_id="corr-456",
            created_at=created_at,
            alpaca_account=account_data,
            alpaca_positions=[],
            alpaca_orders=[],
            internal_ledger=ledger_summary,
            checksum=checksum,
        )

    def test_put_snapshot_creates_item(self, repository, mock_dynamodb_table, sample_snapshot):
        """Test that put_snapshot creates a DynamoDB item."""
        repository.put_snapshot(sample_snapshot)

        # Verify put_item was called
        assert mock_dynamodb_table.put_item.called

        # Get the call args
        call_args = mock_dynamodb_table.put_item.call_args
        item = call_args.kwargs["Item"]

        # Verify item structure
        assert item["PK"] == "SNAPSHOT#test-account-123"
        assert item["SK"].startswith("SNAP#")
        assert item["EntityType"] == "SNAPSHOT"
        assert item["snapshot_id"] == "snap-123"
        assert item["account_id"] == "test-account-123"
        assert item["correlation_id"] == "corr-456"
        assert "ttl" in item
        assert "checksum" in item

    def test_put_snapshot_includes_gsi_keys(self, repository, mock_dynamodb_table, sample_snapshot):
        """Test that put_snapshot includes GSI keys for querying."""
        repository.put_snapshot(sample_snapshot)

        call_args = mock_dynamodb_table.put_item.call_args
        item = call_args.kwargs["Item"]

        # Verify GSI4 keys for correlation_id queries
        assert item["GSI4PK"] == "CORR#corr-456"
        assert item["GSI4SK"].startswith("SNAP#")

    def test_get_snapshot_retrieves_item(self, repository, mock_dynamodb_table):
        """Test that get_snapshot retrieves a specific snapshot."""
        # Mock the response
        mock_dynamodb_table.get_item.return_value = {
            "Item": {
                "PK": "SNAPSHOT#test-account-123",
                "SK": "SNAP#2025-01-15T23:59:59+00:00",
                "EntityType": "SNAPSHOT",
                "snapshot_id": "snap-123",
                "snapshot_version": "1.0",
                "account_id": "test-account-123",
                "period_start": "2025-01-15T00:00:00+00:00",
                "period_end": "2025-01-15T23:59:59+00:00",
                "correlation_id": "corr-456",
                "created_at": "2025-01-15T14:30:00+00:00",
                "alpaca_account": {
                    "account_id": "test-account-123",
                    "status": "ACTIVE",
                    "buying_power": "10000.00",
                    "cash": "5000.00",
                    "equity": "15000.00",
                    "portfolio_value": "15000.00",
                    "currency": "USD",
                },
                "alpaca_positions": [],
                "alpaca_orders": [],
                "internal_ledger": {
                    "ledger_id": "ledger-123",
                    "total_trades": 5,
                    "total_buy_value": "3000.00",
                    "total_sell_value": "3100.00",
                    "strategies_active": ["nuclear"],
                    "strategy_performance": {},
                },
                "checksum": "abc123",
                "ttl": 1234567890,
            }
        }

        result = repository.get_snapshot(
            "test-account-123", datetime(2025, 1, 15, 23, 59, 59, tzinfo=UTC)
        )

        assert result is not None
        assert result.snapshot_id == "snap-123"
        assert result.account_id == "test-account-123"

    def test_get_snapshot_returns_none_when_not_found(self, repository, mock_dynamodb_table):
        """Test that get_snapshot returns None when snapshot not found."""
        mock_dynamodb_table.get_item.return_value = {}

        result = repository.get_snapshot(
            "test-account-123", datetime(2025, 1, 15, 23, 59, 59, tzinfo=UTC)
        )

        assert result is None

    def test_get_latest_snapshot_queries_correctly(self, repository, mock_dynamodb_table):
        """Test that get_latest_snapshot queries with correct parameters."""
        mock_dynamodb_table.query.return_value = {"Items": []}

        repository.get_latest_snapshot("test-account-123")

        # Verify query was called
        assert mock_dynamodb_table.query.called

        call_args = mock_dynamodb_table.query.call_args
        assert "KeyConditionExpression" in call_args.kwargs
        assert call_args.kwargs["ScanIndexForward"] is False  # Most recent first
        assert call_args.kwargs["Limit"] == 1

    def test_query_snapshots_by_date_range(self, repository, mock_dynamodb_table):
        """Test querying snapshots by date range."""
        mock_dynamodb_table.query.return_value = {"Items": []}

        start_date = datetime(2025, 1, 1, 0, 0, 0, tzinfo=UTC)
        end_date = datetime(2025, 1, 31, 23, 59, 59, tzinfo=UTC)

        repository.query_snapshots_by_date_range("test-account-123", start_date, end_date)

        # Verify query was called with correct parameters
        assert mock_dynamodb_table.query.called

        call_args = mock_dynamodb_table.query.call_args
        assert "KeyConditionExpression" in call_args.kwargs
        assert call_args.kwargs["ScanIndexForward"] is False  # Most recent first

        # Verify ExpressionAttributeValues
        values = call_args.kwargs["ExpressionAttributeValues"]
        assert values[":pk"] == "SNAPSHOT#test-account-123"
        assert "SNAP#2025-01-01" in values[":start"]
        assert "SNAP#2025-01-31" in values[":end"]

    def test_query_snapshots_by_correlation(self, repository, mock_dynamodb_table):
        """Test querying snapshots by correlation_id using GSI4."""
        mock_dynamodb_table.query.return_value = {"Items": []}

        repository.query_snapshots_by_correlation("corr-456")

        # Verify query was called
        assert mock_dynamodb_table.query.called

        call_args = mock_dynamodb_table.query.call_args
        assert call_args.kwargs["IndexName"] == "GSI4-CorrelationSnapshotIndex"

        # Verify ExpressionAttributeValues
        values = call_args.kwargs["ExpressionAttributeValues"]
        assert values[":pk"] == "CORR#corr-456"

    def test_convert_decimals_to_strings(self, repository):
        """Test that Decimals are converted to strings for DynamoDB."""
        data = {
            "buying_power": Decimal("10000.00"),
            "cash": Decimal("5000.00"),
            "nested": {"qty": Decimal("100")},
            "list_field": [{"price": Decimal("150.25")}],
        }

        result = repository._convert_decimals_to_strings(data)

        assert isinstance(result["buying_power"], str)
        assert result["buying_power"] == "10000.00"
        assert isinstance(result["nested"]["qty"], str)
        assert result["list_field"][0]["price"] == "150.25"

    def test_convert_strings_to_decimals(self, repository):
        """Test that string representations are converted back to Decimals."""
        data = {
            "buying_power": "10000.00",
            "cash": "5000.00",
            "nested": {"qty": "100"},
            "non_decimal_field": "some_string",
        }

        result = repository._convert_strings_to_decimals(data)

        assert isinstance(result["buying_power"], Decimal)
        assert result["buying_power"] == Decimal("10000.00")
        assert isinstance(result["nested"]["qty"], Decimal)
        # Non-decimal fields should remain as strings
        assert result["non_decimal_field"] == "some_string"
