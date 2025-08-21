"""
Performance tests for multi-strategy management and aggregation.

These tests ensure the strategy manager and aggregation logic
maintain acceptable performance as the number of strategies grows.
"""
import statistics
from datetime import datetime, timezone
from unittest.mock import Mock

import pytest
from tests.performance.conftest import PERFORMANCE_THRESHOLDS, PerformanceBenchmark


class TestMultiStrategyPerformance:
    """Performance tests for multi-strategy execution."""

    def test_strategy_manager_signal_generation_performance(
        self, strategy_manager, performance_benchmark
    ) -> None:
        """Test multi-strategy signal generation stays within threshold."""
        threshold_ms = PERFORMANCE_THRESHOLDS["multi_strategy_generation"]
        
        times = []
        for _ in range(3):  # Fewer iterations for comprehensive test
            with performance_benchmark("multi_strategy_generation") as bench:
                aggregated_signals = strategy_manager.generate_all_signals(
                    datetime.now(timezone.utc)
                )
            times.append(bench.elapsed_ms)
        
        avg_time = statistics.mean(times)
        max_time = max(times)
        
        print(f"\nMulti-Strategy Generation Performance:")
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  Maximum: {max_time:.2f}ms")
        print(f"  Threshold: {threshold_ms}ms")
        
        # Check signal aggregation results
        if hasattr(aggregated_signals, 'strategy_signals'):
            print(f"  Strategies executed: {len(aggregated_signals.strategy_signals)}")
            total_signals = sum(
                len(signals) for signals in aggregated_signals.strategy_signals.values()
            )
            print(f"  Total signals: {total_signals}")
        
        assert avg_time < threshold_ms, (
            f"Multi-strategy generation too slow: {avg_time:.2f}ms > {threshold_ms}ms"
        )
        
        assert aggregated_signals is not None, "Should generate aggregated signals"

    def test_signal_aggregation_performance(
        self, strategy_manager, performance_benchmark
    ) -> None:
        """Test signal aggregation logic performance."""
        from the_alchemiser.domain.strategies.typed_strategy_manager import AggregatedSignals
        from the_alchemiser.domain.strategies.value_objects.strategy_signal import StrategySignal
        from the_alchemiser.domain.strategies.value_objects.confidence import Confidence
        from the_alchemiser.domain.trading.value_objects.symbol import Symbol
        from the_alchemiser.domain.shared_kernel.value_objects.percentage import Percentage
        from the_alchemiser.domain.registry import StrategyType
        
        # Create test signals for aggregation
        test_signals = []
        symbols = ["SPY", "TQQQ", "UVXY", "BIL"]
        
        for i, symbol in enumerate(symbols):
            signal = StrategySignal(
                symbol=Symbol(symbol),
                action="BUY" if i % 2 == 0 else "SELL",
                confidence=Confidence(0.7 + i * 0.05),
                target_allocation=Percentage(0.25),
                reasoning=f"Test signal for {symbol}"
            )
            test_signals.append(signal)
        
        # Create aggregated signals object
        aggregated = AggregatedSignals()
        
        # Add signals from different strategies
        aggregated.add_strategy_signals(StrategyType.NUCLEAR, test_signals[:2])
        aggregated.add_strategy_signals(StrategyType.TECL, test_signals[2:])
        
        times = []
        for _ in range(10):
            with performance_benchmark("signal_aggregation") as bench:
                strategy_manager._aggregate_signals(aggregated)
            times.append(bench.elapsed_ms)
        
        avg_time = statistics.mean(times)
        
        print(f"\nSignal Aggregation Performance:")
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  Signals aggregated: {len(test_signals)}")
        
        # Aggregation should be very fast
        assert avg_time < 10, f"Signal aggregation too slow: {avg_time:.2f}ms"

    def test_strategy_manager_scalability(
        self, mock_market_data_port, performance_benchmark
    ) -> None:
        """Test strategy manager performance with different numbers of strategies."""
        from the_alchemiser.domain.strategies.typed_strategy_manager import TypedStrategyManager
        from the_alchemiser.domain.registry import StrategyType
        
        # Test with different strategy combinations
        strategy_configs = [
            # Single strategy
            {StrategyType.NUCLEAR: 1.0},
            # Two strategies
            {StrategyType.NUCLEAR: 0.5, StrategyType.TECL: 0.5},
            # Three strategies
            {StrategyType.NUCLEAR: 0.4, StrategyType.TECL: 0.3, StrategyType.KLM: 0.3},
        ]
        
        results = {}
        
        for i, config in enumerate(strategy_configs):
            strategy_count = len(config)
            manager = TypedStrategyManager(mock_market_data_port, config)
            
            times = []
            for _ in range(2):  # Limited iterations for scalability test
                with performance_benchmark(f"strategies_{strategy_count}") as bench:
                    aggregated = manager.generate_all_signals(datetime.now(timezone.utc))
                times.append(bench.elapsed_ms)
            
            avg_time = statistics.mean(times)
            results[strategy_count] = avg_time
            
            print(f"\nStrategy Manager Scalability ({strategy_count} strategies):")
            print(f"  Average time: {avg_time:.2f}ms")
            print(f"  Strategies: {list(config.keys())}")
        
        # Verify performance doesn't degrade dramatically with more strategies
        if len(results) > 1:
            single_strategy_time = results[1]
            multi_strategy_time = results[max(results.keys())]
            
            # Multi-strategy should not be more than 5x slower than single strategy
            performance_ratio = multi_strategy_time / single_strategy_time
            print(f"  Performance ratio (multi/single): {performance_ratio:.2f}x")
            
            assert performance_ratio < 5.0, (
                f"Multi-strategy performance degradation too high: {performance_ratio:.2f}x"
            )


