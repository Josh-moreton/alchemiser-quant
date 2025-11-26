#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

Tests for DSL types module.

Validates DSLValue type alias and DslEvaluationError exception handling
to ensure proper error context and inheritance from StrategyExecutionError.
"""

from decimal import Decimal

import pytest

from the_alchemiser.shared.errors.exceptions import AlchemiserError, StrategyExecutionError
from the_alchemiser.shared.schemas.indicator_request import PortfolioFragment
from the_alchemiser.strategy_v2.engines.dsl.types import DslEvaluationError, DSLValue


@pytest.mark.unit
class TestDslEvaluationError:
    """Test DslEvaluationError exception class."""

    def test_error_inherits_from_strategy_execution_error(self) -> None:
        """Test that DslEvaluationError inherits from StrategyExecutionError."""
        error = DslEvaluationError("Test error")
        assert isinstance(error, StrategyExecutionError)
        assert isinstance(error, AlchemiserError)
        assert isinstance(error, Exception)

    def test_error_with_message_only(self) -> None:
        """Test creating error with message only."""
        message = "Invalid operator"
        error = DslEvaluationError(message)

        assert str(error) == message
        assert error.message == message
        assert error.strategy_name == "dsl_engine"
        assert error.operation == "evaluate"
        assert error.expression is None
        assert error.node_type is None
        assert error.correlation_id is None

    def test_error_with_expression_context(self) -> None:
        """Test creating error with expression context."""
        message = "Unknown operator"
        expression = "(unknown-op AAPL GOOGL)"
        error = DslEvaluationError(message, expression=expression)

        assert error.message == message
        assert error.expression == expression
        assert "expression" in error.context
        assert error.context["expression"] == expression

    def test_error_with_node_type_context(self) -> None:
        """Test creating error with node type context."""
        message = "Invalid node"
        node_type = "atom"
        error = DslEvaluationError(message, node_type=node_type)

        assert error.message == message
        assert error.node_type == node_type
        assert "node_type" in error.context
        assert error.context["node_type"] == node_type

    def test_error_with_correlation_id(self) -> None:
        """Test creating error with correlation ID."""
        message = "Evaluation failed"
        correlation_id = "abc-123-def-456"
        error = DslEvaluationError(message, correlation_id=correlation_id)

        assert error.message == message
        assert error.correlation_id == correlation_id
        assert "correlation_id" in error.context
        assert error.context["correlation_id"] == correlation_id

    def test_error_with_all_context(self) -> None:
        """Test creating error with all contextual information."""
        message = "Complete error"
        expression = "(weight-equal AAPL)"
        node_type = "list"
        correlation_id = "xyz-789"

        error = DslEvaluationError(
            message,
            expression=expression,
            node_type=node_type,
            correlation_id=correlation_id,
        )

        assert error.message == message
        assert error.expression == expression
        assert error.node_type == node_type
        assert error.correlation_id == correlation_id
        assert error.strategy_name == "dsl_engine"
        assert error.operation == "evaluate"

        # Verify all context is present
        assert error.context["expression"] == expression
        assert error.context["node_type"] == node_type
        assert error.context["correlation_id"] == correlation_id
        assert error.context["strategy_name"] == "dsl_engine"
        assert error.context["operation"] == "evaluate"

    def test_error_can_be_raised_and_caught(self) -> None:
        """Test that error can be raised and caught properly."""
        with pytest.raises(DslEvaluationError) as exc_info:
            raise DslEvaluationError("Test error", expression="(test)")

        assert exc_info.value.message == "Test error"
        assert exc_info.value.expression == "(test)"

    def test_error_can_be_caught_as_strategy_execution_error(self) -> None:
        """Test that error can be caught as StrategyExecutionError."""
        with pytest.raises(StrategyExecutionError) as exc_info:
            raise DslEvaluationError("Test error")

        assert isinstance(exc_info.value, DslEvaluationError)

    def test_error_can_be_caught_as_alchemiser_error(self) -> None:
        """Test that error can be caught as AlchemiserError."""
        with pytest.raises(AlchemiserError) as exc_info:
            raise DslEvaluationError("Test error")

        assert isinstance(exc_info.value, DslEvaluationError)

    def test_error_to_dict_includes_all_fields(self) -> None:
        """Test that to_dict method includes all error fields."""
        error = DslEvaluationError(
            "Test error",
            expression="(test AAPL)",
            node_type="list",
            correlation_id="test-123",
        )

        error_dict = error.to_dict()

        assert error_dict["error_type"] == "DslEvaluationError"
        assert error_dict["message"] == "Test error"
        assert "timestamp" in error_dict
        assert error_dict["context"]["expression"] == "(test AAPL)"
        assert error_dict["context"]["node_type"] == "list"
        assert error_dict["context"]["correlation_id"] == "test-123"


@pytest.mark.unit
class TestDSLValueType:
    """Test DSLValue type alias validation."""

    def test_portfolio_fragment_is_valid_dsl_value(self) -> None:
        """Test that PortfolioFragment is a valid DSLValue."""
        fragment = PortfolioFragment(
            fragment_id="test-123",
            source_step="test",
            weights={"AAPL": Decimal("0.5"), "GOOGL": Decimal("0.5")},
        )

        # Type checking validates this at compile time
        value: DSLValue = fragment
        assert isinstance(value, PortfolioFragment)

    def test_dict_is_valid_dsl_value(self) -> None:
        """Test that dict with proper types is a valid DSLValue."""
        dict_value: DSLValue = {"AAPL": 100.0, "GOOGL": 200.0}
        assert isinstance(dict_value, dict)

    def test_list_is_valid_dsl_value(self) -> None:
        """Test that list is a valid DSLValue."""
        list_value: DSLValue = ["AAPL", "GOOGL", "MSFT"]
        assert isinstance(list_value, list)

    def test_nested_list_is_valid_dsl_value(self) -> None:
        """Test that nested list is a valid DSLValue."""
        nested_list: DSLValue = [["AAPL", "GOOGL"], ["MSFT", "AMZN"]]
        assert isinstance(nested_list, list)

    def test_string_is_valid_dsl_value(self) -> None:
        """Test that string is a valid DSLValue."""
        string_value: DSLValue = "AAPL"
        assert isinstance(string_value, str)

    def test_int_is_valid_dsl_value(self) -> None:
        """Test that int is a valid DSLValue."""
        int_value: DSLValue = 42
        assert isinstance(int_value, int)

    def test_float_is_valid_dsl_value(self) -> None:
        """Test that float is a valid DSLValue (for intermediate calculations)."""
        float_value: DSLValue = 3.14159
        assert isinstance(float_value, float)

    def test_bool_is_valid_dsl_value(self) -> None:
        """Test that bool is a valid DSLValue."""
        bool_value: DSLValue = True
        assert isinstance(bool_value, bool)

    def test_decimal_is_valid_dsl_value(self) -> None:
        """Test that Decimal is a valid DSLValue (preferred for financial values)."""
        decimal_value: DSLValue = Decimal("100.50")
        assert isinstance(decimal_value, Decimal)

    def test_none_is_valid_dsl_value(self) -> None:
        """Test that None is a valid DSLValue (for absence of value)."""
        none_value: DSLValue = None
        assert none_value is None

    def test_mixed_dict_with_decimal_and_string(self) -> None:
        """Test dict with mixed Decimal and string values."""
        mixed_dict: DSLValue = {
            "price": Decimal("150.25"),
            "symbol": "AAPL",
            "quantity": 100,
        }
        assert isinstance(mixed_dict, dict)
        assert isinstance(mixed_dict["price"], Decimal)
        assert isinstance(mixed_dict["symbol"], str)
        assert isinstance(mixed_dict["quantity"], int)
