"""
Chaos Engineering Tests

Tests system resilience under various failure conditions.
This validates that the trading system can handle unexpected failures gracefully.
"""

import random
import time
from contextlib import contextmanager
from unittest.mock import Mock, patch

import pytest


class ChaosTestFramework:
    """Framework for injecting controlled failures."""

    @staticmethod
    @contextmanager
    def chaos_api_failures(failure_rate: float = 0.1):
        """Inject random API failures."""
        _original_request = None

        def failing_request(*args, **kwargs):
            if random.random() < failure_rate:
                raise ConnectionError("Simulated API failure")
            return {"status": "success", "data": "mock_response"}

        with patch("requests.request", side_effect=failing_request):
            yield

    @staticmethod
    @contextmanager
    def chaos_network_delays(min_delay: float = 1.0, max_delay: float = 5.0):
        """Inject random network delays."""

        def delayed_request(*args, **kwargs):
            delay = random.uniform(min_delay, max_delay)
            time.sleep(delay)
            return {"status": "success", "delay": delay}

        with patch("requests.request", side_effect=delayed_request):
            yield

    @staticmethod
    @contextmanager
    def chaos_memory_pressure():
        """Simulate memory pressure conditions."""

        # Note: In real scenario, would actually consume memory
        # Here we just mock memory-related operations
        def memory_limited_operation(*args, **kwargs):
            if random.random() < 0.3:  # 30% chance of memory error
                raise MemoryError("Simulated memory pressure")
            return "operation_completed"

        with patch("pandas.DataFrame.copy", side_effect=memory_limited_operation):
            yield


