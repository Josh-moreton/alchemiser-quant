"""
Performance & Load Testing

Tests system performance under various load conditions and validates
performance requirements for trading operations.
"""

import concurrent.futures
import gc
import threading
import time
from contextlib import contextmanager
from decimal import Decimal

import numpy as np
import pandas as pd


class PerformanceProfiler:
    """Utilities for performance measurement and profiling."""

    @staticmethod
    @contextmanager
    def measure_execution_time():
        """Context manager to measure execution time."""
        start_time = time.perf_counter()
        start_cpu = time.process_time()

        yield_data = {"elapsed": 0, "cpu_time": 0, "start_time": start_time, "start_cpu": start_cpu}

        try:
            yield yield_data
        finally:
            end_time = time.perf_counter()
            end_cpu = time.process_time()
            yield_data["elapsed"] = end_time - start_time
            yield_data["cpu_time"] = end_cpu - start_cpu

    @staticmethod
    @contextmanager
    def measure_memory_usage():
        """Context manager to measure memory usage."""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        start_memory = process.memory_info().rss / 1024 / 1024  # MB

        yield_data = {
            "start_memory_mb": start_memory,
            "peak_memory_mb": start_memory,
            "end_memory_mb": start_memory,
            "memory_increase_mb": 0,
        }

        try:
            yield yield_data
        finally:
            end_memory = process.memory_info().rss / 1024 / 1024  # MB
            yield_data["end_memory_mb"] = end_memory
            yield_data["memory_increase_mb"] = end_memory - start_memory

            # Force garbage collection to get accurate measurement
            gc.collect()
            final_memory = process.memory_info().rss / 1024 / 1024
            yield_data["final_memory_mb"] = final_memory

    @staticmethod
    def generate_high_frequency_data(symbols: list[str], minutes: int = 60) -> pd.DataFrame:
        """Generate high-frequency market data for load testing."""
        data_points = []
        base_time = pd.Timestamp("2024-01-01 09:30:00")

        for symbol in symbols:
            base_price = np.random.uniform(50, 500)

            for minute in range(minutes):
                timestamp = base_time + pd.Timedelta(minutes=minute)

                # Generate multiple ticks per minute
                for tick in range(20):  # 20 ticks per minute
                    tick_time = timestamp + pd.Timedelta(seconds=tick * 3)

                    # Random walk for price
                    price_change = np.random.normal(0, 0.001)  # 0.1% std dev
                    base_price *= 1 + price_change

                    data_points.append(
                        {
                            "symbol": symbol,
                            "timestamp": tick_time,
                            "price": round(base_price, 2),
                            "volume": np.random.randint(100, 10000),
                            "bid": round(base_price - 0.01, 2),
                            "ask": round(base_price + 0.01, 2),
                        }
                    )

        return pd.DataFrame(data_points)


