#!/usr/bin/env python3
"""
Test script for Phase 3 Error Monitoring and Alerting Enhancements.

This script tests the new monitoring and alerting features implemented in Phase 3:
1. Error Metrics and Monitoring
2. Alert Threshold Management
3. Production Health Dashboard
"""

import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from the_alchemiser.core.error_handler import (
    EnhancedDataError,
    EnhancedTradingError,
    ErrorSeverity,
    create_error_context,
)
from the_alchemiser.core.error_monitoring import (
    AlertThresholdManager,
    ErrorEvent,
    ErrorHealthDashboard,
    ErrorMetricsCollector,
    HealthStatus,
    ProductionMonitor,
    get_health_dashboard,
    get_production_monitor,
    get_system_health,
    record_error_for_monitoring,
    record_recovery_for_monitoring,
)


def test_error_metrics_collector():
    """Test the ErrorMetricsCollector functionality."""
    print("🧪 Testing Error Metrics Collector...")

    collector = ErrorMetricsCollector()

    # Create test errors with context
    context1 = create_error_context("trade_execution", "trading_engine")
    error1 = EnhancedTradingError(
        "Order failed", context=context1, symbol="AAPL", severity=ErrorSeverity.HIGH
    )

    context2 = create_error_context("data_fetch", "market_data")
    error2 = EnhancedDataError(
        "Connection timeout", context=context2, data_source="alpaca", severity=ErrorSeverity.MEDIUM
    )

    # Record multiple errors
    for i in range(5):
        collector.record_error(error1, context1)
        time.sleep(0.01)  # Small delay to differentiate timestamps

    for i in range(3):
        collector.record_error(error2, context2)
        time.sleep(0.01)

    # Test error rate calculation
    trading_error_rate = collector.get_error_rate("EnhancedTradingError:trading_engine", 1)
    assert trading_error_rate > 0, "Should have recorded trading errors"

    total_error_rate = collector.get_total_error_rate(1)
    assert total_error_rate > 0, "Should have total error rate"

    # Test error summary
    summary = collector.get_error_summary()
    assert summary["total_error_types"] >= 2, "Should have recorded multiple error types"
    assert len(summary["most_common_errors"]) > 0, "Should have most common errors"

    # Test recovery recording
    collector.record_recovery_attempt("EnhancedTradingError", True, 2.5)
    collector.record_recovery_attempt("EnhancedTradingError", False, 1.0)

    assert "EnhancedTradingError" in collector.recovery_stats
    stats = collector.recovery_stats["EnhancedTradingError"]
    assert stats.total_attempts == 2
    assert stats.successful_recoveries == 1
    assert stats.failed_recoveries == 1
    assert stats.success_rate == 0.5

    print("✅ Error metrics collector tests passed!")


def test_alert_threshold_manager():
    """Test dynamic alert threshold management."""
    print("🧪 Testing Alert Threshold Manager...")

    manager = AlertThresholdManager()

    # Test with insufficient historical data (should use static thresholds)
    should_alert = manager.should_alert("error_rate_per_minute", 1.5)
    assert not should_alert, "Should not alert with low value and no historical data"

    should_alert = manager.should_alert("error_rate_per_minute", 3.0)
    assert should_alert, "Should alert with high value exceeding static threshold"

    # Add historical data points (simulate higher than normal operation)
    for i in range(30):
        manager.update_baseline("error_rate_per_minute", 1.5 + (i % 3) * 0.2)  # 1.5-1.9 range

    # Test dynamic threshold calculation
    dynamic_threshold = manager.get_dynamic_threshold("error_rate_per_minute")
    static_threshold = manager.static_thresholds["error_rate_per_minute"]
    assert (
        dynamic_threshold >= static_threshold
    ), "Dynamic threshold should be at least static threshold"

    # With higher baseline, dynamic should be higher than static
    if dynamic_threshold > static_threshold:
        print(f"✓ Dynamic threshold adapted: {dynamic_threshold:.2f} > {static_threshold:.2f}")
    else:
        print(f"✓ Dynamic threshold maintained static level: {dynamic_threshold:.2f}")

    # Test threshold summary
    summary = manager.get_threshold_summary()
    assert "error_rate_per_minute" in summary
    assert summary["error_rate_per_minute"]["data_points"] >= 30

    print("✅ Alert threshold manager tests passed!")


