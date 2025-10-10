#!/usr/bin/env python3
"""Tests for DSL event schemas.

Validates that DSL event schemas correctly enforce constraints and
handle edge cases according to institution-grade standards.
"""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from the_alchemiser.shared.events.dsl_events import (
    DecisionEvaluated,
    FilterEvaluated,
    IndicatorComputed,
    PortfolioAllocationProduced,
    StrategyEvaluated,
    StrategyEvaluationRequested,
    TopNSelected,
)
from the_alchemiser.shared.schemas.ast_node import ASTNode
from the_alchemiser.shared.schemas.indicator_request import PortfolioFragment
from the_alchemiser.shared.schemas.strategy_allocation import StrategyAllocation
from the_alchemiser.shared.schemas.technical_indicator import TechnicalIndicator
from the_alchemiser.shared.schemas.trace import Trace


@pytest.mark.unit
class TestStrategyEvaluationRequested:
    """Test StrategyEvaluationRequested event schema."""

    def test_valid_event_creation(self) -> None:
        """Test creating valid StrategyEvaluationRequested event."""
        event = StrategyEvaluationRequested(
            correlation_id="corr-123",
            causation_id="cause-123",
            event_id="event-123",
            timestamp=datetime.now(UTC),
            source_module="test",
            strategy_id="strategy-1",
            strategy_config_path="/path/to/strategy.clj",
        )
        assert event.strategy_id == "strategy-1"
        assert event.event_type == "StrategyEvaluationRequested"
        assert event.schema_version == 1
        assert event.universe == []
        assert event.parameters == {}

    def test_with_optional_fields(self) -> None:
        """Test event with optional fields populated."""
        event = StrategyEvaluationRequested(
            correlation_id="corr-123",
            causation_id="cause-123",
            event_id="event-123",
            timestamp=datetime.now(UTC),
            source_module="test",
            strategy_id="strategy-1",
            strategy_config_path="/path/to/strategy.clj",
            universe=["AAPL", "GOOGL"],
            as_of_date="2025-01-01",
            parameters={"param1": "value1"},
        )
        assert event.universe == ["AAPL", "GOOGL"]
        assert event.as_of_date == "2025-01-01"
        assert event.parameters == {"param1": "value1"}

    def test_empty_strategy_id_fails(self) -> None:
        """Test that empty strategy_id is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            StrategyEvaluationRequested(
                correlation_id="corr-123",
                causation_id="cause-123",
                event_id="event-123",
                timestamp=datetime.now(UTC),
                source_module="test",
                strategy_id="",  # Empty string should fail
                strategy_config_path="/path/to/strategy.clj",
            )
        assert "strategy_id" in str(exc_info.value)

    def test_empty_config_path_fails(self) -> None:
        """Test that empty strategy_config_path is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            StrategyEvaluationRequested(
                correlation_id="corr-123",
                causation_id="cause-123",
                event_id="event-123",
                timestamp=datetime.now(UTC),
                source_module="test",
                strategy_id="strategy-1",
                strategy_config_path="",  # Empty string should fail
            )
        assert "strategy_config_path" in str(exc_info.value)


