#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Test utilities for DSL engine testing.

Provides utilities for strategy discovery, mock data generation,
and test scenario creation.
"""

from __future__ import annotations

import json
import random
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any
from unittest.mock import Mock

from the_alchemiser.shared.dto.technical_indicators_dto import TechnicalIndicatorDTO
from the_alchemiser.shared.events.base import BaseEvent
from the_alchemiser.shared.events.dsl_events import StrategyEvaluationRequested
from the_alchemiser.shared.types.market_data_port import MarketDataPort
from the_alchemiser.shared.value_objects.symbol import Symbol


class MockMarketDataService:
    """Mock market data service for testing DSL engine."""
    
    def __init__(self, seed: int = 42) -> None:
        """Initialize mock market data service with deterministic seed."""
        self.seed = seed
        self._random = random.Random(seed)
        self._price_cache: dict[str, float] = {}
        self._indicator_cache: dict[tuple[str, str, tuple], TechnicalIndicatorDTO] = {}
    
    def get_current_price(self, symbol: str) -> float:
        """Get mock current price for symbol."""
        if symbol not in self._price_cache:
            # Generate deterministic but realistic price
            self._price_cache[symbol] = self._random.uniform(50.0, 500.0)
        return self._price_cache[symbol]
    
    def get_indicator(
        self, 
        symbol: str, 
        indicator_type: str, 
        params: dict[str, Any] | None = None
    ) -> TechnicalIndicatorDTO:
        """Get mock technical indicator value."""
        params_tuple = tuple(sorted((params or {}).items()))
        cache_key = (symbol, indicator_type, params_tuple)
        
        if cache_key not in self._indicator_cache:
            # Generate deterministic indicator values based on type
            value = self._generate_indicator_value(indicator_type, params or {})
            
            self._indicator_cache[cache_key] = TechnicalIndicatorDTO(
                symbol=symbol,
                indicator_type=indicator_type,
                value=value,
                timestamp=datetime.now(UTC),
                parameters=params or {},
                metadata={}
            )
        
        return self._indicator_cache[cache_key]
    
    def _generate_indicator_value(self, indicator_type: str, params: dict[str, Any]) -> float:
        """Generate realistic mock indicator values."""
        # Use indicator type and params to seed deterministic values
        type_seed = hash(indicator_type) % 1000
        param_seed = hash(str(sorted(params.items()))) % 1000
        local_random = random.Random(self.seed + type_seed + param_seed)
        
        if indicator_type.lower() == "rsi":
            # RSI typically ranges 0-100
            return local_random.uniform(20.0, 80.0)
        elif indicator_type.lower() in ["sma", "ema"]:
            # Moving averages - use realistic price-like values
            return local_random.uniform(50.0, 500.0)
        elif indicator_type.lower() == "macd":
            # MACD can be positive or negative
            return local_random.uniform(-5.0, 5.0)
        elif indicator_type.lower() == "bollinger":
            # Bollinger bands - return middle band value
            return local_random.uniform(50.0, 500.0)
        else:
            # Default generic indicator value
            return local_random.uniform(0.0, 100.0)
    
    def reset_cache(self) -> None:
        """Reset all cached data."""
        self._price_cache.clear()
        self._indicator_cache.clear()


class StrategyDiscovery:
    """Utility for discovering and managing CLJ strategy files."""
    
    def __init__(self, repository_root: Path) -> None:
        """Initialize strategy discovery."""
        self.repository_root = repository_root
    
    def discover_clj_files(self) -> list[Path]:
        """Discover all CLJ strategy files in the repository."""
        clj_files = list(self.repository_root.glob("*.clj"))
        return sorted(clj_files)  # Sort for deterministic ordering
    
    def get_strategy_info(self, clj_file: Path) -> dict[str, Any]:
        """Extract strategy information from CLJ file."""
        try:
            content = clj_file.read_text(encoding="utf-8")
            
            # Extract basic info from first few lines
            lines = content.split('\n')[:10]
            
            # Try to extract strategy name from defsymphony
            strategy_name = clj_file.stem
            for line in lines:
                if line.strip().startswith('"') and "defsymphony" in content:
                    # Extract quoted strategy name
                    import re
                    match = re.search(r'"([^"]+)"', line)
                    if match:
                        strategy_name = match.group(1)
                        break
            
            return {
                "file_path": str(clj_file),
                "file_name": clj_file.name,
                "strategy_name": strategy_name,
                "file_size": clj_file.stat().st_size,
                "content_preview": content[:200] + "..." if len(content) > 200 else content
            }
        except Exception as e:
            return {
                "file_path": str(clj_file),
                "file_name": clj_file.name,
                "strategy_name": clj_file.stem,
                "error": str(e)
            }


class ScenarioGenerator:
    """Generator for different market scenarios and test cases."""
    
    def __init__(self, seed: int = 42) -> None:
        """Initialize scenario generator with deterministic seed."""
        self.seed = seed
        self._random = random.Random(seed)
    
    def generate_normal_market_scenario(self) -> dict[str, Any]:
        """Generate a normal market conditions scenario."""
        return {
            "scenario_type": "normal",
            "description": "Normal market conditions with moderate volatility",
            "duration_hours": 6,
            "symbols": ["SPY", "QQQ", "TECL", "UVXY"],
            "price_changes": {
                symbol: self._random.uniform(-0.02, 0.02)  # ±2% daily change
                for symbol in ["SPY", "QQQ", "TECL", "UVXY"]
            },
            "volatility_multiplier": 1.0,
            "events": []
        }
    
    def generate_stress_scenario(self) -> dict[str, Any]:
        """Generate a stress market conditions scenario."""
        return {
            "scenario_type": "stress",
            "description": "High volatility with significant price movements",
            "duration_hours": 2,
            "symbols": ["SPY", "QQQ", "TECL", "UVXY"],
            "price_changes": {
                symbol: self._random.uniform(-0.10, 0.10)  # ±10% change
                for symbol in ["SPY", "QQQ", "TECL", "UVXY"]
            },
            "volatility_multiplier": 3.0,
            "events": ["volatility_spike", "circuit_breaker"]
        }
    
    def generate_edge_case_scenario(self) -> dict[str, Any]:
        """Generate edge case scenario with problematic data."""
        return {
            "scenario_type": "edge",
            "description": "Edge cases with data quality issues",
            "duration_hours": 1,
            "symbols": ["SPY", "QQQ"],
            "price_changes": {},
            "volatility_multiplier": 1.0,
            "events": ["out_of_order_data", "duplicate_events", "missing_data"]
        }
    
    def generate_multi_symbol_scenario(self) -> dict[str, Any]:
        """Generate scenario testing multiple symbols simultaneously."""
        symbols = ["SPY", "QQQ", "TECL", "UVXY", "VTV", "VOX", "IOO", "TQQQ"]
        return {
            "scenario_type": "multi_symbol",
            "description": "Multi-symbol correlation scenario",
            "duration_hours": 4,
            "symbols": symbols,
            "price_changes": {
                symbol: self._random.uniform(-0.05, 0.05)
                for symbol in symbols
            },
            "volatility_multiplier": 1.5,
            "events": ["symbol_correlation"]
        }


class EventSequenceBuilder:
    """Builder for creating sequences of events for testing."""
    
    def __init__(self, correlation_id: str | None = None) -> None:
        """Initialize event sequence builder."""
        self.correlation_id = correlation_id or f"test-{uuid.uuid4().hex[:8]}"
        self.events: list[BaseEvent] = []
    
    def add_strategy_evaluation_request(
        self,
        strategy_id: str,
        strategy_config_path: str,
        universe: list[str] | None = None,
        timestamp: datetime | None = None
    ) -> EventSequenceBuilder:
        """Add a strategy evaluation request event."""
        import uuid
        
        event = StrategyEvaluationRequested(
            event_id=str(uuid.uuid4()),
            event_type="StrategyEvaluationRequested",
            timestamp=timestamp or datetime.now(UTC),
            correlation_id=self.correlation_id,
            source="test_harness",
            strategy_id=strategy_id,
            strategy_config_path=strategy_config_path,
            universe=universe or []
        )
        
        self.events.append(event)
        return self
    
    def build(self) -> list[BaseEvent]:
        """Build the event sequence."""
        return self.events.copy()


def load_golden_data(snapshot_file: Path) -> dict[str, Any] | None:
    """Load golden/snapshot data from file."""
    try:
        if snapshot_file.exists():
            return json.loads(snapshot_file.read_text(encoding="utf-8"))
    except Exception:
        pass
    return None


def save_golden_data(snapshot_file: Path, data: dict[str, Any]) -> None:
    """Save golden/snapshot data to file."""
    snapshot_file.parent.mkdir(parents=True, exist_ok=True)
    snapshot_file.write_text(
        json.dumps(data, indent=2, sort_keys=True, default=str),
        encoding="utf-8"
    )


def assert_events_match_golden(
    actual_events: list[BaseEvent],
    golden_events: list[dict[str, Any]] | None,
    tolerance: float = 1e-6
) -> None:
    """Assert that actual events match golden expectations."""
    if golden_events is None:
        # No golden data to compare against
        return
    
    assert len(actual_events) == len(golden_events), (
        f"Event count mismatch: expected {len(golden_events)}, got {len(actual_events)}"
    )
    
    for i, (actual, expected) in enumerate(zip(actual_events, golden_events)):
        # Compare event types
        assert actual.event_type == expected["event_type"], (
            f"Event {i} type mismatch: expected {expected['event_type']}, "
            f"got {actual.event_type}"
        )
        
        # Compare correlation IDs
        assert actual.correlation_id == expected["correlation_id"], (
            f"Event {i} correlation_id mismatch"
        )
        
        # Additional field comparisons would go here based on specific event types


import uuid