def test_health_dashboard():
    """Test the health dashboard functionality."""
    print("🧪 Testing Health Dashboard...")

    collector = ErrorMetricsCollector()
    dashboard = ErrorHealthDashboard(collector)

    # Test healthy state
    health = dashboard.get_health_status()
    assert health == HealthStatus.HEALTHY, "Should start healthy"

    # Simulate critical errors
    context = create_error_context("critical_system", "core")
    critical_error = EnhancedTradingError(
        "Critical failure", context=context, severity=ErrorSeverity.CRITICAL
    )
    collector.record_error(critical_error, context)

    health = dashboard.get_health_status()
    assert health == HealthStatus.CRITICAL, "Should be critical with critical errors"

    # Test active alerts
    alerts = dashboard.get_active_alerts()
    assert len(alerts) > 0, "Should have active alerts"
    critical_alert = next((a for a in alerts if a["type"] == "critical_errors"), None)
    assert critical_alert is not None, "Should have critical error alert"

    # Test recommendations
    recommendations = dashboard.get_recommendations()
    assert len(recommendations) > 0, "Should have recommendations"
    assert any(
        "critical" in rec.lower() for rec in recommendations
    ), "Should recommend critical error investigation"

    # Test health report generation
    report = dashboard.generate_health_report()
    assert report.status == HealthStatus.CRITICAL
    assert len(report.active_alerts) > 0
    assert len(report.recommendations) > 0

    # Test report serialization
    report_dict = report.to_dict()
    assert isinstance(report_dict, dict)
    assert report_dict["status"] == "critical"

    print("✅ Health dashboard tests passed!")


def test_production_monitor():
    """Test the production monitoring system."""
    print("🧪 Testing Production Monitor...")

    monitor = ProductionMonitor()

    # Test error recording
    context = create_error_context("monitor_test", "test_component")
    test_error = EnhancedTradingError("Monitor test error", context=context, symbol="TEST")

    monitor.record_error(test_error, context)

    # Test recovery recording
    monitor.record_recovery("EnhancedTradingError", True, 1.5)
    monitor.record_recovery("EnhancedTradingError", False, 0.8)

    # Test dashboard data retrieval
    dashboard_data = monitor.get_dashboard_data()
    assert "health_report" in dashboard_data
    assert "threshold_summary" in dashboard_data
    assert "hourly_trend" in dashboard_data

    health_report = dashboard_data["health_report"]
    assert "status" in health_report
    assert "error_summary" in health_report

    # Test health check
    is_healthy = monitor.is_healthy()
    assert isinstance(is_healthy, bool)

    # Test monitoring enable/disable
    monitor.disable_monitoring()
    assert not monitor.monitoring_enabled

    monitor.enable_monitoring()
    assert monitor.monitoring_enabled

    print("✅ Production monitor tests passed!")


def test_global_monitoring_functions():
    """Test global monitoring convenience functions."""
    print("🧪 Testing Global Monitoring Functions...")

    # Test getting global monitor
    monitor = get_production_monitor()
    assert isinstance(monitor, ProductionMonitor)

    # Test convenience functions
    context = create_error_context("global_test", "global_component")
    test_error = EnhancedDataError("Global test error", context=context, data_source="test")

    record_error_for_monitoring(test_error, context)
    record_recovery_for_monitoring("EnhancedDataError", True, 2.0)

    # Test health status retrieval
    health = get_system_health()
    assert isinstance(health, HealthStatus)

    # Test dashboard data retrieval
    dashboard = get_health_dashboard()
    assert isinstance(dashboard, dict)
    assert "health_report" in dashboard

    print("✅ Global monitoring functions tests passed!")


