#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

In-memory event-driven test harness for DSL engine testing.

Provides mock implementations of event-driven infrastructure components
for controlled testing of the DSL engine without external dependencies.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any
from unittest.mock import Mock

from the_alchemiser.shared.dto.strategy_allocation_dto import StrategyAllocationDTO
from the_alchemiser.shared.dto.trace_dto import TraceDTO
from the_alchemiser.shared.events.base import BaseEvent
from the_alchemiser.shared.events.bus import EventBus
from the_alchemiser.shared.events.dsl_events import (
    PortfolioAllocationProduced,
    StrategyEvaluated,
    StrategyEvaluationRequested,
)
from the_alchemiser.shared.events.handlers import EventHandler
from the_alchemiser.shared.types.market_data_port import MarketDataPort
from the_alchemiser.strategy_v2.engines.dsl.engine import DslEngine

from ..utils.dsl_test_utils import MockMarketDataService


class DslTestHarness:
    """Test harness for DSL engine with event-driven mock infrastructure."""

    def __init__(
        self,
        repository_root: str,
        mock_market_data: MockMarketDataService | None = None,
        seed: int = 42,
    ) -> None:
        """Initialize DSL test harness."""
        self.repository_root = repository_root
        self.seed = seed

        # Initialize event infrastructure
        self.event_bus = EventBus()
        self.event_recorder = EventRecorder()
        self.event_bus.subscribe_global(self.event_recorder)

        # Initialize mock market data service
        self.mock_market_data = mock_market_data or MockMarketDataService(seed=seed)

        # Initialize DSL engine with mocked dependencies
        strategies_path = f"{repository_root}/the_alchemiser/strategy_v2/strategies"
        self.dsl_engine = DslEngine(
            strategy_config_path=strategies_path,
            event_bus=self.event_bus,
            market_data_service=self._create_mock_market_data_port(),
        )

        # Subscribe DSL engine to evaluation requests
        self.event_bus.subscribe("StrategyEvaluationRequested", self.dsl_engine)

        # Track virtual time for deterministic testing
        self.virtual_time = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)

    def _create_mock_market_data_port(self) -> MarketDataPort:
        """Create a mock MarketDataPort for testing."""
        mock_port = Mock(spec=MarketDataPort)

        # Configure mock methods to use our mock market data service
        def mock_get_mid_price(symbol):
            symbol_str = str(symbol) if hasattr(symbol, "__str__") else symbol
            return self.mock_market_data.get_current_price(symbol_str)

        def mock_get_latest_quote(symbol):
            # Return a simple mock quote
            symbol_str = str(symbol) if hasattr(symbol, "__str__") else symbol
            price = self.mock_market_data.get_current_price(symbol_str)
            return Mock(bid=price * 0.999, ask=price * 1.001, mid=price)

        def mock_get_bars(symbol, period, timeframe):
            # Generate realistic historical bar data for technical indicators
            import random
            from datetime import timedelta

            from the_alchemiser.shared.types.market_data import BarModel

            symbol_str = str(symbol) if hasattr(symbol, "__str__") else symbol
            base_price = self.mock_market_data.get_current_price(symbol_str)

            # Check if we have a custom RSI value for this symbol
            custom_rsi_key = (symbol_str, "rsi")
            target_rsi = None
            if custom_rsi_key in self.mock_market_data._custom_indicators:
                target_rsi = self.mock_market_data._custom_indicators[custom_rsi_key]

            # Generate 252 days of data (1 year) for sufficient RSI calculation
            bars = []
            current_date = self.virtual_time
            random_gen = random.Random(self.seed + hash(symbol_str))

            # Start with slightly lower price to show progression
            current_price = base_price * 0.95

            for i in range(252):
                if (
                    target_rsi is not None and i >= 240
                ):  # Last 12 days - create trend for target RSI
                    if target_rsi > 70:  # Want high RSI - create upward trend
                        daily_change = random_gen.uniform(
                            0.005, 0.02
                        )  # Positive movement
                    elif target_rsi < 30:  # Want low RSI - create downward trend
                        daily_change = random_gen.uniform(
                            -0.02, -0.005
                        )  # Negative movement
                    else:  # Want neutral RSI - balanced movement
                        daily_change = random_gen.uniform(-0.01, 0.01)
                else:
                    # Generate normal price movement for early data
                    daily_change = random_gen.uniform(-0.03, 0.03)  # ±3% daily movement

                current_price *= 1 + daily_change

                # Ensure price stays positive
                current_price = max(current_price, 1.0)

                # Generate OHLC from close price
                volatility = random_gen.uniform(
                    0.005, 0.02
                )  # 0.5% to 2% intraday range
                high = current_price * (1 + volatility)
                low = current_price * (1 - volatility)
                open_price = current_price * random_gen.uniform(0.99, 1.01)

                bar = BarModel(
                    symbol=symbol_str,
                    timestamp=current_date - timedelta(days=252 - i),
                    open=open_price,
                    high=high,
                    low=low,
                    close=current_price,
                    volume=random_gen.randint(100000, 10000000),
                )
                bars.append(bar)

            return bars

        mock_port.get_mid_price.side_effect = mock_get_mid_price
        mock_port.get_latest_quote.side_effect = mock_get_latest_quote
        mock_port.get_bars.side_effect = mock_get_bars

        return mock_port

    def evaluate_strategy(
        self,
        strategy_file_path: str,
        strategy_id: str | None = None,
        universe: list[str] | None = None,
        correlation_id: str | None = None,
    ) -> DslTestResult:
        """Evaluate a strategy and return test results."""
        # Clear previous events
        self.event_recorder.clear()

        # Generate IDs if not provided
        strategy_id = strategy_id or f"test-strategy-{uuid.uuid4().hex[:8]}"
        correlation_id = correlation_id or f"test-corr-{uuid.uuid4().hex[:8]}"

        # Create evaluation request event
        request_event = StrategyEvaluationRequested(
            event_id=str(uuid.uuid4()),
            event_type="StrategyEvaluationRequested",
            timestamp=self.virtual_time,
            correlation_id=correlation_id,
            causation_id=str(uuid.uuid4()),  # Required field
            source_module="test_harness",  # Required field
            source_component="DslTestHarness",
            strategy_id=strategy_id,
            strategy_config_path=strategy_file_path,
            universe=universe or [],
        )

        # Publish the request
        self.event_bus.publish(request_event)

        # Collect results
        return DslTestResult(
            request_event=request_event,
            all_events=self.event_recorder.events.copy(),
            evaluation_events=self.event_recorder.get_events_by_type(
                "StrategyEvaluated"
            ),
            allocation_events=self.event_recorder.get_events_by_type(
                "PortfolioAllocationProduced"
            ),
            correlation_id=correlation_id,
            strategy_id=strategy_id,
        )

    def advance_virtual_time(self, seconds: int) -> None:
        """Advance virtual time for time-based testing."""
        from datetime import timedelta

        self.virtual_time += timedelta(seconds=seconds)

    def reset_state(self) -> None:
        """Reset harness state for clean testing."""
        self.event_recorder.clear()
        self.mock_market_data.reset_cache()
        self.virtual_time = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)

    def inject_market_conditions(self, conditions: dict[str, Any]) -> None:
        """Inject specific market conditions for scenario testing."""
        # Update mock market data based on conditions
        if "price_changes" in conditions:
            for symbol, price in conditions["price_changes"].items():
                self.mock_market_data._price_cache[symbol] = price

        if "indicator_overrides" in conditions:
            for (symbol, indicator_type, params), value in conditions[
                "indicator_overrides"
            ].items():
                cache_key = (symbol, indicator_type, tuple(sorted(params.items())))
                # Create mock indicator DTO
                from the_alchemiser.shared.dto.technical_indicators_dto import (
                    TechnicalIndicatorDTO,
                )

                self.mock_market_data._indicator_cache[cache_key] = (
                    TechnicalIndicatorDTO(
                        symbol=symbol,
                        indicator_type=indicator_type,
                        value=value,
                        timestamp=self.virtual_time,
                        parameters=params,
                        metadata={},
                    )
                )

        if "rsi_values" in conditions:
            for symbol, rsi_value in conditions["rsi_values"].items():
                self.mock_market_data.set_rsi(symbol, rsi_value)


