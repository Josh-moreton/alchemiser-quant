#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

Tests for refactored DSL strategy engine helper functions.

Validates that the helper functions extracted to reduce cognitive complexity
work correctly and maintain the same behavior as the original implementation.
"""

from __future__ import annotations

import os
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from the_alchemiser.strategy_v2.engines.dsl.strategy_engine import DslStrategyEngine
from the_alchemiser.shared.types.strategy_value_objects import StrategySignal


class TestDslStrategyEngineHelperFunctions:
    """Test DSL strategy engine helper functions for cognitive complexity reduction."""

    @pytest.fixture
    def strategy_engine(self) -> DslStrategyEngine:
        """Create a DSL strategy engine for testing."""
        mock_market_data_port = MagicMock()
        engine = DslStrategyEngine(mock_market_data_port, "test.clj")
        return engine

    def test_get_parallelism_and_workers_defaults(self, strategy_engine: DslStrategyEngine) -> None:
        """Test _get_parallelism_and_workers with default values."""
        parallelism, max_workers = strategy_engine._get_parallelism_and_workers("none", None, 3)
        
        assert parallelism == "none"
        assert max_workers == 3  # min(3 files, cpu_count)

    def test_get_parallelism_and_workers_env_override(self, strategy_engine: DslStrategyEngine) -> None:
        """Test _get_parallelism_and_workers with environment variable overrides."""
        with patch.dict(os.environ, {
            "ALCHEMISER_DSL_PARALLELISM": "threads",
            "ALCHEMISER_DSL_MAX_WORKERS": "8"
        }):
            parallelism, max_workers = strategy_engine._get_parallelism_and_workers("none", None, 10)
            
            assert parallelism == "threads"
            assert max_workers == 8

    def test_get_parallelism_and_workers_explicit_values(self, strategy_engine: DslStrategyEngine) -> None:
        """Test _get_parallelism_and_workers with explicitly provided values."""
        parallelism, max_workers = strategy_engine._get_parallelism_and_workers("processes", 5, 10)
        
        assert parallelism == "processes"
        assert max_workers == 5

    def test_accumulate_results_successful_files(self, strategy_engine: DslStrategyEngine) -> None:
        """Test _accumulate_results with successful file evaluations."""
        dsl_files = ["file1.clj", "file2.clj"]
        file_results = [
            ({"AAPL": 0.6, "MSFT": 0.4}, "trace1", 1.0, 1.0),
            ({"AAPL": 0.3, "GOOGL": 0.7}, "trace2", 1.0, 1.0)
        ]
        
        consolidated = strategy_engine._accumulate_results(dsl_files, file_results)
        
        # Use approximate comparison for floating point values
        assert abs(consolidated["AAPL"] - 0.9) < 1e-10
        assert consolidated["MSFT"] == 0.4
        assert consolidated["GOOGL"] == 0.7

    def test_accumulate_results_with_failed_files(self, strategy_engine: DslStrategyEngine) -> None:
        """Test _accumulate_results handling failed file evaluations."""
        dsl_files = ["file1.clj", "file2.clj", "file3.clj"]
        file_results = [
            ({"AAPL": 0.5}, "trace1", 1.0, 1.0),
            (None, "", 0.0, 0.0),  # Failed evaluation
            ({"MSFT": 0.5}, "trace3", 1.0, 1.0)
        ]
        
        consolidated = strategy_engine._accumulate_results(dsl_files, file_results)
        
        expected = {"AAPL": 0.5, "MSFT": 0.5}
        assert consolidated == expected

    def test_accumulate_results_empty_results(self, strategy_engine: DslStrategyEngine) -> None:
        """Test _accumulate_results with empty results."""
        dsl_files = ["file1.clj"]
        file_results = [(None, "", 0.0, 0.0)]
        
        consolidated = strategy_engine._accumulate_results(dsl_files, file_results)
        
        assert consolidated == {}

    def test_convert_to_signals_positive_weights(self, strategy_engine: DslStrategyEngine) -> None:
        """Test _convert_to_signals with positive weights."""
        consolidated = {"AAPL": 0.4, "MSFT": 0.6}
        timestamp = datetime.now()
        correlation_id = "test-correlation-id"
        
        signals = strategy_engine._convert_to_signals(consolidated, timestamp, correlation_id)
        
        assert len(signals) == 2
        assert all(isinstance(signal, StrategySignal) for signal in signals)
        assert all(signal.action == "BUY" for signal in signals)
        
        symbols = {signal.symbol.value for signal in signals}
        assert symbols == {"AAPL", "MSFT"}
        
        # Check specific signal properties 
        aapl_signal = next(s for s in signals if s.symbol.value == "AAPL")
        assert aapl_signal.target_allocation == Decimal('0.4')
        assert "40.0%" in aapl_signal.reasoning

    def test_convert_to_signals_zero_weights_filtered(self, strategy_engine: DslStrategyEngine) -> None:
        """Test _convert_to_signals filters out zero and negative weights."""
        consolidated = {"AAPL": 0.5, "MSFT": 0.0, "GOOGL": -0.1}
        timestamp = datetime.now()
        correlation_id = "test-correlation-id"
        
        signals = strategy_engine._convert_to_signals(consolidated, timestamp, correlation_id)
        
        assert len(signals) == 1
        assert signals[0].symbol.value == "AAPL"
        assert signals[0].target_allocation == Decimal('0.5')

    def test_convert_to_signals_empty_consolidated(self, strategy_engine: DslStrategyEngine) -> None:
        """Test _convert_to_signals with empty consolidated weights."""
        consolidated = {}
        timestamp = datetime.now()
        correlation_id = "test-correlation-id"
        
        signals = strategy_engine._convert_to_signals(consolidated, timestamp, correlation_id)
        
        assert signals == []

    def test_refactored_generate_signals_integration(self, strategy_engine: DslStrategyEngine) -> None:
        """Test that refactored generate_signals produces the same results."""
        timestamp = datetime.now()
        
        # Mock the DSL engine to return predictable results
        mock_allocation = MagicMock()
        mock_allocation.target_weights = {"AAPL": 0.6, "MSFT": 0.4}
        mock_trace = MagicMock()
        mock_trace.trace_id = "test-trace"
        
        with patch.object(strategy_engine.dsl_engine, 'evaluate_strategy', return_value=(mock_allocation, mock_trace)):
            signals = strategy_engine.generate_signals(timestamp)
            
            assert len(signals) == 2
            assert all(signal.timestamp == timestamp for signal in signals)
            
            # Verify normalized allocations (should sum to 1.0)
            total_allocation = sum(signal.target_allocation for signal in signals)
            assert abs(total_allocation - Decimal('1.0')) < Decimal('1e-10')  # Allow for floating point precision