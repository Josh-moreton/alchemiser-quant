"""
Production Monitoring & Metrics Testing

Tests monitoring capabilities, alerting systems, and performance metrics
that are essential for production trading system operations.
"""

import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest


@dataclass
class MetricPoint:
    """A single metric measurement."""

    name: str
    value: float
    timestamp: datetime
    tags: dict[str, str] = field(default_factory=dict)
    unit: str = ""


@dataclass
class AlertRule:
    """Definition of an alerting rule."""

    name: str
    metric_name: str
    threshold: float
    comparison: str  # 'gt', 'lt', 'eq'
    window_minutes: int = 5
    severity: str = "warning"  # 'critical', 'warning', 'info'


class MetricsCollector:
    """Collects and manages trading system metrics."""

    def __init__(self):
        self.metrics: list[MetricPoint] = []
        self.counters: dict[str, int] = {}
        self.gauges: dict[str, float] = {}
        self.histograms: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def record_counter(self, name: str, value: int = 1, tags: dict[str, str] | None = None):
        """Record a counter metric."""
        with self._lock:
            self.counters[name] = self.counters.get(name, 0) + value
            self.metrics.append(
                MetricPoint(name=name, value=value, timestamp=datetime.now(), tags=tags or {})
            )

    def record_gauge(self, name: str, value: float, tags: dict[str, str] | None = None):
        """Record a gauge metric."""
        with self._lock:
            self.gauges[name] = value
            self.metrics.append(
                MetricPoint(name=name, value=value, timestamp=datetime.now(), tags=tags or {})
            )

    def record_histogram(self, name: str, value: float, tags: dict[str, str] | None = None):
        """Record a histogram metric."""
        with self._lock:
            if name not in self.histograms:
                self.histograms[name] = []
            self.histograms[name].append(value)

            self.metrics.append(
                MetricPoint(name=name, value=value, timestamp=datetime.now(), tags=tags or {})
            )

    def get_counter(self, name: str) -> int:
        """Get current counter value."""
        with self._lock:
            return self.counters.get(name, 0)

    def get_gauge(self, name: str) -> float:
        """Get current gauge value."""
        with self._lock:
            return self.gauges.get(name, 0.0)

    def get_histogram_stats(self, name: str) -> dict[str, float]:
        """Get histogram statistics."""
        with self._lock:
            values = self.histograms.get(name, [])
            if not values:
                return {}

            import numpy as np

            return {
                "count": float(len(values)),
                "mean": float(np.mean(values)),
                "median": float(np.median(values)),
                "p95": float(np.percentile(values, 95)),
                "p99": float(np.percentile(values, 99)),
                "min": float(np.min(values)),
                "max": float(np.max(values)),
            }

    def clear_metrics(self):
        """Clear all collected metrics."""
        with self._lock:
            self.metrics.clear()
            self.counters.clear()
            self.gauges.clear()
            self.histograms.clear()


