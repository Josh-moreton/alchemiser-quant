"""Business Unit: strategy | Status: current.

Test DSL evaluator integration.

Tests complete DSL expression evaluation including operator dispatch,
context management, and AST traversal.
"""

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import Mock

import pytest

from the_alchemiser.shared.events.bus import EventBus
from the_alchemiser.shared.schemas.ast_node import ASTNode
from the_alchemiser.shared.schemas.trace import Trace
from the_alchemiser.strategy_v2.engines.dsl.dsl_evaluator import DslEvaluator
from the_alchemiser.strategy_v2.indicators.indicator_service import IndicatorService


@pytest.mark.unit
@pytest.mark.dsl
class TestDslEvaluator:
    """Test DSL evaluator."""

    @pytest.fixture
    def mock_indicator_service(self):
        """Create mock indicator service."""
        return Mock(spec=IndicatorService)

    @pytest.fixture
    def mock_event_bus(self):
        """Create mock event bus."""
        return Mock(spec=EventBus)

    @pytest.fixture
    def evaluator(self, mock_indicator_service, mock_event_bus):
        """Create evaluator instance."""
        return DslEvaluator(mock_indicator_service, mock_event_bus)

    @pytest.fixture
    def evaluator_no_bus(self, mock_indicator_service):
        """Create evaluator without event bus."""
        return DslEvaluator(mock_indicator_service, None)

    def test_init_registers_operators(self, evaluator):
        """Test that initialization registers all operators."""
        # Check that common operators are registered
        assert evaluator.dispatcher.is_registered(">")
        assert evaluator.dispatcher.is_registered("<")
        assert evaluator.dispatcher.is_registered("=")
        assert evaluator.dispatcher.is_registered("if")
        assert evaluator.dispatcher.is_registered("defsymphony")
        assert evaluator.dispatcher.is_registered("select-top")
        assert evaluator.dispatcher.is_registered("select-bottom")
        assert evaluator.dispatcher.is_registered("weight-equal")
        assert evaluator.dispatcher.is_registered("rsi")

    def test_evaluate_atom_integer(self, evaluator):
        """Test evaluating integer atom raises error (no valid allocation)."""
        ast = ASTNode.atom(Decimal("42"))
        correlation_id = str(uuid.uuid4())
        trace = Trace(
            trace_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            strategy_id="test",
            started_at=datetime.now(UTC),
        )

        # Simple atom doesn't produce valid allocation
        from the_alchemiser.strategy_v2.engines.dsl.types import DslEvaluationError

        with pytest.raises(DslEvaluationError):
            evaluator.evaluate(ast, correlation_id, trace)

    def test_evaluate_atom_string(self, evaluator):
        """Test evaluating string atom produces allocation."""
        ast = ASTNode.atom("AAPL")
        correlation_id = str(uuid.uuid4())
        trace = Trace(
            trace_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            strategy_id="test",
            started_at=datetime.now(UTC),
        )

        # String atom represents an asset and produces allocation
        allocation, result_trace = evaluator.evaluate(ast, correlation_id, trace)
        assert "AAPL" in allocation.target_weights
        assert allocation.target_weights["AAPL"] == Decimal("1.0")

    def test_evaluate_comparison_expression(self, evaluator):
        """Test evaluating comparison expression raises error (no valid allocation)."""
        # (> 10 5) evaluates to True but doesn't produce allocation
        ast = ASTNode.list_node(
            [
                ASTNode.symbol(">"),
                ASTNode.atom(Decimal("10")),
                ASTNode.atom(Decimal("5")),
            ]
        )
        correlation_id = str(uuid.uuid4())
        trace = Trace(
            trace_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            strategy_id="test",
            started_at=datetime.now(UTC),
        )

        # Comparison returns bool, not a valid allocation
        from the_alchemiser.strategy_v2.engines.dsl.types import DslEvaluationError

        with pytest.raises(DslEvaluationError):
            evaluator.evaluate(ast, correlation_id, trace)

    def test_evaluate_weight_equal_single_asset(self, evaluator):
        """Test evaluating weight-equal with single asset."""
        # (weight-equal "AAPL")
        ast = ASTNode.list_node(
            [
                ASTNode.symbol("weight-equal"),
                ASTNode.atom("AAPL"),
            ]
        )
        correlation_id = str(uuid.uuid4())
        trace = Trace(
            trace_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            strategy_id="test",
            started_at=datetime.now(UTC),
        )

        allocation, result_trace = evaluator.evaluate(ast, correlation_id, trace)

        # Should allocate 100% to AAPL
        assert "AAPL" in allocation.target_weights
        assert abs(allocation.target_weights["AAPL"] - Decimal("1.0")) < Decimal("0.01")

    def test_evaluate_weight_equal_multiple_assets(self, evaluator):
        """Test evaluating weight-equal with multiple assets."""
        # (weight-equal "AAPL" "GOOGL" "MSFT")
        ast = ASTNode.list_node(
            [
                ASTNode.symbol("weight-equal"),
                ASTNode.atom("AAPL"),
                ASTNode.atom("GOOGL"),
                ASTNode.atom("MSFT"),
            ]
        )
        correlation_id = str(uuid.uuid4())
        trace = Trace(
            trace_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            strategy_id="test",
            started_at=datetime.now(UTC),
        )

        allocation, result_trace = evaluator.evaluate(ast, correlation_id, trace)

        # Should allocate ~33% to each
        assert len(allocation.target_weights) == 3
        for symbol in ["AAPL", "GOOGL", "MSFT"]:
            assert symbol in allocation.target_weights
            assert abs(allocation.target_weights[symbol] - Decimal("0.333333")) < Decimal("0.01")

    def test_evaluate_defsymphony(self, evaluator):
        """Test evaluating defsymphony expression."""
        # (defsymphony "test-strategy" {} (weight-equal "AAPL"))
        ast = ASTNode.list_node(
            [
                ASTNode.symbol("defsymphony"),
                ASTNode.atom("test-strategy"),
                ASTNode.list_node([], metadata={"node_subtype": "map"}),
                ASTNode.list_node(
                    [
                        ASTNode.symbol("weight-equal"),
                        ASTNode.atom("AAPL"),
                    ]
                ),
            ]
        )
        correlation_id = str(uuid.uuid4())
        trace = Trace(
            trace_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            strategy_id="test",
            started_at=datetime.now(UTC),
        )

        allocation, result_trace = evaluator.evaluate(ast, correlation_id, trace)

        # Should execute the body and return allocation
        assert "AAPL" in allocation.target_weights

    def test_evaluate_if_true_branch(self, evaluator):
        """Test evaluating if with true condition."""
        # (if (> 10 5) (weight-equal "AAPL") (weight-equal "GOOGL"))
        ast = ASTNode.list_node(
            [
                ASTNode.symbol("if"),
                ASTNode.list_node(
                    [
                        ASTNode.symbol(">"),
                        ASTNode.atom(Decimal("10")),
                        ASTNode.atom(Decimal("5")),
                    ]
                ),
                ASTNode.list_node(
                    [
                        ASTNode.symbol("weight-equal"),
                        ASTNode.atom("AAPL"),
                    ]
                ),
                ASTNode.list_node(
                    [
                        ASTNode.symbol("weight-equal"),
                        ASTNode.atom("GOOGL"),
                    ]
                ),
            ]
        )
        correlation_id = str(uuid.uuid4())
        trace = Trace(
            trace_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            strategy_id="test",
            started_at=datetime.now(UTC),
        )

        allocation, result_trace = evaluator.evaluate(ast, correlation_id, trace)

        # Should take then branch and allocate to AAPL
        assert "AAPL" in allocation.target_weights
        assert "GOOGL" not in allocation.target_weights

    def test_evaluate_if_false_branch(self, evaluator):
        """Test evaluating if with false condition."""
        # (if (< 10 5) (weight-equal "AAPL") (weight-equal "GOOGL"))
        ast = ASTNode.list_node(
            [
                ASTNode.symbol("if"),
                ASTNode.list_node(
                    [
                        ASTNode.symbol("<"),
                        ASTNode.atom(Decimal("10")),
                        ASTNode.atom(Decimal("5")),
                    ]
                ),
                ASTNode.list_node(
                    [
                        ASTNode.symbol("weight-equal"),
                        ASTNode.atom("AAPL"),
                    ]
                ),
                ASTNode.list_node(
                    [
                        ASTNode.symbol("weight-equal"),
                        ASTNode.atom("GOOGL"),
                    ]
                ),
            ]
        )
        correlation_id = str(uuid.uuid4())
        trace = Trace(
            trace_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            strategy_id="test",
            started_at=datetime.now(UTC),
        )

        allocation, result_trace = evaluator.evaluate(ast, correlation_id, trace)

        # Should take else branch and allocate to GOOGL
        assert "GOOGL" in allocation.target_weights
        assert "AAPL" not in allocation.target_weights

    def test_evaluate_nested_expressions(self, evaluator):
        """Test evaluating nested expressions."""
        # (weight-equal (if (> 10 5) "AAPL" "GOOGL"))
        ast = ASTNode.list_node(
            [
                ASTNode.symbol("weight-equal"),
                ASTNode.list_node(
                    [
                        ASTNode.symbol("if"),
                        ASTNode.list_node(
                            [
                                ASTNode.symbol(">"),
                                ASTNode.atom(Decimal("10")),
                                ASTNode.atom(Decimal("5")),
                            ]
                        ),
                        ASTNode.atom("AAPL"),
                        ASTNode.atom("GOOGL"),
                    ]
                ),
            ]
        )
        correlation_id = str(uuid.uuid4())
        trace = Trace(
            trace_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            strategy_id="test",
            started_at=datetime.now(UTC),
        )

        allocation, result_trace = evaluator.evaluate(ast, correlation_id, trace)

        # Should evaluate if first, then pass result to weight-equal
        assert "AAPL" in allocation.target_weights

    def test_evaluate_with_trace(self, evaluator):
        """Test that evaluation returns updated trace."""
        ast = ASTNode.list_node(
            [
                ASTNode.symbol("weight-equal"),
                ASTNode.atom("AAPL"),
            ]
        )
        correlation_id = str(uuid.uuid4())
        trace = Trace(
            trace_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            strategy_id="test",
            started_at=datetime.now(UTC),
        )

        allocation, result_trace = evaluator.evaluate(ast, correlation_id, trace)

        # Trace should be returned
        assert result_trace is not None
        assert result_trace.trace_id == trace.trace_id

    def test_evaluate_publishes_events(self, evaluator, mock_event_bus):
        """Test that evaluation publishes events when event bus is present."""
        # (if (> 10 5) (weight-equal "AAPL") (weight-equal "GOOGL"))
        ast = ASTNode.list_node(
            [
                ASTNode.symbol("if"),
                ASTNode.list_node(
                    [
                        ASTNode.symbol(">"),
                        ASTNode.atom(Decimal("10")),
                        ASTNode.atom(Decimal("5")),
                    ]
                ),
                ASTNode.list_node(
                    [
                        ASTNode.symbol("weight-equal"),
                        ASTNode.atom("AAPL"),
                    ]
                ),
                ASTNode.list_node(
                    [
                        ASTNode.symbol("weight-equal"),
                        ASTNode.atom("GOOGL"),
                    ]
                ),
            ]
        )
        correlation_id = str(uuid.uuid4())
        trace = Trace(
            trace_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            strategy_id="test",
            started_at=datetime.now(UTC),
        )

        evaluator.evaluate(ast, correlation_id, trace)

        # Should have published decision event
        assert mock_event_bus.publish.called

    def test_evaluate_without_event_bus(self, evaluator_no_bus):
        """Test that evaluation works without event bus."""
        ast = ASTNode.list_node(
            [
                ASTNode.symbol("weight-equal"),
                ASTNode.atom("AAPL"),
            ]
        )
        correlation_id = str(uuid.uuid4())
        trace = Trace(
            trace_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            strategy_id="test",
            started_at=datetime.now(UTC),
        )

        # Should not raise
        allocation, result_trace = evaluator_no_bus.evaluate(ast, correlation_id, trace)
        assert "AAPL" in allocation.target_weights

    def test_evaluate_invalid_result_type_raises_error(self, evaluator):
        """Test that evaluation raises error for invalid result types."""
        # Create a mock that returns an invalid type
        # We'll use a simple integer which should trigger the error
        ast = ASTNode.atom(Decimal("42"))
        correlation_id = str(uuid.uuid4())
        trace = Trace(
            trace_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            strategy_id="test",
            started_at=datetime.now(UTC),
        )

        # Integer result cannot be converted to valid allocation
        from the_alchemiser.strategy_v2.engines.dsl.types import DslEvaluationError

        with pytest.raises(DslEvaluationError) as exc_info:
            evaluator.evaluate(ast, correlation_id, trace)

        # Verify error message mentions invalid type
        assert "invalid type" in str(exc_info.value).lower()
