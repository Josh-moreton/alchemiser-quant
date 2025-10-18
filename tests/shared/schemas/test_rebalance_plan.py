"""Business Unit: shared | Status: current.

Tests for rebalance plan schemas (DTOs).

This test module validates RebalancePlanItem and RebalancePlan DTOs directly,
ensuring proper validation, immutability, numerical correctness, and serialization.
"""

# ruff: noqa: S101  # Allow asserts in tests
# ruff: noqa: DTZ001  # Allow naive datetime for testing timezone conversion

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlan, RebalancePlanItem


class TestRebalancePlanItem:
    """Test suite for RebalancePlanItem DTO."""

    @pytest.mark.unit
    def test_create_valid_item(self) -> None:
        """Test creating a valid rebalance plan item."""
        item = RebalancePlanItem(
            symbol="AAPL",
            current_weight=Decimal("0.3"),
            target_weight=Decimal("0.5"),
            weight_diff=Decimal("0.2"),
            target_value=Decimal("5000.00"),
            current_value=Decimal("3000.00"),
            trade_amount=Decimal("2000.00"),
            action="BUY",
            priority=1,
        )

        assert item.symbol == "AAPL"
        assert item.current_weight == Decimal("0.3")
        assert item.target_weight == Decimal("0.5")
        assert item.trade_amount == Decimal("2000.00")
        assert item.action == "BUY"
        assert item.priority == 1

    @pytest.mark.unit
    def test_item_is_frozen(self) -> None:
        """Test that RebalancePlanItem is immutable."""
        item = RebalancePlanItem(
            symbol="AAPL",
            current_weight=Decimal("0.3"),
            target_weight=Decimal("0.5"),
            weight_diff=Decimal("0.2"),
            target_value=Decimal("5000.00"),
            current_value=Decimal("3000.00"),
            trade_amount=Decimal("2000.00"),
            action="BUY",
            priority=1,
        )

        with pytest.raises(ValidationError):
            item.symbol = "TSLA"  # type: ignore

    @pytest.mark.unit
    def test_symbol_normalized_to_uppercase(self) -> None:
        """Test symbol is normalized to uppercase."""
        item = RebalancePlanItem(
            symbol="aapl",  # lowercase
            current_weight=Decimal("0.3"),
            target_weight=Decimal("0.5"),
            weight_diff=Decimal("0.2"),
            target_value=Decimal("5000.00"),
            current_value=Decimal("3000.00"),
            trade_amount=Decimal("2000.00"),
            action="BUY",
            priority=1,
        )

        assert item.symbol == "AAPL"

    @pytest.mark.unit
    def test_symbol_whitespace_stripped(self) -> None:
        """Test symbol whitespace is stripped during normalization."""
        item = RebalancePlanItem(
            symbol="  AAPL  ",  # with whitespace
            current_weight=Decimal("0.3"),
            target_weight=Decimal("0.5"),
            weight_diff=Decimal("0.2"),
            target_value=Decimal("5000.00"),
            current_value=Decimal("3000.00"),
            trade_amount=Decimal("2000.00"),
            action="SELL",
            priority=2,
        )

        assert item.symbol == "AAPL"

    @pytest.mark.unit
    def test_action_normalized_to_uppercase(self) -> None:
        """Test action is normalized to uppercase."""
        item = RebalancePlanItem(
            symbol="AAPL",
            current_weight=Decimal("0.3"),
            target_weight=Decimal("0.3"),
            weight_diff=Decimal("0.0"),
            target_value=Decimal("3000.00"),
            current_value=Decimal("3000.00"),
            trade_amount=Decimal("0.00"),
            action="hold",  # lowercase
            priority=3,
        )

        assert item.action == "HOLD"

    @pytest.mark.unit
    def test_invalid_action_rejected(self) -> None:
        """Test invalid action is rejected."""
        with pytest.raises(ValidationError, match="Action must be one of"):
            RebalancePlanItem(
                symbol="AAPL",
                current_weight=Decimal("0.3"),
                target_weight=Decimal("0.5"),
                weight_diff=Decimal("0.2"),
                target_value=Decimal("5000.00"),
                current_value=Decimal("3000.00"),
                trade_amount=Decimal("2000.00"),
                action="INVALID",
                priority=1,
            )

    @pytest.mark.unit
    def test_weight_constraints(self) -> None:
        """Test weight must be between 0 and 1."""
        # Valid boundary values
        item = RebalancePlanItem(
            symbol="AAPL",
            current_weight=Decimal("0.0"),  # Lower bound
            target_weight=Decimal("1.0"),  # Upper bound
            weight_diff=Decimal("1.0"),
            target_value=Decimal("10000.00"),
            current_value=Decimal("0.00"),
            trade_amount=Decimal("10000.00"),
            action="BUY",
            priority=1,
        )
        assert item.current_weight == Decimal("0.0")
        assert item.target_weight == Decimal("1.0")

        # Invalid: negative weight
        with pytest.raises(ValidationError):
            RebalancePlanItem(
                symbol="AAPL",
                current_weight=Decimal("-0.1"),
                target_weight=Decimal("0.5"),
                weight_diff=Decimal("0.6"),
                target_value=Decimal("5000.00"),
                current_value=Decimal("-1000.00"),
                trade_amount=Decimal("6000.00"),
                action="BUY",
                priority=1,
            )

        # Invalid: weight > 1.0
        with pytest.raises(ValidationError):
            RebalancePlanItem(
                symbol="AAPL",
                current_weight=Decimal("0.5"),
                target_weight=Decimal("1.5"),
                weight_diff=Decimal("1.0"),
                target_value=Decimal("15000.00"),
                current_value=Decimal("5000.00"),
                trade_amount=Decimal("10000.00"),
                action="BUY",
                priority=1,
            )

    @pytest.mark.unit
    def test_priority_constraints(self) -> None:
        """Test priority must be between 1 and 5."""
        # Valid boundary values
        item = RebalancePlanItem(
            symbol="AAPL",
            current_weight=Decimal("0.3"),
            target_weight=Decimal("0.5"),
            weight_diff=Decimal("0.2"),
            target_value=Decimal("5000.00"),
            current_value=Decimal("3000.00"),
            trade_amount=Decimal("2000.00"),
            action="BUY",
            priority=1,  # Min priority
        )
        assert item.priority == 1

        item = RebalancePlanItem(
            symbol="AAPL",
            current_weight=Decimal("0.3"),
            target_weight=Decimal("0.5"),
            weight_diff=Decimal("0.2"),
            target_value=Decimal("5000.00"),
            current_value=Decimal("3000.00"),
            trade_amount=Decimal("2000.00"),
            action="BUY",
            priority=5,  # Max priority
        )
        assert item.priority == 5

        # Invalid: priority = 0
        with pytest.raises(ValidationError):
            RebalancePlanItem(
                symbol="AAPL",
                current_weight=Decimal("0.3"),
                target_weight=Decimal("0.5"),
                weight_diff=Decimal("0.2"),
                target_value=Decimal("5000.00"),
                current_value=Decimal("3000.00"),
                trade_amount=Decimal("2000.00"),
                action="BUY",
                priority=0,
            )

        # Invalid: priority = 6
        with pytest.raises(ValidationError):
            RebalancePlanItem(
                symbol="AAPL",
                current_weight=Decimal("0.3"),
                target_weight=Decimal("0.5"),
                weight_diff=Decimal("0.2"),
                target_value=Decimal("5000.00"),
                current_value=Decimal("3000.00"),
                trade_amount=Decimal("2000.00"),
                action="BUY",
                priority=6,
            )

    @pytest.mark.unit
    def test_trade_amount_can_be_negative(self) -> None:
        """Test trade amount can be negative for sells."""
        item = RebalancePlanItem(
            symbol="AAPL",
            current_weight=Decimal("0.5"),
            target_weight=Decimal("0.3"),
            weight_diff=Decimal("-0.2"),
            target_value=Decimal("3000.00"),
            current_value=Decimal("5000.00"),
            trade_amount=Decimal("-2000.00"),  # Negative for sell
            action="SELL",
            priority=1,
        )

        assert item.trade_amount == Decimal("-2000.00")
        assert item.action == "SELL"

    @pytest.mark.unit
    def test_empty_symbol_rejected(self) -> None:
        """Test empty symbol is rejected."""
        with pytest.raises(ValidationError):
            RebalancePlanItem(
                symbol="",  # Empty
                current_weight=Decimal("0.3"),
                target_weight=Decimal("0.5"),
                weight_diff=Decimal("0.2"),
                target_value=Decimal("5000.00"),
                current_value=Decimal("3000.00"),
                trade_amount=Decimal("2000.00"),
                action="BUY",
                priority=1,
            )

    @pytest.mark.unit
    def test_symbol_too_long_rejected(self) -> None:
        """Test symbol exceeding max length is rejected."""
        with pytest.raises(ValidationError):
            RebalancePlanItem(
                symbol="VERYLONGSYMBOL",  # > 10 chars
                current_weight=Decimal("0.3"),
                target_weight=Decimal("0.5"),
                weight_diff=Decimal("0.2"),
                target_value=Decimal("5000.00"),
                current_value=Decimal("3000.00"),
                trade_amount=Decimal("2000.00"),
                action="BUY",
                priority=1,
            )