class TestPerformanceBenchmarks:
    """Test performance benchmarks for core trading operations."""

    def test_indicator_calculation_performance(self):
        """Test performance of technical indicator calculations."""
        # Generate large dataset
        data_size = 10000
        prices = np.random.randn(data_size).cumsum() + 100

        def calculate_moving_average(prices, window):
            """Calculate moving average."""
            return pd.Series(prices).rolling(window=window).mean()

        def calculate_rsi(prices, period=14):
            """Calculate RSI indicator."""
            price_series = pd.Series(prices)
            delta = price_series.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            return 100 - (100 / (1 + rs))

        # Test moving average performance
        with PerformanceProfiler.measure_execution_time() as timer:
            ma_20 = calculate_moving_average(prices, 20)
            ma_50 = calculate_moving_average(prices, 50)
            ma_200 = calculate_moving_average(prices, 200)

        # Should complete within reasonable time
        assert (
            timer["elapsed"] < 1.0
        ), f"Moving average calculation too slow: {timer['elapsed']:.3f}s"
        assert len(ma_20) == data_size
        assert len(ma_50) == data_size
        assert len(ma_200) == data_size

        # Test RSI performance
        with PerformanceProfiler.measure_execution_time() as timer:
            rsi = calculate_rsi(prices)

        assert timer["elapsed"] < 0.5, f"RSI calculation too slow: {timer['elapsed']:.3f}s"
        assert len(rsi) == data_size

        # Validate calculations are reasonable
        assert ma_20.iloc[-1] > 0
        assert 0 <= rsi.iloc[-1] <= 100

    def test_portfolio_calculation_performance(self):
        """Test performance of portfolio calculations with many positions."""
        # Create large portfolio
        num_positions = 1000
        positions = {}

        for i in range(num_positions):
            symbol = f"STOCK{i:04d}"
            positions[symbol] = {
                "quantity": np.random.randint(10, 1000),
                "avg_price": Decimal(str(round(np.random.uniform(10, 500), 2))),
                "current_price": Decimal(str(round(np.random.uniform(10, 500), 2))),
            }

        def calculate_portfolio_value(positions):
            """Calculate total portfolio value."""
            total_value = Decimal("0")
            for symbol, position in positions.items():
                market_value = position["quantity"] * position["current_price"]
                total_value += market_value
            return total_value

        def calculate_portfolio_pnl(positions):
            """Calculate portfolio P&L."""
            total_pnl = Decimal("0")
            for symbol, position in positions.items():
                cost_basis = position["quantity"] * position["avg_price"]
                market_value = position["quantity"] * position["current_price"]
                pnl = market_value - cost_basis
                total_pnl += pnl
            return total_pnl

        # Test portfolio value calculation
        with PerformanceProfiler.measure_execution_time() as timer:
            portfolio_value = calculate_portfolio_value(positions)

        assert timer["elapsed"] < 0.1, f"Portfolio calculation too slow: {timer['elapsed']:.3f}s"
        assert portfolio_value > 0

        # Test P&L calculation
        with PerformanceProfiler.measure_execution_time() as timer:
            portfolio_pnl = calculate_portfolio_pnl(positions)

        assert timer["elapsed"] < 0.1, f"P&L calculation too slow: {timer['elapsed']:.3f}s"
        assert isinstance(portfolio_pnl, Decimal)

    def test_data_processing_throughput(self):
        """Test throughput for processing high-frequency market data."""
        # Generate high-frequency data
        symbols = [f"STOCK{i:03d}" for i in range(50)]  # 50 symbols
        market_data = PerformanceProfiler.generate_high_frequency_data(symbols, minutes=30)

        def process_market_data_batch(data):
            """Process a batch of market data."""
            processed = []

            for _, row in data.iterrows():
                # Simulate processing overhead
                processed_row = {
                    "symbol": row["symbol"],
                    "normalized_price": row["price"] / 100.0,
                    "spread": row["ask"] - row["bid"],
                    "mid_price": (row["bid"] + row["ask"]) / 2,
                    "volume_bucket": "high" if row["volume"] > 5000 else "low",
                }
                processed.append(processed_row)

            return processed

        data_size = len(market_data)

        with PerformanceProfiler.measure_execution_time() as timer:
            processed_data = process_market_data_batch(market_data)

        # Calculate throughput
        throughput = data_size / timer["elapsed"]  # records per second

        assert (
            throughput > 10000
        ), f"Data processing throughput too low: {throughput:.0f} records/sec"
        assert len(processed_data) == data_size

        # Validate processed data quality
        sample_record = processed_data[0]
        assert "normalized_price" in sample_record
        assert "spread" in sample_record
        assert sample_record["volume_bucket"] in ["high", "low"]

    def test_memory_efficiency_large_datasets(self):
        """Test memory efficiency when processing large datasets."""
        # Test with increasing dataset sizes
        dataset_sizes = [1000, 5000, 10000, 25000]
        memory_usage = []

        for size in dataset_sizes:
            # Generate dataset
            data = pd.DataFrame(
                {
                    "price": np.random.randn(size).cumsum() + 100,
                    "volume": np.random.randint(1000, 100000, size),
                    "timestamp": pd.date_range(start="2024-01-01", periods=size, freq="1min"),
                }
            )

            with PerformanceProfiler.measure_memory_usage() as memory:
                # Perform operations that might consume memory
                data["ma_20"] = data["price"].rolling(20).mean()
                data["ma_50"] = data["price"].rolling(50).mean()
                data["price_change"] = data["price"].pct_change()
                data["volume_ma"] = data["volume"].rolling(10).mean()

                # Calculate some statistics
                stats = {
                    "mean_price": data["price"].mean(),
                    "std_price": data["price"].std(),
                    "max_volume": data["volume"].max(),
                    "correlation": data["price"].corr(data["volume"]),
                }

            memory_usage.append(
                {
                    "size": size,
                    "memory_increase": memory["memory_increase_mb"],
                    "memory_per_record": memory["memory_increase_mb"]
                    / size
                    * 1024,  # KB per record
                }
            )

        # Memory usage should scale reasonably with data size
        for usage in memory_usage:
            # Should use less than 1KB per record on average
            assert (
                usage["memory_per_record"] < 1.0
            ), f"Memory usage too high: {usage['memory_per_record']:.2f} KB/record"

        # Memory efficiency should not degrade significantly with size
        if len(memory_usage) >= 2:
            small_efficiency = memory_usage[0]["memory_per_record"]
            large_efficiency = memory_usage[-1]["memory_per_record"]

            # Large datasets shouldn't be more than 2x less efficient
            assert (
                large_efficiency < small_efficiency * 2.0
            ), "Memory efficiency degrades too much with size"


