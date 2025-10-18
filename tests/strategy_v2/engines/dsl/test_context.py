"""Business Unit: strategy | Status: current.

Test DSL evaluation context.

Tests context utilities for type coercion, decimal handling, and state management.
"""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import Mock

import pytest

from the_alchemiser.shared.schemas.trace import Trace
from the_alchemiser.strategy_v2.engines.dsl.context import DslContext


@pytest.mark.unit
@pytest.mark.dsl
class TestDslContext:
    """Test DSL context."""

    @pytest.fixture
    def mock_indicator_service(self):
        """Create mock indicator service."""
        return Mock()

    @pytest.fixture
    def mock_event_publisher(self):
        """Create mock event publisher."""
        return Mock()

    @pytest.fixture
    def mock_evaluate_node(self):
        """Create mock evaluate_node function."""
        return Mock(return_value=42)

    @pytest.fixture
    def context(self, mock_indicator_service, mock_event_publisher, mock_evaluate_node):
        """Create context instance."""
        trace = Trace(
            trace_id="test-trace-id",
            correlation_id="test-correlation-id",
            strategy_id="test-strategy",
            started_at=datetime.now(UTC),
            entries=[],
        )
        return DslContext(
            indicator_service=mock_indicator_service,
            event_publisher=mock_event_publisher,
            correlation_id="test-correlation-id",
            trace=trace,
            evaluate_node=mock_evaluate_node,
        )

    def test_init_sets_attributes(self, context, mock_indicator_service, mock_event_publisher):
        """Test that initialization sets all attributes."""
        assert context.indicator_service is mock_indicator_service
        assert context.event_publisher is mock_event_publisher
        assert context.correlation_id == "test-correlation-id"
        assert context.trace is not None
        assert context.evaluate_node is not None
        assert context.timestamp is not None

    def test_as_decimal_from_decimal(self, context):
        """Test as_decimal with Decimal input."""
        result = context.as_decimal(Decimal("42.5"))
        assert result == Decimal("42.5")
        assert isinstance(result, Decimal)

    def test_as_decimal_from_int(self, context):
        """Test as_decimal with int input."""
        result = context.as_decimal(42)
        assert result == Decimal("42")
        assert isinstance(result, Decimal)

    def test_as_decimal_from_float(self, context):
        """Test as_decimal with float input."""
        result = context.as_decimal(3.14)
        assert isinstance(result, Decimal)
        assert abs(result - Decimal("3.14")) < Decimal("0.01")

    def test_as_decimal_from_string(self, context):
        """Test as_decimal with string input."""
        result = context.as_decimal("123.45")
        assert result == Decimal("123.45")
        assert isinstance(result, Decimal)

    def test_as_decimal_from_invalid_string(self, context):
        """Test as_decimal with invalid string returns zero."""
        result = context.as_decimal("not-a-number")
        assert result == Decimal("0")

    def test_as_decimal_from_none(self, context):
        """Test as_decimal with None returns zero."""
        result = context.as_decimal(None)
        assert result == Decimal("0")

    def test_as_decimal_from_bool_true(self, context):
        """Test as_decimal with bool True returns Decimal('1')."""
        result = context.as_decimal(True)
        assert result == Decimal("1")
        assert isinstance(result, Decimal)

    def test_as_decimal_from_bool_false(self, context):
        """Test as_decimal with bool False returns Decimal('0')."""
        result = context.as_decimal(False)
        assert result == Decimal("0")
        assert isinstance(result, Decimal)

    def test_coerce_param_value_int(self, context):
        """Test coerce_param_value with int."""
        result = context.coerce_param_value(42)
        assert result == 42
        assert isinstance(result, int)

    def test_coerce_param_value_float(self, context):
        """Test coerce_param_value with float."""
        result = context.coerce_param_value(3.14)
        assert result == 3.14
        assert isinstance(result, float)

    def test_coerce_param_value_decimal(self, context):
        """Test coerce_param_value with Decimal."""
        val = Decimal("123.45")
        result = context.coerce_param_value(val)
        assert result == val
        assert isinstance(result, Decimal)

    def test_coerce_param_value_string(self, context):
        """Test coerce_param_value with string."""
        result = context.coerce_param_value("test")
        assert result == "test"
        assert isinstance(result, str)

    def test_coerce_param_value_bool(self, context):
        """Test coerce_param_value with bool converts to int."""
        result_true = context.coerce_param_value(True)
        result_false = context.coerce_param_value(False)
        assert result_true == 1
        assert result_false == 0

    def test_coerce_param_value_none(self, context):
        """Test coerce_param_value with None returns 0."""
        result = context.coerce_param_value(None)
        assert result == 0

    def test_coerce_param_value_single_item_list(self, context):
        """Test coerce_param_value with single-item list unwraps it."""
        result = context.coerce_param_value([42])
        assert result == 42

    def test_coerce_param_value_multi_item_list(self, context):
        """Test coerce_param_value with multi-item list converts to string."""
        result = context.coerce_param_value([1, 2, 3])
        assert isinstance(result, str)

    def test_coerce_param_value_dict(self, context):
        """Test coerce_param_value with dict converts to string."""
        result = context.coerce_param_value({"key": "value"})
        assert isinstance(result, str)

    def test_evaluate_node_is_callable(self, context, mock_evaluate_node):
        """Test that evaluate_node function is accessible."""
        from the_alchemiser.shared.schemas.ast_node import ASTNode

        node = ASTNode.atom("test")
        result = context.evaluate_node(node, "corr-id", context.trace)

        mock_evaluate_node.assert_called_once()
        assert result == 42


@pytest.mark.unit
@pytest.mark.dsl
@pytest.mark.property
class TestDslContextPropertyBased:
    """Property-based tests for context."""

    def _make_context(self):
        """Create context instance."""
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
            evaluate_node=Mock(),
        )

    def test_as_decimal_preserves_precision(self):
        """Test that as_decimal preserves decimal precision."""
        context = self._make_context()
        test_values = [
            Decimal("0.123456789"),
            Decimal("1234567890.123456789"),
            Decimal("-0.000000001"),
        ]

        for val in test_values:
            result = context.as_decimal(val)
            assert result == val

    def test_as_decimal_never_raises(self):
        """Test that as_decimal never raises exceptions."""
        context = self._make_context()
        test_values = [
            42,
            3.14,
            "123",
            "invalid",
            None,
            # Skip booleans as they're int subclass and handled correctly
            [],
            {},
        ]

        for val in test_values:
            result = context.as_decimal(val)
            assert isinstance(result, Decimal)

    def test_coerce_param_value_always_returns_primitive(self):
        """Test that coerce_param_value always returns a primitive type."""
        context = self._make_context()
        test_values = [
            42,
            3.14,
            Decimal("123"),
            "test",
            True,
            False,
            None,
            [42],
        ]

        for val in test_values:
            result = context.coerce_param_value(val)
            assert isinstance(result, (int, float, Decimal, str))
