"""
Stress Testing & Edge Case Performance

Tests system behavior under extreme conditions and edge cases
that could occur in production trading environments.
"""

import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

import numpy as np
import pandas as pd
import psutil


class TestStressConditions:
    """Test system performance under stress conditions."""

    def test_extreme_market_volatility_performance(self):
        """Test performance during extreme market volatility."""

        def generate_volatile_market_data(duration_minutes: int = 10):
            """Generate extremely volatile market data."""
            data_points = []
            base_time = pd.Timestamp("2024-01-01 09:30:00")

            symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]

            for symbol in symbols:
                base_price = 150.0

                # Generate tick-by-tick data during volatile period
                for minute in range(duration_minutes):
                    for second in range(60):  # Every second
                        timestamp = base_time + pd.Timedelta(minutes=minute, seconds=second)

                        # Extreme volatility: ±5% per minute potential
                        price_change = np.random.normal(0, 0.005)  # High volatility

                        # Occasional extreme moves (flash crashes)
                        if np.random.random() < 0.001:  # 0.1% chance
                            price_change = np.random.choice([-0.10, 0.10])  # ±10% flash move

                        base_price *= 1 + price_change

                        data_points.append(
                            {
                                "symbol": symbol,
                                "timestamp": timestamp,
                                "price": round(max(base_price, 0.01), 2),  # Prevent negative prices
                                "volume": np.random.randint(1000, 50000),
                                "bid_ask_spread": np.random.uniform(
                                    0.01, 0.50
                                ),  # Wide spreads during volatility
                            }
                        )

            return pd.DataFrame(data_points)

        def process_volatile_data(market_data: pd.DataFrame) -> dict:
            """Process volatile market data efficiently."""
            start_time = time.time()

            # Calculate real-time indicators during volatility
            results = {}
            for symbol in market_data["symbol"].unique():
                symbol_data = market_data[market_data["symbol"] == symbol].copy()
                symbol_data = symbol_data.sort_values("timestamp")

                # Fast moving averages for real-time processing
                symbol_data["ma_5"] = symbol_data["price"].rolling(5).mean()
                symbol_data["ma_20"] = symbol_data["price"].rolling(20).mean()

                # Volatility measures
                symbol_data["price_change"] = symbol_data["price"].pct_change()
                symbol_data["volatility"] = symbol_data["price_change"].rolling(20).std()

                # Detect extreme moves
                extreme_moves = symbol_data[abs(symbol_data["price_change"]) > 0.05]

                results[symbol] = {
                    "data_points": len(symbol_data),
                    "extreme_moves": len(extreme_moves),
                    "max_volatility": symbol_data["volatility"].max(),
                    "final_price": symbol_data["price"].iloc[-1],
                }

            processing_time = time.time() - start_time

            return {
                "results": results,
                "processing_time": processing_time,
                "total_data_points": len(market_data),
            }

        # Generate and process volatile data
        volatile_data = generate_volatile_market_data(duration_minutes=5)
        result = process_volatile_data(volatile_data)

        # Validate performance under extreme volatility
        data_per_second = result["total_data_points"] / result["processing_time"]
        assert (
            data_per_second > 5000
        ), f"Processing too slow for volatile data: {data_per_second:.0f} points/sec"

        # Should detect extreme moves in all symbols
        extreme_move_count = sum(r["extreme_moves"] for r in result["results"].values())
        assert extreme_move_count > 0, "Should detect some extreme moves in volatile data"

        # Processing time should be reasonable even with volatility
        assert (
            result["processing_time"] < 2.0
        ), f"Processing time too high: {result['processing_time']:.2f}s"

    def test_high_frequency_order_flow(self):
        """Test handling of high-frequency order flow."""

        class HighFrequencyOrderProcessor:
            def __init__(self):
                self.orders_processed = 0
                self.orders_rejected = 0
                self.processing_times = []
                self._lock = threading.Lock()

            def process_order(self, order: dict) -> dict:
                """Process a single order with timing."""
                start_time = time.perf_counter()

                try:
                    # Validate order
                    if not self._validate_order(order):
                        with self._lock:
                            self.orders_rejected += 1
                        return {"status": "rejected", "reason": "validation_failed"}

                    # Simulate order processing overhead
                    # In real HFT, this would be microseconds, but we simulate with small delays
                    time.sleep(0.0001)  # 0.1ms processing time

                    processing_time = time.perf_counter() - start_time

                    with self._lock:
                        self.orders_processed += 1
                        self.processing_times.append(processing_time)

                    return {
                        "status": "processed",
                        "order_id": order["order_id"],
                        "processing_time": processing_time,
                    }

                except Exception:
                    with self._lock:
                        self.orders_rejected += 1
                    return {"status": "error", "processing_time": time.perf_counter() - start_time}

            def _validate_order(self, order: dict) -> bool:
                """Fast order validation."""
                required_fields = ["order_id", "symbol", "quantity", "price", "side"]

                # Check required fields
                for field in required_fields:
                    if field not in order:
                        return False

                # Basic validation
                if order["quantity"] <= 0 or order["price"] <= 0:
                    return False

                if order["side"] not in ["BUY", "SELL"]:
                    return False

                return True

            def get_stats(self) -> dict:
                """Get processing statistics."""
                with self._lock:
                    avg_processing_time = (
                        np.mean(self.processing_times) if self.processing_times else 0
                    )
                    max_processing_time = max(self.processing_times) if self.processing_times else 0

                    return {
                        "orders_processed": self.orders_processed,
                        "orders_rejected": self.orders_rejected,
                        "avg_processing_time_ms": avg_processing_time * 1000,
                        "max_processing_time_ms": max_processing_time * 1000,
                        "total_orders": self.orders_processed + self.orders_rejected,
                    }

        processor = HighFrequencyOrderProcessor()

        # Generate high-frequency order flow
        symbols = ["AAPL", "GOOGL", "MSFT"]
        order_rate = 10000  # orders per second target
        test_duration = 5  # seconds

        def generate_order_flow(orders_per_second: int, duration: float):
            """Generate continuous order flow."""
            order_count = 0
            start_time = time.time()

            while time.time() - start_time < duration:
                batch_start = time.time()
                batch_size = 100  # Process in batches

                for _ in range(batch_size):
                    order = {
                        "order_id": f"ORDER_{order_count:08d}",
                        "symbol": np.random.choice(symbols),
                        "quantity": np.random.randint(1, 1000),
                        "price": round(np.random.uniform(50, 500), 2),
                        "side": np.random.choice(["BUY", "SELL"]),
                        "timestamp": time.time(),
                    }

                    processor.process_order(order)
                    order_count += 1

                # Rate limiting
                batch_duration = time.time() - batch_start
                expected_duration = batch_size / orders_per_second
                if batch_duration < expected_duration:
                    time.sleep(expected_duration - batch_duration)

            return order_count

        # Run high-frequency order processing
        start_time = time.time()
        total_orders = generate_order_flow(order_rate, test_duration)
        actual_duration = time.time() - start_time

        stats = processor.get_stats()

        # Validate high-frequency performance
        actual_rate = total_orders / actual_duration
        assert (
            actual_rate > order_rate * 0.8
        ), f"Order rate too low: {actual_rate:.0f}/sec vs target {order_rate}/sec"

        # Processing time should be very low for HFT
        assert (
            stats["avg_processing_time_ms"] < 1.0
        ), f"Average processing time too high: {stats['avg_processing_time_ms']:.3f}ms"
        assert (
            stats["max_processing_time_ms"] < 5.0
        ), f"Maximum processing time too high: {stats['max_processing_time_ms']:.3f}ms"

        # Should process most orders successfully
        success_rate = stats["orders_processed"] / stats["total_orders"]
        assert success_rate > 0.95, f"Success rate too low: {success_rate:.2%}"

    def test_memory_pressure_resilience(self):
        """Test system resilience under memory pressure."""

        def allocate_large_datasets():
            """Allocate progressively larger datasets to create memory pressure."""
            datasets = []

            try:
                # Start with reasonable size and increase
                for size_mb in [10, 25, 50, 100, 200]:
                    # Allocate large numpy arrays
                    size_elements = (size_mb * 1024 * 1024) // 8  # 8 bytes per float64
                    large_array = np.random.randn(size_elements)

                    # Perform operations to ensure memory is actually used
                    processed = np.sqrt(np.abs(large_array)) + 1.0
                    datasets.append(processed)

                    # Small delay between allocations
                    time.sleep(0.1)

            except MemoryError:
                # Expected when approaching memory limits
                pass

            return datasets

        def trading_operations_under_pressure(datasets):
            """Perform trading operations while memory is under pressure."""
            operations_completed = 0
            operations_failed = 0

            try:
                for i in range(100):  # Attempt 100 operations
                    try:
                        # Simulate portfolio calculation under memory pressure
                        portfolio_size = 1000
                        positions = np.random.randn(portfolio_size)
                        prices = np.random.uniform(50, 500, portfolio_size)

                        # Memory-intensive calculations
                        portfolio_value = np.sum(positions * prices)
                        portfolio_variance = np.var(positions * prices)

                        # Simulate indicator calculations
                        price_series = np.random.randn(1000).cumsum() + 100
                        moving_avg = np.convolve(price_series, np.ones(20) / 20, mode="valid")

                        operations_completed += 1

                        # Clean up intermediate results
                        del positions, prices, price_series, moving_avg

                    except MemoryError:
                        operations_failed += 1
                        # Attempt garbage collection
                        import gc

                        gc.collect()

            except Exception:
                # Other types of failures
                operations_failed += 1

            return {
                "completed": operations_completed,
                "failed": operations_failed,
                "success_rate": (
                    operations_completed / (operations_completed + operations_failed)
                    if (operations_completed + operations_failed) > 0
                    else 0
                ),
            }

        # Get baseline memory
        process = psutil.Process(os.getpid())
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Create memory pressure
        large_datasets = allocate_large_datasets()

        # Measure memory under pressure
        pressure_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = pressure_memory - baseline_memory

        # Perform trading operations under memory pressure
        results = trading_operations_under_pressure(large_datasets)

        # Clean up
        del large_datasets
        import gc

        gc.collect()

        # Validate resilience under memory pressure
        assert (
            results["success_rate"] > 0.5
        ), f"Success rate too low under memory pressure: {results['success_rate']:.2%}"
        assert results["completed"] > 20, f"Too few operations completed: {results['completed']}"

        # Should have created significant memory pressure
        assert (
            memory_increase > 100
        ), f"Insufficient memory pressure created: {memory_increase:.0f}MB"

    def test_concurrent_strategy_execution(self):
        """Test concurrent execution of multiple trading strategies."""

        class TradingStrategy:
            def __init__(self, strategy_id: str, complexity: str = "medium"):
                self.strategy_id = strategy_id
                self.complexity = complexity
                self.signals_generated = 0
                self.execution_times = []
                self._lock = threading.Lock()

            def process_market_data(self, market_data: dict) -> dict:
                """Process market data and generate signals."""
                start_time = time.time()

                try:
                    # Simulate different strategy complexities
                    if self.complexity == "simple":
                        calculation_time = 0.001  # 1ms
                    elif self.complexity == "medium":
                        calculation_time = 0.005  # 5ms
                    else:  # complex
                        calculation_time = 0.020  # 20ms

                    # Simulate strategy calculations
                    time.sleep(calculation_time)

                    # Generate signal
                    signal = {
                        "strategy_id": self.strategy_id,
                        "symbol": market_data.get("symbol", "UNKNOWN"),
                        "action": np.random.choice(["BUY", "SELL", "HOLD"]),
                        "confidence": np.random.uniform(0.1, 0.9),
                        "timestamp": time.time(),
                    }

                    execution_time = time.time() - start_time

                    with self._lock:
                        self.signals_generated += 1
                        self.execution_times.append(execution_time)

                    return signal

                except Exception:
                    return {"error": "strategy_failed", "strategy_id": self.strategy_id}

            def get_performance_stats(self) -> dict:
                """Get strategy performance statistics."""
                with self._lock:
                    avg_time = np.mean(self.execution_times) if self.execution_times else 0
                    max_time = max(self.execution_times) if self.execution_times else 0

                    return {
                        "strategy_id": self.strategy_id,
                        "signals_generated": self.signals_generated,
                        "avg_execution_time_ms": avg_time * 1000,
                        "max_execution_time_ms": max_time * 1000,
                    }

        # Create multiple strategies with different complexities
        strategies = [
            TradingStrategy("SIMPLE_MA_1", "simple"),
            TradingStrategy("SIMPLE_MA_2", "simple"),
            TradingStrategy("MEDIUM_RSI_1", "medium"),
            TradingStrategy("MEDIUM_RSI_2", "medium"),
            TradingStrategy("COMPLEX_ML_1", "complex"),
            TradingStrategy("COMPLEX_ML_2", "complex"),
        ]

        # Generate market data stream
        symbols = ["AAPL", "GOOGL", "MSFT", "AMZN"]
        test_duration = 10  # seconds
        data_rate = 100  # data points per second

        def strategy_worker(strategy: TradingStrategy, duration: float):
            """Worker function for strategy execution."""
            worker_start = time.time()
            signals = []

            while time.time() - worker_start < duration:
                # Generate market data
                market_data = {
                    "symbol": np.random.choice(symbols),
                    "price": np.random.uniform(50, 500),
                    "volume": np.random.randint(1000, 100000),
                    "timestamp": time.time(),
                }

                # Process with strategy
                signal = strategy.process_market_data(market_data)
                signals.append(signal)

                # Rate limiting
                time.sleep(1.0 / data_rate)

            return signals

        # Run strategies concurrently
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=len(strategies)) as executor:
            futures = [
                executor.submit(strategy_worker, strategy, test_duration) for strategy in strategies
            ]

            all_signals = []
            for future in futures:
                strategy_signals = future.result()
                all_signals.extend(strategy_signals)

        actual_duration = time.time() - start_time

        # Collect performance statistics
        strategy_stats = [strategy.get_performance_stats() for strategy in strategies]

        # Validate concurrent strategy performance
        total_signals = sum(stats["signals_generated"] for stats in strategy_stats)
        assert (
            total_signals > len(strategies) * data_rate * test_duration * 0.8
        ), f"Too few signals generated: {total_signals}"

        # Each strategy should perform according to its complexity
        for stats in strategy_stats:
            if "SIMPLE" in stats["strategy_id"]:
                assert (
                    stats["avg_execution_time_ms"] < 5
                ), f"Simple strategy too slow: {stats['avg_execution_time_ms']:.2f}ms"
            elif "MEDIUM" in stats["strategy_id"]:
                assert (
                    stats["avg_execution_time_ms"] < 15
                ), f"Medium strategy too slow: {stats['avg_execution_time_ms']:.2f}ms"
            else:  # COMPLEX
                assert (
                    stats["avg_execution_time_ms"] < 50
                ), f"Complex strategy too slow: {stats['avg_execution_time_ms']:.2f}ms"

        # All strategies should generate reasonable number of signals
        for stats in strategy_stats:
            assert (
                stats["signals_generated"] > 10
            ), f"Strategy {stats['strategy_id']} generated too few signals: {stats['signals_generated']}"

    def test_edge_case_data_handling(self):
        """Test handling of edge case market data."""

        def create_edge_case_data():
            """Create market data with various edge cases."""
            edge_cases = []

            # Normal data point for comparison
            edge_cases.append(
                {
                    "type": "normal",
                    "symbol": "AAPL",
                    "price": 150.00,
                    "volume": 1000000,
                    "timestamp": "2024-01-01T10:00:00Z",
                }
            )

            # Price edge cases
            edge_cases.extend(
                [
                    {
                        "type": "very_low_price",
                        "symbol": "PENNY",
                        "price": 0.0001,
                        "volume": 1000000,
                    },
                    {
                        "type": "very_high_price",
                        "symbol": "BRK.A",
                        "price": 500000.00,
                        "volume": 100,
                    },
                    {"type": "zero_volume", "symbol": "ILLIQUID", "price": 100.00, "volume": 0},
                    {"type": "huge_volume", "symbol": "VIRAL", "price": 50.00, "volume": 999999999},
                ]
            )

            # Precision edge cases
            edge_cases.extend(
                [
                    {
                        "type": "many_decimals",
                        "symbol": "PRECISE",
                        "price": 123.456789,
                        "volume": 1000,
                    },
                    {
                        "type": "price_precision",
                        "symbol": "CRYPTO",
                        "price": 0.000012345,
                        "volume": 10000000,
                    },
                ]
            )

            # Invalid/corrupted data
            edge_cases.extend(
                [
                    {"type": "negative_price", "symbol": "ERROR", "price": -10.00, "volume": 1000},
                    {
                        "type": "negative_volume",
                        "symbol": "ERROR2",
                        "price": 100.00,
                        "volume": -1000,
                    },
                    {"type": "missing_symbol", "price": 100.00, "volume": 1000},
                    {
                        "type": "non_numeric_price",
                        "symbol": "BAD",
                        "price": "invalid",
                        "volume": 1000,
                    },
                ]
            )

            return edge_cases

        def process_edge_case_data(data_points: list) -> dict:
            """Process edge case data with robust handling."""
            results = {
                "processed": 0,
                "skipped": 0,
                "errors": 0,
                "edge_cases_handled": {},
                "processing_times": [],
            }

            for data_point in data_points:
                start_time = time.time()

                try:
                    # Robust data validation
                    if not self._validate_data_point(data_point):
                        results["skipped"] += 1
                        results["edge_cases_handled"][data_point.get("type", "unknown")] = "skipped"
                        continue

                    # Process valid data
                    processed_point = self._process_data_point(data_point)

                    if processed_point:
                        results["processed"] += 1
                        results["edge_cases_handled"][
                            data_point.get("type", "unknown")
                        ] = "processed"
                    else:
                        results["skipped"] += 1
                        results["edge_cases_handled"][data_point.get("type", "unknown")] = "skipped"

                except Exception:
                    results["errors"] += 1
                    results["edge_cases_handled"][data_point.get("type", "unknown")] = "error"

                finally:
                    processing_time = time.time() - start_time
                    results["processing_times"].append(processing_time)

            return results

        def _validate_data_point(self, data_point: dict) -> bool:
            """Validate a data point."""
            # Check required fields
            if "symbol" not in data_point:
                return False

            # Validate price
            try:
                price = float(data_point.get("price", 0))
                if price <= 0 or price > 1000000:  # Reasonable price range
                    return False
            except (ValueError, TypeError):
                return False

            # Validate volume
            try:
                volume = int(data_point.get("volume", 0))
                if volume < 0 or volume > 1000000000:  # Reasonable volume range
                    return False
            except (ValueError, TypeError):
                return False

            return True

        def _process_data_point(self, data_point: dict) -> dict:
            """Process a validated data point."""
            try:
                # Convert to Decimal for precision
                price = Decimal(str(data_point["price"])).quantize(Decimal("0.01"))
                volume = int(data_point["volume"])

                return {
                    "symbol": data_point["symbol"],
                    "price": price,
                    "volume": volume,
                    "market_value": price * volume,
                }
            except Exception:
                return None

        # Create and process edge case data
        edge_case_data = create_edge_case_data()
        results = process_edge_case_data(edge_case_data)

        # Validate edge case handling
        assert results["processed"] > 0, "Should process some valid data points"
        assert results["skipped"] > results["errors"], "Should skip invalid data rather than error"

        # Should handle specific edge cases appropriately
        assert (
            results["edge_cases_handled"]["normal"] == "processed"
        ), "Normal data should be processed"
        assert (
            results["edge_cases_handled"]["negative_price"] == "skipped"
        ), "Negative prices should be skipped"
        assert (
            results["edge_cases_handled"]["negative_volume"] == "skipped"
        ), "Negative volume should be skipped"

        # Processing should be fast even for edge cases
        avg_processing_time = np.mean(results["processing_times"])
        assert (
            avg_processing_time < 0.001
        ), f"Edge case processing too slow: {avg_processing_time:.4f}s"

        # Error rate should be low (validation should catch most issues)
        error_rate = results["errors"] / len(edge_case_data)
        assert error_rate < 0.2, f"Error rate too high: {error_rate:.2%}"
