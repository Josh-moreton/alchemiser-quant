"""Business Unit: portfolio | Status: current

Test portfolio analysis handler for event-driven architecture.

Tests that the handler correctly processes SignalGenerated events,
handles errors gracefully, and emits appropriate events.
"""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import Mock
from uuid import uuid4

import pytest

from the_alchemiser.portfolio_v2.handlers.portfolio_analysis_handler import (
    PortfolioAnalysisHandler,
    _build_positions_dict,
    _normalize_account_info,
    _to_decimal_safe,
)
from the_alchemiser.shared.errors.exceptions import (
    DataProviderError,
    NegativeCashBalanceError,
    PortfolioError,
)
from the_alchemiser.shared.events import (
    BaseEvent,
    SignalGenerated,
    WorkflowFailed,
)


class TestHelperFunctions:
    """Test helper functions used in portfolio analysis."""

    def test_to_decimal_safe_with_number(self):
        """Test converting numeric values to Decimal."""
        assert _to_decimal_safe(42) == Decimal("42")
        assert _to_decimal_safe(3.14) == Decimal("3.14")
        assert _to_decimal_safe("123.45") == Decimal("123.45")

    def test_to_decimal_safe_with_object_value_attribute(self):
        """Test converting object with value attribute."""
        obj = Mock()
        obj.value = 99.9
        assert _to_decimal_safe(obj) == Decimal("99.9")

    def test_to_decimal_safe_with_invalid_value(self):
        """Test converting invalid values returns Decimal 0."""
        assert _to_decimal_safe(None) == Decimal("0")
        assert _to_decimal_safe("invalid") == Decimal("0")
        assert _to_decimal_safe({}) == Decimal("0")

    def test_normalize_account_info_from_dict(self):
        """Test normalizing account info from dictionary."""
        account_dict = {
            "cash": "1000.50",
            "buying_power": "2000.75",
            "portfolio_value": "5000.25",
        }
        result = _normalize_account_info(account_dict)
        assert result["cash"] == Decimal("1000.50")
        assert result["buying_power"] == Decimal("2000.75")
        assert result["portfolio_value"] == Decimal("5000.25")

    def test_normalize_account_info_from_object(self):
        """Test normalizing account info from SDK object."""
        account_obj = Mock()
        account_obj.cash = 1500.0
        account_obj.buying_power = 3000.0
        account_obj.portfolio_value = 7500.0

        result = _normalize_account_info(account_obj)
        assert result["cash"] == Decimal("1500.0")
        assert result["buying_power"] == Decimal("3000.0")
        assert result["portfolio_value"] == Decimal("7500.0")

    def test_normalize_account_info_raises_on_zero_cash(self):
        """Test normalizing account info raises error for zero or negative cash."""
        account_dict = {"cash": 0, "buying_power": 1000, "portfolio_value": 1000}
        with pytest.raises(NegativeCashBalanceError):
            _normalize_account_info(account_dict)

        account_dict_negative = {"cash": -100, "buying_power": 1000, "portfolio_value": 1000}
        with pytest.raises(NegativeCashBalanceError):
            _normalize_account_info(account_dict_negative)

    def test_build_positions_dict(self):
        """Test building positions dictionary from position list."""
        pos1 = Mock()
        pos1.symbol = "AAPL"
        pos1.market_value = 5000.0

        pos2 = Mock()
        pos2.symbol = "GOOGL"
        pos2.market_value = 3000.0

        positions = [pos1, pos2]
        result = _build_positions_dict(positions)

        assert result["AAPL"] == Decimal("5000.0")
        assert result["GOOGL"] == Decimal("3000.0")

    def test_build_positions_dict_empty_list(self):
        """Test building positions dict from empty list."""
        result = _build_positions_dict([])
        assert result == {}

    def test_build_positions_dict_with_invalid_position(self):
        """Test positions without required attributes are skipped."""
        pos1 = Mock()
        pos1.symbol = "AAPL"
        pos1.market_value = 5000.0

        pos2 = Mock(spec=[])  # No attributes

        positions = [pos1, pos2]
        result = _build_positions_dict(positions)

        assert len(result) == 1
        assert result["AAPL"] == 5000.0


