"""
Performance tests for individual trading strategy engines.

These tests ensure no major performance regressions in strategy execution.
"""

import statistics
from datetime import datetime, timezone
from typing import List
from unittest.mock import Mock

import pytest
from tests.performance.conftest import PERFORMANCE_THRESHOLDS, PerformanceBenchmark


class TestNuclearStrategyPerformance:
    """Performance tests for Nuclear strategy engine."""

    def test_nuclear_signal_generation_performance(
        self, nuclear_engine, mock_market_data_port, performance_benchmark
    ) -> None:
        """Test Nuclear strategy signal generation stays within performance threshold."""
        threshold_ms = PERFORMANCE_THRESHOLDS["nuclear_signal_generation"]

        # Run multiple iterations to get stable measurements
        times = []
        for _ in range(5):
            with performance_benchmark("nuclear_signal_generation") as bench:
                signals = nuclear_engine.generate_signals(
                    mock_market_data_port, datetime.now(timezone.utc)
                )
            times.append(bench.elapsed_ms)

        avg_time = statistics.mean(times)
        max_time = max(times)

        # Log performance results
        print(f"\nNuclear Signal Generation Performance:")
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  Maximum: {max_time:.2f}ms")
        print(f"  Threshold: {threshold_ms}ms")
        print(f"  Signals generated: {len(signals) if signals else 0}")

        # Performance assertion
        assert (
            avg_time < threshold_ms
        ), f"Nuclear signal generation too slow: {avg_time:.2f}ms > {threshold_ms}ms"

        # Ensure we actually generated signals in reasonable time
        assert signals is not None, "Nuclear strategy should generate signals"

    def test_nuclear_signal_validation_performance(
        self, nuclear_engine, performance_benchmark
    ) -> None:
        """Test Nuclear strategy signal validation performance."""
        from the_alchemiser.domain.strategies.value_objects.strategy_signal import StrategySignal
        from the_alchemiser.domain.strategies.value_objects.confidence import Confidence
        from the_alchemiser.domain.trading.value_objects.symbol import Symbol
        from the_alchemiser.domain.shared_kernel.value_objects.percentage import Percentage

        # Create test signals
        test_signals = [
            StrategySignal(
                symbol=Symbol("SPY"),
                action="BUY",
                confidence=Confidence(0.8),
                target_allocation=Percentage(0.25),
                reasoning="Test signal",
            ),
            StrategySignal(
                symbol=Symbol("TQQQ"),
                action="SELL",
                confidence=Confidence(0.7),
                target_allocation=Percentage(0.15),
                reasoning="Another test signal",
            ),
        ]

        threshold_ms = PERFORMANCE_THRESHOLDS["strategy_validation"]

        times = []
        for _ in range(10):
            with performance_benchmark("signal_validation") as bench:
                result = nuclear_engine.validate_signals(test_signals)
            times.append(bench.elapsed_ms)

        avg_time = statistics.mean(times)

        print(f"\nNuclear Signal Validation Performance:")
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  Threshold: {threshold_ms}ms")

        assert (
            avg_time < threshold_ms
        ), f"Signal validation too slow: {avg_time:.2f}ms > {threshold_ms}ms"
        assert result is True, "Valid signals should pass validation"


class TestTECLStrategyPerformance:
    """Performance tests for TECL strategy engine."""

    def test_tecl_signal_generation_performance(
        self, tecl_engine, sample_indicators, performance_benchmark
    ) -> None:
        """Test TECL strategy signal generation stays within performance threshold."""
        import pandas as pd

        threshold_ms = PERFORMANCE_THRESHOLDS["tecl_signal_generation"]

        # Mock the internal methods for consistent testing
        market_data = {
            symbol: pd.DataFrame({"Close": [100.0] * 50})
            for symbol in ["SPY", "TQQQ", "TECL", "UVXY", "BIL"]
        }

        tecl_engine.get_market_data = Mock(return_value=market_data)
        tecl_engine.calculate_indicators = Mock(return_value=sample_indicators)

        times = []
        for _ in range(5):
            with performance_benchmark("tecl_signal_generation") as bench:
                signals = tecl_engine.generate_signals(datetime.now())
            times.append(bench.elapsed_ms)

        avg_time = statistics.mean(times)
        max_time = max(times)

        print(f"\nTECL Signal Generation Performance:")
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  Maximum: {max_time:.2f}ms")
        print(f"  Threshold: {threshold_ms}ms")
        print(f"  Signals generated: {len(signals) if signals else 0}")

        assert (
            avg_time < threshold_ms
        ), f"TECL signal generation too slow: {avg_time:.2f}ms > {threshold_ms}ms"

        assert signals is not None, "TECL strategy should generate signals"


class TestKLMStrategyPerformance:
    """Performance tests for KLM ensemble strategy engine."""

    def test_klm_signal_generation_performance(
        self, klm_engine, sample_indicators, performance_benchmark
    ) -> None:
        """Test KLM strategy signal generation stays within performance threshold."""
        import pandas as pd

        threshold_ms = PERFORMANCE_THRESHOLDS["klm_signal_generation"]

        # Mock market data for KLM testing
        market_data = {
            symbol: pd.DataFrame({"Close": [100.0] * 50})
            for symbol in ["SPY", "TQQQ", "TECL", "UVXY", "BIL", "QQQ", "VTV", "XLP", "XLF", "RETL"]
        }

        klm_engine.get_market_data = Mock(return_value=market_data)
        klm_engine.calculate_indicators = Mock(return_value=sample_indicators)

        times = []
        for _ in range(3):  # Fewer iterations since KLM is more expensive
            with performance_benchmark("klm_signal_generation") as bench:
                signals = klm_engine.generate_signals(Mock(), datetime.now(timezone.utc))
            times.append(bench.elapsed_ms)

        avg_time = statistics.mean(times)
        max_time = max(times)

        print(f"\nKLM Signal Generation Performance:")
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  Maximum: {max_time:.2f}ms")
        print(f"  Threshold: {threshold_ms}ms")
        print(f"  Signals generated: {len(signals) if signals else 0}")

        assert (
            avg_time < threshold_ms
        ), f"KLM signal generation too slow: {avg_time:.2f}ms > {threshold_ms}ms"

        assert signals is not None, "KLM strategy should generate signals"

    def test_klm_variant_evaluation_performance(
        self, klm_engine, sample_indicators, performance_benchmark
    ) -> None:
        """Test KLM variant evaluation performance."""
        import pandas as pd

        market_data = {
            symbol: pd.DataFrame({"Close": [100.0] * 20}) for symbol in ["SPY", "TQQQ", "QQQ"]
        }

        # Test individual variant performance
        times = []
        for _ in range(5):
            with performance_benchmark("klm_variant_evaluation") as bench:
                results = klm_engine._evaluate_all_variants(sample_indicators, market_data)
            times.append(bench.elapsed_ms)

        avg_time = statistics.mean(times)

        print(f"\nKLM Variant Evaluation Performance:")
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  Variants evaluated: {len(results) if results else 0}")

        # Should complete variant evaluation in reasonable time
        assert avg_time < 300, f"Variant evaluation too slow: {avg_time:.2f}ms"
        assert results, "Should have variant evaluation results"
