"""
Performance test fixtures and configuration.
"""
import time
from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import Mock

import pandas as pd
import pytest
from the_alchemiser.domain.strategies.nuclear_typed_engine import NuclearTypedEngine
from the_alchemiser.domain.strategies.tecl_strategy_engine import TECLStrategyEngine
from the_alchemiser.domain.strategies.typed_klm_ensemble_engine import TypedKLMStrategyEngine
from the_alchemiser.domain.strategies.typed_strategy_manager import TypedStrategyManager


@pytest.fixture
def mock_market_data_port():
    """Mock market data port for performance testing."""
    mock_port = Mock()
    mock_port.get_current_price.return_value = 100.0
    mock_port.get_data.return_value = {
        "SPY": pd.DataFrame({"Close": [100.0] * 100}),
        "TQQQ": pd.DataFrame({"Close": [50.0] * 100}),
        "TECL": pd.DataFrame({"Close": [80.0] * 100}),
        "UVXY": pd.DataFrame({"Close": [20.0] * 100}),
        "BIL": pd.DataFrame({"Close": [91.0] * 100}),
    }
    return mock_port


@pytest.fixture
def sample_indicators() -> Dict[str, Dict[str, float]]:
    """Sample indicators for performance testing."""
    return {
        "SPY": {
            "rsi_10": 65.0,
            "rsi_70": 58.0,
            "current_price": 450.0,
            "vix_current": 18.5,
        },
        "TQQQ": {
            "rsi_10": 70.0,
            "current_price": 50.0,
        },
        "TECL": {
            "rsi_10": 68.0,
            "current_price": 80.0,
        },
        "UVXY": {
            "rsi_10": 45.0,
            "current_price": 20.0,
        },
        "BIL": {
            "rsi_10": 50.0,
            "current_price": 91.0,
        },
    }


@pytest.fixture
def nuclear_engine():
    """Nuclear strategy engine for performance testing."""
    return NuclearTypedEngine()


@pytest.fixture
def tecl_engine(mock_market_data_port):
    """TECL strategy engine for performance testing."""
    return TECLStrategyEngine(mock_market_data_port)


@pytest.fixture
def klm_engine():
    """KLM strategy engine for performance testing."""
    return TypedKLMStrategyEngine()


@pytest.fixture
def strategy_manager(mock_market_data_port):
    """Typed strategy manager for performance testing."""
    from the_alchemiser.domain.registry import StrategyType
    
    allocations = {
        StrategyType.NUCLEAR: 0.4,
        StrategyType.TECL: 0.3,
        StrategyType.KLM: 0.3,
    }
    return TypedStrategyManager(mock_market_data_port, allocations)


class PerformanceBenchmark:
    """Helper class for performance measurements."""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = 0.0
        self.end_time = 0.0
        
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        
    @property
    def elapsed_time(self) -> float:
        """Get elapsed time in seconds."""
        return self.end_time - self.start_time
    
    @property 
    def elapsed_ms(self) -> float:
        """Get elapsed time in milliseconds."""
        return self.elapsed_time * 1000


@pytest.fixture
def performance_benchmark():
    """Performance benchmark fixture."""
    return PerformanceBenchmark


# Performance thresholds in milliseconds
PERFORMANCE_THRESHOLDS = {
    "nuclear_signal_generation": 100,  # Nuclear should generate signals in <100ms
    "tecl_signal_generation": 150,     # TECL should generate signals in <150ms  
    "klm_signal_generation": 500,      # KLM ensemble may take longer due to multiple variants
    "multi_strategy_generation": 800,  # All strategies combined should be <800ms
    "strategy_validation": 50,         # Signal validation should be very fast
}