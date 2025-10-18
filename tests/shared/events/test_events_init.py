"""Business Unit: shared | Status: current.

Tests for shared.events.__init__ module exports and interface.

Validates that the events __init__ module correctly exports the expected
public API for event-driven architecture and maintains proper module structure.
"""

from __future__ import annotations

from datetime import UTC


class TestEventsModuleInterface:
    """Test suite for events module public API."""

    def test_all_exports_defined(self) -> None:
        """Test that __all__ contains expected 19 exports."""
        from the_alchemiser.shared import events

        # Check __all__ exists
        assert hasattr(events, "__all__"), "Module must define __all__"

        # Expected exports: 3 infrastructure + 16 event schemas
        expected_exports = {
            # Infrastructure
            "BaseEvent",
            "EventBus",
            "EventHandler",
            # Workflow lifecycle events
            "StartupEvent",
            "WorkflowStarted",
            "WorkflowCompleted",
            "WorkflowFailed",
            # Trading flow events
            "SignalGenerated",
            "RebalancePlanned",
            "TradeExecuted",
            "TradeExecutionStarted",
            # State management events
            "PortfolioStateChanged",
            "AllocationComparisonCompleted",
            # Execution coordination events
            "ExecutionPhaseCompleted",
            "OrderSettlementCompleted",
            "BulkSettlementCompleted",
            # Notification events
            "ErrorNotificationRequested",
            "TradingNotificationRequested",
            "SystemNotificationRequested",
        }

        actual_exports = set(events.__all__)

        assert actual_exports == expected_exports, (
            f"__all__ mismatch. "
            f"Missing: {expected_exports - actual_exports}, "
            f"Extra: {actual_exports - expected_exports}"
        )

    def test_all_exports_importable(self) -> None:
        """Test that all exports in __all__ can be imported."""
        from the_alchemiser.shared import events

        for export_name in events.__all__:
            assert hasattr(events, export_name), (
                f"Export '{export_name}' listed in __all__ but not importable"
            )

            # Verify it's not None
            exported_item = getattr(events, export_name)
            assert exported_item is not None, f"Export '{export_name}' is None"

    def test_infrastructure_exports(self) -> None:
        """Test that infrastructure classes are properly exported."""
        from the_alchemiser.shared.events import BaseEvent, EventBus, EventHandler

        # Verify BaseEvent is a class
        assert isinstance(BaseEvent, type), "BaseEvent should be a class"
        assert hasattr(BaseEvent, "model_config"), "BaseEvent should be a Pydantic model"

        # Verify EventBus is a class
        assert isinstance(EventBus, type), "EventBus should be a class"
        assert hasattr(EventBus, "publish"), "EventBus should have publish method"
        assert hasattr(EventBus, "subscribe"), "EventBus should have subscribe method"

        # EventHandler is a Protocol (runtime_checkable)
        assert hasattr(EventHandler, "handle_event"), (
            "EventHandler protocol should define handle_event"
        )
        assert hasattr(EventHandler, "can_handle"), "EventHandler protocol should define can_handle"

    def test_workflow_event_exports(self) -> None:
        """Test that workflow lifecycle events are properly exported."""
        from the_alchemiser.shared.events import (
            StartupEvent,
            WorkflowCompleted,
            WorkflowFailed,
            WorkflowStarted,
        )

        # All should be classes that inherit from BaseEvent
        workflow_events = [StartupEvent, WorkflowStarted, WorkflowCompleted, WorkflowFailed]

        for event_class in workflow_events:
            assert isinstance(event_class, type), f"{event_class.__name__} should be a class"
            # Verify it has Pydantic model attributes
            assert hasattr(event_class, "model_fields"), (
                f"{event_class.__name__} should be a Pydantic model"
            )

    def test_trading_event_exports(self) -> None:
        """Test that trading flow events are properly exported."""
        from the_alchemiser.shared.events import (
            RebalancePlanned,
            SignalGenerated,
            TradeExecuted,
            TradeExecutionStarted,
        )

        # All should be classes that inherit from BaseEvent
        trading_events = [
            SignalGenerated,
            RebalancePlanned,
            TradeExecuted,
            TradeExecutionStarted,
        ]

        for event_class in trading_events:
            assert isinstance(event_class, type), f"{event_class.__name__} should be a class"
            # Verify it has Pydantic model attributes
            assert hasattr(event_class, "model_fields"), (
                f"{event_class.__name__} should be a Pydantic model"
            )

    def test_state_management_event_exports(self) -> None:
        """Test that state management events are properly exported."""
        from the_alchemiser.shared.events import (
            AllocationComparisonCompleted,
            PortfolioStateChanged,
        )

        state_events = [PortfolioStateChanged, AllocationComparisonCompleted]

        for event_class in state_events:
            assert isinstance(event_class, type), f"{event_class.__name__} should be a class"
            assert hasattr(event_class, "model_fields"), (
                f"{event_class.__name__} should be a Pydantic model"
            )

    def test_execution_coordination_event_exports(self) -> None:
        """Test that execution coordination events are properly exported."""
        from the_alchemiser.shared.events import (
            BulkSettlementCompleted,
            ExecutionPhaseCompleted,
            OrderSettlementCompleted,
        )

        execution_events = [
            ExecutionPhaseCompleted,
            OrderSettlementCompleted,
            BulkSettlementCompleted,
        ]

        for event_class in execution_events:
            assert isinstance(event_class, type), f"{event_class.__name__} should be a class"
            assert hasattr(event_class, "model_fields"), (
                f"{event_class.__name__} should be a Pydantic model"
            )

    def test_notification_event_exports(self) -> None:
        """Test that notification events are properly exported."""
        from the_alchemiser.shared.events import (
            ErrorNotificationRequested,
            SystemNotificationRequested,
            TradingNotificationRequested,
        )

        notification_events = [
            ErrorNotificationRequested,
            TradingNotificationRequested,
            SystemNotificationRequested,
        ]

        for event_class in notification_events:
            assert isinstance(event_class, type), f"{event_class.__name__} should be a class"
            assert hasattr(event_class, "model_fields"), (
                f"{event_class.__name__} should be a Pydantic model"
            )

    def test_no_unintended_exports(self) -> None:
        """Test that only intended items are exported (no namespace pollution)."""
        from the_alchemiser.shared import events

        # Get all public symbols (excluding dunder attributes)
        public_symbols = [name for name in dir(events) if not name.startswith("_")]

        # Get __all__
        declared_exports = set(events.__all__)

        # Public symbols should only include __all__ items (and no extras)
        extra_exports = set(public_symbols) - declared_exports

        # Allow module-level metadata that Python adds automatically
        allowed_extras = {
            "annotations",  # from __future__ import annotations
            # Submodules (Python makes these visible even if not in __all__)
            "base",
            "bus",
            "handlers",
            "schemas",
            "dsl_events",  # DSL events module (not exported in __all__)
        }

        unexpected_exports = extra_exports - allowed_extras

        assert not unexpected_exports, (
            f"Module exports unexpected symbols: {unexpected_exports}. "
            f"These should either be added to __all__ or made private with _ prefix."
        )

    def test_module_docstring(self) -> None:
        """Test that module has proper docstring with business unit."""
        from the_alchemiser.shared import events

        # Verify module docstring exists
        assert events.__doc__ is not None, "Module should have a docstring"
        assert len(events.__doc__) > 0, "Module docstring should not be empty"

        # Verify business unit identifier in docstring
        assert "Business Unit: shared" in events.__doc__, (
            "Module docstring should contain 'Business Unit: shared'"
        )
        assert "Status: current" in events.__doc__, (
            "Module docstring should contain 'Status: current'"
        )

        # Verify module purpose is documented
        assert "event" in events.__doc__.lower(), (
            "Module docstring should mention 'event' or related terms"
        )

    def test_type_preservation(self) -> None:
        """Test that type information is preserved through re-exports."""
        from the_alchemiser.shared import events
        from the_alchemiser.shared.events.base import BaseEvent as SourceBaseEvent
        from the_alchemiser.shared.events.bus import EventBus as SourceEventBus
        from the_alchemiser.shared.events.handlers import EventHandler as SourceEventHandler
        from the_alchemiser.shared.events.schemas import SignalGenerated as SourceSignalGenerated

        # Verify infrastructure classes are the same objects (not copies)
        assert events.BaseEvent is SourceBaseEvent, (
            "Re-exported BaseEvent should be the same object as source"
        )
        assert events.EventBus is SourceEventBus, (
            "Re-exported EventBus should be the same object as source"
        )
        assert events.EventHandler is SourceEventHandler, (
            "Re-exported EventHandler should be the same object as source"
        )

        # Verify event schemas are the same objects
        assert events.SignalGenerated is SourceSignalGenerated, (
            "Re-exported SignalGenerated should be the same object as source"
        )

    def test_repeated_imports_same_object(self) -> None:
        """Test that repeated imports return the same class objects."""
        from the_alchemiser.shared.events import BaseEvent as BaseEvent1
        from the_alchemiser.shared.events import BaseEvent as BaseEvent2
        from the_alchemiser.shared.events import EventBus as EventBus1
        from the_alchemiser.shared.events import EventBus as EventBus2

        # Verify they are the exact same objects
        assert BaseEvent1 is BaseEvent2, "Repeated BaseEvent imports should return same object"
        assert EventBus1 is EventBus2, "Repeated EventBus imports should return same object"

    def test_event_schemas_have_schema_version(self) -> None:
        """Test that all exported event schemas have schema_version field."""
        from the_alchemiser.shared import events

        # Get all event classes (exclude infrastructure)
        event_classes = [
            getattr(events, name)
            for name in events.__all__
            if name not in {"BaseEvent", "EventBus", "EventHandler"}
        ]

        for event_class in event_classes:
            # Check that the class has model_fields (it's a Pydantic model)
            assert hasattr(event_class, "model_fields"), (
                f"{event_class.__name__} should be a Pydantic model"
            )

            # Check that schema_version is in the model fields
            assert "schema_version" in event_class.model_fields, (
                f"{event_class.__name__} should have schema_version field"
            )

    def test_event_schemas_inherit_from_base_event(self) -> None:
        """Test that all exported event schemas inherit from BaseEvent."""
        from the_alchemiser.shared import events

        base_event = events.BaseEvent

        # Get all event classes (exclude infrastructure)
        event_classes = [
            getattr(events, name)
            for name in events.__all__
            if name not in {"BaseEvent", "EventBus", "EventHandler"}
        ]

        for event_class in event_classes:
            # Check that the class is a subclass of BaseEvent
            assert issubclass(event_class, base_event), (
                f"{event_class.__name__} should inherit from BaseEvent"
            )

    def test_base_event_has_correlation_fields(self) -> None:
        """Test that BaseEvent includes required correlation tracking fields."""
        from the_alchemiser.shared.events import BaseEvent

        # Verify correlation tracking fields exist
        assert "correlation_id" in BaseEvent.model_fields, (
            "BaseEvent should have correlation_id field"
        )
        assert "causation_id" in BaseEvent.model_fields, "BaseEvent should have causation_id field"
        assert "event_id" in BaseEvent.model_fields, "BaseEvent should have event_id field"
        assert "event_type" in BaseEvent.model_fields, "BaseEvent should have event_type field"
        assert "timestamp" in BaseEvent.model_fields, "BaseEvent should have timestamp field"

    def test_event_bus_has_required_methods(self) -> None:
        """Test that EventBus has all required methods for pub/sub."""
        from the_alchemiser.shared.events import EventBus

        # Verify EventBus has required methods
        required_methods = [
            "publish",
            "subscribe",
            "subscribe_global",
            "unsubscribe",
            "unsubscribe_global",
            "get_handler_count",
            "get_event_count",
            "clear_handlers",
            "get_stats",
        ]

        for method_name in required_methods:
            assert hasattr(EventBus, method_name), f"EventBus should have {method_name} method"
            assert callable(getattr(EventBus, method_name)), (
                f"EventBus.{method_name} should be callable"
            )

    def test_module_has_no_import_side_effects(self) -> None:
        """Test that importing the module does not trigger side effects."""
        import sys

        # Remove the module from cache if it exists
        module_name = "the_alchemiser.shared.events"
        original_module = sys.modules[module_name] if module_name in sys.modules else None

        try:
            # Force re-import
            if module_name in sys.modules:
                del sys.modules[module_name]

            # Import should not raise any exceptions or trigger I/O
            from the_alchemiser.shared import events

            # Verify module was imported successfully
            assert events is not None
            assert hasattr(events, "__all__")

        finally:
            # Restore original module state
            if original_module is not None:
                sys.modules[module_name] = original_module


