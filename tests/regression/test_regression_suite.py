"""
Regression Testing Framework

Comprehensive regression testing to prevent production issues and ensure
system reliability across different trading scenarios and configurations.
"""

import json
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from unittest.mock import patch

import numpy as np


@dataclass
class RegressionTestCase:
    """Definition of a regression test case."""

    name: str
    description: str
    test_function: str
    expected_results: dict[str, Any] = field(default_factory=dict)
    tolerance: dict[str, float] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    version_added: str = ""
    last_updated: datetime = field(default_factory=datetime.now)
    critical: bool = False


@dataclass
class BaselineData:
    """Baseline data for regression comparison."""

    test_name: str
    timestamp: datetime
    results: dict[str, Any]
    environment: dict[str, str] = field(default_factory=dict)
    version: str = ""


class RegressionDataManager:
    """Manages baseline data and regression test results."""

    def __init__(self, baseline_dir: str = None):
        self.baseline_dir = Path(baseline_dir or tempfile.mkdtemp())
        self.baseline_dir.mkdir(exist_ok=True)
        self.baselines: dict[str, BaselineData] = {}
        self._load_baselines()

    def _get_baseline_file(self, test_name: str) -> Path:
        """Get baseline file path for a test."""
        return self.baseline_dir / f"{test_name}_baseline.json"

    def _load_baselines(self):
        """Load existing baseline data."""
        for baseline_file in self.baseline_dir.glob("*_baseline.json"):
            try:
                with open(baseline_file) as f:
                    data = json.load(f)
                    baseline = BaselineData(
                        test_name=data["test_name"],
                        timestamp=datetime.fromisoformat(data["timestamp"]),
                        results=data["results"],
                        environment=data.get("environment", {}),
                        version=data.get("version", ""),
                    )
                    self.baselines[baseline.test_name] = baseline
            except Exception as e:
                print(f"Warning: Could not load baseline {baseline_file}: {e}")

    def save_baseline(
        self,
        test_name: str,
        results: dict[str, Any],
        environment: dict[str, str] = None,
        version: str = "",
    ):
        """Save baseline data for a test."""
        baseline = BaselineData(
            test_name=test_name,
            timestamp=datetime.now(),
            results=results,
            environment=environment or {},
            version=version,
        )

        baseline_file = self._get_baseline_file(test_name)
        with open(baseline_file, "w") as f:
            json.dump(
                {
                    "test_name": baseline.test_name,
                    "timestamp": baseline.timestamp.isoformat(),
                    "results": baseline.results,
                    "environment": baseline.environment,
                    "version": baseline.version,
                },
                f,
                indent=2,
                default=str,
            )

        self.baselines[test_name] = baseline

    def get_baseline(self, test_name: str) -> BaselineData | None:
        """Get baseline data for a test."""
        return self.baselines.get(test_name)

    def compare_results(
        self, test_name: str, current_results: dict[str, Any], tolerance: dict[str, float] = None
    ) -> dict[str, Any]:
        """Compare current results with baseline."""
        baseline = self.get_baseline(test_name)
        if not baseline:
            return {
                "status": "no_baseline",
                "message": f"No baseline found for test {test_name}",
                "has_regression": False,
            }

        tolerance = tolerance or {}
        differences = {}
        regressions = []

        # Compare numeric values
        for key, current_value in current_results.items():
            if key not in baseline.results:
                differences[key] = {
                    "status": "new_metric",
                    "current": current_value,
                    "baseline": None,
                }
                continue

            baseline_value = baseline.results[key]

            # Handle numeric comparisons
            if isinstance(current_value, int | float) and isinstance(baseline_value, int | float):
                tol = tolerance.get(key, 0.05)  # 5% default tolerance
                relative_diff = abs(current_value - baseline_value) / max(
                    abs(baseline_value), 1e-10
                )

                if relative_diff > tol:
                    differences[key] = {
                        "status": "regression",
                        "current": current_value,
                        "baseline": baseline_value,
                        "relative_diff": relative_diff,
                        "tolerance": tol,
                    }
                    regressions.append(key)
                else:
                    differences[key] = {
                        "status": "passed",
                        "current": current_value,
                        "baseline": baseline_value,
                        "relative_diff": relative_diff,
                    }

            # Handle exact comparisons for strings, booleans
            elif current_value != baseline_value:
                differences[key] = {
                    "status": "changed",
                    "current": current_value,
                    "baseline": baseline_value,
                }
                regressions.append(key)
            else:
                differences[key] = {
                    "status": "passed",
                    "current": current_value,
                    "baseline": baseline_value,
                }

        # Check for missing metrics
        for key in baseline.results:
            if key not in current_results:
                differences[key] = {
                    "status": "missing",
                    "current": None,
                    "baseline": baseline.results[key],
                }
                regressions.append(key)

        return {
            "status": "regression" if regressions else "passed",
            "has_regression": len(regressions) > 0,
            "regressions": regressions,
            "differences": differences,
            "baseline_timestamp": baseline.timestamp,
            "comparison_timestamp": datetime.now(),
        }


