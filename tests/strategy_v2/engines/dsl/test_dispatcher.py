"""Business Unit: strategy | Status: current.

Test DSL operator dispatcher and registry.

Tests registration, dispatch, and error handling for the DSL operator dispatcher.
"""

from unittest.mock import Mock

import pytest

from the_alchemiser.shared.schemas.ast_node import ASTNode
from the_alchemiser.strategy_v2.engines.dsl.context import DslContext
from the_alchemiser.strategy_v2.engines.dsl.dispatcher import DslDispatcher
from the_alchemiser.strategy_v2.engines.dsl.types import DslEvaluationError


@pytest.mark.unit
@pytest.mark.dsl
class TestDslDispatcher:
    """Test DSL dispatcher."""

    @pytest.fixture
    def dispatcher(self):
        """Create dispatcher instance."""
        return DslDispatcher()

    @pytest.fixture
    def mock_context(self):
        """Create mock DSL context."""
        context = Mock(spec=DslContext)
        context.correlation_id = "test-correlation-id"
        return context

    def test_init_empty(self, dispatcher):
        """Test dispatcher initializes with empty symbol table."""
        assert len(dispatcher.symbol_table) == 0
        assert dispatcher.list_symbols() == []

    def test_register_simple_operator(self, dispatcher):
        """Test registering a simple operator."""
        def test_op(args, context):
            return "test_result"
        
        dispatcher.register("test-op", test_op)
        assert dispatcher.is_registered("test-op")
        assert "test-op" in dispatcher.list_symbols()

    def test_register_multiple_operators(self, dispatcher):
        """Test registering multiple operators."""
        def op1(args, context):
            return 1
        
        def op2(args, context):
            return 2
        
        dispatcher.register("op1", op1)
        dispatcher.register("op2", op2)
        
        assert dispatcher.is_registered("op1")
        assert dispatcher.is_registered("op2")
        assert len(dispatcher.list_symbols()) == 2

    def test_dispatch_simple_operator(self, dispatcher, mock_context):
        """Test dispatching to a simple operator."""
        def test_op(args, context):
            return len(args)
        
        dispatcher.register("test-op", test_op)
        
        args = [ASTNode.atom("1"), ASTNode.atom("2")]
        result = dispatcher.dispatch("test-op", args, mock_context)
        assert result == 2

    def test_dispatch_with_context(self, dispatcher, mock_context):
        """Test that context is passed to operator."""
        called_with_context = []
        
        def test_op(args, context):
            called_with_context.append(context)
            return "done"
        
        dispatcher.register("test-op", test_op)
        dispatcher.dispatch("test-op", [], mock_context)
        
        assert len(called_with_context) == 1
        assert called_with_context[0] is mock_context

    def test_dispatch_unknown_symbol(self, dispatcher, mock_context):
        """Test error on dispatching unknown symbol."""
        with pytest.raises(DslEvaluationError, match="Unknown DSL function: unknown"):
            dispatcher.dispatch("unknown", [], mock_context)

    def test_is_registered_true(self, dispatcher):
        """Test is_registered returns True for registered symbol."""
        dispatcher.register("test", lambda args, ctx: None)
        assert dispatcher.is_registered("test") is True

    def test_is_registered_false(self, dispatcher):
        """Test is_registered returns False for unregistered symbol."""
        assert dispatcher.is_registered("nonexistent") is False

    def test_list_symbols_empty(self, dispatcher):
        """Test list_symbols returns empty list initially."""
        assert dispatcher.list_symbols() == []

    def test_list_symbols_with_operators(self, dispatcher):
        """Test list_symbols returns all registered symbols."""
        dispatcher.register("op1", lambda args, ctx: None)
        dispatcher.register("op2", lambda args, ctx: None)
        dispatcher.register("op3", lambda args, ctx: None)
        
        symbols = dispatcher.list_symbols()
        assert len(symbols) == 3
        assert "op1" in symbols
        assert "op2" in symbols
        assert "op3" in symbols

    def test_register_overwrites_existing(self, dispatcher, mock_context):
        """Test that registering same symbol overwrites previous."""
        def op1(args, context):
            return "first"
        
        def op2(args, context):
            return "second"
        
        dispatcher.register("test", op1)
        dispatcher.register("test", op2)
        
        result = dispatcher.dispatch("test", [], mock_context)
        assert result == "second"

    def test_dispatch_with_exception(self, dispatcher, mock_context):
        """Test that operator exceptions propagate."""
        def failing_op(args, context):
            raise ValueError("Test error")
        
        dispatcher.register("fail", failing_op)
        
        with pytest.raises(ValueError, match="Test error"):
            dispatcher.dispatch("fail", [], mock_context)

    def test_register_comparison_operators(self, dispatcher):
        """Test registering all comparison operators."""
        ops = [">", "<", ">=", "<=", "="]
        for op in ops:
            dispatcher.register(op, lambda args, ctx: True)
        
        for op in ops:
            assert dispatcher.is_registered(op)

    def test_dispatch_preserves_args(self, dispatcher, mock_context):
        """Test that args are passed unchanged to operator."""
        received_args = []
        
        def test_op(args, context):
            received_args.extend(args)
            return None
        
        dispatcher.register("test", test_op)
        
        args = [
            ASTNode.atom("1"),
            ASTNode.symbol("test"),
            ASTNode.list_node([ASTNode.atom("2")]),
        ]
        dispatcher.dispatch("test", args, mock_context)
        
        assert len(received_args) == 3
        assert received_args[0] is args[0]
        assert received_args[1] is args[1]
        assert received_args[2] is args[2]