class TestStrategyLoopPerformance:
    """Performance tests for strategy execution loops."""

    def test_strategy_execution_loop_performance(
        self, nuclear_engine, mock_market_data_port, performance_benchmark
    ) -> None:
        """Test repeated strategy execution performance (simulating trading loop)."""
        
        # Simulate multiple trading cycles
        execution_times = []
        
        for cycle in range(10):
            with performance_benchmark(f"execution_cycle_{cycle}") as bench:
                # Simulate a trading cycle: generate signals, validate, process
                signals = nuclear_engine.generate_signals(
                    datetime.now(timezone.utc)
                )
                
                # Validate signals as batch
                if signals:
                    nuclear_engine.validate_signals(signals)
                        
            execution_times.append(bench.elapsed_ms)
        
        avg_cycle_time = statistics.mean(execution_times)
        max_cycle_time = max(execution_times)
        std_deviation = statistics.stdev(execution_times) if len(execution_times) > 1 else 0
        
        print(f"\nStrategy Execution Loop Performance:")
        print(f"  Average cycle time: {avg_cycle_time:.2f}ms")
        print(f"  Maximum cycle time: {max_cycle_time:.2f}ms")
        print(f"  Standard deviation: {std_deviation:.2f}ms")
        print(f"  Total cycles: {len(execution_times)}")
        
        # Performance should be consistent across cycles
        assert avg_cycle_time < 150, f"Average cycle time too slow: {avg_cycle_time:.2f}ms"
        assert std_deviation < 50, f"Performance too variable: {std_deviation:.2f}ms std dev"

    def test_memory_usage_stability(
        self, strategy_manager, performance_benchmark
    ) -> None:
        """Test memory usage doesn't grow excessively during repeated operations."""
        import gc
        import psutil
        import os
        
        # Get current process
        process = psutil.Process(os.getpid())
        
        # Record initial memory
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Run multiple strategy generation cycles
        for _ in range(20):
            aggregated = strategy_manager.generate_all_signals(datetime.now(timezone.utc))
            # Force garbage collection to detect memory leaks
            gc.collect()
        
        # Record final memory
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_growth = final_memory - initial_memory
        
        print(f"\nMemory Usage Analysis:")
        print(f"  Initial memory: {initial_memory:.2f} MB")
        print(f"  Final memory: {final_memory:.2f} MB")
        print(f"  Memory growth: {memory_growth:.2f} MB")
        
        # Memory growth should be minimal (less than 50MB for 20 cycles)
        assert memory_growth < 50, (
            f"Excessive memory growth detected: {memory_growth:.2f} MB"
        )