class EventRecorder(EventHandler):
    """Event handler that records all events for analysis."""

    def __init__(self) -> None:
        """Initialize the event recorder."""
        self.events: list[BaseEvent] = []
        self.event_counts: dict[str, int] = {}
        self.events_by_type: dict[str, list[BaseEvent]] = {}

    def handle_event(self, event: BaseEvent) -> None:
        """Record an event."""
        self.events.append(event)
        self.event_counts[event.event_type] = (
            self.event_counts.get(event.event_type, 0) + 1
        )

        if event.event_type not in self.events_by_type:
            self.events_by_type[event.event_type] = []
        self.events_by_type[event.event_type].append(event)

    def can_handle(self, event_type: str) -> bool:
        """Handle all event types."""
        return True

    def clear(self) -> None:
        """Clear all recorded events."""
        self.events.clear()
        self.event_counts.clear()
        self.events_by_type.clear()

    def get_events_by_type(self, event_type: str) -> list[BaseEvent]:
        """Get all events of a specific type."""
        return self.events_by_type.get(event_type, [])

    def get_events_by_correlation_id(self, correlation_id: str) -> list[BaseEvent]:
        """Get all events with a specific correlation ID."""
        return [
            event for event in self.events if event.correlation_id == correlation_id
        ]


class DslTestResult:
    """Result container for DSL engine test evaluation."""

    def __init__(
        self,
        request_event: StrategyEvaluationRequested,
        all_events: list[BaseEvent],
        evaluation_events: list[BaseEvent],
        allocation_events: list[BaseEvent],
        correlation_id: str,
        strategy_id: str,
    ) -> None:
        """Initialize test result."""
        self.request_event = request_event
        self.all_events = all_events
        self.evaluation_events = evaluation_events
        self.allocation_events = allocation_events
        self.correlation_id = correlation_id
        self.strategy_id = strategy_id

    @property
    def success(self) -> bool:
        """Check if strategy evaluation was successful."""
        return len(self.evaluation_events) > 0 or len(self.allocation_events) > 0

    @property
    def allocation_result(self) -> StrategyAllocationDTO | None:
        """Get the strategy allocation result if available."""
        for event in self.allocation_events:
            if isinstance(event, PortfolioAllocationProduced):
                return event.allocation
        return None

    @property
    def trace_result(self) -> TraceDTO | None:
        """Get the trace result if available."""
        for event in self.evaluation_events:
            if isinstance(event, StrategyEvaluated):
                return event.trace
        return None

    def get_event_summary(self) -> dict[str, Any]:
        """Get a summary of all events for this test."""
        event_counts = {}
        for event in self.all_events:
            event_counts[event.event_type] = event_counts.get(event.event_type, 0) + 1

        return {
            "total_events": len(self.all_events),
            "event_counts": event_counts,
            "success": self.success,
            "has_allocation": self.allocation_result is not None,
            "has_trace": self.trace_result is not None,
            "correlation_id": self.correlation_id,
            "strategy_id": self.strategy_id,
        }

    def to_snapshot_data(self) -> dict[str, Any]:
        """Convert test result to snapshot data for golden testing."""
        data = {
            "request": {
                "strategy_id": self.strategy_id,
                "correlation_id": self.correlation_id,
                "timestamp": self.request_event.timestamp.isoformat(),
                "strategy_config_path": self.request_event.strategy_config_path,
                "universe": self.request_event.universe,
            },
            "summary": self.get_event_summary(),
            "events": [],
        }

        # Add event details (excluding sensitive timestamps for deterministic comparison)
        for event in self.all_events:
            event_data = {
                "event_type": event.event_type,
                "correlation_id": event.correlation_id,
                "source_module": event.source_module,
            }

            # Add type-specific data
            if isinstance(event, StrategyEvaluated) or isinstance(event, PortfolioAllocationProduced):
                if event.allocation:
                    event_data["allocation"] = {
                        "allocations": {
                            k: float(v)
                            for k, v in event.allocation.target_weights.items()
                        },
                        "total_allocation": float(
                            sum(event.allocation.target_weights.values())
                        ),
                        "correlation_id": event.allocation.correlation_id,
                    }

            data["events"].append(event_data)

        # Add allocation data to main level if available
        if self.allocation_result:
            data["allocation"] = {
                "allocations": {
                    k: float(v)
                    for k, v in self.allocation_result.target_weights.items()
                },
                "total_allocation": float(
                    sum(self.allocation_result.target_weights.values())
                ),
                "correlation_id": self.allocation_result.correlation_id,
            }

        return data


class MockIndicatorService:
    """Mock indicator service for testing without real market data."""

    def __init__(self, market_data_service: MockMarketDataService) -> None:
        """Initialize mock indicator service."""
        self.market_data_service = market_data_service

    def compute_indicator(
        self, symbol: str, indicator_type: str, params: dict[str, Any] | None = None
    ) -> float:
        """Compute mock indicator value."""
        indicator_dto = self.market_data_service.get_indicator(
            symbol, indicator_type, params
        )
        return indicator_dto.value
