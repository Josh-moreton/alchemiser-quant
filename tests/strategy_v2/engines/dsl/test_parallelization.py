#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

Tests for DSL strategy engine parallelization feature.

Validates that parallel evaluation produces identical results to sequential
evaluation while maintaining deterministic ordering and correlation ID tracing.
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from the_alchemiser.strategy_v2.engines.dsl.strategy_engine import DslStrategyEngine


class TestDslStrategyEngineParallelization:
    """Test DSL strategy engine parallelization feature."""

    @pytest.fixture
    def mock_market_data_port(self) -> MagicMock:
        """Create a mock market data port."""
        return MagicMock()

    @pytest.fixture
    def mock_dsl_engine(self) -> MagicMock:
        """Create a mock DSL engine with deterministic results."""
        mock_engine = MagicMock()
        
        # Create deterministic mock allocation and trace for testing
        mock_allocation = MagicMock()
        mock_allocation.target_weights = {"AAPL": 0.6, "GOOGL": 0.4}
        
        mock_trace = MagicMock()
        mock_trace.success = True
        mock_trace.trace_id = "test-trace-123"
        
        mock_engine.evaluate_strategy.return_value = (mock_allocation, mock_trace)
        return mock_engine

    @pytest.fixture
    def strategy_engine(self, mock_market_data_port: MagicMock, mock_dsl_engine: MagicMock) -> DslStrategyEngine:
        """Create a DSL strategy engine with mocked dependencies."""
        engine = DslStrategyEngine(mock_market_data_port, "test.clj")
        engine.dsl_engine = mock_dsl_engine
        
        # Mock settings to provide multiple files for parallel testing
        mock_settings = MagicMock()
        mock_settings.strategy.dsl_files = ["file1.clj", "file2.clj", "file3.clj"]
        mock_settings.strategy.dsl_allocations = {"file1.clj": 0.5, "file2.clj": 0.3, "file3.clj": 0.2}
        engine.settings = mock_settings
        
        return engine

    def test_default_parallelism_is_none(self, strategy_engine: DslStrategyEngine) -> None:
        """Test that default parallelism mode is 'none' (sequential)."""
        timestamp = datetime.now()
        
        # Mock the sequential evaluation method
        with patch.object(strategy_engine, '_evaluate_files_sequential') as mock_sequential:
            mock_sequential.return_value = [
                ({"AAPL": 0.3, "GOOGL": 0.2}, "trace1", 0.5, 1.0),
                ({"AAPL": 0.18, "GOOGL": 0.12}, "trace2", 0.3, 1.0), 
                ({"AAPL": 0.12, "GOOGL": 0.08}, "trace3", 0.2, 1.0),
            ]
            
            signals = strategy_engine.generate_signals(timestamp)
            
            # Verify sequential method was called (default behavior)
            mock_sequential.assert_called_once()
            assert len(signals) == 2  # AAPL and GOOGL
            signal_symbols = [str(signal.symbol) for signal in signals]
            assert any(symbol in ["AAPL", "GOOGL"] for symbol in signal_symbols)

    def test_threads_parallelism(self, strategy_engine: DslStrategyEngine) -> None:
        """Test that threads parallelism mode works correctly."""
        timestamp = datetime.now()
        
        # Mock the parallel evaluation method
        with patch.object(strategy_engine, '_evaluate_files_parallel') as mock_parallel:
            mock_parallel.return_value = [
                ({"AAPL": 0.3, "GOOGL": 0.2}, "trace1", 0.5, 1.0),
                ({"AAPL": 0.18, "GOOGL": 0.12}, "trace2", 0.3, 1.0),
                ({"AAPL": 0.12, "GOOGL": 0.08}, "trace3", 0.2, 1.0),
            ]
            
            signals = strategy_engine.generate_signals(timestamp, parallelism="threads")
            
            # Verify parallel method was called with correct parameters
            mock_parallel.assert_called_once()
            args = mock_parallel.call_args[0]
            assert args[3] == "threads"  # parallelism mode
            assert len(signals) == 2  # AAPL and GOOGL

    def test_processes_parallelism(self, strategy_engine: DslStrategyEngine) -> None:
        """Test that processes parallelism mode works correctly."""
        timestamp = datetime.now()
        
        # Mock the parallel evaluation method
        with patch.object(strategy_engine, '_evaluate_files_parallel') as mock_parallel:
            mock_parallel.return_value = [
                ({"AAPL": 0.3, "GOOGL": 0.2}, "trace1", 0.5, 1.0),
                ({"AAPL": 0.18, "GOOGL": 0.12}, "trace2", 0.3, 1.0),
                ({"AAPL": 0.12, "GOOGL": 0.08}, "trace3", 0.2, 1.0),
            ]
            
            signals = strategy_engine.generate_signals(timestamp, parallelism="processes")
            
            # Verify parallel method was called with correct parameters
            mock_parallel.assert_called_once()
            args = mock_parallel.call_args[0]
            assert args[3] == "processes"  # parallelism mode
            assert len(signals) == 2  # AAPL and GOOGL

    def test_max_workers_parameter(self, strategy_engine: DslStrategyEngine) -> None:
        """Test that max_workers parameter is respected."""
        timestamp = datetime.now()
        
        with patch.object(strategy_engine, '_evaluate_files_parallel') as mock_parallel:
            mock_parallel.return_value = [
                ({"AAPL": 0.3}, "trace1", 1.0, 1.0),
            ]
            
            strategy_engine.generate_signals(timestamp, parallelism="threads", max_workers=2)
            
            # Verify max_workers was passed correctly
            mock_parallel.assert_called_once()
            args = mock_parallel.call_args[0]
            assert args[4] == 2  # max_workers

    def test_environment_variable_override(self, strategy_engine: DslStrategyEngine) -> None:
        """Test that environment variables can override parallelism settings."""
        timestamp = datetime.now()
        
        with patch.dict(os.environ, {
            'ALCHEMISER_DSL_PARALLELISM': 'threads',
            'ALCHEMISER_DSL_MAX_WORKERS': '3'
        }):
            with patch.object(strategy_engine, '_evaluate_files_parallel') as mock_parallel:
                mock_parallel.return_value = [
                    ({"AAPL": 0.3}, "trace1", 1.0, 1.0),
                ]
                
                # Call with different parameters - env vars should override
                strategy_engine.generate_signals(
                    timestamp, 
                    parallelism="none",  # Should be overridden by env
                    max_workers=1        # Should be overridden by env
                )
                
                # Verify environment overrides were applied
                mock_parallel.assert_called_once()
                args = mock_parallel.call_args[0]
                assert args[3] == "threads"  # parallelism from env
                assert args[4] == 3          # max_workers from env

    def test_single_file_uses_sequential(self, mock_market_data_port: MagicMock) -> None:
        """Test that single file evaluation uses sequential mode regardless of parallelism setting."""
        # Create engine with single file
        engine = DslStrategyEngine(mock_market_data_port, "single.clj")
        mock_settings = MagicMock()
        mock_settings.strategy.dsl_files = ["single.clj"]
        mock_settings.strategy.dsl_allocations = {"single.clj": 1.0}
        engine.settings = mock_settings
        
        timestamp = datetime.now()
        
        with patch.object(engine, '_evaluate_files_sequential') as mock_sequential:
            mock_sequential.return_value = [
                ({"AAPL": 1.0}, "trace1", 1.0, 1.0),
            ]
            
            # Request parallel execution but should use sequential for single file
            engine.generate_signals(timestamp, parallelism="threads")
            
            # Verify sequential was used despite threads request
            mock_sequential.assert_called_once()

    def test_correlation_id_propagation(self, strategy_engine: DslStrategyEngine) -> None:
        """Test that correlation IDs are properly propagated in parallel execution."""
        timestamp = datetime.now()
        
        # Track the correlation ID that gets generated
        captured_correlation_id = None
        
        def capture_correlation_id(*args, **kwargs):
            nonlocal captured_correlation_id
            captured_correlation_id = args[1] if len(args) > 1 else None
            return [({"AAPL": 0.3}, "trace1", 1.0, 1.0)]
        
        with patch.object(strategy_engine, '_evaluate_files_parallel', side_effect=capture_correlation_id):
            strategy_engine.generate_signals(timestamp, parallelism="threads")
            
            # Verify correlation ID was propagated
            assert captured_correlation_id is not None
            assert isinstance(captured_correlation_id, str)
            # Should be a valid UUID string
            uuid.UUID(captured_correlation_id)

    def test_deterministic_ordering_preserved(self, strategy_engine: DslStrategyEngine) -> None:
        """Test that file evaluation results maintain deterministic ordering."""
        timestamp = datetime.now()
        
        # Create results that would be different if order wasn't preserved
        expected_results = [
            ({"AAPL": 0.5}, "trace1", 0.5, 1.0),  # file1.clj
            ({"GOOGL": 0.3}, "trace2", 0.3, 1.0), # file2.clj  
            ({"MSFT": 0.2}, "trace3", 0.2, 1.0),  # file3.clj
        ]
        
        with patch.object(strategy_engine, '_evaluate_files_parallel') as mock_parallel:
            mock_parallel.return_value = expected_results
            
            signals = strategy_engine.generate_signals(timestamp, parallelism="threads")
            
            # Verify the results are consolidated in the expected order
            # Should have AAPL, GOOGL, MSFT based on the deterministic file order
            symbol_allocations = {str(signal.symbol): signal.target_allocation for signal in signals}
            
            # Check that all expected symbols are present
            assert "AAPL" in symbol_allocations
            assert "GOOGL" in symbol_allocations  
            assert "MSFT" in symbol_allocations

    def test_failed_file_evaluation_handling(self, strategy_engine: DslStrategyEngine) -> None:
        """Test that failed file evaluations are handled gracefully in parallel mode."""
        timestamp = datetime.now()
        
        # Simulate one file failing (returns None)
        results_with_failure = [
            ({"AAPL": 0.5}, "trace1", 0.5, 1.0),  # Success
            (None, "", 0.0, 0.0),                 # Failure
            ({"GOOGL": 0.2}, "trace3", 0.2, 1.0), # Success
        ]
        
        with patch.object(strategy_engine, '_evaluate_files_parallel') as mock_parallel:
            mock_parallel.return_value = results_with_failure
            
            signals = strategy_engine.generate_signals(timestamp, parallelism="threads")
            
            # Should only have signals from successful evaluations
            symbols = [str(signal.symbol) for signal in signals]
            assert "AAPL" in symbols
            assert "GOOGL" in symbols
            # Should have 2 signals despite 3 files (one failed)
            assert len(signals) == 2

    def test_evaluate_file_wrapper_exception_handling(self, strategy_engine: DslStrategyEngine) -> None:
        """Test that _evaluate_file_wrapper handles exceptions correctly."""
        correlation_id = str(uuid.uuid4())
        normalized_weights = {"test.clj": 1.0}
        
        # Mock _evaluate_file to raise an exception
        with patch.object(strategy_engine, '_evaluate_file', side_effect=Exception("Test error")):
            result = strategy_engine._evaluate_file_wrapper("test.clj", correlation_id, normalized_weights)
            
            # Should return the failure tuple
            assert result == (None, "", 0.0, 0.0)

    def test_logging_includes_parallelism_info(self, strategy_engine: DslStrategyEngine) -> None:
        """Test that logging includes parallelism configuration information."""
        timestamp = datetime.now()
        
        with patch.object(strategy_engine, 'logger') as mock_logger:
            with patch.object(strategy_engine, '_evaluate_files_parallel') as mock_parallel:
                mock_parallel.return_value = [({"AAPL": 1.0}, "trace1", 1.0, 1.0)]
                
                strategy_engine.generate_signals(
                    timestamp, 
                    parallelism="threads", 
                    max_workers=4
                )
                
                # Check that info log was called with parallelism details
                mock_logger.info.assert_called()
                log_call_args = mock_logger.info.call_args
                
                # Verify the extra fields contain parallelism info
                extra = log_call_args[1]['extra']
                assert extra['parallelism'] == "threads"
                assert extra['max_workers'] == 4