class TestChaosEngineering:
    """Test system resilience under chaos conditions."""

    def test_api_intermittent_failures(self):
        """Test behavior with 10% API failure rate."""

        def api_client_with_retry(max_retries=3):
            """Simulate API client with retry logic."""
            for attempt in range(max_retries):
                try:
                    # This would be patched by chaos framework
                    import requests

                    response = requests.request("GET", "https://api.example.com/data")
                    return response
                except ConnectionError:
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(0.1 * (attempt + 1))  # Exponential backoff

            return None

        with ChaosTestFramework.chaos_api_failures(failure_rate=0.1):
            success_count = 0
            total_attempts = 50

            for _ in range(total_attempts):
                try:
                    result = api_client_with_retry()
                    if result and result.get("status") == "success":
                        success_count += 1
                except ConnectionError:
                    pass  # Expected occasional failures

            # Should successfully get data >80% of the time with retries
            success_rate = success_count / total_attempts
            assert success_rate > 0.8, f"Success rate {success_rate:.2%} too low"

    def test_network_latency_resilience(self):
        """Test behavior under high network latency."""

        def time_bounded_operation(timeout: float = 3.0):
            """Operation that must complete within timeout."""
            start_time = time.time()

            try:
                import requests

                response = requests.request("GET", "https://api.example.com/data")
                elapsed = time.time() - start_time

                if elapsed > timeout:
                    raise TimeoutError("Operation timed out")

                return response

            except Exception as e:
                elapsed = time.time() - start_time
                return {"error": str(e), "elapsed": elapsed}

        with ChaosTestFramework.chaos_network_delays(min_delay=0.5, max_delay=2.0):
            timeout_count = 0
            success_count = 0
            total_attempts = 20

            for _ in range(total_attempts):
                result = time_bounded_operation(timeout=3.0)

                if isinstance(result, dict) and "error" in result:
                    if "timeout" in result["error"].lower():
                        timeout_count += 1
                else:
                    success_count += 1

            # Should handle reasonable latency without too many timeouts
            timeout_rate = timeout_count / total_attempts
            assert timeout_rate < 0.3, f"Too many timeouts: {timeout_rate:.2%}"

    def test_memory_pressure_handling(self):
        """Test behavior under memory pressure."""

        def memory_intensive_operation():
            """Simulate memory-intensive operation."""
            try:
                import pandas as pd

                # This would be patched to occasionally fail
                df = pd.DataFrame({"data": range(1000)})
                df_copy = df.copy()  # This might fail under memory pressure
                return len(df_copy)
            except MemoryError:
                # Fallback to lighter operation
                return -1  # Indicate fallback was used

        with ChaosTestFramework.chaos_memory_pressure():
            fallback_count = 0
            success_count = 0
            total_attempts = 20

            for _ in range(total_attempts):
                result = memory_intensive_operation()

                if result == -1:
                    fallback_count += 1
                else:
                    success_count += 1

            # Should handle memory pressure gracefully
            assert fallback_count > 0, "Should have triggered fallback mechanism"
            assert success_count > 0, "Should have some successful operations"

    def test_partial_system_failure(self):
        """Test behavior when part of the system fails."""

        class TradingSystem:
            def __init__(self):
                self.data_provider = Mock()
                self.signal_generator = Mock()
                self.order_executor = Mock()
                self.state_manager = Mock()

            def execute_trading_cycle(self):
                """Execute a complete trading cycle."""
                try:
                    # Get market data
                    market_data = self.data_provider.get_current_data()
                    if not market_data:
                        raise Exception("Data provider failed")

                    # Generate signals
                    signals = self.signal_generator.generate_signals(market_data)
                    if not signals:
                        return {"status": "no_signals", "trades": 0}

                    # Execute orders
                    trades = self.order_executor.execute_orders(signals)

                    # Update state
                    self.state_manager.update_state(trades)

                    return {"status": "success", "trades": len(trades)}

                except Exception as e:
                    # Graceful degradation
                    return {"status": "error", "error": str(e)}

        trading_system = TradingSystem()

        # Configure mocks for various failure scenarios
        test_scenarios = [
            # Normal operation
            {
                "data_provider": {"get_current_data": {"AAPL": 150.0}},
                "signal_generator": {"generate_signals": [{"symbol": "AAPL", "action": "BUY"}]},
                "order_executor": {"execute_orders": [{"symbol": "AAPL", "status": "filled"}]},
                "expected_status": "success",
            },
            # Data provider failure
            {"data_provider": {"get_current_data": None}, "expected_status": "error"},
            # No signals generated
            {
                "data_provider": {"get_current_data": {"AAPL": 150.0}},
                "signal_generator": {"generate_signals": []},
                "expected_status": "no_signals",
            },
        ]

        for scenario in test_scenarios:
            # Configure mocks based on scenario
            if "data_provider" in scenario:
                trading_system.data_provider.get_current_data.return_value = scenario[
                    "data_provider"
                ]["get_current_data"]

            if "signal_generator" in scenario:
                trading_system.signal_generator.generate_signals.return_value = scenario[
                    "signal_generator"
                ]["generate_signals"]

            if "order_executor" in scenario:
                trading_system.order_executor.execute_orders.return_value = scenario[
                    "order_executor"
                ]["execute_orders"]

            # Execute and validate
            result = trading_system.execute_trading_cycle()
            assert result["status"] == scenario["expected_status"]

    def test_cascading_failure_prevention(self):
        """Test prevention of cascading failures."""

        class ComponentWithCircuitBreaker:
            def __init__(self, failure_threshold: int = 3):
                self.failure_threshold = failure_threshold
                self.failure_count = 0
                self.circuit_open = False
                self.last_failure_time = None

            def call_external_service(self):
                """Simulate calling external service with circuit breaker."""
                if self.circuit_open:
                    # Check if we should try to close circuit
                    if time.time() - self.last_failure_time > 60:  # 60 second timeout
                        self.circuit_open = False
                        self.failure_count = 0
                    else:
                        raise Exception("Circuit breaker is open")

                # Simulate random failures
                if random.random() < 0.3:  # 30% failure rate
                    self.failure_count += 1
                    self.last_failure_time = time.time()

                    if self.failure_count >= self.failure_threshold:
                        self.circuit_open = True

                    raise Exception("Service call failed")

                # Reset failure count on success
                self.failure_count = 0
                return "success"

        component = ComponentWithCircuitBreaker(failure_threshold=3)

        failure_count = 0
        circuit_breaker_activations = 0
        total_calls = 50

        for _ in range(total_calls):
            try:
                _result = component.call_external_service()
            except Exception as e:
                failure_count += 1
                if "circuit breaker" in str(e).lower():
                    circuit_breaker_activations += 1

        # Circuit breaker should have activated to prevent cascading failures
        assert circuit_breaker_activations > 0, "Circuit breaker should have activated"

        # Total failures should be reasonable (not every call failing)
        failure_rate = failure_count / total_calls
        assert failure_rate < 0.8, f"Failure rate {failure_rate:.2%} too high"

    def test_resource_exhaustion_handling(self):
        """Test handling of resource exhaustion scenarios."""

        class ResourceManager:
            def __init__(self, max_connections: int = 5):
                self.max_connections = max_connections
                self.active_connections = 0
                self.connection_pool = []

            def acquire_connection(self):
                """Acquire a connection from the pool."""
                if self.active_connections >= self.max_connections:
                    raise Exception("Connection pool exhausted")

                self.active_connections += 1
                connection = Mock()
                connection.id = f"conn_{self.active_connections}"
                self.connection_pool.append(connection)
                return connection

            def release_connection(self, connection):
                """Release a connection back to the pool."""
                if connection in self.connection_pool:
                    self.connection_pool.remove(connection)
                    self.active_connections -= 1

            def get_connection_count(self):
                """Get current active connection count."""
                return self.active_connections

        resource_manager = ResourceManager(max_connections=3)

        # Test normal operation
        conn1 = resource_manager.acquire_connection()
        _conn2 = resource_manager.acquire_connection()
        assert resource_manager.get_connection_count() == 2

        # Test resource exhaustion
        _conn3 = resource_manager.acquire_connection()
        assert resource_manager.get_connection_count() == 3

        # Should fail when pool is exhausted
        with pytest.raises(Exception, match="Connection pool exhausted"):
            resource_manager.acquire_connection()

        # Test resource cleanup
        resource_manager.release_connection(conn1)
        assert resource_manager.get_connection_count() == 2

        # Should be able to acquire again after release
        _conn4 = resource_manager.acquire_connection()
        assert resource_manager.get_connection_count() == 3

    def test_data_corruption_resilience(self):
        """Test resilience against data corruption."""

        def validate_market_data(data):
            """Validate market data integrity."""
            errors = []

            if not isinstance(data, dict):
                errors.append("Data is not a dictionary")
                return errors

            required_fields = ["symbol", "price", "timestamp", "volume"]
            for field in required_fields:
                if field not in data:
                    errors.append(f"Missing field: {field}")

            # Validate price
            if "price" in data:
                try:
                    price = float(data["price"])
                    if price <= 0:
                        errors.append("Price must be positive")
                    if price > 1000000:  # Unreasonably high
                        errors.append("Price seems unreasonably high")
                except (ValueError, TypeError):
                    errors.append("Price is not a valid number")

            # Validate volume
            if "volume" in data:
                try:
                    volume = int(data["volume"])
                    if volume < 0:
                        errors.append("Volume cannot be negative")
                except (ValueError, TypeError):
                    errors.append("Volume is not a valid integer")

            return errors

        # Test valid data
        valid_data = {
            "symbol": "AAPL",
            "price": 150.50,
            "timestamp": "2024-01-01T10:00:00Z",
            "volume": 1000000,
        }

        errors = validate_market_data(valid_data)
        assert len(errors) == 0, f"Valid data should pass validation: {errors}"

        # Test various corruption scenarios
        corruption_scenarios = [
            # Missing field
            {"symbol": "AAPL", "price": 150.50, "volume": 1000000},
            # Invalid price
            {
                "symbol": "AAPL",
                "price": -10,
                "timestamp": "2024-01-01T10:00:00Z",
                "volume": 1000000,
            },
            # Invalid volume
            {
                "symbol": "AAPL",
                "price": 150.50,
                "timestamp": "2024-01-01T10:00:00Z",
                "volume": -500,
            },
            # Non-numeric price
            {
                "symbol": "AAPL",
                "price": "invalid",
                "timestamp": "2024-01-01T10:00:00Z",
                "volume": 1000000,
            },
            # Not a dictionary
            "invalid_data_format",
        ]

        for corrupted_data in corruption_scenarios:
            errors = validate_market_data(corrupted_data)
            assert len(errors) > 0, f"Corrupted data should fail validation: {corrupted_data}"

        # Test recovery mechanism
        def safe_data_processor(data):
            """Process data with corruption handling."""
            errors = validate_market_data(data)

            if errors:
                # Return default/fallback data
                return {
                    "symbol": "UNKNOWN",
                    "price": 0.0,
                    "timestamp": "1970-01-01T00:00:00Z",
                    "volume": 0,
                    "status": "fallback",
                    "errors": errors,
                }

            return {**data, "status": "valid"}

        # Test that processor handles corruption gracefully
        for corrupted_data in corruption_scenarios:
            result = safe_data_processor(corrupted_data)
            assert result["status"] in ["valid", "fallback"]
            if result["status"] == "fallback":
                assert "errors" in result
                assert len(result["errors"]) > 0