@pytest.mark.unit
class TestStrategyEvaluated:
    """Test StrategyEvaluated event schema."""

    def test_valid_success_event(self) -> None:
        """Test creating valid success event."""
        allocation = StrategyAllocation(
            target_weights={"AAPL": Decimal("0.5"), "GOOGL": Decimal("0.5")},
            correlation_id="corr-123",
        )
        trace = Trace(
            trace_id="trace-123",
            correlation_id="corr-123",
            strategy_id="strategy-1",
            started_at=datetime.now(UTC),
        )
        event = StrategyEvaluated(
            correlation_id="corr-123",
            causation_id="cause-123",
            event_id="event-123",
            timestamp=datetime.now(UTC),
            source_module="test",
            strategy_id="strategy-1",
            allocation=allocation,
            trace=trace,
            success=True,
        )
        assert event.success is True
        assert event.error_message is None
        assert event.error_code is None

    def test_valid_failure_event(self) -> None:
        """Test creating valid failure event."""
        allocation = StrategyAllocation(
            target_weights={"AAPL": Decimal("1.0")},  # Non-empty for valid allocation
            correlation_id="corr-123",
        )
        trace = Trace(
            trace_id="trace-123",
            correlation_id="corr-123",
            strategy_id="strategy-1",
            started_at=datetime.now(UTC),
        )
        event = StrategyEvaluated(
            correlation_id="corr-123",
            causation_id="cause-123",
            event_id="event-123",
            timestamp=datetime.now(UTC),
            source_module="test",
            strategy_id="strategy-1",
            allocation=allocation,
            trace=trace,
            success=False,
            error_message="Evaluation failed",
            error_code="EVAL_ERROR",
        )
        assert event.success is False
        assert event.error_message == "Evaluation failed"
        assert event.error_code == "EVAL_ERROR"


@pytest.mark.unit
class TestIndicatorComputed:
    """Test IndicatorComputed event schema."""

    def test_valid_event_creation(self) -> None:
        """Test creating valid IndicatorComputed event."""
        indicator = TechnicalIndicator(
            symbol="AAPL",
            timestamp=datetime.now(UTC),
            current_price=Decimal("150.0"),
        )
        event = IndicatorComputed(
            correlation_id="corr-123",
            causation_id="cause-123",
            event_id="event-123",
            timestamp=datetime.now(UTC),
            source_module="test",
            request_id="req-123",
            indicator=indicator,
            computation_time_ms=5.0,
        )
        assert event.request_id == "req-123"
        assert event.computation_time_ms == 5.0
        assert event.computation_metadata == {}

    def test_negative_computation_time_fails(self) -> None:
        """Test that negative computation time is rejected."""
        indicator = TechnicalIndicator(
            symbol="AAPL",
            timestamp=datetime.now(UTC),
            current_price=Decimal("150.0"),
        )
        with pytest.raises(ValidationError) as exc_info:
            IndicatorComputed(
                correlation_id="corr-123",
                causation_id="cause-123",
                event_id="event-123",
                timestamp=datetime.now(UTC),
                source_module="test",
                request_id="req-123",
                indicator=indicator,
                computation_time_ms=-1.0,  # Negative should fail
            )
        assert "computation_time_ms" in str(exc_info.value)

    def test_zero_computation_time_accepted(self) -> None:
        """Test that zero computation time is accepted."""
        indicator = TechnicalIndicator(
            symbol="AAPL",
            timestamp=datetime.now(UTC),
            current_price=Decimal("150.0"),
        )
        event = IndicatorComputed(
            correlation_id="corr-123",
            causation_id="cause-123",
            event_id="event-123",
            timestamp=datetime.now(UTC),
            source_module="test",
            request_id="req-123",
            indicator=indicator,
            computation_time_ms=0.0,  # Zero should be accepted
        )
        assert event.computation_time_ms == 0.0

    def test_excessive_computation_time_fails(self) -> None:
        """Test that computation time exceeding max limit is rejected."""
        indicator = TechnicalIndicator(
            symbol="AAPL",
            timestamp=datetime.now(UTC),
            current_price=Decimal("150.0"),
        )
        with pytest.raises(ValidationError) as exc_info:
            IndicatorComputed(
                correlation_id="corr-123",
                causation_id="cause-123",
                event_id="event-123",
                timestamp=datetime.now(UTC),
                source_module="test",
                request_id="req-123",
                indicator=indicator,
                computation_time_ms=400000.0,  # Exceeds 300000ms (5 min) limit
            )
        assert "computation_time_ms" in str(exc_info.value)