class TradingSystemRegressionSuite:
    """Comprehensive regression testing suite for trading system."""

    def __init__(self, baseline_dir: str = None):
        self.data_manager = RegressionDataManager(baseline_dir)
        self.test_cases: list[RegressionTestCase] = []
        self._setup_test_cases()

    def _setup_test_cases(self):
        """Setup regression test cases."""
        # Performance regression tests
        self.test_cases.extend(
            [
                RegressionTestCase(
                    name="indicator_calculation_performance",
                    description="Ensure indicator calculations maintain performance standards",
                    test_function="test_indicator_performance_regression",
                    tolerance={
                        "execution_time_ms": 0.20,
                        "memory_usage_mb": 0.15,
                    },  # 20% time, 15% memory
                    tags=["performance", "indicators"],
                    critical=True,
                ),
                RegressionTestCase(
                    name="portfolio_calculation_accuracy",
                    description="Verify portfolio calculations remain accurate",
                    test_function="test_portfolio_accuracy_regression",
                    tolerance={"total_value": 0.001, "unrealized_pnl": 0.001},  # 0.1% tolerance
                    tags=["accuracy", "portfolio"],
                    critical=True,
                ),
                RegressionTestCase(
                    name="trade_execution_latency",
                    description="Monitor trade execution performance",
                    test_function="test_trade_execution_regression",
                    tolerance={"avg_latency_ms": 0.30, "p95_latency_ms": 0.25},  # 30% avg, 25% p95
                    tags=["performance", "trading"],
                    critical=True,
                ),
                RegressionTestCase(
                    name="risk_management_accuracy",
                    description="Ensure risk calculations remain accurate",
                    test_function="test_risk_management_regression",
                    tolerance={
                        "position_sizing": 0.01,
                        "stop_loss": 0.001,
                    },  # 1% position, 0.1% stops
                    tags=["accuracy", "risk"],
                    critical=True,
                ),
                RegressionTestCase(
                    name="market_data_processing",
                    description="Verify market data processing performance",
                    test_function="test_market_data_regression",
                    tolerance={
                        "processing_rate": 0.15,
                        "latency_ms": 0.20,
                    },  # 15% rate, 20% latency
                    tags=["performance", "data"],
                    critical=False,
                ),
            ]
        )

    def run_indicator_performance_regression(self) -> dict[str, Any]:
        """Test indicator calculation performance regression."""
        # Mock trading system components for testing
        try:
            from the_alchemiser.core.indicators.ema import ExponentialMovingAverage
            from the_alchemiser.core.indicators.rsi import RelativeStrengthIndex
            from the_alchemiser.core.indicators.sma import SimpleMovingAverage
        except ImportError:
            # Mock the indicators if they don't exist yet
            class MockIndicator:
                def __init__(self, period):
                    self.period = period
                    self.values = []

                def update(self, value):
                    self.values.append(value)
                    return sum(self.values[-self.period :]) / min(len(self.values), self.period)

            simple_moving_average = MockIndicator
            exponential_moving_average = MockIndicator
            relative_strength_index = MockIndicator

        # Generate test data
        np.random.seed(42)  # Reproducible results
        prices = 100 + np.cumsum(np.random.randn(1000) * 0.5)

        results = {}

        # Test SMA performance
        start_time = time.time()
        sma = simple_moving_average(period=20)
        _sma_values = [sma.update(price) for price in prices]
        sma_time = (time.time() - start_time) * 1000

        # Test EMA performance
        start_time = time.time()
        ema = exponential_moving_average(period=20)
        _ema_values = [ema.update(price) for price in prices]
        ema_time = (time.time() - start_time) * 1000

        # Test RSI performance
        start_time = time.time()
        rsi = relative_strength_index(period=14)
        _rsi_values = [rsi.update(price) for price in prices]
        rsi_time = (time.time() - start_time) * 1000

        results.update(
            {
                "sma_execution_time_ms": sma_time,
                "ema_execution_time_ms": ema_time,
                "rsi_execution_time_ms": rsi_time,
                "total_execution_time_ms": sma_time + ema_time + rsi_time,
                "data_points_processed": len(prices),
                "processing_rate_points_per_ms": len(prices) / (sma_time + ema_time + rsi_time),
            }
        )

        return results

    def run_portfolio_accuracy_regression(self) -> dict[str, Any]:
        """Test portfolio calculation accuracy regression."""
        from the_alchemiser.core.trading.portfolio import Portfolio
        from the_alchemiser.core.trading.position import Position

        # Create test portfolio with known positions
        portfolio = Portfolio()

        # Add test positions with known values
        positions_data = [
            {
                "symbol": "AAPL",
                "quantity": 100,
                "avg_price": Decimal("150.00"),
                "current_price": Decimal("155.00"),
            },
            {
                "symbol": "GOOGL",
                "quantity": 50,
                "avg_price": Decimal("2500.00"),
                "current_price": Decimal("2450.00"),
            },
            {
                "symbol": "MSFT",
                "quantity": 200,
                "avg_price": Decimal("300.00"),
                "current_price": Decimal("310.00"),
            },
        ]

        total_value = Decimal("0")
        unrealized_pnl = Decimal("0")

        for pos_data in positions_data:
            position = Position(
                symbol=pos_data["symbol"],
                quantity=pos_data["quantity"],
                average_price=pos_data["avg_price"],
            )
            # Mock current price
            position._current_price = pos_data["current_price"]
            portfolio.add_position(position)

            # Calculate expected values
            market_value = pos_data["quantity"] * pos_data["current_price"]
            cost_basis = pos_data["quantity"] * pos_data["avg_price"]
            total_value += market_value
            unrealized_pnl += market_value - cost_basis

        # Get portfolio calculations
        calculated_value = portfolio.get_total_value()
        calculated_pnl = portfolio.get_unrealized_pnl()

        return {
            "total_value": float(calculated_value),
            "expected_total_value": float(total_value),
            "unrealized_pnl": float(calculated_pnl),
            "expected_unrealized_pnl": float(unrealized_pnl),
            "value_accuracy": (
                float(abs(calculated_value - total_value) / total_value) if total_value else 0
            ),
            "pnl_accuracy": (
                float(abs(calculated_pnl - unrealized_pnl) / abs(unrealized_pnl))
                if unrealized_pnl
                else 0
            ),
            "position_count": len(portfolio.positions),
        }

    def run_trade_execution_regression(self) -> dict[str, Any]:
        """Test trade execution performance regression."""
        from the_alchemiser.core.trading.execution_engine import ExecutionEngine

        # Mock execution engine
        execution_engine = ExecutionEngine()
        execution_times = []

        # Simulate multiple trade executions
        for i in range(100):
            start_time = time.time()

            # Mock trade execution
            with patch.object(execution_engine, "execute_order") as mock_execute:
                mock_execute.return_value = {"status": "filled", "fill_time": 0.025}

                order = {
                    "symbol": "AAPL" if i % 2 == 0 else "GOOGL",
                    "quantity": 100,
                    "side": "buy" if i % 2 == 0 else "sell",
                    "order_type": "market",
                }

                execution_engine.execute_order(order)
                execution_time = (time.time() - start_time) * 1000
                execution_times.append(execution_time)

        # Calculate statistics
        avg_latency = np.mean(execution_times)
        p95_latency = np.percentile(execution_times, 95)
        p99_latency = np.percentile(execution_times, 99)

        return {
            "avg_latency_ms": float(avg_latency),
            "p95_latency_ms": float(p95_latency),
            "p99_latency_ms": float(p99_latency),
            "min_latency_ms": float(np.min(execution_times)),
            "max_latency_ms": float(np.max(execution_times)),
            "total_executions": len(execution_times),
            "executions_per_second": 1000.0 / avg_latency if avg_latency > 0 else 0,
        }

    def run_risk_management_regression(self) -> dict[str, Any]:
        """Test risk management calculations regression."""
        from the_alchemiser.core.trading.portfolio import Portfolio
        from the_alchemiser.core.trading.risk_manager import RiskManager

        # Setup test portfolio
        portfolio = Portfolio()
        risk_manager = RiskManager(portfolio)

        # Test position sizing
        account_value = Decimal("100000")
        risk_per_trade = Decimal("0.02")  # 2%
        entry_price = Decimal("150.00")
        stop_loss_price = Decimal("145.00")

        position_size = risk_manager.calculate_position_size(
            account_value=account_value,
            risk_per_trade=risk_per_trade,
            entry_price=entry_price,
            stop_loss_price=stop_loss_price,
        )

        # Expected calculation: (100000 * 0.02) / (150 - 145) = 2000 / 5 = 400 shares
        expected_size = 400

        # Test stop loss calculation
        current_price = Decimal("155.00")
        position_size * current_price
        stop_loss_distance = risk_manager.calculate_stop_loss_distance(
            entry_price=entry_price,
            current_price=current_price,
            position_size=position_size,
            max_loss=account_value * risk_per_trade,
        )

        return {
            "position_sizing": float(position_size),
            "expected_position_size": expected_size,
            "position_size_accuracy": abs(position_size - expected_size) / expected_size,
            "stop_loss_distance": float(stop_loss_distance),
            "account_value": float(account_value),
            "risk_per_trade": float(risk_per_trade),
            "max_portfolio_risk": float(risk_manager.get_portfolio_risk()),
        }

    def run_market_data_regression(self) -> dict[str, Any]:
        """Test market data processing performance regression."""
        from the_alchemiser.core.data.market_data_processor import MarketDataProcessor

        # Mock market data processor
        processor = MarketDataProcessor()

        # Generate test market data
        num_symbols = 100
        num_updates_per_symbol = 1000

        start_time = time.time()
        processed_count = 0

        for symbol_idx in range(num_symbols):
            symbol = f"TEST{symbol_idx:03d}"

            for update_idx in range(num_updates_per_symbol):
                quote_data = {
                    "symbol": symbol,
                    "bid": 100.0 + update_idx * 0.01,
                    "ask": 100.05 + update_idx * 0.01,
                    "timestamp": time.time(),
                }

                # Mock processing
                with patch.object(processor, "process_quote") as mock_process:
                    mock_process.return_value = True
                    processor.process_quote(quote_data)
                    processed_count += 1

        total_time = (time.time() - start_time) * 1000  # Convert to ms
        processing_rate = processed_count / total_time if total_time > 0 else 0

        return {
            "processing_rate": processing_rate,  # quotes per ms
            "latency_ms": total_time / processed_count if processed_count > 0 else 0,
            "total_processed": processed_count,
            "total_time_ms": total_time,
            "symbols_processed": num_symbols,
            "updates_per_symbol": num_updates_per_symbol,
        }

    def run_regression_test(self, test_name: str, save_baseline: bool = False) -> dict[str, Any]:
        """Run a specific regression test."""
        test_case = next((tc for tc in self.test_cases if tc.name == test_name), None)
        if not test_case:
            raise ValueError(f"Unknown test case: {test_name}")

        # Run the test function
        if test_name == "indicator_calculation_performance":
            current_results = self.run_indicator_performance_regression()
        elif test_name == "portfolio_calculation_accuracy":
            current_results = self.run_portfolio_accuracy_regression()
        elif test_name == "trade_execution_latency":
            current_results = self.run_trade_execution_regression()
        elif test_name == "risk_management_accuracy":
            current_results = self.run_risk_management_regression()
        elif test_name == "market_data_processing":
            current_results = self.run_market_data_regression()
        else:
            raise ValueError(f"Test function not implemented: {test_name}")

        # Save baseline if requested
        if save_baseline:
            self.data_manager.save_baseline(
                test_name=test_name,
                results=current_results,
                environment={"python_version": "3.11", "os": "test"},
                version="1.0.0",
            )
            return {"status": "baseline_saved", "test_name": test_name, "results": current_results}

        # Compare with baseline
        comparison = self.data_manager.compare_results(
            test_name=test_name, current_results=current_results, tolerance=test_case.tolerance
        )

        return {
            "test_name": test_name,
            "test_case": test_case,
            "current_results": current_results,
            "comparison": comparison,
        }

    def run_all_tests(self, save_baselines: bool = False) -> dict[str, Any]:
        """Run all regression tests."""
        results = {}
        failed_tests = []
        critical_failures = []

        for test_case in self.test_cases:
            try:
                result = self.run_regression_test(test_case.name, save_baseline=save_baselines)
                results[test_case.name] = result

                if not save_baselines and result["comparison"]["has_regression"]:
                    failed_tests.append(test_case.name)
                    if test_case.critical:
                        critical_failures.append(test_case.name)

            except Exception as e:
                results[test_case.name] = {
                    "status": "error",
                    "error": str(e),
                    "test_case": test_case,
                }
                failed_tests.append(test_case.name)
                if test_case.critical:
                    critical_failures.append(test_case.name)

        return {
            "total_tests": len(self.test_cases),
            "passed_tests": len(self.test_cases) - len(failed_tests),
            "failed_tests": len(failed_tests),
            "critical_failures": len(critical_failures),
            "failed_test_names": failed_tests,
            "critical_failure_names": critical_failures,
            "all_results": results,
            "timestamp": datetime.now(),
        }