class TestPortfolioAnalysisHandler:
    """Test PortfolioAnalysisHandler event processing."""

    @pytest.fixture
    def mock_container(self):
        """Create mock application container."""
        container = Mock()

        # Mock event bus
        mock_event_bus = Mock()
        container.services.event_bus.return_value = mock_event_bus

        # Mock infrastructure
        mock_alpaca = Mock()
        container.infrastructure.alpaca_manager.return_value = mock_alpaca

        return container

    @pytest.fixture
    def handler(self, mock_container):
        """Create handler instance."""
        return PortfolioAnalysisHandler(mock_container)

    @pytest.fixture
    def sample_signal_event(self):
        """Create sample SignalGenerated event."""
        correlation_id = str(uuid4())

        return SignalGenerated(
            event_id=str(uuid4()),
            correlation_id=correlation_id,
            causation_id=correlation_id,
            timestamp=datetime.now(UTC),
            source_module="test",
            signals_data={
                "signals": [
                    {
                        "symbol": "AAPL",
                        "weight": 0.6,
                        "strategy": "momentum",
                    },
                    {
                        "symbol": "GOOGL",
                        "weight": 0.4,
                        "strategy": "value",
                    },
                ],
                "strategy_allocations": {
                    "momentum": 0.6,
                    "value": 0.4,
                },
            },
            consolidated_portfolio={
                "target_allocations": {
                    "AAPL": 0.6,
                    "GOOGL": 0.4,
                },
                "metadata": {},
            },
            signal_count=2,
        )

    def test_handler_initialization(self, handler, mock_container):
        """Test handler is initialized correctly."""
        assert handler.container == mock_container
        assert handler.event_bus is not None
        assert handler.logger is not None

    def test_can_handle_signal_generated(self, handler):
        """Test handler can handle SignalGenerated event type."""
        assert handler.can_handle("SignalGenerated") is True

    def test_can_handle_other_event_types(self, handler):
        """Test handler rejects other event types."""
        assert handler.can_handle("RebalancePlanned") is False
        assert handler.can_handle("TradeExecuted") is False

    def test_handle_event_ignores_non_signal_events(self, handler):
        """Test handler ignores non-SignalGenerated events."""
        other_event = Mock(spec=BaseEvent)
        other_event.event_type = "SomeOtherEvent"

        # Should not raise exception
        handler.handle_event(other_event)

    def test_extract_strategy_names_from_signals(self, handler, sample_signal_event):
        """Test extracting strategy names from signals data."""
        strategy_names = handler._extract_strategy_names_from_event(sample_signal_event)

        assert "momentum" in strategy_names
        assert "value" in strategy_names
        assert len(strategy_names) == 2

    def test_extract_strategy_names_from_allocations(self, handler):
        """Test extracting strategy names from allocations as fallback."""
        event = SignalGenerated(
            event_id=str(uuid4()),
            correlation_id=str(uuid4()),
            causation_id=str(uuid4()),
            timestamp=datetime.now(UTC),
            source_module="test",
            signals_data={
                "strategy_allocations": {
                    "trend": 0.5,
                    "mean_reversion": 0.5,
                },
            },
            consolidated_portfolio={"target_allocations": {}},
            signal_count=0,
        )

        strategy_names = handler._extract_strategy_names_from_event(event)

        assert "trend" in strategy_names
        assert "mean_reversion" in strategy_names

    def test_extract_strategy_names_fallback_to_unknown(self, handler):
        """Test fallback to 'unknown' when no strategy names found."""
        event = SignalGenerated(
            event_id=str(uuid4()),
            correlation_id=str(uuid4()),
            causation_id=str(uuid4()),
            timestamp=datetime.now(UTC),
            source_module="test",
            signals_data={},
            consolidated_portfolio={"target_allocations": {}},
            signal_count=0,
        )

        strategy_names = handler._extract_strategy_names_from_event(event)

        assert strategy_names == ["unknown"]

    def test_extract_from_signals_with_valid_data(self, handler):
        """Test extracting strategy names from valid signals list."""
        signals_data = {
            "signals": [
                {"strategy": "momentum", "symbol": "AAPL"},
                {"strategy": "value", "symbol": "GOOGL"},
                {"strategy": "momentum", "symbol": "MSFT"},  # Duplicate
            ],
        }

        result = handler._extract_from_signals(signals_data)

        assert "momentum" in result
        assert "value" in result
        assert len(result) == 2  # No duplicates

    def test_extract_from_signals_with_missing_strategy_key(self, handler):
        """Test handling signals without strategy key."""
        signals_data = {
            "signals": [
                {"symbol": "AAPL"},  # No strategy key
            ],
        }

        result = handler._extract_from_signals(signals_data)

        assert result == []

    def test_extract_from_signals_with_invalid_data(self, handler):
        """Test handling invalid signals data structures."""
        assert handler._extract_from_signals(None) == []
        assert handler._extract_from_signals({}) == []
        assert handler._extract_from_signals({"signals": "not a list"}) == []

    def test_extract_from_strategy_allocations_with_valid_data(self, handler):
        """Test extracting strategy names from allocations."""
        signals_data = {
            "strategy_allocations": {
                "growth": 0.5,
                "defensive": 0.5,
            },
        }

        result = handler._extract_from_strategy_allocations(signals_data)

        assert "growth" in result
        assert "defensive" in result

    def test_extract_from_strategy_allocations_with_invalid_data(self, handler):
        """Test handling invalid strategy allocations."""
        assert handler._extract_from_strategy_allocations(None) == []
        assert handler._extract_from_strategy_allocations({}) == []
        assert (
            handler._extract_from_strategy_allocations({"strategy_allocations": "not dict"}) == []
        )

    def test_get_comprehensive_account_data_success(self, handler, mock_container):
        """Test successful retrieval of account data."""
        mock_alpaca = mock_container.infrastructure.alpaca_manager.return_value

        # Setup mock account info
        mock_account = Mock()
        mock_account.cash = 10000.0
        mock_account.buying_power = 20000.0
        mock_account.portfolio_value = 30000.0
        mock_alpaca.get_account.return_value = mock_account

        # Setup mock positions
        mock_position = Mock()
        mock_position.symbol = "AAPL"
        mock_position.market_value = 5000.0
        mock_alpaca.get_positions.return_value = [mock_position]

        # Setup mock orders
        mock_order = Mock()
        mock_order.id = "order-123"
        mock_order.symbol = "GOOGL"
        mock_order.side = "buy"
        mock_order.qty = 10
        mock_alpaca.get_orders.return_value = [mock_order]

        result = handler._get_comprehensive_account_data()

        assert result is not None
        assert result["account_info"]["cash"] == Decimal("10000.0")
        assert result["current_positions"]["AAPL"] == Decimal("5000.0")
        assert len(result["open_orders"]) == 1
        assert result["open_orders"][0]["symbol"] == "GOOGL"

    def test_get_comprehensive_account_data_no_account(self, handler, mock_container):
        """Test handling when account info cannot be retrieved."""
        mock_alpaca = mock_container.infrastructure.alpaca_manager.return_value
        mock_alpaca.get_account.return_value = None

        with pytest.raises(DataProviderError):
            handler._get_comprehensive_account_data()

    def test_get_comprehensive_account_data_exception(self, handler, mock_container):
        """Test handling exceptions during account data retrieval."""
        mock_alpaca = mock_container.infrastructure.alpaca_manager.return_value
        mock_alpaca.get_account.side_effect = Exception("API error")

        with pytest.raises(DataProviderError):
            handler._get_comprehensive_account_data()

    def test_handle_event_with_exception_calls_emit_failure(self, handler, mock_container):
        """Test that exceptions during event handling trigger failure emission logic."""
        # Create a minimal valid event
        event = SignalGenerated(
            event_id=str(uuid4()),
            correlation_id=str(uuid4()),
            causation_id=str(uuid4()),
            timestamp=datetime.now(UTC),
            source_module="test",
            signals_data={"signals": []},
            consolidated_portfolio={
                "target_allocations": {"AAPL": "0.5", "GOOGL": "0.5"},
                "correlation_id": str(uuid4()),
                "timestamp": datetime.now(UTC),
                "strategy_count": 1,
            },
            signal_count=0,
        )

        # Force an exception during processing
        mock_alpaca = mock_container.infrastructure.alpaca_manager.return_value
        mock_alpaca.get_account.side_effect = Exception("Test error")

        # Mock is_workflow_failed to return False so emission isn't skipped
        mock_event_bus = mock_container.services.event_bus.return_value
        mock_event_bus.is_workflow_failed.return_value = False

        # Track emitted events
        emitted_events = []
        handler.event_bus.publish = lambda event: emitted_events.append(event)

        # Handle event - should raise PortfolioError
        with pytest.raises(PortfolioError):
            handler.handle_event(event)

        # Verify WorkflowFailed was emitted
        assert len(emitted_events) == 1
        assert isinstance(emitted_events[0], WorkflowFailed)
        assert emitted_events[0].failure_reason  # Verify it's not empty


