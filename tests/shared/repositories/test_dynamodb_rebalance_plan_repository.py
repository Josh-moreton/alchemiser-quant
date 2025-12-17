"""Business Unit: shared | Status: current.

Tests for DynamoDB rebalance plan repository.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from the_alchemiser.shared.repositories.dynamodb_rebalance_plan_repository import (
    DynamoDBRebalancePlanRepository,
)
from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlan, RebalancePlanItem


class TestDynamoDBRebalancePlanRepository:
    """Test suite for DynamoDBRebalancePlanRepository."""

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
        repo = MagicMock(spec=DynamoDBRebalancePlanRepository)
        repo._table = mock_dynamodb_table
        repo._ttl_days = 90

        # Bind the actual methods to the mock
        repo.save_plan = DynamoDBRebalancePlanRepository.save_plan.__get__(repo)
        repo.get_plan_by_id = DynamoDBRebalancePlanRepository.get_plan_by_id.__get__(repo)
        repo.get_plans_by_correlation_id = (
            DynamoDBRebalancePlanRepository.get_plans_by_correlation_id.__get__(repo)
        )

        return repo

    @pytest.fixture
    def sample_plan(self):
        """Create a sample rebalance plan."""
        return RebalancePlan(
            plan_id="plan-123",
            correlation_id="corr-456",
            causation_id="cause-789",
            timestamp=datetime(2025, 1, 15, 14, 30, 0, tzinfo=UTC),
            items=[
                RebalancePlanItem(
                    symbol="AAPL",
                    current_weight=Decimal("0.3"),
                    target_weight=Decimal("0.4"),
                    weight_diff=Decimal("0.1"),
                    current_value=Decimal("3000"),
                    target_value=Decimal("4000"),
                    trade_amount=Decimal("1000"),
                    action="BUY",
                    priority=1,
                ),
                RebalancePlanItem(
                    symbol="TSLA",
                    current_weight=Decimal("0.2"),
                    target_weight=Decimal("0.1"),
                    weight_diff=Decimal("-0.1"),
                    current_value=Decimal("2000"),
                    target_value=Decimal("1000"),
                    trade_amount=Decimal("1000"),
                    action="SELL",
                    priority=2,
                ),
            ],
            total_portfolio_value=Decimal("10000"),
            total_trade_value=Decimal("2000"),
        )

    def test_save_plan_creates_dynamo_item(self, repository, mock_dynamodb_table, sample_plan):
        """Test that save_plan creates the correct DynamoDB item."""
        repository.save_plan(sample_plan)

        # Verify put_item was called
        assert mock_dynamodb_table.put_item.call_count == 1

        # Get the call
        call = mock_dynamodb_table.put_item.call_args
        item = call.kwargs["Item"]

        # Verify main item structure
        assert item["PK"] == "PLAN#plan-123"
        assert item["SK"] == "METADATA"
        assert item["EntityType"] == "REBALANCE_PLAN"
        assert item["plan_id"] == "plan-123"
        assert item["correlation_id"] == "corr-456"
        assert item["causation_id"] == "cause-789"

        # Verify summary fields
        assert item["item_count"] == 2
        assert item["total_trade_value"] == "2000"
        assert item["total_portfolio_value"] == "10000"
        assert item["buy_count"] == 1
        assert item["sell_count"] == 1
        assert item["hold_count"] == 0

        # Verify GSI keys
        assert item["GSI1PK"] == "CORR#corr-456"
        assert "GSI1SK" in item

        # Verify TTL is set
        assert "ttl" in item
        assert isinstance(item["ttl"], int)

        # Verify plan_data is serialized JSON
        assert "plan_data" in item
        plan_data = json.loads(item["plan_data"])
        assert plan_data["plan_id"] == "plan-123"

    def test_save_plan_with_all_buy_items(self, repository, mock_dynamodb_table):
        """Test save_plan with only BUY actions."""
        plan = RebalancePlan(
            plan_id="plan-buy-only",
            correlation_id="corr-1",
            causation_id="cause-1",
            timestamp=datetime.now(UTC),
            items=[
                RebalancePlanItem(
                    symbol="AAPL",
                    current_weight=Decimal("0"),
                    target_weight=Decimal("0.5"),
                    weight_diff=Decimal("0.5"),
                    current_value=Decimal("0"),
                    target_value=Decimal("5000"),
                    trade_amount=Decimal("5000"),
                    action="BUY",
                    priority=1,
                ),
            ],
            total_portfolio_value=Decimal("10000"),
            total_trade_value=Decimal("5000"),
        )

        repository.save_plan(plan)

        item = mock_dynamodb_table.put_item.call_args.kwargs["Item"]
        assert item["buy_count"] == 1
        assert item["sell_count"] == 0
        assert item["hold_count"] == 0

    def test_save_plan_with_hold_items(self, repository, mock_dynamodb_table):
        """Test save_plan with HOLD actions."""
        plan = RebalancePlan(
            plan_id="plan-with-hold",
            correlation_id="corr-2",
            causation_id="cause-2",
            timestamp=datetime.now(UTC),
            items=[
                RebalancePlanItem(
                    symbol="AAPL",
                    current_weight=Decimal("0.5"),
                    target_weight=Decimal("0.5"),
                    weight_diff=Decimal("0"),
                    current_value=Decimal("5000"),
                    target_value=Decimal("5000"),
                    trade_amount=Decimal("0"),
                    action="HOLD",
                    priority=1,
                ),
            ],
            total_portfolio_value=Decimal("10000"),
            total_trade_value=Decimal("0"),
        )

        repository.save_plan(plan)

        item = mock_dynamodb_table.put_item.call_args.kwargs["Item"]
        assert item["buy_count"] == 0
        assert item["sell_count"] == 0
        assert item["hold_count"] == 1

    def test_save_plan_dynamodb_error_raises_runtime_error(
        self, repository, mock_dynamodb_table, sample_plan
    ):
        """Test that DynamoDB errors are wrapped in RuntimeError."""
        from botocore.exceptions import ClientError

        mock_dynamodb_table.put_item.side_effect = ClientError(
            {"Error": {"Code": "InternalServerError", "Message": "DynamoDB error"}},
            "PutItem",
        )

        with pytest.raises(RuntimeError) as exc_info:
            repository.save_plan(sample_plan)

        assert "Failed to persist rebalance plan" in str(exc_info.value)

    def test_get_plan_by_id_success(self, repository, mock_dynamodb_table, sample_plan):
        """Test retrieving a plan by ID."""
        # Mock the response with serialized plan data
        mock_dynamodb_table.get_item.return_value = {
            "Item": {
                "PK": "PLAN#plan-123",
                "SK": "METADATA",
                "plan_id": "plan-123",
                "plan_data": json.dumps(sample_plan.to_dict()),
            }
        }

        result = repository.get_plan_by_id("plan-123")

        assert result is not None
        assert result.plan_id == "plan-123"
        assert result.correlation_id == "corr-456"
        assert len(result.items) == 2

        # Verify get_item was called with correct key
        mock_dynamodb_table.get_item.assert_called_once_with(
            Key={"PK": "PLAN#plan-123", "SK": "METADATA"}
        )

    def test_get_plan_by_id_not_found(self, repository, mock_dynamodb_table):
        """Test getting a plan that doesn't exist."""
        mock_dynamodb_table.get_item.return_value = {}

        result = repository.get_plan_by_id("nonexistent")

        assert result is None

    def test_get_plan_by_id_dynamodb_error_returns_none(self, repository, mock_dynamodb_table):
        """Test that DynamoDB errors are handled gracefully."""
        from botocore.exceptions import ClientError

        mock_dynamodb_table.get_item.side_effect = ClientError(
            {"Error": {"Code": "InternalServerError", "Message": "DynamoDB error"}},
            "GetItem",
        )

        result = repository.get_plan_by_id("plan-123")

        assert result is None

    def test_get_plans_by_correlation_id_success(
        self, repository, mock_dynamodb_table, sample_plan
    ):
        """Test querying plans by correlation_id."""
        mock_dynamodb_table.query.return_value = {
            "Items": [
                {"plan_data": json.dumps(sample_plan.to_dict())},
            ]
        }

        results = repository.get_plans_by_correlation_id("corr-456")

        assert len(results) == 1
        assert results[0].plan_id == "plan-123"

        # Verify query was called with correct parameters
        call_kwargs = mock_dynamodb_table.query.call_args.kwargs
        assert call_kwargs["IndexName"] == "GSI1-CorrelationIndex"
        assert call_kwargs["ExpressionAttributeValues"][":pk"] == "CORR#corr-456"
        assert call_kwargs["ScanIndexForward"] is False

    def test_get_plans_by_correlation_id_empty(self, repository, mock_dynamodb_table):
        """Test querying plans with no results."""
        mock_dynamodb_table.query.return_value = {"Items": []}

        results = repository.get_plans_by_correlation_id("nonexistent")

        assert results == []

    def test_get_plans_by_correlation_id_dynamodb_error_returns_empty(
        self, repository, mock_dynamodb_table
    ):
        """Test that DynamoDB errors are handled gracefully."""
        from botocore.exceptions import ClientError

        mock_dynamodb_table.query.side_effect = ClientError(
            {"Error": {"Code": "InternalServerError", "Message": "DynamoDB error"}},
            "Query",
        )

        results = repository.get_plans_by_correlation_id("corr-123")

        assert results == []

    def test_get_plans_by_correlation_id_multiple_results(
        self, repository, mock_dynamodb_table, sample_plan
    ):
        """Test querying correlation_id that has multiple plans."""
        plan2_dict = sample_plan.to_dict()
        plan2_dict["plan_id"] = "plan-456"

        mock_dynamodb_table.query.return_value = {
            "Items": [
                {"plan_data": json.dumps(sample_plan.to_dict())},
                {"plan_data": json.dumps(plan2_dict)},
            ]
        }

        results = repository.get_plans_by_correlation_id("corr-456")

        assert len(results) == 2
        plan_ids = {r.plan_id for r in results}
        assert plan_ids == {"plan-123", "plan-456"}

    def test_ttl_calculation(self, repository, mock_dynamodb_table, sample_plan):
        """Test that TTL is calculated correctly based on ttl_days."""
        from datetime import timedelta

        repository._ttl_days = 30  # Override default

        # Capture the current time before save
        before_save = datetime.now(UTC)

        repository.save_plan(sample_plan)

        item = mock_dynamodb_table.put_item.call_args.kwargs["Item"]
        ttl_timestamp = item["ttl"]

        # TTL should be approximately now + 30 days
        expected_ttl = (before_save + timedelta(days=30)).timestamp()
        assert abs(ttl_timestamp - expected_ttl) < 60  # Within 60 seconds