@pytest.mark.unit
class TestPortfolioAllocationProduced:
    """Test PortfolioAllocationProduced event schema."""

    def test_valid_event_creation(self) -> None:
        """Test creating valid PortfolioAllocationProduced event."""
        allocation = StrategyAllocation(
            target_weights={"AAPL": Decimal("1.0")},
            correlation_id="corr-123",
        )
        event = PortfolioAllocationProduced(
            correlation_id="corr-123",
            causation_id="cause-123",
            event_id="event-123",
            timestamp=datetime.now(UTC),
            source_module="test",
            strategy_id="strategy-1",
            allocation=allocation,
            allocation_type="final",
        )
        assert event.allocation_type == "final"
        assert event.strategy_id == "strategy-1"

    def test_valid_intermediate_allocation(self) -> None:
        """Test creating valid intermediate allocation event."""
        allocation = StrategyAllocation(
            target_weights={"AAPL": Decimal("1.0")},
            correlation_id="corr-123",
        )
        event = PortfolioAllocationProduced(
            correlation_id="corr-123",
            causation_id="cause-123",
            event_id="event-123",
            timestamp=datetime.now(UTC),
            source_module="test",
            strategy_id="strategy-1",
            allocation=allocation,
            allocation_type="intermediate",
        )
        assert event.allocation_type == "intermediate"

    def test_invalid_allocation_type_fails(self) -> None:
        """Test that invalid allocation_type values are rejected."""
        allocation = StrategyAllocation(
            target_weights={"AAPL": Decimal("1.0")},
            correlation_id="corr-123",
        )
        with pytest.raises(ValidationError) as exc_info:
            PortfolioAllocationProduced(
                correlation_id="corr-123",
                causation_id="cause-123",
                event_id="event-123",
                timestamp=datetime.now(UTC),
                source_module="test",
                strategy_id="strategy-1",
                allocation=allocation,
                allocation_type="invalid",  # type: ignore[arg-type]  # Testing validation
            )
        assert "allocation_type" in str(exc_info.value)


@pytest.mark.unit
class TestFilterEvaluated:
    """Test FilterEvaluated event schema."""

    def test_valid_event_creation(self) -> None:
        """Test creating valid FilterEvaluated event."""
        filter_expr = ASTNode.list_node([ASTNode.symbol("filter"), ASTNode.symbol("rsi")])
        event = FilterEvaluated(
            correlation_id="corr-123",
            causation_id="cause-123",
            event_id="event-123",
            timestamp=datetime.now(UTC),
            source_module="test",
            filter_expression=filter_expr,
            input_symbols=["AAPL", "GOOGL", "MSFT"],
            filtered_symbols=["AAPL", "GOOGL"],
            filter_criteria={"rsi_threshold": 30},
        )
        assert len(event.input_symbols) == 3
        assert len(event.filtered_symbols) == 2
        assert event.filter_criteria["rsi_threshold"] == 30

    def test_empty_symbols_lists_accepted(self) -> None:
        """Test that empty symbol lists are accepted."""
        filter_expr = ASTNode.symbol("filter")
        event = FilterEvaluated(
            correlation_id="corr-123",
            causation_id="cause-123",
            event_id="event-123",
            timestamp=datetime.now(UTC),
            source_module="test",
            filter_expression=filter_expr,
        )
        assert event.input_symbols == []
        assert event.filtered_symbols == []