class AlertManager:
    """Manages alerting based on metric thresholds."""

    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.alert_rules: list[AlertRule] = []
        self.active_alerts: list[dict[str, Any]] = []
        self._lock = threading.Lock()

    def add_alert_rule(self, rule: AlertRule):
        """Add an alerting rule."""
        with self._lock:
            self.alert_rules.append(rule)

    def check_alerts(self) -> list[dict[str, Any]]:
        """Check all alert rules and return triggered alerts."""
        triggered_alerts = []
        current_time = datetime.now()

        with self._lock:
            for rule in self.alert_rules:
                # Get recent metrics for this rule
                recent_metrics = [
                    m
                    for m in self.metrics_collector.metrics
                    if (
                        m.name == rule.metric_name
                        and current_time - m.timestamp <= timedelta(minutes=rule.window_minutes)
                    )
                ]

                if not recent_metrics:
                    continue

                # Calculate aggregate value (latest for gauges, sum for counters)
                if rule.metric_name in self.metrics_collector.gauges:
                    current_value = recent_metrics[-1].value  # Latest gauge value
                else:
                    current_value = sum(m.value for m in recent_metrics)  # Sum for counters

                # Check threshold
                alert_triggered = False
                if rule.comparison == "gt" and current_value > rule.threshold:
                    alert_triggered = True
                elif rule.comparison == "lt" and current_value < rule.threshold:
                    alert_triggered = True
                elif rule.comparison == "eq" and abs(current_value - rule.threshold) < 0.001:
                    alert_triggered = True

                if alert_triggered:
                    alert = {
                        "rule_name": rule.name,
                        "metric_name": rule.metric_name,
                        "current_value": current_value,
                        "threshold": rule.threshold,
                        "severity": rule.severity,
                        "timestamp": current_time,
                        "window_minutes": rule.window_minutes,
                    }
                    triggered_alerts.append(alert)

        return triggered_alerts

    def get_alert_summary(self) -> dict[str, Any]:
        """Get summary of alerting system status."""
        alerts = self.check_alerts()

        return {
            "total_rules": len(self.alert_rules),
            "active_alerts": len(alerts),
            "critical_alerts": len([a for a in alerts if a["severity"] == "critical"]),
            "warning_alerts": len([a for a in alerts if a["severity"] == "warning"]),
            "alerts": alerts,
        }


class TradingSystemMonitor:
    """Comprehensive monitoring for trading system components."""

    def __init__(self):
        self.metrics = MetricsCollector()
        self.alerts = AlertManager(self.metrics)
        self._setup_default_alerts()

    def _setup_default_alerts(self):
        """Setup default alerting rules for trading system."""
        # Performance alerts
        self.alerts.add_alert_rule(
            AlertRule(
                name="High API Latency",
                metric_name="api_latency_ms",
                threshold=1000.0,  # 1 second
                comparison="gt",
                severity="warning",
            )
        )

        self.alerts.add_alert_rule(
            AlertRule(
                name="Critical API Latency",
                metric_name="api_latency_ms",
                threshold=5000.0,  # 5 seconds
                comparison="gt",
                severity="critical",
            )
        )

        # Error rate alerts
        self.alerts.add_alert_rule(
            AlertRule(
                name="High Error Rate",
                metric_name="api_errors",
                threshold=10,  # 10 errors in 5 minutes
                comparison="gt",
                severity="warning",
            )
        )

        # Portfolio alerts
        self.alerts.add_alert_rule(
            AlertRule(
                name="Large Portfolio Drawdown",
                metric_name="portfolio_drawdown_pct",
                threshold=10.0,  # 10% drawdown
                comparison="gt",
                severity="critical",
            )
        )

        # System resource alerts
        self.alerts.add_alert_rule(
            AlertRule(
                name="High Memory Usage",
                metric_name="memory_usage_pct",
                threshold=80.0,  # 80% memory usage
                comparison="gt",
                severity="warning",
            )
        )

    @contextmanager
    def measure_api_call(self, api_name: str):
        """Context manager to measure API call performance."""
        start_time = time.time()
        error_occurred = False

        try:
            yield
        except Exception as e:
            error_occurred = True
            self.metrics.record_counter(
                "api_errors", tags={"api": api_name, "error_type": type(e).__name__}
            )
            raise
        finally:
            latency_ms = (time.time() - start_time) * 1000
            self.metrics.record_histogram(
                "api_latency_ms",
                latency_ms,
                tags={"api": api_name, "success": str(not error_occurred)},
            )

    def record_trade_execution(
        self, symbol: str, quantity: int, price: Decimal, execution_time_ms: float, success: bool
    ):
        """Record trade execution metrics."""
        self.metrics.record_counter(
            "trades_executed" if success else "trades_failed", tags={"symbol": symbol}
        )

        self.metrics.record_histogram(
            "trade_execution_time_ms",
            execution_time_ms,
            tags={"symbol": symbol, "success": str(success)},
        )

        if success:
            self.metrics.record_histogram(
                "trade_quantity", float(quantity), tags={"symbol": symbol}
            )

            self.metrics.record_histogram("trade_price", float(price), tags={"symbol": symbol})

    def record_portfolio_metrics(
        self,
        total_value: Decimal,
        unrealized_pnl: Decimal,
        drawdown_pct: float,
        position_count: int,
    ):
        """Record portfolio-level metrics."""
        self.metrics.record_gauge("portfolio_value", float(total_value))
        self.metrics.record_gauge("portfolio_unrealized_pnl", float(unrealized_pnl))
        self.metrics.record_gauge("portfolio_drawdown_pct", drawdown_pct)
        self.metrics.record_gauge("portfolio_position_count", float(position_count))

    def record_system_metrics(
        self, cpu_usage_pct: float, memory_usage_pct: float, queue_backlog: int
    ):
        """Record system resource metrics."""
        self.metrics.record_gauge("cpu_usage_pct", cpu_usage_pct)
        self.metrics.record_gauge("memory_usage_pct", memory_usage_pct)
        self.metrics.record_gauge("queue_backlog", float(queue_backlog))

    def get_monitoring_summary(self) -> dict[str, Any]:
        """Get comprehensive monitoring summary."""
        alert_summary = self.alerts.get_alert_summary()

        # Performance metrics
        api_latency_stats = self.metrics.get_histogram_stats("api_latency_ms")
        trade_execution_stats = self.metrics.get_histogram_stats("trade_execution_time_ms")

        return {
            "timestamp": datetime.now(),
            "alerts": alert_summary,
            "performance": {
                "api_latency": api_latency_stats,
                "trade_execution": trade_execution_stats,
                "total_api_calls": len(self.metrics.histograms.get("api_latency_ms", [])),
                "total_trades": (
                    self.metrics.get_counter("trades_executed")
                    + self.metrics.get_counter("trades_failed")
                ),
            },
            "portfolio": {
                "value": self.metrics.get_gauge("portfolio_value"),
                "unrealized_pnl": self.metrics.get_gauge("portfolio_unrealized_pnl"),
                "drawdown_pct": self.metrics.get_gauge("portfolio_drawdown_pct"),
                "position_count": self.metrics.get_gauge("portfolio_position_count"),
            },
            "system": {
                "cpu_usage_pct": self.metrics.get_gauge("cpu_usage_pct"),
                "memory_usage_pct": self.metrics.get_gauge("memory_usage_pct"),
                "queue_backlog": self.metrics.get_gauge("queue_backlog"),
            },
        }