class TestPortfolioAnalysisHandlerErrorPaths:
    """Test error handling paths in portfolio analysis handler."""

    @pytest.fixture
    def mock_container(self):
        """Create mock application container."""
        container = Mock()
        mock_event_bus = Mock()
        container.services.event_bus.return_value = mock_event_bus
        mock_alpaca = Mock()
        container.infrastructure.alpaca_manager.return_value = mock_alpaca
        return container

    @pytest.fixture
    def handler(self, mock_container):
        """Create handler instance."""
        return PortfolioAnalysisHandler(mock_container)

    def test_handle_signal_with_missing_account_data(self, handler, mock_container):
        """Test handling SignalGenerated when account data is missing."""
        mock_alpaca = mock_container.infrastructure.alpaca_manager.return_value
        mock_alpaca.get_account.return_value = None

        # Mock is_workflow_failed to return False so emission isn't skipped
        mock_event_bus = mock_container.services.event_bus.return_value
        mock_event_bus.is_workflow_failed.return_value = False

        event = SignalGenerated(
            event_id=str(uuid4()),
            correlation_id=str(uuid4()),
            causation_id=str(uuid4()),
            timestamp=datetime.now(UTC),
            source_module="test",
            signals_data={"signals": []},
            consolidated_portfolio={
                "target_allocations": {
                    "AAPL": Decimal("0.5"),
                    "GOOGL": Decimal("0.5"),
                },
                "correlation_id": str(uuid4()),
                "timestamp": datetime.now(UTC),
                "strategy_count": 1,
            },
            signal_count=0,
        )

        # Track emitted events
        emitted_events = []
        handler.event_bus.publish = lambda event: emitted_events.append(event)

        # Should raise DataProviderError
        with pytest.raises(DataProviderError):
            handler.handle_event(event)

        # Should emit WorkflowFailed
        assert len(emitted_events) == 1
        assert isinstance(emitted_events[0], WorkflowFailed)
        assert emitted_events[0].failure_reason

    def test_handle_signal_validates_consolidated_portfolio_schema(self, handler, mock_container):
        """Test handling SignalGenerated validates consolidated portfolio properly."""
        # Setup valid account data
        mock_alpaca = mock_container.infrastructure.alpaca_manager.return_value
        mock_account = Mock()
        mock_account.cash = 10000.0
        mock_account.buying_power = 20000.0
        mock_account.portfolio_value = 30000.0
        mock_alpaca.get_account.return_value = mock_account
        mock_alpaca.get_positions.return_value = []
        mock_alpaca.get_orders.return_value = []

        # Mock is_workflow_failed to return False so emission isn't skipped
        mock_event_bus = mock_container.services.event_bus.return_value
        mock_event_bus.is_workflow_failed.return_value = False

        # Create event with empty target_allocations (invalid)
        event = SignalGenerated(
            event_id=str(uuid4()),
            correlation_id=str(uuid4()),
            causation_id=str(uuid4()),
            timestamp=datetime.now(UTC),
            source_module="test",
            signals_data={"signals": []},
            consolidated_portfolio={
                "target_allocations": {},  # Empty - will fail validation
                "correlation_id": str(uuid4()),
                "timestamp": datetime.now(UTC),
                "strategy_count": 1,
            },
            signal_count=0,
        )

        # Track emitted events
        emitted_events = []
        handler.event_bus.publish = lambda event: emitted_events.append(event)

        # Should raise PortfolioError due to validation error
        with pytest.raises(PortfolioError):
            handler.handle_event(event)

        # Should emit WorkflowFailed
        assert len(emitted_events) == 1
        assert isinstance(emitted_events[0], WorkflowFailed)

    def test_idempotency_duplicate_events_skipped(self, handler, mock_container):
        """Test that duplicate events are skipped for idempotency."""
        # Setup valid account data
        mock_alpaca = mock_container.infrastructure.alpaca_manager.return_value
        mock_account = Mock()
        mock_account.cash = 10000.0
        mock_account.buying_power = 20000.0
        mock_account.portfolio_value = 30000.0
        mock_alpaca.get_account.return_value = mock_account
        mock_alpaca.get_positions.return_value = []
        mock_alpaca.get_orders.return_value = []

        # Mock is_workflow_failed to return False so emission isn't skipped
        mock_event_bus = mock_container.services.event_bus.return_value
        mock_event_bus.is_workflow_failed.return_value = False

        # Create an event with a consistent event_id
        event_id = "test-event-123"
        event = SignalGenerated(
            event_id=event_id,
            correlation_id=str(uuid4()),
            causation_id=str(uuid4()),
            timestamp=datetime.now(UTC),
            source_module="test",
            signals_data={"signals": []},
            consolidated_portfolio={
                "target_allocations": {
                    "AAPL": Decimal("0.5"),
                    "GOOGL": Decimal("0.5"),
                },
                "correlation_id": str(uuid4()),
                "timestamp": datetime.now(UTC),
                "strategy_count": 1,
            },
            signal_count=0,
        )

        # Track how many times _handle_signal_generated is called
        original_handler = handler._handle_signal_generated
        call_count = 0

        def counting_handler(event):
            nonlocal call_count
            call_count += 1
            return original_handler(event)

        handler._handle_signal_generated = counting_handler

        # Process the same event twice
        try:
            handler.handle_event(event)
        except Exception:
            pass  # First event may fail, but should still be marked as processed

        first_call_count = call_count

        # Process the same event again - should be skipped
        handler.handle_event(event)

        # Second call should NOT increment call_count (event was already processed)
        assert call_count == first_call_count, "Duplicate event should be skipped"