@pytest.mark.unit
class TestTopNSelected:
    """Test TopNSelected event schema."""

    def test_valid_event_creation(self) -> None:
        """Test creating valid TopNSelected event."""
        selection_expr = ASTNode.list_node(
            [ASTNode.symbol("select-top"), ASTNode.atom(Decimal("3"))]
        )
        event = TopNSelected(
            correlation_id="corr-123",
            causation_id="cause-123",
            event_id="event-123",
            timestamp=datetime.now(UTC),
            source_module="test",
            selection_expression=selection_expr,
            input_symbols=["AAPL", "GOOGL", "MSFT", "TSLA"],
            selected_symbols=["AAPL", "GOOGL", "MSFT"],
            n_selected=3,
        )
        assert event.n_selected == 3
        assert len(event.selected_symbols) == 3

    def test_negative_n_selected_fails(self) -> None:
        """Test that negative n_selected is rejected."""
        selection_expr = ASTNode.symbol("select")
        with pytest.raises(ValidationError) as exc_info:
            TopNSelected(
                correlation_id="corr-123",
                causation_id="cause-123",
                event_id="event-123",
                timestamp=datetime.now(UTC),
                source_module="test",
                selection_expression=selection_expr,
                n_selected=-1,  # Negative should fail
            )
        assert "n_selected" in str(exc_info.value)

    def test_zero_n_selected_accepted(self) -> None:
        """Test that zero n_selected is accepted."""
        selection_expr = ASTNode.symbol("select")
        event = TopNSelected(
            correlation_id="corr-123",
            causation_id="cause-123",
            event_id="event-123",
            timestamp=datetime.now(UTC),
            source_module="test",
            selection_expression=selection_expr,
            n_selected=0,
        )
        assert event.n_selected == 0

    def test_n_selected_mismatch_fails(self) -> None:
        """Test that n_selected must match length of selected_symbols."""
        selection_expr = ASTNode.symbol("select")
        with pytest.raises(ValidationError) as exc_info:
            TopNSelected(
                correlation_id="corr-123",
                causation_id="cause-123",
                event_id="event-123",
                timestamp=datetime.now(UTC),
                source_module="test",
                selection_expression=selection_expr,
                selected_symbols=["AAPL", "GOOGL"],
                n_selected=5,  # Mismatch: says 5 but only 2 symbols
            )
        assert "n_selected" in str(exc_info.value)
        assert "must match length" in str(exc_info.value)


@pytest.mark.unit
class TestDecisionEvaluated:
    """Test DecisionEvaluated event schema."""

    def test_valid_event_with_then_branch(self) -> None:
        """Test creating valid event with 'then' branch."""
        decision_expr = ASTNode.list_node([ASTNode.symbol("if"), ASTNode.symbol("test")])
        event = DecisionEvaluated(
            correlation_id="corr-123",
            causation_id="cause-123",
            event_id="event-123",
            timestamp=datetime.now(UTC),
            source_module="test",
            decision_expression=decision_expr,
            condition_result=True,
            branch_taken="then",
        )
        assert event.condition_result is True
        assert event.branch_taken == "then"
        assert event.branch_result is None

    def test_valid_event_with_else_branch(self) -> None:
        """Test creating valid event with 'else' branch."""
        decision_expr = ASTNode.symbol("if")
        event = DecisionEvaluated(
            correlation_id="corr-123",
            causation_id="cause-123",
            event_id="event-123",
            timestamp=datetime.now(UTC),
            source_module="test",
            decision_expression=decision_expr,
            condition_result=False,
            branch_taken="else",
        )
        assert event.condition_result is False
        assert event.branch_taken == "else"

    def test_valid_event_with_branch_result(self) -> None:
        """Test event with branch result."""
        decision_expr = ASTNode.symbol("if")
        fragment = PortfolioFragment(
            fragment_id="frag-1",
            source_step="decision",
            weights={"AAPL": 1.0},
        )
        event = DecisionEvaluated(
            correlation_id="corr-123",
            causation_id="cause-123",
            event_id="event-123",
            timestamp=datetime.now(UTC),
            source_module="test",
            decision_expression=decision_expr,
            condition_result=True,
            branch_taken="then",
            branch_result=fragment,
        )
        assert event.branch_result is not None
        assert event.branch_result.fragment_id == "frag-1"

    def test_empty_branch_taken_fails(self) -> None:
        """Test that empty branch_taken is rejected."""
        decision_expr = ASTNode.symbol("if")
        with pytest.raises(ValidationError) as exc_info:
            DecisionEvaluated(
                correlation_id="corr-123",
                causation_id="cause-123",
                event_id="event-123",
                timestamp=datetime.now(UTC),
                source_module="test",
                decision_expression=decision_expr,
                condition_result=True,
                branch_taken="",  # type: ignore[arg-type]  # Testing validation
            )
        assert "branch_taken" in str(exc_info.value)

    def test_invalid_branch_taken_fails(self) -> None:
        """Test that invalid branch_taken values are rejected."""
        decision_expr = ASTNode.symbol("if")
        with pytest.raises(ValidationError) as exc_info:
            DecisionEvaluated(
                correlation_id="corr-123",
                causation_id="cause-123",
                event_id="event-123",
                timestamp=datetime.now(UTC),
                source_module="test",
                decision_expression=decision_expr,
                condition_result=True,
                branch_taken="maybe",  # type: ignore[arg-type]  # Testing validation
            )
        assert "branch_taken" in str(exc_info.value)


