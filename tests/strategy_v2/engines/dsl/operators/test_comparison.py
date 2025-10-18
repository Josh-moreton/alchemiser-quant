"""Business Unit: strategy | Status: current.

Test DSL comparison operators.

Tests comparison and equality operators (>, <, >=, <=, =) with various input types
and edge cases.
"""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import Mock

import pytest
from hypothesis import given
from hypothesis import strategies as st

from the_alchemiser.shared.schemas.ast_node import ASTNode
from the_alchemiser.shared.schemas.trace import Trace
from the_alchemiser.strategy_v2.engines.dsl.context import DslContext
from the_alchemiser.strategy_v2.engines.dsl.operators.comparison import (
    equal,
    greater_equal,
    greater_than,
    less_equal,
    less_than,
    register_comparison_operators,
)
from the_alchemiser.strategy_v2.engines.dsl.types import DslEvaluationError


@pytest.mark.unit
@pytest.mark.dsl
class TestComparisonOperators:
    """Test comparison operators."""

    @pytest.fixture
    def context(self):
        """Create mock context."""

        def evaluate_node(node, corr_id, trace):
            if node.is_atom():
                return node.get_atom_value()
            if node.is_symbol():
                return node.get_symbol_name()
            return None

        trace = Trace(
            trace_id="test-trace-id",
            correlation_id="test",
            strategy_id="test-strategy",
            started_at=datetime.now(UTC),
            entries=[],
        )
        return DslContext(
            indicator_service=Mock(),
            event_publisher=Mock(),
            correlation_id="test",
            trace=trace,
            evaluate_node=evaluate_node,
        )

    def test_greater_than_true(self, context):
        """Test > operator returns True when left > right."""
        args = [ASTNode.atom(Decimal("10")), ASTNode.atom(Decimal("5"))]
        result = greater_than(args, context)
        assert result is True

    def test_greater_than_false(self, context):
        """Test > operator returns False when left <= right."""
        args = [ASTNode.atom(Decimal("5")), ASTNode.atom(Decimal("10"))]
        result = greater_than(args, context)
        assert result is False

    def test_greater_than_equal_values(self, context):
        """Test > operator with equal values."""
        args = [ASTNode.atom(Decimal("5")), ASTNode.atom(Decimal("5"))]
        result = greater_than(args, context)
        assert result is False

    def test_greater_than_wrong_arg_count(self, context):
        """Test > operator with wrong number of arguments."""
        with pytest.raises(DslEvaluationError, match="requires exactly 2 arguments"):
            greater_than([ASTNode.atom(Decimal("1"))], context)

        with pytest.raises(DslEvaluationError, match="requires exactly 2 arguments"):
            greater_than(
                [
                    ASTNode.atom(Decimal("1")),
                    ASTNode.atom(Decimal("2")),
                    ASTNode.atom(Decimal("3")),
                ],
                context,
            )

    def test_less_than_true(self, context):
        """Test < operator returns True when left < right."""
        args = [ASTNode.atom(Decimal("5")), ASTNode.atom(Decimal("10"))]
        result = less_than(args, context)
        assert result is True

    def test_less_than_false(self, context):
        """Test < operator returns False when left >= right."""
        args = [ASTNode.atom(Decimal("10")), ASTNode.atom(Decimal("5"))]
        result = less_than(args, context)
        assert result is False

    def test_less_than_equal_values(self, context):
        """Test < operator with equal values."""
        args = [ASTNode.atom(Decimal("5")), ASTNode.atom(Decimal("5"))]
        result = less_than(args, context)
        assert result is False

    def test_less_than_wrong_arg_count(self, context):
        """Test < operator with wrong number of arguments."""
        with pytest.raises(DslEvaluationError, match="requires exactly 2 arguments"):
            less_than([ASTNode.atom(Decimal("1"))], context)

    def test_greater_equal_true_greater(self, context):
        """Test >= operator returns True when left > right."""
        args = [ASTNode.atom(Decimal("10")), ASTNode.atom(Decimal("5"))]
        result = greater_equal(args, context)
        assert result is True

    def test_greater_equal_true_equal(self, context):
        """Test >= operator returns True when left == right."""
        args = [ASTNode.atom(Decimal("5")), ASTNode.atom(Decimal("5"))]
        result = greater_equal(args, context)
        assert result is True

    def test_greater_equal_false(self, context):
        """Test >= operator returns False when left < right."""
        args = [ASTNode.atom(Decimal("5")), ASTNode.atom(Decimal("10"))]
        result = greater_equal(args, context)
        assert result is False

    def test_greater_equal_wrong_arg_count(self, context):
        """Test >= operator with wrong number of arguments."""
        with pytest.raises(DslEvaluationError, match="requires exactly 2 arguments"):
            greater_equal([], context)

    def test_less_equal_true_less(self, context):
        """Test <= operator returns True when left < right."""
        args = [ASTNode.atom(Decimal("5")), ASTNode.atom(Decimal("10"))]
        result = less_equal(args, context)
        assert result is True

    def test_less_equal_true_equal(self, context):
        """Test <= operator returns True when left == right."""
        args = [ASTNode.atom(Decimal("5")), ASTNode.atom(Decimal("5"))]
        result = less_equal(args, context)
        assert result is True

    def test_less_equal_false(self, context):
        """Test <= operator returns False when left > right."""
        args = [ASTNode.atom(Decimal("10")), ASTNode.atom(Decimal("5"))]
        result = less_equal(args, context)
        assert result is False

    def test_less_equal_wrong_arg_count(self, context):
        """Test <= operator with wrong number of arguments."""
        with pytest.raises(DslEvaluationError, match="requires exactly 2 arguments"):
            less_equal([ASTNode.atom(Decimal("1"))], context)

    def test_equal_numbers_true(self, context):
        """Test = operator with equal numbers."""
        args = [ASTNode.atom(Decimal("42")), ASTNode.atom(Decimal("42"))]
        result = equal(args, context)
        assert result is True

    def test_equal_numbers_false(self, context):
        """Test = operator with different numbers."""
        args = [ASTNode.atom(Decimal("42")), ASTNode.atom(Decimal("43"))]
        result = equal(args, context)
        assert result is False

    def test_equal_strings_true(self, context):
        """Test = operator with equal strings."""
        args = [ASTNode.atom("AAPL"), ASTNode.atom("AAPL")]
        result = equal(args, context)
        assert result is True

    def test_equal_strings_false(self, context):
        """Test = operator with different strings."""
        args = [ASTNode.atom("AAPL"), ASTNode.atom("GOOGL")]
        result = equal(args, context)
        assert result is False

    def test_equal_mixed_types_false(self, context):
        """Test = operator with mixed types returns False."""
        args = [ASTNode.atom(Decimal("42")), ASTNode.atom("42")]
        result = equal(args, context)
        assert result is False

    def test_equal_wrong_arg_count(self, context):
        """Test = operator with wrong number of arguments."""
        with pytest.raises(DslEvaluationError, match="requires exactly 2 arguments"):
            equal([ASTNode.atom(Decimal("1"))], context)

    def test_register_comparison_operators(self):
        """Test registering all comparison operators."""
        from the_alchemiser.strategy_v2.engines.dsl.dispatcher import DslDispatcher

        dispatcher = DslDispatcher()
        register_comparison_operators(dispatcher)

        assert dispatcher.is_registered(">")
        assert dispatcher.is_registered("<")
        assert dispatcher.is_registered(">=")
        assert dispatcher.is_registered("<=")
        assert dispatcher.is_registered("=")

    def test_comparison_with_negative_numbers(self, context):
        """Test comparison operators with negative numbers."""
        # -5 > -10
        args = [ASTNode.atom(Decimal("-5")), ASTNode.atom(Decimal("-10"))]
        assert greater_than(args, context) is True

        # -10 < -5
        args = [ASTNode.atom(Decimal("-10")), ASTNode.atom(Decimal("-5"))]
        assert less_than(args, context) is True

    def test_comparison_with_zero(self, context):
        """Test comparison operators with zero."""
        # 0 > -1
        args = [ASTNode.atom(Decimal("0")), ASTNode.atom(Decimal("-1"))]
        assert greater_than(args, context) is True

        # 0 < 1
        args = [ASTNode.atom(Decimal("0")), ASTNode.atom(Decimal("1"))]
        assert less_than(args, context) is True

    def test_comparison_with_decimals(self, context):
        """Test comparison operators with decimal values."""
        # 3.14 > 3.13
        args = [ASTNode.atom(Decimal("3.14")), ASTNode.atom(Decimal("3.13"))]
        assert greater_than(args, context) is True

        # 3.14 == 3.14
        args = [ASTNode.atom(Decimal("3.14")), ASTNode.atom(Decimal("3.14"))]
        assert equal(args, context) is True


