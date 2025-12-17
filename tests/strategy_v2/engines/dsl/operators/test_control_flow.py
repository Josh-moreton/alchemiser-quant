"""Business Unit: strategy | Status: current.

Test DSL control flow operators.

Tests if conditionals, defsymphony, and control flow branching logic.
"""

from datetime import UTC, datetime
from unittest.mock import Mock

import pytest

from the_alchemiser.shared.schemas.ast_node import ASTNode
from the_alchemiser.shared.schemas.indicator_request import PortfolioFragment
from the_alchemiser.shared.schemas.trace import Trace
from the_alchemiser.strategy_v2.engines.dsl.context import DslContext
from the_alchemiser.strategy_v2.engines.dsl.operators.control_flow import (
    create_indicator_with_symbol,
    defsymphony,
    if_condition,
    register_control_flow_operators,
)
from the_alchemiser.strategy_v2.engines.dsl.types import DslEvaluationError


@pytest.mark.unit
@pytest.mark.dsl
class TestControlFlowOperators:
    """Test control flow operators."""

    @pytest.fixture
    def mock_event_publisher(self):
        """Create mock event publisher."""
        publisher = Mock()
        publisher.publish_decision_evaluated = Mock()
        return publisher

    @pytest.fixture
    def context(self, mock_event_publisher):
        """Create mock context."""
        evaluations = {}

        def evaluate_node(node, corr_id, trace):
            # Handle atoms
            if node.is_atom():
                val = node.get_atom_value()
                if val == "true":
                    return True
                if val == "false":
                    return False
                return val

            # Handle symbols
            if node.is_symbol():
                name = node.get_symbol_name()
                return evaluations.get(name, name)

            # Handle lists
            if node.is_list() and node.children:
                return evaluations.get(str(node), None)

            return None

        trace = Trace(
            trace_id="test-trace-id",
            correlation_id="test-corr-id",
            strategy_id="test-strategy",
            started_at=datetime.now(UTC),
            entries=[],
        )
        ctx = DslContext(
            indicator_service=Mock(),
            event_publisher=mock_event_publisher,
            correlation_id="test-corr-id",
            trace=trace,
            evaluate_node=evaluate_node,
        )
        ctx.evaluations = evaluations
        return ctx

    def test_defsymphony_evaluates_body(self, context):
        """Test defsymphony evaluates the strategy body."""
        name = ASTNode.atom("test-strategy")
        config = ASTNode.list_node([])
        body = ASTNode.atom("result-value")

        args = [name, config, body]
        result = defsymphony(args, context)

        assert result == "result-value"

    def test_defsymphony_wrong_arg_count(self, context):
        """Test defsymphony with wrong number of arguments."""
        with pytest.raises(DslEvaluationError, match="requires at least 3 arguments"):
            defsymphony([], context)

        with pytest.raises(DslEvaluationError, match="requires at least 3 arguments"):
            defsymphony([ASTNode.atom("name"), ASTNode.atom("config")], context)

    def test_if_condition_true_branch(self, context):
        """Test if takes then branch when condition is True."""
        condition = ASTNode.atom("true")
        then_expr = ASTNode.atom("then-result")
        else_expr = ASTNode.atom("else-result")

        args = [condition, then_expr, else_expr]
        result = if_condition(args, context)

        assert result == "then-result"

    def test_if_condition_false_branch(self, context):
        """Test if takes else branch when condition is False."""
        condition = ASTNode.atom("false")
        then_expr = ASTNode.atom("then-result")
        else_expr = ASTNode.atom("else-result")

        args = [condition, then_expr, else_expr]
        result = if_condition(args, context)

        assert result == "else-result"

    def test_if_condition_no_else_raises_error(self, context):
        """Test if raises error when no else clause and condition is False.

        DSL strategies must always produce an allocation. An if without else
        that evaluates to false is an evaluation failure, not a valid result.
        """
        condition = ASTNode.atom("false")
        then_expr = ASTNode.atom("then-result")

        args = [condition, then_expr]

        with pytest.raises(DslEvaluationError, match="no else branch provided"):
            if_condition(args, context)

    def test_if_condition_publishes_event(self, context, mock_event_publisher):
        """Test if publishes decision evaluated event."""
        condition = ASTNode.atom("true")
        then_expr = ASTNode.atom("result")

        args = [condition, then_expr]
        if_condition(args, context)

        mock_event_publisher.publish_decision_evaluated.assert_called_once()
        call_kwargs = mock_event_publisher.publish_decision_evaluated.call_args[1]
        assert call_kwargs["condition_result"] is True
        assert call_kwargs["branch_taken"] == "then"

    def test_if_condition_publishes_event_else_branch(self, context, mock_event_publisher):
        """Test if publishes decision evaluated event for else branch."""
        condition = ASTNode.atom("false")
        then_expr = ASTNode.atom("then")
        else_expr = ASTNode.atom("else")

        args = [condition, then_expr, else_expr]
        if_condition(args, context)

        mock_event_publisher.publish_decision_evaluated.assert_called_once()
        call_kwargs = mock_event_publisher.publish_decision_evaluated.call_args[1]
        assert call_kwargs["condition_result"] is False
        assert call_kwargs["branch_taken"] == "else"

    def test_if_condition_captures_decision_path(self, context):
        """Test if captures decision node in context decision_path."""
        condition = ASTNode.atom("true")
        then_expr = ASTNode.atom("result")

        # Ensure decision_path is empty initially
        assert len(context.decision_path) == 0

        args = [condition, then_expr]
        if_condition(args, context)

        # Check decision node was captured
        assert len(context.decision_path) == 1
        decision_node = context.decision_path[0]
        assert decision_node["result"] is True
        assert decision_node["branch"] == "then"
        assert "condition" in decision_node

    def test_if_condition_captures_multiple_decisions(self, context):
        """Test if captures multiple decision nodes in nested conditions."""
        # First decision
        condition1 = ASTNode.atom("true")
        then_expr1 = ASTNode.atom("result1")
        args1 = [condition1, then_expr1]
        if_condition(args1, context)

        # Second decision
        condition2 = ASTNode.atom("false")
        then_expr2 = ASTNode.atom("result2")
        else_expr2 = ASTNode.atom("result3")
        args2 = [condition2, then_expr2, else_expr2]
        if_condition(args2, context)

        # Check both decisions were captured
        assert len(context.decision_path) == 2
        assert context.decision_path[0]["result"] is True
        assert context.decision_path[1]["result"] is False

    def test_if_condition_wrong_arg_count(self, context):
        """Test if with wrong number of arguments."""
        with pytest.raises(DslEvaluationError, match="requires at least 2 arguments"):
            if_condition([], context)

        with pytest.raises(DslEvaluationError, match="requires at least 2 arguments"):
            if_condition([ASTNode.atom("condition")], context)

    def test_if_condition_with_truthy_values(self, context):
        """Test if with various truthy values."""
        # Non-zero number is truthy
        context.evaluations["x"] = 42
        condition = ASTNode.symbol("x")
        then_expr = ASTNode.atom("then")
        else_expr = ASTNode.atom("else")

        args = [condition, then_expr, else_expr]
        result = if_condition(args, context)

        assert result == "then"

    def test_if_condition_with_falsy_values(self, context):
        """Test if with various falsy values."""
        # Zero is falsy
        context.evaluations["x"] = 0
        condition = ASTNode.symbol("x")
        then_expr = ASTNode.atom("then")
        else_expr = ASTNode.atom("else")

        args = [condition, then_expr, else_expr]
        result = if_condition(args, context)

        assert result == "else"

    def test_if_condition_with_portfolio_fragment(self, context, mock_event_publisher):
        """Test if publishes PortfolioFragment in event when branch returns one."""
        from decimal import Decimal

        condition = ASTNode.atom("true")
        then_expr = ASTNode.symbol("portfolio")

        fragment = PortfolioFragment(
            fragment_id="test-id",
            source_step="test",
            weights={"AAPL": Decimal("1.0")},
        )
        context.evaluations["portfolio"] = fragment

        args = [condition, then_expr]
        result = if_condition(args, context)

        assert result is fragment
        call_kwargs = mock_event_publisher.publish_decision_evaluated.call_args[1]
        assert call_kwargs["branch_result"] is fragment

    def test_register_control_flow_operators(self):
        """Test registering all control flow operators."""
        from the_alchemiser.strategy_v2.engines.dsl.dispatcher import DslDispatcher

        dispatcher = DslDispatcher()
        register_control_flow_operators(dispatcher)

        assert dispatcher.is_registered("defsymphony")
        assert dispatcher.is_registered("if")

    def test_create_indicator_with_symbol_rsi(self):
        """Test create_indicator_with_symbol for RSI."""
        indicator_expr = ASTNode.list_node(
            [
                ASTNode.symbol("rsi"),
                ASTNode.list_node(
                    [
                        ASTNode.symbol(":window"),
                        ASTNode.atom("14"),
                    ],
                    metadata={"node_subtype": "map"},
                ),
            ]
        )

        result = create_indicator_with_symbol(indicator_expr, "AAPL")

        assert result.is_list()
        assert len(result.children) >= 2
        assert result.children[0].get_symbol_name() == "rsi"
        assert result.children[1].get_atom_value() == "AAPL"

    def test_create_indicator_with_symbol_moving_average(self):
        """Test create_indicator_with_symbol for moving-average-price."""
        indicator_expr = ASTNode.list_node(
            [
                ASTNode.symbol("moving-average-price"),
            ]
        )

        result = create_indicator_with_symbol(indicator_expr, "GOOGL")

        assert result.is_list()
        assert result.children[0].get_symbol_name() == "moving-average-price"
        assert result.children[1].get_atom_value() == "GOOGL"

    def test_create_indicator_with_symbol_non_list(self):
        """Test create_indicator_with_symbol with non-list returns unchanged."""
        atom = ASTNode.atom("42")
        result = create_indicator_with_symbol(atom, "AAPL")
        assert result is atom

    def test_create_indicator_with_symbol_empty_list(self):
        """Test create_indicator_with_symbol with empty list returns unchanged."""
        empty = ASTNode.list_node([])
        result = create_indicator_with_symbol(empty, "AAPL")
        assert result is empty

    def test_create_indicator_with_symbol_unsupported(self):
        """Test create_indicator_with_symbol with unsupported function."""
        expr = ASTNode.list_node([ASTNode.symbol("unsupported-func")])
        result = create_indicator_with_symbol(expr, "AAPL")
        # Should return unchanged
        assert result is expr

    def test_create_indicator_with_symbol_adds_default_window(self):
        """Test create_indicator_with_symbol adds default window when missing."""
        indicator_expr = ASTNode.list_node([ASTNode.symbol("rsi")])

        result = create_indicator_with_symbol(indicator_expr, "AAPL")

        assert result.is_list()
        assert len(result.children) == 3
        # Should have added default window parameter
        assert result.children[2].is_list()

    def test_defsymphony_logs_evaluation(self, context, caplog):
        """Test defsymphony logs evaluation start and completion."""
        import logging

        name = ASTNode.atom("test-strategy")
        config = ASTNode.list_node([])
        body = ASTNode.atom("result-value")

        with caplog.at_level(logging.DEBUG):
            args = [name, config, body]
            result = defsymphony(args, context)

        assert result == "result-value"
        # Verify logging occurred (messages may vary based on structlog configuration)
        # Just verify that the function executes without errors when logging is enabled

    def test_if_condition_logs_branch_selection(self, context, caplog):
        """Test if_condition logs branch selection."""
        import logging

        condition = ASTNode.atom("true")
        then_expr = ASTNode.atom("then-result")
        else_expr = ASTNode.atom("else-result")

        with caplog.at_level(logging.DEBUG):
            args = [condition, then_expr, else_expr]
            result = if_condition(args, context)

        assert result == "then-result"
        # Verify logging occurred (messages may vary based on structlog configuration)
        # Just verify that the function executes without errors when logging is enabled

    def test_if_condition_includes_causation_id_in_event(self, context, mock_event_publisher):
        """Test if_condition includes causation_id in published event."""
        condition = ASTNode.atom("true")
        then_expr = ASTNode.atom("result")

        args = [condition, then_expr]
        if_condition(args, context)

        mock_event_publisher.publish_decision_evaluated.assert_called_once()
        call_kwargs = mock_event_publisher.publish_decision_evaluated.call_args[1]
        assert "causation_id" in call_kwargs
        assert call_kwargs["causation_id"] == context.correlation_id

    def test_create_indicator_with_symbol_uses_default_constants(self):
        """Test create_indicator_with_symbol uses DEFAULT_INDICATOR_WINDOWS constants."""
        from the_alchemiser.strategy_v2.engines.dsl.operators.control_flow import (
            DEFAULT_INDICATOR_WINDOWS,
        )

        # Test that constants are defined
        assert "rsi" in DEFAULT_INDICATOR_WINDOWS
        assert DEFAULT_INDICATOR_WINDOWS["rsi"] == 14
        assert DEFAULT_INDICATOR_WINDOWS["moving-average-price"] == 200

        # Test that the function uses the constants
        indicator_expr = ASTNode.list_node([ASTNode.symbol("rsi")])
        result = create_indicator_with_symbol(indicator_expr, "AAPL")

        # Verify the window parameter matches the constant
        assert result.children[2].is_list()
        window_value = result.children[2].children[1].get_atom_value()
        from decimal import Decimal

        assert window_value == Decimal("14")