class TestRebalancePlan:
    """Test suite for RebalancePlan DTO."""

    def _make_valid_item(self, symbol: str = "AAPL") -> RebalancePlanItem:
        """Helper to create a valid item."""
        return RebalancePlanItem(
            symbol=symbol,
            current_weight=Decimal("0.3"),
            target_weight=Decimal("0.5"),
            weight_diff=Decimal("0.2"),
            target_value=Decimal("5000.00"),
            current_value=Decimal("3000.00"),
            trade_amount=Decimal("2000.00"),
            action="BUY",
            priority=1,
        )

    @pytest.mark.unit
    def test_create_valid_plan(self) -> None:
        """Test creating a valid rebalance plan."""
        items = [self._make_valid_item()]

        plan = RebalancePlan(
            correlation_id="corr-123",
            causation_id="cause-123",
            timestamp=datetime.now(UTC),
            plan_id="plan-123",
            items=items,
            total_portfolio_value=Decimal("10000.00"),
            total_trade_value=Decimal("2000.00"),
        )

        assert plan.plan_id == "plan-123"
        assert plan.correlation_id == "corr-123"
        assert plan.causation_id == "cause-123"
        assert len(plan.items) == 1
        assert plan.total_portfolio_value == Decimal("10000.00")
        assert plan.total_trade_value == Decimal("2000.00")

    @pytest.mark.unit
    def test_plan_is_frozen(self) -> None:
        """Test that RebalancePlan is immutable."""
        items = [self._make_valid_item()]
        plan = RebalancePlan(
            correlation_id="corr-123",
            causation_id="cause-123",
            timestamp=datetime.now(UTC),
            plan_id="plan-123",
            items=items,
            total_portfolio_value=Decimal("10000.00"),
            total_trade_value=Decimal("2000.00"),
        )

        with pytest.raises(ValidationError):
            plan.plan_id = "new-plan"  # type: ignore

    @pytest.mark.unit
    def test_empty_items_list_rejected(self) -> None:
        """Test plan with empty items list is rejected."""
        with pytest.raises(ValidationError):
            RebalancePlan(
                correlation_id="corr-123",
                causation_id="cause-123",
                timestamp=datetime.now(UTC),
                plan_id="plan-123",
                items=[],  # Empty list
                total_portfolio_value=Decimal("10000.00"),
                total_trade_value=Decimal("0.00"),
            )

    @pytest.mark.unit
    def test_urgency_normalized_to_uppercase(self) -> None:
        """Test execution urgency is normalized to uppercase."""
        items = [self._make_valid_item()]
        plan = RebalancePlan(
            correlation_id="corr-123",
            causation_id="cause-123",
            timestamp=datetime.now(UTC),
            plan_id="plan-123",
            items=items,
            total_portfolio_value=Decimal("10000.00"),
            total_trade_value=Decimal("2000.00"),
            execution_urgency="high",  # lowercase
        )

        assert plan.execution_urgency == "HIGH"

    @pytest.mark.unit
    def test_invalid_urgency_rejected(self) -> None:
        """Test invalid urgency level is rejected."""
        items = [self._make_valid_item()]
        with pytest.raises(ValidationError, match="Urgency must be one of"):
            RebalancePlan(
                correlation_id="corr-123",
                causation_id="cause-123",
                timestamp=datetime.now(UTC),
                plan_id="plan-123",
                items=items,
                total_portfolio_value=Decimal("10000.00"),
                total_trade_value=Decimal("2000.00"),
                execution_urgency="CRITICAL",  # Invalid
            )

    @pytest.mark.unit
    def test_valid_urgency_levels(self) -> None:
        """Test all valid urgency levels are accepted."""
        items = [self._make_valid_item()]
        for urgency in ["LOW", "NORMAL", "HIGH", "URGENT"]:
            plan = RebalancePlan(
                correlation_id="corr-123",
                causation_id="cause-123",
                timestamp=datetime.now(UTC),
                plan_id=f"plan-{urgency}",
                items=items,
                total_portfolio_value=Decimal("10000.00"),
                total_trade_value=Decimal("2000.00"),
                execution_urgency=urgency,
            )
            assert plan.execution_urgency == urgency

    @pytest.mark.unit
    def test_naive_timestamp_converted_to_utc(self) -> None:
        """Test naive datetime is converted to UTC."""
        items = [self._make_valid_item()]
        naive_dt = datetime(2025, 1, 6, 12, 0, 0)  # No timezone

        plan = RebalancePlan(
            correlation_id="corr-123",
            causation_id="cause-123",
            timestamp=naive_dt,
            plan_id="plan-123",
            items=items,
            total_portfolio_value=Decimal("10000.00"),
            total_trade_value=Decimal("2000.00"),
        )

        assert plan.timestamp.tzinfo is not None
        assert plan.timestamp.tzinfo == UTC

    @pytest.mark.unit
    def test_timezone_aware_timestamp_preserved(self) -> None:
        """Test timezone-aware datetime is preserved."""
        items = [self._make_valid_item()]
        aware_dt = datetime(2025, 1, 6, 12, 0, 0, tzinfo=UTC)

        plan = RebalancePlan(
            correlation_id="corr-123",
            causation_id="cause-123",
            timestamp=aware_dt,
            plan_id="plan-123",
            items=items,
            total_portfolio_value=Decimal("10000.00"),
            total_trade_value=Decimal("2000.00"),
        )

        assert plan.timestamp.tzinfo == UTC
        assert plan.timestamp == aware_dt

    @pytest.mark.unit
    def test_optional_fields_default_values(self) -> None:
        """Test optional fields have correct defaults."""
        items = [self._make_valid_item()]
        plan = RebalancePlan(
            correlation_id="corr-123",
            causation_id="cause-123",
            timestamp=datetime.now(UTC),
            plan_id="plan-123",
            items=items,
            total_portfolio_value=Decimal("10000.00"),
            total_trade_value=Decimal("2000.00"),
            # Not specifying optional fields
        )

        assert plan.max_drift_tolerance == Decimal("0.05")
        assert plan.execution_urgency == "NORMAL"
        assert plan.estimated_duration_minutes is None
        assert plan.metadata is None

    @pytest.mark.unit
    def test_metadata_can_be_set(self) -> None:
        """Test metadata field accepts arbitrary dict."""
        items = [self._make_valid_item()]
        metadata = {
            "strategy": "momentum",
            "rebalance_reason": "drift_exceeded",
            "risk_score": 0.75,
        }

        plan = RebalancePlan(
            correlation_id="corr-123",
            causation_id="cause-123",
            timestamp=datetime.now(UTC),
            plan_id="plan-123",
            items=items,
            total_portfolio_value=Decimal("10000.00"),
            total_trade_value=Decimal("2000.00"),
            metadata=metadata,
        )

        assert plan.metadata == metadata


