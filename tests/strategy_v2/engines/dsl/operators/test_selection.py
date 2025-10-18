"""Business Unit: strategy | Status: current.

Test DSL selection operators.

Tests select-top and select-bottom operators for asset selection.
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
from the_alchemiser.strategy_v2.engines.dsl.operators.selection import (
    register_selection_operators,
    select_bottom,
    select_top,
)
from the_alchemiser.strategy_v2.engines.dsl.types import DslEvaluationError


@pytest.mark.unit
@pytest.mark.dsl
class TestSelectionOperators:
    """Test selection operators."""

    @pytest.fixture
    def context(self):
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

    def test_select_top_integer(self, context):
        """Test select-top with integer argument."""
        args = [ASTNode.atom(Decimal("5"))]
        result = select_top(args, context)
        assert result == 5
        assert isinstance(result, int)

    def test_select_top_float(self, context):
        """Test select-top with float argument."""
        args = [ASTNode.atom(Decimal("3.7"))]
        result = select_top(args, context)
        assert result == 3
        assert isinstance(result, int)

    def test_select_top_decimal(self, context):
        """Test select-top with Decimal argument."""
        args = [ASTNode.atom(Decimal("10"))]
        result = select_top(args, context)
        assert result == 10

    def test_select_top_converts_to_int(self, context):
        """Test select-top converts float to int."""
        args = [ASTNode.atom(Decimal("7.9"))]
        result = select_top(args, context)
        assert result == 7

    def test_select_top_no_args(self, context):
        """Test select-top with no arguments raises error."""
        with pytest.raises(DslEvaluationError, match="requires at least 1 argument"):
            select_top([], context)

    def test_select_top_zero(self, context):
        """Test select-top with zero."""
        args = [ASTNode.atom(Decimal("0"))]
        result = select_top(args, context)
        assert result == 0

    def test_select_top_negative(self, context):
        """Test select-top with negative number."""
        args = [ASTNode.atom(Decimal("-5"))]
        result = select_top(args, context)
        assert result == -5

    def test_select_bottom_integer(self, context):
        """Test select-bottom with integer argument."""
        args = [ASTNode.atom(Decimal("3"))]
        result = select_bottom(args, context)
        assert result == 3
        assert isinstance(result, int)

    def test_select_bottom_float(self, context):
        """Test select-bottom with float argument."""
        args = [ASTNode.atom(Decimal("4.2"))]
        result = select_bottom(args, context)
        assert result == 4
        assert isinstance(result, int)

    def test_select_bottom_decimal(self, context):
        """Test select-bottom with Decimal argument."""
        args = [ASTNode.atom(Decimal("8"))]
        result = select_bottom(args, context)
        assert result == 8

    def test_select_bottom_converts_to_int(self, context):
        """Test select-bottom converts float to int."""
        args = [ASTNode.atom(Decimal("6.1"))]
        result = select_bottom(args, context)
        assert result == 6

    def test_select_bottom_no_args(self, context):
        """Test select-bottom with no arguments raises error."""
        with pytest.raises(DslEvaluationError, match="requires at least 1 argument"):
            select_bottom([], context)

    def test_select_bottom_zero(self, context):
        """Test select-bottom with zero."""
        args = [ASTNode.atom(Decimal("0"))]
        result = select_bottom(args, context)
        assert result == 0

    def test_select_bottom_negative(self, context):
        """Test select-bottom with negative number."""
        args = [ASTNode.atom(Decimal("-3"))]
        result = select_bottom(args, context)
        assert result == -3

    def test_select_top_ignores_extra_args(self, context):
        """Test select-top only uses first argument."""
        args = [ASTNode.atom(Decimal("5")), ASTNode.atom(Decimal("10"))]
        result = select_top(args, context)
        assert result == 5

    def test_select_bottom_ignores_extra_args(self, context):
        """Test select-bottom only uses first argument."""
        args = [ASTNode.atom(Decimal("3")), ASTNode.atom(Decimal("7"))]
        result = select_bottom(args, context)
        assert result == 3

    def test_register_selection_operators(self):
        """Test registering all selection operators."""
        from the_alchemiser.strategy_v2.engines.dsl.dispatcher import DslDispatcher

        dispatcher = DslDispatcher()
        register_selection_operators(dispatcher)

        assert dispatcher.is_registered("select-top")
        assert dispatcher.is_registered("select-bottom")

    def test_select_top_large_number(self, context):
        """Test select-top with large number."""
        args = [ASTNode.atom(Decimal("1000"))]
        result = select_top(args, context)
        assert result == 1000

    def test_select_bottom_large_number(self, context):
        """Test select-bottom with large number."""
        args = [ASTNode.atom(Decimal("999"))]
        result = select_bottom(args, context)
        assert result == 999


@pytest.mark.unit
@pytest.mark.dsl
@pytest.mark.property
class TestSelectionOperatorsPropertyBased:
    """Property-based tests for selection operators."""

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
        n=st.decimals(
            min_value=0,
            max_value=100,
            allow_nan=False,
            allow_infinity=False,
        )
    )
    def test_select_top_always_returns_int(self, n):
        """Property: select-top always returns an integer."""
        context = self._make_context()
        args = [ASTNode.atom(n)]
        result = select_top(args, context)
        assert isinstance(result, int)

    @given(
        n=st.decimals(
            min_value=0,
            max_value=100,
            allow_nan=False,
            allow_infinity=False,
        )
    )
    def test_select_bottom_always_returns_int(self, n):
        """Property: select-bottom always returns an integer."""
        context = self._make_context()
        args = [ASTNode.atom(n)]
        result = select_bottom(args, context)
        assert isinstance(result, int)

    @given(n=st.integers(min_value=0, max_value=100))
    def test_select_top_preserves_integer_value(self, n):
        """Property: select-top preserves integer values."""
        context = self._make_context()
        args = [ASTNode.atom(Decimal(str(n)))]
        result = select_top(args, context)
        assert result == n

    @given(n=st.integers(min_value=0, max_value=100))
    def test_select_bottom_preserves_integer_value(self, n):
        """Property: select-bottom preserves integer values."""
        context = self._make_context()
        args = [ASTNode.atom(Decimal(str(n)))]
        result = select_bottom(args, context)
        assert result == n

    @given(
        n=st.decimals(
            min_value=0.1,
            max_value=100,
            allow_nan=False,
            allow_infinity=False,
        )
    )
    def test_select_top_truncates_decimals(self, n):
        """Property: select-top truncates decimal values."""
        context = self._make_context()
        args = [ASTNode.atom(n)]
        result = select_top(args, context)
        assert result == int(n)

    @given(
        n=st.decimals(
            min_value=0.1,
            max_value=100,
            allow_nan=False,
            allow_infinity=False,
        )
    )
    def test_select_bottom_truncates_decimals(self, n):
        """Property: select-bottom truncates decimal values."""
        context = self._make_context()
        args = [ASTNode.atom(n)]
        result = select_bottom(args, context)
        assert result == int(n)