class TestRegressionFramework:
    """Test the regression testing framework itself."""

    def test_baseline_data_management(self):
        """Test baseline data saving and loading."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = RegressionDataManager(temp_dir)

            # Save baseline
            test_results = {"metric1": 100.0, "metric2": "test_value", "metric3": True}

            manager.save_baseline(
                test_name="test_baseline",
                results=test_results,
                environment={"env": "test"},
                version="1.0.0",
            )

            # Load baseline
            baseline = manager.get_baseline("test_baseline")
            assert baseline is not None
            assert baseline.test_name == "test_baseline"
            assert baseline.results == test_results
            assert baseline.environment["env"] == "test"
            assert baseline.version == "1.0.0"

    def test_regression_comparison_accuracy(self):
        """Test regression comparison logic."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = RegressionDataManager(temp_dir)

            # Save baseline
            baseline_results = {
                "performance_metric": 100.0,
                "accuracy_metric": 0.95,
                "count_metric": 1000,
            }
            manager.save_baseline("test_comparison", baseline_results)

            # Test passing comparison (within tolerance)
            current_results = {
                "performance_metric": 102.0,  # 2% increase, within 5% tolerance
                "accuracy_metric": 0.94,  # 1% decrease, within 5% tolerance
                "count_metric": 1000,  # Exact match
            }

            comparison = manager.compare_results("test_comparison", current_results)
            assert not comparison["has_regression"]
            assert comparison["status"] == "passed"

            # Test failing comparison (outside tolerance)
            failing_results = {
                "performance_metric": 120.0,  # 20% increase, outside tolerance
                "accuracy_metric": 0.85,  # 10% decrease, outside tolerance
                "count_metric": 800,  # Significant change
            }

            comparison = manager.compare_results("test_comparison", failing_results)
            assert comparison["has_regression"]
            assert comparison["status"] == "regression"
            assert len(comparison["regressions"]) > 0

    def test_regression_suite_execution(self):
        """Test regression suite execution."""
        with tempfile.TemporaryDirectory() as temp_dir:
            suite = TradingSystemRegressionSuite(temp_dir)

            # First run - save baselines
            baseline_results = suite.run_all_tests(save_baselines=True)
            assert baseline_results["total_tests"] > 0

            # Second run - compare against baselines
            comparison_results = suite.run_all_tests(save_baselines=False)
            assert comparison_results["total_tests"] == baseline_results["total_tests"]

            # Should mostly pass (some variation expected)
            assert comparison_results["critical_failures"] == 0  # No critical failures expected

    def test_individual_regression_tests(self):
        """Test individual regression test functions."""
        suite = TradingSystemRegressionSuite()

        # Test each regression test individually
        test_functions = [
            "indicator_calculation_performance",
            "portfolio_calculation_accuracy",
            "trade_execution_latency",
            "risk_management_accuracy",
            "market_data_processing",
        ]

        for test_name in test_functions:
            # Run and save baseline
            result = suite.run_regression_test(test_name, save_baseline=True)
            assert result["status"] == "baseline_saved"
            assert "results" in result
            assert len(result["results"]) > 0

            # Run comparison test
            comparison_result = suite.run_regression_test(test_name, save_baseline=False)
            assert "comparison" in comparison_result
            assert "current_results" in comparison_result