class TestEventBusIntegration:
    """Integration tests for EventBus exported from __init__."""

    def test_can_create_event_bus_instance(self) -> None:
        """Test that EventBus can be instantiated from the main export."""
        from the_alchemiser.shared.events import EventBus

        bus = EventBus()
        assert bus is not None
        assert isinstance(bus, EventBus)

    def test_can_create_and_publish_event(self) -> None:
        """Test basic event creation and publishing through exported classes."""
        from datetime import datetime

        from the_alchemiser.shared.events import BaseEvent, EventBus

        # Create event bus
        bus = EventBus()

        # Create a simple event
        event = BaseEvent(
            correlation_id="test-correlation-123",
            causation_id="test-causation-456",
            event_id="test-event-789",
            event_type="TestEvent",
            timestamp=datetime.now(UTC),
            source_module="test_module",
        )

        # Should be able to publish without errors
        bus.publish(event)

        # Verify event count increased
        assert bus.get_event_count() == 1


class TestEventSchemaExports:
    """Tests for specific event schema exports."""

    def test_signal_generated_event_structure(self) -> None:
        """Test that SignalGenerated event has expected structure."""
        from the_alchemiser.shared.events import SignalGenerated

        # Verify required fields exist
        required_fields = {
            "correlation_id",
            "causation_id",
            "event_id",
            "event_type",
            "timestamp",
            "source_module",
            "schema_version",
            "signals_data",
            "consolidated_portfolio",
            "signal_count",
        }

        actual_fields = set(SignalGenerated.model_fields.keys())

        assert required_fields.issubset(actual_fields), (
            f"SignalGenerated missing required fields: {required_fields - actual_fields}"
        )

    def test_rebalance_planned_event_structure(self) -> None:
        """Test that RebalancePlanned event has expected structure."""
        from the_alchemiser.shared.events import RebalancePlanned

        # Verify required fields exist
        required_fields = {
            "correlation_id",
            "causation_id",
            "event_id",
            "event_type",
            "timestamp",
            "source_module",
            "schema_version",
            "rebalance_plan",
            "allocation_comparison",
            "trades_required",
        }

        actual_fields = set(RebalancePlanned.model_fields.keys())

        assert required_fields.issubset(actual_fields), (
            f"RebalancePlanned missing required fields: {required_fields - actual_fields}"
        )

    def test_trade_executed_event_structure(self) -> None:
        """Test that TradeExecuted event has expected structure."""
        from the_alchemiser.shared.events import TradeExecuted

        # Verify required fields exist
        required_fields = {
            "correlation_id",
            "causation_id",
            "event_id",
            "event_type",
            "timestamp",
            "source_module",
            "schema_version",
            "execution_data",
            "success",
            "orders_placed",
            "orders_succeeded",
        }

        actual_fields = set(TradeExecuted.model_fields.keys())

        assert required_fields.issubset(actual_fields), (
            f"TradeExecuted missing required fields: {required_fields - actual_fields}"
        )