@pytest.mark.unit
@pytest.mark.dsl
@pytest.mark.property
class TestComparisonOperatorsPropertyBased:
    """Property-based tests for comparison operators."""

    def _make_context(self):
        """Create mock context."""

        def evaluate_node(node, corr_id, trace):
            if node.is_atom():
                return node.get_atom_value()
            return None

        trace = Trace(
            trace_id="test-trace-id",
            correlation_id="test",
            strategy_id="test-strategy",
            started_at=datetime.now(UTC),
            entries=[],
        )
        return DslContext(
            indicator_service=Mock(),
            event_publisher=Mock(),
            correlation_id="test",
            trace=trace,
            evaluate_node=evaluate_node,
        )

    @given(
        a=st.decimals(min_value=-1000, max_value=1000, allow_nan=False, allow_infinity=False),
        b=st.decimals(min_value=-1000, max_value=1000, allow_nan=False, allow_infinity=False),
    )
    def test_greater_than_property(self, a, b):
        """Property: (a > b) iff a is actually greater than b."""
        context = self._make_context()
        args = [ASTNode.atom(a), ASTNode.atom(b)]
        result = greater_than(args, context)
        assert result == (a > b)

    @given(
        a=st.decimals(min_value=-1000, max_value=1000, allow_nan=False, allow_infinity=False),
        b=st.decimals(min_value=-1000, max_value=1000, allow_nan=False, allow_infinity=False),
    )
    def test_less_than_property(self, a, b):
        """Property: (a < b) iff a is actually less than b."""
        context = self._make_context()
        args = [ASTNode.atom(a), ASTNode.atom(b)]
        result = less_than(args, context)
        assert result == (a < b)

    @given(
        a=st.decimals(min_value=-1000, max_value=1000, allow_nan=False, allow_infinity=False),
        b=st.decimals(min_value=-1000, max_value=1000, allow_nan=False, allow_infinity=False),
    )
    def test_equal_property(self, a, b):
        """Property: (a = b) iff a equals b."""
        context = self._make_context()
        args = [ASTNode.atom(a), ASTNode.atom(b)]
        result = equal(args, context)
        assert result == (a == b)

    @given(val=st.decimals(min_value=-1000, max_value=1000, allow_nan=False, allow_infinity=False))
    def test_reflexive_equal(self, val):
        """Property: a = a is always True."""
        context = self._make_context()
        args = [ASTNode.atom(val), ASTNode.atom(val)]
        result = equal(args, context)
        assert result is True

    @given(val=st.decimals(min_value=-1000, max_value=1000, allow_nan=False, allow_infinity=False))
    def test_reflexive_greater_equal(self, val):
        """Property: a >= a is always True."""
        context = self._make_context()
        args = [ASTNode.atom(val), ASTNode.atom(val)]
        result = greater_equal(args, context)
        assert result is True

    @given(val=st.decimals(min_value=-1000, max_value=1000, allow_nan=False, allow_infinity=False))
    def test_reflexive_less_equal(self, val):
        """Property: a <= a is always True."""
        context = self._make_context()
        args = [ASTNode.atom(val), ASTNode.atom(val)]
        result = less_equal(args, context)
        assert result is True
