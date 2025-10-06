"""Business Unit: strategy | Status: current.

Test DSL event publisher.

Tests event publishing for DSL evaluation events including indicator computation
and decision evaluation.
"""

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import Mock

import pytest

from the_alchemiser.shared.events.bus import EventBus
from the_alchemiser.shared.schemas.ast_node import ASTNode
from the_alchemiser.shared.schemas.indicator_request import PortfolioFragment
from the_alchemiser.shared.schemas.technical_indicator import TechnicalIndicator
from the_alchemiser.strategy_v2.engines.dsl.events import DslEventPublisher


@pytest.mark.unit
@pytest.mark.dsl
class TestDslEventPublisher:
    """Test DSL event publisher."""

    @pytest.fixture
    def mock_event_bus(self):
        """Create mock event bus."""
        bus = Mock(spec=EventBus)
        bus.publish = Mock()
        return bus

    @pytest.fixture
    def publisher(self, mock_event_bus):
        """Create publisher instance with mock event bus."""
        return DslEventPublisher(mock_event_bus)

    @pytest.fixture
    def publisher_no_bus(self):
        """Create publisher instance without event bus."""
        return DslEventPublisher(None)

    def test_init_with_event_bus(self, mock_event_bus):
        """Test initialization with event bus."""
        publisher = DslEventPublisher(mock_event_bus)
        assert publisher.event_bus is mock_event_bus

    def test_init_without_event_bus(self):
        """Test initialization without event bus."""
        publisher = DslEventPublisher(None)
        assert publisher.event_bus is None

    def test_publish_indicator_computed(self, publisher, mock_event_bus):
        """Test publishing indicator computed event."""
        request_id = str(uuid.uuid4())
        correlation_id = str(uuid.uuid4())
        indicator = TechnicalIndicator(
            symbol="AAPL",
            timestamp=datetime.now(UTC),
            current_price=Decimal("150.0"),
        )
        
        publisher.publish_indicator_computed(
            request_id=request_id,
            indicator=indicator,
            computation_time_ms=5.0,
            correlation_id=correlation_id,
        )
        
        # Verify event was published
        mock_event_bus.publish.assert_called_once()
        event = mock_event_bus.publish.call_args[0][0]
        assert event.correlation_id == correlation_id

    def test_publish_indicator_computed_no_bus(self, publisher_no_bus):
        """Test publishing indicator computed event with no bus does nothing."""
        indicator = TechnicalIndicator(
            symbol="AAPL",
            timestamp=datetime.now(UTC),
            current_price=Decimal("150.0"),
        )
        
        # Should not raise
        publisher_no_bus.publish_indicator_computed(
            request_id=str(uuid.uuid4()),
            indicator=indicator,
            computation_time_ms=5.0,
            correlation_id=str(uuid.uuid4()),
        )

    def test_publish_decision_evaluated(self, publisher, mock_event_bus):
        """Test publishing decision evaluated event."""
        decision_expr = ASTNode.list_node([
            ASTNode.symbol("if"),
            ASTNode.symbol("condition"),
            ASTNode.symbol("then"),
        ])
        correlation_id = str(uuid.uuid4())
        
        publisher.publish_decision_evaluated(
            decision_expression=decision_expr,
            condition_result=True,
            branch_taken="then",
            branch_result=None,
            correlation_id=correlation_id,
        )
        
        # Verify event was published
        mock_event_bus.publish.assert_called_once()
        event = mock_event_bus.publish.call_args[0][0]
        assert event.correlation_id == correlation_id
        assert event.condition_result is True
        assert event.branch_taken == "then"

    def test_publish_decision_evaluated_with_portfolio(self, publisher, mock_event_bus):
        """Test publishing decision evaluated event with portfolio result."""
        decision_expr = ASTNode.symbol("if")
        fragment = PortfolioFragment(
            fragment_id="test-id",
            source_step="test",
            weights={"AAPL": 0.5, "GOOGL": 0.5},
        )
        correlation_id = str(uuid.uuid4())
        
        publisher.publish_decision_evaluated(
            decision_expression=decision_expr,
            condition_result=False,
            branch_taken="else",
            branch_result=fragment,
            correlation_id=correlation_id,
        )
        
        # Verify event was published
        mock_event_bus.publish.assert_called_once()
        event = mock_event_bus.publish.call_args[0][0]
        assert event.branch_result is fragment

    def test_publish_decision_evaluated_no_bus(self, publisher_no_bus):
        """Test publishing decision evaluated event with no bus does nothing."""
        decision_expr = ASTNode.symbol("if")
        
        # Should not raise
        publisher_no_bus.publish_decision_evaluated(
            decision_expression=decision_expr,
            condition_result=True,
            branch_taken="then",
            branch_result=None,
            correlation_id=str(uuid.uuid4()),
        )

    def test_publish_decision_with_causation_id(self, publisher, mock_event_bus):
        """Test that causation_id is passed through correctly."""
        decision_expr = ASTNode.symbol("if")
        correlation_id = str(uuid.uuid4())
        causation_id = str(uuid.uuid4())
        
        publisher.publish_decision_evaluated(
            decision_expression=decision_expr,
            condition_result=True,
            branch_taken="then",
            branch_result=None,
            correlation_id=correlation_id,
            causation_id=causation_id,
        )
        
        event = mock_event_bus.publish.call_args[0][0]
        assert event.causation_id == causation_id

    def test_publish_decision_without_causation_id(self, publisher, mock_event_bus):
        """Test that causation_id defaults to correlation_id when not provided."""
        decision_expr = ASTNode.symbol("if")
        correlation_id = str(uuid.uuid4())
        
        publisher.publish_decision_evaluated(
            decision_expression=decision_expr,
            condition_result=True,
            branch_taken="then",
            branch_result=None,
            correlation_id=correlation_id,
        )
        
        event = mock_event_bus.publish.call_args[0][0]
        assert event.causation_id == correlation_id

    def test_publish_indicator_with_causation_id(self, publisher, mock_event_bus):
        """Test publishing indicator event with causation_id."""
        request_id = str(uuid.uuid4())
        correlation_id = str(uuid.uuid4())
        causation_id = str(uuid.uuid4())
        indicator = TechnicalIndicator(
            symbol="AAPL",
            timestamp=datetime.now(UTC),
            current_price=Decimal("150.0"),
        )
        
        publisher.publish_indicator_computed(
            request_id=request_id,
            indicator=indicator,
            computation_time_ms=5.0,
            correlation_id=correlation_id,
            causation_id=causation_id,
        )
        
        event = mock_event_bus.publish.call_args[0][0]
        assert event.causation_id == causation_id

    def test_publish_multiple_events(self, publisher, mock_event_bus):
        """Test publishing multiple events."""
        indicator = TechnicalIndicator(
            symbol="AAPL",
            timestamp=datetime.now(UTC),
            current_price=Decimal("150.0"),
        )
        
        # Publish first event
        publisher.publish_indicator_computed(
            request_id=str(uuid.uuid4()),
            indicator=indicator,
            computation_time_ms=5.0,
            correlation_id=str(uuid.uuid4()),
        )
        
        # Publish second event
        publisher.publish_decision_evaluated(
            decision_expression=ASTNode.symbol("if"),
            condition_result=True,
            branch_taken="then",
            branch_result=None,
            correlation_id=str(uuid.uuid4()),
        )
        
        # Verify both events were published
        assert mock_event_bus.publish.call_count == 2

    def test_publish_indicator_with_negative_computation_time(self, publisher):
        """Test that negative computation_time_ms raises ValueError."""
        indicator = TechnicalIndicator(
            symbol="AAPL",
            timestamp=datetime.now(UTC),
            current_price=Decimal("150.0"),
        )
        
        with pytest.raises(ValueError, match="computation_time_ms must be non-negative"):
            publisher.publish_indicator_computed(
                request_id=str(uuid.uuid4()),
                indicator=indicator,
                computation_time_ms=-1.0,
                correlation_id=str(uuid.uuid4()),
            )

    def test_publish_indicator_with_empty_request_id(self, publisher):
        """Test that empty request_id raises ValueError."""
        indicator = TechnicalIndicator(
            symbol="AAPL",
            timestamp=datetime.now(UTC),
            current_price=Decimal("150.0"),
        )
        
        with pytest.raises(ValueError, match="request_id must not be empty"):
            publisher.publish_indicator_computed(
                request_id="",
                indicator=indicator,
                computation_time_ms=5.0,
                correlation_id=str(uuid.uuid4()),
            )

    def test_publish_indicator_with_whitespace_request_id(self, publisher):
        """Test that whitespace-only request_id raises ValueError."""
        indicator = TechnicalIndicator(
            symbol="AAPL",
            timestamp=datetime.now(UTC),
            current_price=Decimal("150.0"),
        )
        
        with pytest.raises(ValueError, match="request_id must not be empty"):
            publisher.publish_indicator_computed(
                request_id="   ",
                indicator=indicator,
                computation_time_ms=5.0,
                correlation_id=str(uuid.uuid4()),
            )

    def test_publish_indicator_with_custom_event_id(self, publisher, mock_event_bus):
        """Test publishing with custom event_id for deterministic testing."""
        custom_event_id = "test-event-id-123"
        indicator = TechnicalIndicator(
            symbol="AAPL",
            timestamp=datetime.now(UTC),
            current_price=Decimal("150.0"),
        )
        
        publisher.publish_indicator_computed(
            request_id=str(uuid.uuid4()),
            indicator=indicator,
            computation_time_ms=5.0,
            correlation_id=str(uuid.uuid4()),
            event_id=custom_event_id,
        )
        
        event = mock_event_bus.publish.call_args[0][0]
        assert event.event_id == custom_event_id

    def test_publish_indicator_with_custom_timestamp(self, publisher, mock_event_bus):
        """Test publishing with custom timestamp for deterministic testing."""
        custom_timestamp = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        indicator = TechnicalIndicator(
            symbol="AAPL",
            timestamp=datetime.now(UTC),
            current_price=Decimal("150.0"),
        )
        
        publisher.publish_indicator_computed(
            request_id=str(uuid.uuid4()),
            indicator=indicator,
            computation_time_ms=5.0,
            correlation_id=str(uuid.uuid4()),
            timestamp=custom_timestamp,
        )
        
        event = mock_event_bus.publish.call_args[0][0]
        assert event.timestamp == custom_timestamp

    def test_publish_decision_with_custom_event_id(self, publisher, mock_event_bus):
        """Test publishing decision with custom event_id."""
        custom_event_id = "test-decision-id-456"
        decision_expr = ASTNode.symbol("if")
        
        publisher.publish_decision_evaluated(
            decision_expression=decision_expr,
            condition_result=True,
            branch_taken="then",
            branch_result=None,
            correlation_id=str(uuid.uuid4()),
            event_id=custom_event_id,
        )
        
        event = mock_event_bus.publish.call_args[0][0]
        assert event.event_id == custom_event_id

    def test_publish_decision_with_custom_timestamp(self, publisher, mock_event_bus):
        """Test publishing decision with custom timestamp."""
        custom_timestamp = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        decision_expr = ASTNode.symbol("if")
        
        publisher.publish_decision_evaluated(
            decision_expression=decision_expr,
            condition_result=True,
            branch_taken="then",
            branch_result=None,
            correlation_id=str(uuid.uuid4()),
            timestamp=custom_timestamp,
        )
        
        event = mock_event_bus.publish.call_args[0][0]
        assert event.timestamp == custom_timestamp

    def test_publish_indicator_error_handling(self, mock_event_bus):
        """Test error handling when event bus publish fails."""
        from the_alchemiser.strategy_v2.engines.dsl.events import EventPublishError
        
        # Make publish raise an exception
        mock_event_bus.publish.side_effect = RuntimeError("Bus failure")
        publisher = DslEventPublisher(mock_event_bus)
        
        indicator = TechnicalIndicator(
            symbol="AAPL",
            timestamp=datetime.now(UTC),
            current_price=Decimal("150.0"),
        )
        
        with pytest.raises(EventPublishError, match="Failed to publish IndicatorComputed event"):
            publisher.publish_indicator_computed(
                request_id=str(uuid.uuid4()),
                indicator=indicator,
                computation_time_ms=5.0,
                correlation_id=str(uuid.uuid4()),
            )

    def test_publish_decision_error_handling(self, mock_event_bus):
        """Test error handling when decision event bus publish fails."""
        from the_alchemiser.strategy_v2.engines.dsl.events import EventPublishError
        
        # Make publish raise an exception
        mock_event_bus.publish.side_effect = RuntimeError("Bus failure")
        publisher = DslEventPublisher(mock_event_bus)
        
        decision_expr = ASTNode.symbol("if")
        
        with pytest.raises(EventPublishError, match="Failed to publish DecisionEvaluated event"):
            publisher.publish_decision_evaluated(
                decision_expression=decision_expr,
                condition_result=True,
                branch_taken="then",
                branch_result=None,
                correlation_id=str(uuid.uuid4()),
            )