class TestConcurrentExecution:
    """Test concurrent execution and thread safety."""

    def test_concurrent_indicator_calculations(self):
        """Test concurrent calculation of indicators on different symbols."""
        symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]
        data_size = 1000

        def calculate_indicators_for_symbol(symbol):
            """Calculate indicators for a single symbol."""
            # Generate random price data
            prices = np.random.randn(data_size).cumsum() + 100

            # Calculate multiple indicators
            ma_20 = pd.Series(prices).rolling(20).mean()
            ma_50 = pd.Series(prices).rolling(50).mean()

            # Simulate some processing time
            time.sleep(0.01)

            return {
                "symbol": symbol,
                "final_price": prices[-1],
                "ma_20_final": ma_20.iloc[-1],
                "ma_50_final": ma_50.iloc[-1],
                "data_points": len(prices),
            }

        # Test sequential execution
        with PerformanceProfiler.measure_execution_time() as sequential_timer:
            sequential_results = []
            for symbol in symbols:
                result = calculate_indicators_for_symbol(symbol)
                sequential_results.append(result)

        # Test concurrent execution
        with PerformanceProfiler.measure_execution_time() as concurrent_timer:
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                future_to_symbol = {
                    executor.submit(calculate_indicators_for_symbol, symbol): symbol
                    for symbol in symbols
                }

                concurrent_results = []
                for future in concurrent.futures.as_completed(future_to_symbol):
                    result = future.result()
                    concurrent_results.append(result)

        # Concurrent execution should be faster
        speedup = sequential_timer["elapsed"] / concurrent_timer["elapsed"]
        assert speedup > 1.5, f"Concurrent execution speedup too low: {speedup:.2f}x"

        # Results should be equivalent
        assert len(sequential_results) == len(concurrent_results) == len(symbols)

        # Validate all symbols were processed
        sequential_symbols = {r["symbol"] for r in sequential_results}
        concurrent_symbols = {r["symbol"] for r in concurrent_results}
        assert sequential_symbols == concurrent_symbols == set(symbols)

    def test_thread_safety_portfolio_updates(self):
        """Test thread safety of portfolio updates."""

        class ThreadSafePortfolio:
            def __init__(self):
                self._positions = {}
                self._lock = threading.Lock()
                self._total_value = Decimal("0")

            def update_position(self, symbol: str, quantity: int, price: Decimal):
                """Thread-safe position update."""
                with self._lock:
                    if symbol in self._positions:
                        old_value = (
                            self._positions[symbol]["quantity"] * self._positions[symbol]["price"]
                        )
                        self._total_value -= old_value

                    self._positions[symbol] = {"quantity": quantity, "price": price}

                    new_value = quantity * price
                    self._total_value += new_value

            def get_position(self, symbol: str):
                """Thread-safe position retrieval."""
                with self._lock:
                    return self._positions.get(symbol, {}).copy()

            def get_total_value(self):
                """Thread-safe total value retrieval."""
                with self._lock:
                    return self._total_value

            def get_position_count(self):
                """Thread-safe position count."""
                with self._lock:
                    return len(self._positions)

        portfolio = ThreadSafePortfolio()
        symbols = [f"STOCK{i:03d}" for i in range(100)]

        def update_random_positions(portfolio, symbols, num_updates=50):
            """Perform random portfolio updates."""
            for _ in range(num_updates):
                symbol = np.random.choice(symbols)
                quantity = np.random.randint(10, 1000)
                price = Decimal(str(round(np.random.uniform(10, 500), 2)))

                portfolio.update_position(symbol, quantity, price)

                # Small delay to increase chance of race conditions
                time.sleep(0.001)

        # Run concurrent updates
        num_threads = 10
        updates_per_thread = 50

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [
                executor.submit(update_random_positions, portfolio, symbols, updates_per_thread)
                for _ in range(num_threads)
            ]

            # Wait for all threads to complete
            for future in concurrent.futures.as_completed(futures):
                future.result()

        # Validate portfolio consistency
        final_position_count = portfolio.get_position_count()
        final_total_value = portfolio.get_total_value()

        assert final_position_count > 0, "Portfolio should have positions after updates"
        assert final_total_value > 0, "Portfolio should have positive value"

        # Manually verify total value calculation
        manual_total = Decimal("0")
        for symbol in symbols:
            position = portfolio.get_position(symbol)
            if position:
                manual_total += position["quantity"] * position["price"]

        assert abs(manual_total - final_total_value) < Decimal(
            "0.01"
        ), "Portfolio value calculation inconsistent"

    def test_high_frequency_data_processing(self):
        """Test processing high-frequency data streams."""
        import queue

        class HighFrequencyDataProcessor:
            def __init__(self, max_queue_size=1000):
                self.data_queue = queue.Queue(maxsize=max_queue_size)
                self.processed_count = 0
                self.processing_errors = 0
                self._stop_processing = False

            def add_data_point(self, data_point):
                """Add data point to processing queue."""
                try:
                    self.data_queue.put(data_point, timeout=0.1)
                    return True
                except queue.Full:
                    return False

            def process_data_stream(self):
                """Process data stream continuously."""
                while not self._stop_processing:
                    try:
                        data_point = self.data_queue.get(timeout=0.1)

                        # Simulate processing
                        if "price" in data_point and "volume" in data_point:
                            # Simple validation and processing
                            if data_point["price"] > 0 and data_point["volume"] > 0:
                                self.processed_count += 1
                            else:
                                self.processing_errors += 1

                        self.data_queue.task_done()

                    except queue.Empty:
                        continue
                    except Exception:
                        self.processing_errors += 1

            def stop_processing(self):
                """Stop the data processing."""
                self._stop_processing = True

        processor = HighFrequencyDataProcessor()

        # Start processing thread
        processing_thread = threading.Thread(target=processor.process_data_stream)
        processing_thread.start()

        # Generate high-frequency data
        symbols = ["AAPL", "GOOGL", "MSFT"]
        data_points_per_symbol = 1000

        with PerformanceProfiler.measure_execution_time() as timer:
            successful_adds = 0

            for symbol in symbols:
                base_price = np.random.uniform(50, 500)

                for i in range(data_points_per_symbol):
                    data_point = {
                        "symbol": symbol,
                        "price": base_price + np.random.normal(0, 1),
                        "volume": np.random.randint(100, 10000),
                        "timestamp": time.time(),
                    }

                    if processor.add_data_point(data_point):
                        successful_adds += 1

        # Allow processing to complete
        time.sleep(1.0)
        processor.stop_processing()
        processing_thread.join()

        total_expected = len(symbols) * data_points_per_symbol

        # Validate processing performance
        assert (
            successful_adds > total_expected * 0.95
        ), f"Too many dropped data points: {successful_adds}/{total_expected}"
        assert processor.processed_count > 0, "No data points were processed"
        assert processor.processing_errors < successful_adds * 0.05, "Too many processing errors"

        # Calculate throughput
        throughput = successful_adds / timer["elapsed"]
        assert throughput > 5000, f"Data processing throughput too low: {throughput:.0f} points/sec"


