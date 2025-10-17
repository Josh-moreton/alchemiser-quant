"""Business Unit: strategy | Status: current.

Test DSL Engine.

Tests DSL engine initialization, event handling, strategy evaluation,
error handling, and idempotency guarantees.
"""

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from the_alchemiser.shared.events.bus import EventBus
from the_alchemiser.shared.events.dsl_events import (
    PortfolioAllocationProduced,
    StrategyEvaluated,
    StrategyEvaluationRequested,
)
from the_alchemiser.shared.schemas.ast_node import ASTNode
from the_alchemiser.shared.schemas.strategy_allocation import StrategyAllocation
from the_alchemiser.shared.schemas.trace import Trace
from the_alchemiser.strategy_v2.engines.dsl import DslEngine, DslEngineError


@pytest.mark.unit
@pytest.mark.dsl
class TestDslEngine:
    """Test DSL Engine class."""

    @pytest.fixture
    def mock_event_bus(self):
        """Create mock event bus."""
        bus = Mock(spec=EventBus)
        bus.subscribe = Mock()
        bus.publish = Mock()
        return bus

    @pytest.fixture
    def engine(self):
        """Create engine instance without event bus."""
        return DslEngine()

    @pytest.fixture
    def engine_with_bus(self, mock_event_bus):
        """Create engine instance with event bus."""
        return DslEngine(event_bus=mock_event_bus)

    def test_init_default(self, engine):
        """Test default initialization."""
        assert engine.strategy_config_path == "."
        assert engine.event_bus is None
        assert engine.parser is not None
        assert engine.evaluator is not None
        assert engine.indicator_service is not None
        assert isinstance(engine._processed_events, set)
        assert len(engine._processed_events) == 0

    def test_init_with_config_path(self):
        """Test initialization with config path."""
        engine = DslEngine(strategy_config_path="/test/path")
        assert engine.strategy_config_path == "/test/path"

    def test_init_with_event_bus_subscribes(self, mock_event_bus):
        """Test initialization with event bus subscribes to events."""
        engine = DslEngine(event_bus=mock_event_bus)
        
        # Verify subscription
        mock_event_bus.subscribe.assert_called_once_with("StrategyEvaluationRequested", engine)
        assert engine.event_bus is mock_event_bus

    def test_can_handle_correct_event(self, engine):
        """Test can_handle returns True for StrategyEvaluationRequested."""
        assert engine.can_handle("StrategyEvaluationRequested") is True

    def test_can_handle_incorrect_event(self, engine):
        """Test can_handle returns False for other events."""
        assert engine.can_handle("SomeOtherEvent") is False
        assert engine.can_handle("StrategyEvaluated") is False

    def test_handle_event_idempotency(self, engine):
        """Test event handler rejects duplicate events."""
        # Create mock event
        event = Mock(spec=StrategyEvaluationRequested)
        event.event_id = str(uuid.uuid4())
        event.correlation_id = str(uuid.uuid4())
        event.strategy_id = "test_strategy"
        event.strategy_config_path = "test.clj"
        
        # First call should process
        with patch.object(engine, "_handle_evaluation_request") as mock_handler:
            engine.handle_event(event)
            mock_handler.assert_called_once_with(event)
        
        # Second call with same event should be skipped
        with patch.object(engine, "_handle_evaluation_request") as mock_handler:
            engine.handle_event(event)
            mock_handler.assert_not_called()
        
        # Verify event_id was tracked
        assert event.event_id in engine._processed_events

    def test_handle_event_unhandled_type(self, engine):
        """Test handle_event logs warning for unhandled event types."""
        # Create mock event that is not StrategyEvaluationRequested
        event = Mock()
        event.event_id = str(uuid.uuid4())
        event.correlation_id = str(uuid.uuid4())
        
        with patch.object(engine.logger, "warning") as mock_warning:
            engine.handle_event(event)
            mock_warning.assert_called_once()

    def test_evaluate_strategy_generates_correlation_id(self, engine):
        """Test evaluate_strategy generates correlation_id if not provided."""
        with patch.object(engine, "_parse_strategy_file") as mock_parse:
            mock_ast = ASTNode.atom("test")
            mock_parse.return_value = mock_ast
            
            with patch.object(engine.evaluator, "evaluate") as mock_evaluate:
                mock_allocation = StrategyAllocation(
                    target_weights={"AAPL": Decimal("0.5"), "GOOGL": Decimal("0.5")},
                    correlation_id="test-corr",
                    as_of=datetime.now(UTC),
                )
                mock_trace = Trace(
                    trace_id=str(uuid.uuid4()),
                    correlation_id="test-corr",
                    strategy_id="test",
                    started_at=datetime.now(UTC),
                )
                mock_evaluate.return_value = (mock_allocation, mock_trace)
                
                allocation, trace = engine.evaluate_strategy("test.clj")
                
                # Verify correlation_id was generated
                assert allocation.correlation_id is not None
                assert trace.correlation_id is not None

    def test_evaluate_strategy_uses_provided_correlation_id(self, engine):
        """Test evaluate_strategy uses provided correlation_id."""
        correlation_id = str(uuid.uuid4())
        
        with patch.object(engine, "_parse_strategy_file") as mock_parse:
            mock_ast = ASTNode.atom("test")
            mock_parse.return_value = mock_ast
            
            with patch.object(engine.evaluator, "evaluate") as mock_evaluate:
                mock_allocation = StrategyAllocation(
                    target_weights={"AAPL": Decimal("1.0")},
                    correlation_id=correlation_id,
                    as_of=datetime.now(UTC),
                )
                mock_trace = Trace(
                    trace_id=str(uuid.uuid4()),
                    correlation_id=correlation_id,
                    strategy_id="test",
                    started_at=datetime.now(UTC),
                )
                mock_evaluate.return_value = (mock_allocation, mock_trace)
                
                allocation, trace = engine.evaluate_strategy("test.clj", correlation_id)
                
                # Verify correlation_id was passed through
                assert allocation.correlation_id == correlation_id
                assert trace.correlation_id == correlation_id

    def test_evaluate_strategy_error_raises_typed_exception(self, engine):
        """Test evaluate_strategy raises DslEngineError with context on failure."""
        with patch.object(engine, "_parse_strategy_file") as mock_parse:
            mock_parse.side_effect = Exception("Test error")
            
            with pytest.raises(DslEngineError) as exc_info:
                engine.evaluate_strategy("test.clj")
            
            # Verify exception has context
            assert "Test error" in str(exc_info.value)
            assert exc_info.value.module == "strategy_v2.engines.dsl"

    def test_parse_strategy_file_not_found_raises_error(self, engine):
        """Test _parse_strategy_file raises error for non-existent file."""
        with pytest.raises(DslEngineError) as exc_info:
            engine._parse_strategy_file("nonexistent.clj")
        
        assert "Strategy file not found" in str(exc_info.value)

    def test_resolve_strategy_path_uses_provided_path(self, engine):
        """Test _resolve_strategy_path uses provided path if not empty."""
        path = engine._resolve_strategy_path("provided.clj", "ignored_id")
        assert path == "provided.clj"

    def test_resolve_strategy_path_tries_strategy_id(self, engine, tmp_path):
        """Test _resolve_strategy_path tries strategy_id based paths."""
        # Create temporary strategy file
        strategy_file = tmp_path / "test_strategy.clj"
        strategy_file.write_text("(portfolio [])")
        
        # Create engine with temp directory
        engine = DslEngine(strategy_config_path=str(tmp_path))
        
        # Resolve should find the file
        path = engine._resolve_strategy_path("", "test_strategy")
        assert "test_strategy.clj" in path

    def test_resolve_strategy_path_fallback(self, engine):
        """Test _resolve_strategy_path returns fallback for non-existent files."""
        path = engine._resolve_strategy_path("", "nonexistent_strategy")
        # Should return first possible path as fallback
        assert path == "nonexistent_strategy.clj"

    def test_publish_completion_events(self, engine_with_bus, mock_event_bus):
        """Test _publish_completion_events publishes correct events."""
        request_event = StrategyEvaluationRequested(
            event_id=str(uuid.uuid4()),
            correlation_id=str(uuid.uuid4()),
            causation_id=str(uuid.uuid4()),
            timestamp=datetime.now(UTC),
            source_module="test",
            strategy_id="test_strategy",
            strategy_config_path="test.clj",
        )
        
        allocation = StrategyAllocation(
            target_weights={"AAPL": Decimal("0.5"), "GOOGL": Decimal("0.5")},
            correlation_id=request_event.correlation_id,
            as_of=datetime.now(UTC),
        )
        
        trace = Trace(
            trace_id=str(uuid.uuid4()),
            correlation_id=request_event.correlation_id,
            strategy_id="test_strategy",
            started_at=datetime.now(UTC),
        ).mark_completed(success=True)
        
        engine_with_bus._publish_completion_events(request_event, allocation, trace)
        
        # Verify two events were published
        assert mock_event_bus.publish.call_count == 2
        
        # Check first event is StrategyEvaluated
        first_event = mock_event_bus.publish.call_args_list[0][0][0]
        assert isinstance(first_event, StrategyEvaluated)
        assert first_event.correlation_id == request_event.correlation_id
        assert first_event.causation_id == request_event.event_id
        assert first_event.success is True
        
        # Check second event is PortfolioAllocationProduced
        second_event = mock_event_bus.publish.call_args_list[1][0][0]
        assert isinstance(second_event, PortfolioAllocationProduced)
        assert second_event.correlation_id == request_event.correlation_id
        assert second_event.causation_id == request_event.event_id

    def test_publish_completion_events_no_bus(self, engine):
        """Test _publish_completion_events does nothing without event bus."""
        request_event = Mock(spec=StrategyEvaluationRequested)
        allocation = Mock(spec=StrategyAllocation)
        trace = Mock(spec=Trace)
        
        # Should not raise
        engine._publish_completion_events(request_event, allocation, trace)

    def test_publish_error_events(self, engine_with_bus, mock_event_bus):
        """Test _publish_error_events publishes error event."""
        request_event = StrategyEvaluationRequested(
            event_id=str(uuid.uuid4()),
            correlation_id=str(uuid.uuid4()),
            causation_id=str(uuid.uuid4()),
            timestamp=datetime.now(UTC),
            source_module="test",
            strategy_id="test_strategy",
            strategy_config_path="test.clj",
        )
        
        error_message = "Test error message"
        
        engine_with_bus._publish_error_events(request_event, error_message)
        
        # Verify one event was published
        assert mock_event_bus.publish.call_count == 1
        
        # Check event is StrategyEvaluated with error
        event = mock_event_bus.publish.call_args[0][0]
        assert isinstance(event, StrategyEvaluated)
        assert event.correlation_id == request_event.correlation_id
        assert event.causation_id == request_event.event_id
        assert event.success is False
        assert event.error_message == error_message

    def test_publish_error_events_no_bus(self, engine):
        """Test _publish_error_events does nothing without event bus."""
        request_event = Mock(spec=StrategyEvaluationRequested)
        error_message = "Test error"
        
        # Should not raise
        engine._publish_error_events(request_event, error_message)

    def test_timestamp_consistency_in_completion_events(self, engine_with_bus, mock_event_bus):
        """Test that completion events use same timestamp."""
        request_event = StrategyEvaluationRequested(
            event_id=str(uuid.uuid4()),
            correlation_id=str(uuid.uuid4()),
            causation_id=str(uuid.uuid4()),
            timestamp=datetime.now(UTC),
            source_module="test",
            strategy_id="test_strategy",
            strategy_config_path="test.clj",
        )
        
        allocation = StrategyAllocation(
            target_weights={"CASH": Decimal("1.0")},
            correlation_id=request_event.correlation_id,
            as_of=datetime.now(UTC),
        )
        
        trace = Trace(
            trace_id=str(uuid.uuid4()),
            correlation_id=request_event.correlation_id,
            strategy_id="test_strategy",
            started_at=datetime.now(UTC),
        ).mark_completed(success=True)
        
        engine_with_bus._publish_completion_events(request_event, allocation, trace)
        
        # Get timestamps from both events
        first_event = mock_event_bus.publish.call_args_list[0][0][0]
        second_event = mock_event_bus.publish.call_args_list[1][0][0]
        
        # Timestamps should be identical
        assert first_event.timestamp == second_event.timestamp

    def test_evaluate_strategy_captures_decision_path_in_trace(self, engine):
        """Test that decision path is captured during evaluation and added to trace metadata."""
        # Create a simple strategy with an if condition
        strategy_code = """
        (defsymphony "test-strategy" {}
          (weight-equal
            [(if (> 5 3)
              [(asset "AAPL" "Apple Inc.")]
              [(asset "MSFT" "Microsoft Corp.")])]))
        """
        
        # Write to a temp file
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".clj", delete=False) as f:
            f.write(strategy_code)
            temp_path = f.name
        
        try:
            # Evaluate the strategy
            allocation, trace = engine.evaluate_strategy(temp_path, str(uuid.uuid4()))
            
            # Check that decision_path is in trace metadata
            assert "decision_path" in trace.metadata
            decision_path = trace.metadata["decision_path"]
            
            # Should have at least one decision
            assert len(decision_path) > 0
            
            # Check decision node structure
            decision_node = decision_path[0]
            assert "condition" in decision_node
            assert "result" in decision_node
            assert "branch" in decision_node
            assert "values" in decision_node
            
            # The condition should have been True (5 > 3)
            assert decision_node["result"] is True
            assert decision_node["branch"] == "then"
            
            # Allocation should be for AAPL (since condition was true)
            assert "AAPL" in allocation.target_weights
            
        finally:
            # Clean up temp file
            Path(temp_path).unlink(missing_ok=True)