class TestRebalancePlanSerializationIntegration:
    """Test integration between RebalancePlan serialization and repository."""

    @pytest.fixture
    def sample_plan_with_metadata(self):
        """Create a plan with strategy attribution metadata."""
        return RebalancePlan(
            plan_id="plan-with-meta",
            correlation_id="corr-meta",
            causation_id="cause-meta",
            timestamp=datetime(2025, 1, 15, 14, 30, 0, tzinfo=UTC),
            items=[
                RebalancePlanItem(
                    symbol="NVDA",
                    current_weight=Decimal("0"),
                    target_weight=Decimal("0.3"),
                    weight_diff=Decimal("0.3"),
                    current_value=Decimal("0"),
                    target_value=Decimal("3000"),
                    trade_amount=Decimal("3000"),
                    action="BUY",
                    priority=1,
                ),
            ],
            total_portfolio_value=Decimal("10000"),
            total_trade_value=Decimal("3000"),
            metadata={
                "strategy_attribution": {
                    "NVDA": {
                        "momentum_strategy": 0.6,
                        "mean_reversion_strategy": 0.4,
                    }
                }
            },
        )

    def test_metadata_preserved_through_serialization(self, sample_plan_with_metadata):
        """Test that metadata survives serialization/deserialization."""
        # Serialize to dict (as done in repository)
        plan_dict = sample_plan_with_metadata.to_dict()
        json_str = json.dumps(plan_dict)

        # Deserialize (as done in repository)
        plan_data = json.loads(json_str)
        restored_plan = RebalancePlan.from_dict(plan_data)

        # Verify metadata is preserved
        assert restored_plan.metadata is not None
        assert "strategy_attribution" in restored_plan.metadata
        assert "NVDA" in restored_plan.metadata["strategy_attribution"]
        assert restored_plan.metadata["strategy_attribution"]["NVDA"]["momentum_strategy"] == 0.6

    def test_empty_metadata_handled(self):
        """Test that plans without metadata serialize correctly."""
        plan = RebalancePlan(
            plan_id="plan-no-meta",
            correlation_id="corr-1",
            causation_id="cause-1",
            timestamp=datetime.now(UTC),
            items=[
                RebalancePlanItem(
                    symbol="AAPL",
                    current_weight=Decimal("0.5"),
                    target_weight=Decimal("0.5"),
                    weight_diff=Decimal("0"),
                    current_value=Decimal("5000"),
                    target_value=Decimal("5000"),
                    trade_amount=Decimal("0"),
                    action="HOLD",
                    priority=1,
                ),
            ],
            total_portfolio_value=Decimal("10000"),
            total_trade_value=Decimal("0"),
            metadata=None,
        )

        plan_dict = plan.to_dict()
        json_str = json.dumps(plan_dict)
        plan_data = json.loads(json_str)
        restored_plan = RebalancePlan.from_dict(plan_data)

        # Metadata should be None or empty
        assert restored_plan.metadata is None or restored_plan.metadata == {}