class TestLoadTesting:
    """Test system behavior under various load conditions."""

    def test_sustained_load_simulation(self):
        """Test system performance under sustained load."""

        class TradingSystemSimulator:
            def __init__(self):
                self.orders_processed = 0
                self.signals_generated = 0
                self.data_points_processed = 0
                self.errors = 0

            def process_market_data(self, data_point):
                """Process a single market data point."""
                try:
                    # Simulate data validation
                    if data_point.get("price", 0) <= 0:
                        raise ValueError("Invalid price")

                    self.data_points_processed += 1

                    # Simulate signal generation (every 10th data point)
                    if self.data_points_processed % 10 == 0:
                        self.signals_generated += 1

                        # Simulate order placement (every 50th data point)
                        if self.data_points_processed % 50 == 0:
                            self.orders_processed += 1

                    return True

                except Exception:
                    self.errors += 1
                    return False

        simulator = TradingSystemSimulator()

        # Generate sustained load
        test_duration = 10  # seconds
        data_rate = 1000  # data points per second

        start_time = time.time()
        data_points_sent = 0

        while time.time() - start_time < test_duration:
            # Generate batch of data points
            batch_size = 100
            batch_start = time.time()

            for _ in range(batch_size):
                data_point = {
                    "symbol": f"STOCK{np.random.randint(1, 100):03d}",
                    "price": np.random.uniform(50, 500),
                    "volume": np.random.randint(100, 10000),
                    "timestamp": time.time(),
                }

                simulator.process_market_data(data_point)
                data_points_sent += 1

            # Rate limiting to maintain target data rate
            batch_duration = time.time() - batch_start
            expected_duration = batch_size / data_rate
            if batch_duration < expected_duration:
                time.sleep(expected_duration - batch_duration)

        # Validate sustained performance
        actual_duration = time.time() - start_time
        actual_rate = data_points_sent / actual_duration

        assert (
            actual_rate > data_rate * 0.9
        ), f"Failed to maintain target data rate: {actual_rate:.0f}/{data_rate}"
        assert (
            simulator.errors < data_points_sent * 0.01
        ), f"Too many processing errors: {simulator.errors}"
        assert (
            simulator.data_points_processed > data_points_sent * 0.95
        ), "Too many data points dropped"

        # Check signal and order generation rates
        signal_rate = simulator.signals_generated / simulator.data_points_processed
        order_rate = simulator.orders_processed / simulator.data_points_processed

        assert (
            0.08 <= signal_rate <= 0.12
        ), f"Signal generation rate out of range: {signal_rate:.3f}"
        assert 0.015 <= order_rate <= 0.025, f"Order generation rate out of range: {order_rate:.3f}"

    def test_peak_load_handling(self):
        """Test system behavior during peak load conditions."""

        class LoadBalancer:
            def __init__(self, max_concurrent_requests=10):
                self.max_concurrent_requests = max_concurrent_requests
                self.active_requests = 0
                self.total_requests = 0
                self.rejected_requests = 0
                self.completed_requests = 0
                self._lock = threading.Lock()

            def handle_request(self, request_id):
                """Handle an incoming request."""
                with self._lock:
                    self.total_requests += 1

                    if self.active_requests >= self.max_concurrent_requests:
                        self.rejected_requests += 1
                        return {"status": "rejected", "reason": "overload"}

                    self.active_requests += 1

                try:
                    # Simulate request processing time
                    processing_time = np.random.uniform(0.01, 0.05)
                    time.sleep(processing_time)

                    result = {
                        "status": "completed",
                        "request_id": request_id,
                        "processing_time": processing_time,
                    }

                    with self._lock:
                        self.completed_requests += 1

                    return result

                finally:
                    with self._lock:
                        self.active_requests -= 1

            def get_stats(self):
                """Get load balancer statistics."""
                with self._lock:
                    return {
                        "total_requests": self.total_requests,
                        "completed_requests": self.completed_requests,
                        "rejected_requests": self.rejected_requests,
                        "active_requests": self.active_requests,
                        "rejection_rate": self.rejected_requests / max(self.total_requests, 1),
                    }

        load_balancer = LoadBalancer(max_concurrent_requests=5)

        # Generate peak load with many concurrent requests
        num_concurrent_threads = 20
        requests_per_thread = 10

        def send_requests(thread_id, num_requests):
            """Send multiple requests from a single thread."""
            results = []
            for i in range(num_requests):
                request_id = f"thread-{thread_id}-req-{i}"
                result = load_balancer.handle_request(request_id)
                results.append(result)
            return results

        with PerformanceProfiler.measure_execution_time() as timer:
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=num_concurrent_threads
            ) as executor:
                futures = [
                    executor.submit(send_requests, thread_id, requests_per_thread)
                    for thread_id in range(num_concurrent_threads)
                ]

                all_results = []
                for future in concurrent.futures.as_completed(futures):
                    thread_results = future.result()
                    all_results.extend(thread_results)

        stats = load_balancer.get_stats()

        # Validate peak load handling
        total_expected = num_concurrent_threads * requests_per_thread
        assert stats["total_requests"] == total_expected

        # Should reject some requests under peak load but not too many
        assert (
            0.1 <= stats["rejection_rate"] <= 0.7
        ), f"Rejection rate out of range: {stats['rejection_rate']:.2%}"

        # Should complete most accepted requests
        expected_completions = stats["total_requests"] - stats["rejected_requests"]
        assert stats["completed_requests"] == expected_completions

        # Should handle load efficiently
        throughput = stats["completed_requests"] / timer["elapsed"]
        assert throughput > 50, f"Peak load throughput too low: {throughput:.0f} req/sec"

    def test_memory_leak_detection(self):
        """Test for memory leaks during extended operation."""
        import gc
        import os

        import psutil

        process = psutil.Process(os.getpid())

        def create_and_process_data():
            """Create and process data that might cause memory leaks."""
            # Create large temporary data structures
            large_dataframe = pd.DataFrame(
                {"price": np.random.randn(10000), "volume": np.random.randint(1000, 100000, 10000)}
            )

            # Perform operations that might hold references
            moving_averages = {}
            for window in [5, 10, 20, 50]:
                moving_averages[f"ma_{window}"] = large_dataframe["price"].rolling(window).mean()

            # Simulate processing
            result = {
                "mean_price": large_dataframe["price"].mean(),
                "total_volume": large_dataframe["volume"].sum(),
                "correlation": large_dataframe["price"].corr(large_dataframe["volume"]),
                "ma_final": moving_averages["ma_20"].iloc[-1],
            }

            # Explicitly delete large objects (good practice)
            del large_dataframe
            del moving_averages

            return result

        # Baseline memory measurement
        gc.collect()
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB

        memory_measurements = [baseline_memory]

        # Run operation multiple times to detect leaks
        num_iterations = 50

        for i in range(num_iterations):
            result = create_and_process_data()

            # Force garbage collection
            gc.collect()

            # Measure memory every 10 iterations
            if i % 10 == 9:
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_measurements.append(current_memory)

        # Analyze memory usage trend
        memory_increases = []
        for i in range(1, len(memory_measurements)):
            increase = memory_measurements[i] - memory_measurements[i - 1]
            memory_increases.append(increase)

        # Check for consistent memory growth (indicating leak)
        avg_increase = np.mean(memory_increases)
        max_increase = max(memory_increases)

        # Should not have consistent upward trend
        assert (
            avg_increase < 5.0
        ), f"Potential memory leak detected: avg increase {avg_increase:.2f} MB per batch"

        # Should not have any single large jump
        assert max_increase < 20.0, f"Large memory jump detected: {max_increase:.2f} MB"

        # Total memory increase should be bounded
        total_increase = memory_measurements[-1] - baseline_memory
        assert total_increase < 50.0, f"Total memory increase too high: {total_increase:.2f} MB"