class TestRebalancePlanSerialization:
    """Test suite for RebalancePlan serialization."""

    def _make_valid_item(self, symbol: str = "AAPL") -> RebalancePlanItem:
        """Helper to create a valid item."""
        return RebalancePlanItem(
            symbol=symbol,
            current_weight=Decimal("0.3"),
            target_weight=Decimal("0.5"),
            weight_diff=Decimal("0.2"),
            target_value=Decimal("5000.00"),
            current_value=Decimal("3000.00"),
            trade_amount=Decimal("2000.00"),
            action="BUY",
            priority=1,
        )

    def _make_valid_plan(self, num_items: int = 1) -> RebalancePlan:
        """Helper to create a valid plan."""
        symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
        items = [self._make_valid_item(symbols[i % len(symbols)]) for i in range(num_items)]

        return RebalancePlan(
            correlation_id="corr-123",
            causation_id="cause-123",
            timestamp=datetime(2025, 1, 6, 12, 30, 45, tzinfo=UTC),
            plan_id="plan-123",
            items=items,
            total_portfolio_value=Decimal("10000.00"),
            total_trade_value=Decimal("2000.00"),
            max_drift_tolerance=Decimal("0.05"),
            execution_urgency="NORMAL",
        )

    @pytest.mark.unit
    def test_to_dict_serialization(self) -> None:
        """Test to_dict serializes properly."""
        plan = self._make_valid_plan()
        data = plan.to_dict()

        # Check required fields
        assert data["plan_id"] == "plan-123"
        assert data["correlation_id"] == "corr-123"
        assert data["causation_id"] == "cause-123"

        # Check datetime serialization
        assert isinstance(data["timestamp"], str)
        assert "2025-01-06" in data["timestamp"]

        # Check Decimal serialization
        assert isinstance(data["total_portfolio_value"], str)
        assert data["total_portfolio_value"] == "10000.00"
        assert isinstance(data["total_trade_value"], str)
        assert data["total_trade_value"] == "2000.00"

        # Check items serialization
        assert isinstance(data["items"], list)
        assert len(data["items"]) == 1
        assert isinstance(data["items"][0]["trade_amount"], str)

    @pytest.mark.unit
    def test_from_dict_deserialization(self) -> None:
        """Test from_dict deserializes properly."""
        data = {
            "correlation_id": "corr-123",
            "causation_id": "cause-123",
            "timestamp": "2025-01-06T12:30:45+00:00",
            "plan_id": "plan-123",
            "items": [
                {
                    "symbol": "AAPL",
                    "current_weight": "0.3",
                    "target_weight": "0.5",
                    "weight_diff": "0.2",
                    "target_value": "5000.00",
                    "current_value": "3000.00",
                    "trade_amount": "2000.00",
                    "action": "BUY",
                    "priority": 1,
                }
            ],
            "total_portfolio_value": "10000.00",
            "total_trade_value": "2000.00",
        }

        plan = RebalancePlan.from_dict(data)

        assert plan.plan_id == "plan-123"
        assert plan.correlation_id == "corr-123"
        assert isinstance(plan.timestamp, datetime)
        assert isinstance(plan.total_portfolio_value, Decimal)
        assert plan.total_portfolio_value == Decimal("10000.00")
        assert len(plan.items) == 1
        assert isinstance(plan.items[0].trade_amount, Decimal)

    @pytest.mark.unit
    def test_round_trip_serialization(self) -> None:
        """Test round-trip: plan -> to_dict -> from_dict -> to_dict."""
        plan1 = self._make_valid_plan()

        # First serialization
        data1 = plan1.to_dict()

        # Deserialize
        plan2 = RebalancePlan.from_dict(data1)

        # Second serialization
        data2 = plan2.to_dict()

        # Compare
        assert data1 == data2
        assert plan1.plan_id == plan2.plan_id
        assert plan1.correlation_id == plan2.correlation_id
        assert plan1.total_portfolio_value == plan2.total_portfolio_value
        assert len(plan1.items) == len(plan2.items)

    @pytest.mark.unit
    def test_decimal_precision_preserved(self) -> None:
        """Test Decimal precision is preserved through serialization."""
        items = [
            RebalancePlanItem(
                symbol="AAPL",
                current_weight=Decimal("0.333333333"),  # High precision
                target_weight=Decimal("0.500000000"),
                weight_diff=Decimal("0.166666667"),
                target_value=Decimal("5000.123456"),
                current_value=Decimal("3000.987654"),
                trade_amount=Decimal("2000.135802"),
                action="BUY",
                priority=1,
            )
        ]

        plan = RebalancePlan(
            correlation_id="corr-123",
            causation_id="cause-123",
            timestamp=datetime.now(UTC),
            plan_id="plan-123",
            items=items,
            total_portfolio_value=Decimal("10000.123456789"),
            total_trade_value=Decimal("2000.135802"),
        )

        # Serialize and deserialize
        data = plan.to_dict()
        restored = RebalancePlan.from_dict(data)

        # Check precision preserved
        assert restored.total_portfolio_value == Decimal("10000.123456789")
        assert restored.items[0].current_weight == Decimal("0.333333333")
        assert restored.items[0].target_value == Decimal("5000.123456")

    @pytest.mark.unit
    def test_multiple_items_serialization(self) -> None:
        """Test serialization with multiple items."""
        plan = self._make_valid_plan(num_items=5)

        data = plan.to_dict()
        restored = RebalancePlan.from_dict(data)

        assert len(restored.items) == 5
        for orig_item, restored_item in zip(plan.items, restored.items, strict=False):
            assert orig_item.symbol == restored_item.symbol
            assert orig_item.trade_amount == restored_item.trade_amount

    @pytest.mark.unit
    def test_metadata_serialization(self) -> None:
        """Test metadata is preserved through serialization."""
        metadata = {
            "strategy": "momentum",
            "rebalance_reason": "drift_exceeded",
            "risk_score": 0.75,
            "nested": {"key": "value"},
        }

        items = [self._make_valid_item()]
        plan = RebalancePlan(
            correlation_id="corr-123",
            causation_id="cause-123",
            timestamp=datetime.now(UTC),
            plan_id="plan-123",
            items=items,
            total_portfolio_value=Decimal("10000.00"),
            total_trade_value=Decimal("2000.00"),
            metadata=metadata,
        )

        data = plan.to_dict()
        restored = RebalancePlan.from_dict(data)

        assert restored.metadata == metadata