@pytest.mark.unit
class TestEventImmutability:
    """Test that all events are immutable (frozen)."""

    def test_indicator_computed_is_frozen(self) -> None:
        """Test that IndicatorComputed events are immutable."""
        indicator = TechnicalIndicator(
            symbol="AAPL",
            timestamp=datetime.now(UTC),
            current_price=Decimal("150.0"),
        )
        event = IndicatorComputed(
            correlation_id="corr-123",
            causation_id="cause-123",
            event_id="event-123",
            timestamp=datetime.now(UTC),
            source_module="test",
            request_id="req-123",
            indicator=indicator,
            computation_time_ms=5.0,
        )
        with pytest.raises(ValidationError):
            event.request_id = "new-id"  # type: ignore[misc]  # Should fail - testing immutability

    def test_decision_evaluated_is_frozen(self) -> None:
        """Test that DecisionEvaluated events are immutable."""
        decision_expr = ASTNode.symbol("if")
        event = DecisionEvaluated(
            correlation_id="corr-123",
            causation_id="cause-123",
            event_id="event-123",
            timestamp=datetime.now(UTC),
            source_module="test",
            decision_expression=decision_expr,
            condition_result=True,
            branch_taken="then",
        )
        with pytest.raises(ValidationError):
            event.branch_taken = "else"  # type: ignore[misc]  # Should fail - testing immutability


@pytest.mark.unit
class TestEventSerialization:
    """Test event serialization and deserialization."""

    def test_indicator_computed_serialization(self) -> None:
        """Test IndicatorComputed can be serialized to dict."""
        indicator = TechnicalIndicator(
            symbol="AAPL",
            timestamp=datetime.now(UTC),
            current_price=Decimal("150.0"),
        )
        event = IndicatorComputed(
            correlation_id="corr-123",
            causation_id="cause-123",
            event_id="event-123",
            timestamp=datetime.now(UTC),
            source_module="test",
            request_id="req-123",
            indicator=indicator,
            computation_time_ms=5.0,
        )
        event_dict = event.to_dict()
        assert event_dict["event_type"] == "IndicatorComputed"
        assert event_dict["request_id"] == "req-123"
        assert "correlation_id" in event_dict

    def test_decision_evaluated_serialization(self) -> None:
        """Test DecisionEvaluated can be serialized to dict."""
        decision_expr = ASTNode.symbol("if")
        event = DecisionEvaluated(
            correlation_id="corr-123",
            causation_id="cause-123",
            event_id="event-123",
            timestamp=datetime.now(UTC),
            source_module="test",
            decision_expression=decision_expr,
            condition_result=True,
            branch_taken="then",
        )
        event_dict = event.to_dict()
        assert event_dict["event_type"] == "DecisionEvaluated"
        assert event_dict["branch_taken"] == "then"
        assert event_dict["condition_result"] is True