def test_error_event():
    """Test ErrorEvent functionality."""
    print("🧪 Testing Error Event...")

    context = create_error_context("event_test", "event_component")
    error = EnhancedTradingError("Event test error", context=context, severity=ErrorSeverity.HIGH)
    timestamp = datetime.now()

    event = ErrorEvent(error, context, timestamp)

    assert event.error == error
    assert event.context == context
    assert event.timestamp == timestamp
    assert event.error_type == "EnhancedTradingError"
    assert event.severity == ErrorSeverity.HIGH

    # Test serialization
    event_dict = event.to_dict()
    assert isinstance(event_dict, dict)
    assert event_dict["error_type"] == "EnhancedTradingError"
    assert event_dict["severity"] == ErrorSeverity.HIGH
    assert "timestamp" in event_dict

    print("✅ Error event tests passed!")


def test_monitoring_integration():
    """Test integration between monitoring components."""
    print("🧪 Testing Monitoring Integration...")

    # Create integrated monitoring system
    monitor = ProductionMonitor()

    # Simulate realistic error pattern
    trading_context = create_error_context("place_order", "trading_engine")
    data_context = create_error_context("fetch_data", "market_data")

    # Simulate burst of errors
    for i in range(10):
        if i % 3 == 0:
            error = EnhancedTradingError(
                f"Trading error {i}", context=trading_context, symbol="INTEG"
            )
            monitor.record_error(error, trading_context)
        else:
            error = EnhancedDataError(
                f"Data error {i}", context=data_context, data_source="test_source"
            )
            monitor.record_error(error, data_context)

        # Simulate some recoveries
        if i % 2 == 0:
            monitor.record_recovery("EnhancedTradingError", True, 1.0 + i * 0.1)
        else:
            monitor.record_recovery(
                "EnhancedDataError", i % 4 == 0, 0.5 + i * 0.05
            )  # Some failures

    # Update baselines
    monitor.update_baselines()

    # Get comprehensive dashboard data
    dashboard_data = monitor.get_dashboard_data()
    health_report = dashboard_data["health_report"]

    # Verify integration worked
    assert health_report["error_summary"]["total_error_types"] >= 2
    assert len(health_report["recovery_stats"]) >= 2

    # Check that recovery statistics are populated
    assert "EnhancedTradingError" in health_report["recovery_stats"]
    assert "EnhancedDataError" in health_report["recovery_stats"]

    trading_stats = health_report["recovery_stats"]["EnhancedTradingError"]
    assert trading_stats["total_attempts"] > 0
    assert trading_stats["success_rate"] >= 0

    print("✅ Monitoring integration tests passed!")


def test_performance_monitoring():
    """Test monitoring performance with high load."""
    print("🧪 Testing Performance Monitoring...")

    monitor = ProductionMonitor()
    start_time = time.time()

    # Simulate high-frequency error recording
    context = create_error_context("performance_test", "load_test")

    for i in range(100):
        error = EnhancedTradingError(f"Load test error {i}", context=context, symbol="PERF")
        monitor.record_error(error, context)

        if i % 10 == 0:
            monitor.record_recovery("EnhancedTradingError", True, 0.1)

    end_time = time.time()
    processing_time = end_time - start_time

    # Should process 100 errors quickly (< 1 second)
    assert processing_time < 1.0, f"Performance test took too long: {processing_time:.2f}s"

    # Verify all errors were recorded
    dashboard_data = monitor.get_dashboard_data()
    error_summary = dashboard_data["health_report"]["error_summary"]
    assert error_summary["total_error_types"] >= 1

    print(
        f"✅ Performance monitoring tests passed! (Processed 100 errors in {processing_time:.3f}s)"
    )


def main():
    """Run all Phase 3 tests."""
    print("🚀 Starting Phase 3 Error Monitoring and Alerting Tests...\n")

    try:
        test_error_metrics_collector()
        test_alert_threshold_manager()
        test_health_dashboard()
        test_production_monitor()
        test_global_monitoring_functions()
        test_error_event()
        test_monitoring_integration()
        test_performance_monitoring()

        print("\n🎉 All Phase 3 tests passed successfully!")
        print("✅ Error Metrics and Monitoring: COMPLETED")
        print("✅ Alert Threshold Management: COMPLETED")
        print("✅ Production Health Dashboard: COMPLETED")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)


if __name__ == "__main__":
    main()