class TestProductionMonitoring:
    """Test production monitoring and alerting capabilities."""

    def test_metrics_collection_accuracy(self):
        """Test that metrics are collected accurately."""
        monitor = TradingSystemMonitor()

        # Record various metrics
        monitor.metrics.record_counter("test_counter", 5)
        monitor.metrics.record_counter("test_counter", 3)
        monitor.metrics.record_gauge("test_gauge", 42.5)
        monitor.metrics.record_histogram("test_histogram", 10.0)
        monitor.metrics.record_histogram("test_histogram", 20.0)
        monitor.metrics.record_histogram("test_histogram", 30.0)

        # Validate counter
        assert monitor.metrics.get_counter("test_counter") == 8

        # Validate gauge
        assert monitor.metrics.get_gauge("test_gauge") == 42.5

        # Validate histogram
        hist_stats = monitor.metrics.get_histogram_stats("test_histogram")
        assert hist_stats["count"] == 3
        assert hist_stats["mean"] == 20.0
        assert hist_stats["min"] == 10.0
        assert hist_stats["max"] == 30.0

    def test_api_performance_monitoring(self):
        """Test API performance monitoring."""
        monitor = TradingSystemMonitor()

        # Simulate API calls with monitoring
        def slow_api_call():
            time.sleep(0.1)  # 100ms delay
            return {"status": "success"}

        def fast_api_call():
            time.sleep(0.01)  # 10ms delay
            return {"status": "success"}

        def failing_api_call():
            raise ConnectionError("API unavailable")

        # Test successful API calls
        with monitor.measure_api_call("test_api"):
            _result = slow_api_call()

        with monitor.measure_api_call("test_api"):
            _result = fast_api_call()

        # Test failed API call
        with pytest.raises(ConnectionError):
            with monitor.measure_api_call("test_api"):
                failing_api_call()

        # Validate metrics
        latency_stats = monitor.metrics.get_histogram_stats("api_latency_ms")
        assert latency_stats["count"] == 3  # 2 successful + 1 failed
        assert latency_stats["min"] > 0  # At least some measurable time
        assert latency_stats["max"] > 50  # At least 50ms (slow call should be ~100ms)

        # Check error counting
        assert monitor.metrics.get_counter("api_errors") == 1

    def test_trade_execution_monitoring(self):
        """Test trade execution monitoring."""
        monitor = TradingSystemMonitor()

        # Record successful trades
        monitor.record_trade_execution(
            symbol="AAPL",
            quantity=100,
            price=Decimal("150.00"),
            execution_time_ms=25.5,
            success=True,
        )

        monitor.record_trade_execution(
            symbol="GOOGL",
            quantity=50,
            price=Decimal("2500.00"),
            execution_time_ms=30.2,
            success=True,
        )

        # Record failed trade
        monitor.record_trade_execution(
            symbol="MSFT",
            quantity=200,
            price=Decimal("300.00"),
            execution_time_ms=45.0,
            success=False,
        )

        # Validate metrics
        assert monitor.metrics.get_counter("trades_executed") == 2
        assert monitor.metrics.get_counter("trades_failed") == 1

        execution_stats = monitor.metrics.get_histogram_stats("trade_execution_time_ms")
        assert execution_stats["count"] == 3
        assert execution_stats["mean"] > 25  # Average should be > 25ms
        assert execution_stats["max"] == 45.0  # Failed trade had highest latency

    def test_portfolio_monitoring(self):
        """Test portfolio-level monitoring."""
        monitor = TradingSystemMonitor()

        # Record portfolio metrics
        monitor.record_portfolio_metrics(
            total_value=Decimal("100000.00"),
            unrealized_pnl=Decimal("5000.00"),
            drawdown_pct=2.5,
            position_count=10,
        )

        # Update portfolio metrics (simulate change)
        monitor.record_portfolio_metrics(
            total_value=Decimal("98000.00"),
            unrealized_pnl=Decimal("-2000.00"),
            drawdown_pct=5.2,
            position_count=8,
        )

        # Validate current metrics (should be latest values)
        assert monitor.metrics.get_gauge("portfolio_value") == 98000.00
        assert monitor.metrics.get_gauge("portfolio_unrealized_pnl") == -2000.00
        assert monitor.metrics.get_gauge("portfolio_drawdown_pct") == 5.2
        assert monitor.metrics.get_gauge("portfolio_position_count") == 8.0

    def test_alerting_system(self):
        """Test alerting system functionality."""
        monitor = TradingSystemMonitor()

        # Trigger high latency alert
        monitor.metrics.record_histogram("api_latency_ms", 1500.0)  # Above warning threshold

        # Trigger error rate alert
        for _ in range(12):  # Above error threshold
            monitor.metrics.record_counter("api_errors")

        # Trigger portfolio drawdown alert
        monitor.record_portfolio_metrics(
            total_value=Decimal("100000.00"),
            unrealized_pnl=Decimal("-15000.00"),
            drawdown_pct=15.0,  # Above critical threshold
            position_count=5,
        )

        # Check alerts
        alert_summary = monitor.alerts.get_alert_summary()

        assert alert_summary["active_alerts"] > 0
        assert alert_summary["critical_alerts"] > 0  # Portfolio drawdown should be critical
        assert alert_summary["warning_alerts"] > 0  # API latency should be warning

        # Validate specific alerts
        alerts = alert_summary["alerts"]
        alert_names = [alert["rule_name"] for alert in alerts]

        assert "High API Latency" in alert_names
        assert "High Error Rate" in alert_names
        assert "Large Portfolio Drawdown" in alert_names

    def test_system_resource_monitoring(self):
        """Test system resource monitoring."""
        monitor = TradingSystemMonitor()

        # Record system metrics over time
        system_scenarios = [
            {"cpu": 45.0, "memory": 60.0, "queue": 5},  # Normal
            {"cpu": 75.0, "memory": 85.0, "queue": 25},  # High load
            {"cpu": 95.0, "memory": 95.0, "queue": 100},  # Critical load
        ]

        for scenario in system_scenarios:
            monitor.record_system_metrics(
                cpu_usage_pct=scenario["cpu"],
                memory_usage_pct=scenario["memory"],
                queue_backlog=scenario["queue"],
            )
            time.sleep(0.01)  # Small delay between measurements

        # Check final values (should be latest)
        assert monitor.metrics.get_gauge("cpu_usage_pct") == 95.0
        assert monitor.metrics.get_gauge("memory_usage_pct") == 95.0
        assert monitor.metrics.get_gauge("queue_backlog") == 100.0

        # Check for memory usage alert
        alert_summary = monitor.alerts.get_alert_summary()
        memory_alerts = [
            a for a in alert_summary["alerts"] if a["rule_name"] == "High Memory Usage"
        ]
        assert len(memory_alerts) > 0

    def test_monitoring_summary_completeness(self):
        """Test that monitoring summary includes all necessary information."""
        monitor = TradingSystemMonitor()

        # Generate some activity
        with monitor.measure_api_call("alpaca_api"):
            time.sleep(0.05)

        monitor.record_trade_execution("AAPL", 100, Decimal("150.00"), 25.0, True)
        monitor.record_portfolio_metrics(Decimal("100000"), Decimal("1000"), 1.5, 5)
        monitor.record_system_metrics(50.0, 70.0, 10)

        # Get summary
        summary = monitor.get_monitoring_summary()

        # Validate structure
        required_keys = ["timestamp", "alerts", "performance", "portfolio", "system"]
        for key in required_keys:
            assert key in summary

        # Validate alerts section
        assert "total_rules" in summary["alerts"]
        assert "active_alerts" in summary["alerts"]
        assert "critical_alerts" in summary["alerts"]

        # Validate performance section
        assert "api_latency" in summary["performance"]
        assert "trade_execution" in summary["performance"]
        assert "total_api_calls" in summary["performance"]

        # Validate portfolio section
        assert "value" in summary["portfolio"]
        assert "unrealized_pnl" in summary["portfolio"]
        assert "drawdown_pct" in summary["portfolio"]

        # Validate system section
        assert "cpu_usage_pct" in summary["system"]
        assert "memory_usage_pct" in summary["system"]
        assert "queue_backlog" in summary["system"]

    def test_concurrent_metrics_collection(self):
        """Test metrics collection under concurrent access."""
        monitor = TradingSystemMonitor()

        def worker_function(worker_id: int):
            """Worker function that records metrics."""
            for i in range(100):
                monitor.metrics.record_counter(f"worker_{worker_id}_counter")
                monitor.metrics.record_gauge(f"worker_{worker_id}_gauge", float(i))
                monitor.metrics.record_histogram("shared_histogram", float(worker_id * 10 + i))
                time.sleep(0.001)  # Small delay

        # Run concurrent workers
        import threading

        threads = []
        num_workers = 5

        for worker_id in range(num_workers):
            thread = threading.Thread(target=worker_function, args=(worker_id,))
            threads.append(thread)
            thread.start()

        # Wait for all workers to complete
        for thread in threads:
            thread.join()

        # Validate results
        for worker_id in range(num_workers):
            assert monitor.metrics.get_counter(f"worker_{worker_id}_counter") == 100
            assert monitor.metrics.get_gauge(f"worker_{worker_id}_gauge") == 99.0  # Last value

        # Validate shared histogram
        hist_stats = monitor.metrics.get_histogram_stats("shared_histogram")
        assert hist_stats["count"] == num_workers * 100  # 5 workers * 100 records each
        assert hist_stats["min"] >= 0
        assert hist_stats["max"] < 500  # Max should be 4*10 + 99 = 439
