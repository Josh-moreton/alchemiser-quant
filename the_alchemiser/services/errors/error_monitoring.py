#!/usr/bin/env python3
"""Business Unit: utilities; Status: current.

Error Monitoring and Alerting Framework for The Alchemiser Trading System.

This module implements Phase 3 of the error handling enhancement plan:
- Error Metrics and Monitoring for real-time tracking
- Alert Threshold Management with dynamic thresholds
- Production Health Dashboard for system health monitoring
"""

import logging
import statistics
from collections import defaultdict, deque
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

from the_alchemiser.utils.num import floats_equal

from .context import ErrorContextData
from .handler import ErrorSeverity


class HealthStatus(Enum):
    """Overall system health status."""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class ErrorEvent:
    """Represents an error event for monitoring."""

    def __init__(self, error: Exception, context: ErrorContextData, timestamp: datetime) -> None:
        self.error = error
        self.context = context
        self.timestamp = timestamp
        self.error_type = error.__class__.__name__
        self.severity = getattr(error, "severity", ErrorSeverity.MEDIUM)

    def to_dict(self) -> dict[str, Any]:
        """Convert error event to dictionary."""
        return {
            "error_type": self.error_type,
            "severity": self.severity,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context.to_dict() if self.context else None,
            "message": str(self.error),
        }


class RecoveryStats:
    """Statistics for error recovery attempts."""

    def __init__(self) -> None:
        self.total_attempts = 0
        self.successful_recoveries = 0
        self.failed_recoveries = 0
        self.average_recovery_time = 0.0
        self.last_recovery_attempt: datetime | None = None

    @property
    def success_rate(self) -> float:
        """Calculate recovery success rate."""
        if self.total_attempts == 0:
            return 0.0
        return self.successful_recoveries / self.total_attempts

    def to_dict(self) -> dict[str, Any]:
        """Convert recovery stats to dictionary."""
        return {
            "total_attempts": self.total_attempts,
            "successful_recoveries": self.successful_recoveries,
            "failed_recoveries": self.failed_recoveries,
            "success_rate": self.success_rate,
            "average_recovery_time": self.average_recovery_time,
            "last_recovery_attempt": (
                self.last_recovery_attempt.isoformat() if self.last_recovery_attempt else None
            ),
        }


class ErrorMetricsCollector:
    """Collect and track error metrics for monitoring."""

    def __init__(self, max_history_hours: int = 24) -> None:
        self.max_history_hours = max_history_hours
        self.error_counts: dict[str, int] = defaultdict(int)
        self.error_rates: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=1000))
        self.critical_errors: deque[ErrorEvent] = deque(maxlen=100)
        self.recovery_stats: dict[str, RecoveryStats] = defaultdict(RecoveryStats)
        self.hourly_error_counts: dict[datetime, int] = {}
        self.logger = logging.getLogger(__name__)

    def record_error(self, error: Exception, context: ErrorContextData | None = None) -> None:
        """Record error occurrence for metrics."""
        now = datetime.now(UTC)
        error_key = f"{error.__class__.__name__}:{context.component if context else 'unknown'}"

        # Update counts
        self.error_counts[error_key] += 1

        # Record timestamp for rate calculation
        self.error_rates[error_key].append(now.timestamp())

        # Track critical errors
        if hasattr(error, "severity") and error.severity == ErrorSeverity.CRITICAL:
            if context:
                self.critical_errors.append(ErrorEvent(error, context, now))

        # Update hourly counts
        hour_key = now.replace(minute=0, second=0, microsecond=0)
        self.hourly_error_counts[hour_key] = self.hourly_error_counts.get(hour_key, 0) + 1

        # Clean old data
        self._cleanup_old_data()

    def record_recovery_attempt(
        self, error_type: str, success: bool, recovery_time: float = 0.0
    ) -> None:
        """Record error recovery attempt."""
        stats = self.recovery_stats[error_type]
        stats.total_attempts += 1
        stats.last_recovery_attempt = datetime.now(UTC)

        if success:
            stats.successful_recoveries += 1
        else:
            stats.failed_recoveries += 1

        # Update average recovery time (exponential moving average)
        if recovery_time > 0:
            if floats_equal(stats.average_recovery_time, 0.0):
                stats.average_recovery_time = recovery_time
            else:
                # Exponential moving average with alpha = 0.3
                stats.average_recovery_time = (
                    0.3 * recovery_time + 0.7 * stats.average_recovery_time
                )

    def get_error_rate(self, error_type: str, window_minutes: int = 5) -> float:
        """Get error rate for specific error type."""
        cutoff = (datetime.now(UTC) - timedelta(minutes=window_minutes)).timestamp()
        recent_errors = [ts for ts in self.error_rates.get(error_type, []) if ts > cutoff]
        return len(recent_errors) / window_minutes  # errors per minute

    def get_total_error_rate(self, window_minutes: int = 5) -> float:
        """Get total error rate across all error types."""
        cutoff = (datetime.now(UTC) - timedelta(minutes=window_minutes)).timestamp()
        total_errors = 0

        for error_timestamps in self.error_rates.values():
            total_errors += len([ts for ts in error_timestamps if ts > cutoff])

        return total_errors / window_minutes  # errors per minute

    def get_critical_errors_count(self, window_minutes: int = 5) -> int:
        """Get count of critical errors in time window."""
        cutoff = datetime.now(UTC) - timedelta(minutes=window_minutes)
        return len([e for e in self.critical_errors if e.timestamp > cutoff])

    def get_error_summary(self) -> dict[str, Any]:
        """Get comprehensive error summary."""
        now = datetime.now(UTC)

        return {
            "total_error_types": len(self.error_counts),
            "error_counts": dict(self.error_counts),
            "recent_error_rate_5min": self.get_total_error_rate(5),
            "recent_error_rate_15min": self.get_total_error_rate(15),
            "recent_error_rate_60min": self.get_total_error_rate(60),
            "critical_errors_5min": self.get_critical_errors_count(5),
            "critical_errors_15min": self.get_critical_errors_count(15),
            "critical_errors_60min": self.get_critical_errors_count(60),
            "most_common_errors": sorted(
                self.error_counts.items(), key=lambda x: x[1], reverse=True
            )[:10],
            "recovery_statistics": {k: v.to_dict() for k, v in self.recovery_stats.items()},
            "timestamp": now.isoformat(),
        }

    def get_hourly_trend(self, hours: int = 24) -> dict[str, int]:
        """Get hourly error counts for trend analysis."""
        cutoff = datetime.now(UTC) - timedelta(hours=hours)
        return {
            hour.isoformat(): count
            for hour, count in self.hourly_error_counts.items()
            if hour > cutoff
        }

    def _cleanup_old_data(self) -> None:
        """Remove old data beyond retention period."""
        cutoff = datetime.now(UTC) - timedelta(hours=self.max_history_hours)

        # Clean hourly counts
        self.hourly_error_counts = {
            hour: count for hour, count in self.hourly_error_counts.items() if hour > cutoff
        }


class AlertThresholdManager:
    """Manage dynamic alert thresholds based on historical data."""

    def __init__(self) -> None:
        self.static_thresholds = {
            "error_rate_per_minute": 2.0,  # errors per minute
            "critical_errors_5min": 1,  # count in 5 minutes
            "recovery_failure_rate": 0.5,  # 50% recovery failures
            "circuit_breaker_trips": 3,  # trips in 10 minutes
        }
        self.historical_data: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=1000))
        self.threshold_multipliers = {
            "error_rate_per_minute": 2.0,  # Alert at 2x normal rate
            "critical_errors_5min": 1.5,  # Alert at 1.5x normal rate
            "recovery_failure_rate": 2.0,  # Alert at 2x normal failure rate
        }
        self.logger = logging.getLogger(__name__)

    def update_baseline(self, metric_name: str, value: float) -> None:
        """Update baseline historical data for metric."""
        self.historical_data[metric_name].append(value)

    def should_alert(self, metric_name: str, current_value: float) -> bool:
        """Determine if current metric value should trigger alert."""
        threshold = self.get_dynamic_threshold(metric_name)
        should_trigger = current_value > threshold

        if should_trigger:
            self.logger.warning(
                f"Alert threshold exceeded for {metric_name}: {current_value:.2f} > {threshold:.2f}"
            )

        return should_trigger

    def get_dynamic_threshold(self, metric_name: str) -> float:
        """Calculate dynamic threshold based on historical data."""
        historical: deque[float] = self.historical_data.get(metric_name, deque())

        # Need at least 20 data points for meaningful statistics
        if len(historical) < 20:
            return self.static_thresholds.get(metric_name, 1.0)

        try:
            # Use all historical values for now (they're all recent due to maxlen)
            recent_values = list(historical)

            if not recent_values:
                return self.static_thresholds.get(metric_name, 1.0)

            # Calculate baseline using 95th percentile
            baseline = statistics.quantiles(recent_values, n=20)[18]  # Approximates 95th percentile

            # Apply multiplier for alert threshold
            multiplier = self.threshold_multipliers.get(metric_name, 2.0)
            dynamic_threshold = baseline * multiplier

            # Don't go below static threshold
            static_threshold = self.static_thresholds.get(metric_name, 1.0)
            return float(max(dynamic_threshold, static_threshold))

        except Exception as e:
            self.logger.error(f"Error calculating dynamic threshold for {metric_name}: {e}")
            return self.static_thresholds.get(metric_name, 1.0)

    def get_threshold_summary(self) -> dict[str, dict[str, float]]:
        """Get summary of current thresholds."""
        summary = {}
        for metric_name in self.static_thresholds:
            summary[metric_name] = {
                "static_threshold": self.static_thresholds[metric_name],
                "dynamic_threshold": self.get_dynamic_threshold(metric_name),
                "data_points": len(self.historical_data.get(metric_name, [])),
            }
        return summary


class HealthReport:
    """Comprehensive health report for the system."""

    def __init__(
        self,
        status: HealthStatus,
        timestamp: datetime,
        error_summary: dict[str, Any],
        active_alerts: list[dict[str, Any]],
        recovery_stats: dict[str, RecoveryStats],
        recommendations: list[str],
    ) -> None:
        self.status = status
        self.timestamp = timestamp
        self.error_summary = error_summary
        self.active_alerts = active_alerts
        self.recovery_stats = recovery_stats
        self.recommendations = recommendations

    def to_dict(self) -> dict[str, Any]:
        """Convert health report to dictionary."""
        return {
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "error_summary": self.error_summary,
            "active_alerts": self.active_alerts,
            "recovery_stats": {k: v.to_dict() for k, v in self.recovery_stats.items()},
            "recommendations": self.recommendations,
        }


class ErrorHealthDashboard:
    """Real-time error health monitoring dashboard."""

    def __init__(self, metrics_collector: ErrorMetricsCollector) -> None:
        self.metrics = metrics_collector
        self.alerts = AlertThresholdManager()
        self.logger = logging.getLogger(__name__)

    def get_health_status(self) -> HealthStatus:
        """Get overall system health status."""
        # Check for critical errors in last 5 minutes
        critical_count = self.metrics.get_critical_errors_count(5)
        if critical_count > 0:
            return HealthStatus.CRITICAL

        # Check error rates
        current_error_rate = self.metrics.get_total_error_rate(5)
        if self.alerts.should_alert("error_rate_per_minute", current_error_rate):
            return HealthStatus.WARNING

        # Check recovery failure rates
        total_recoveries = 0
        failed_recoveries = 0
        for stats in self.metrics.recovery_stats.values():
            total_recoveries += stats.total_attempts
            failed_recoveries += stats.failed_recoveries

        if total_recoveries > 0:
            failure_rate = failed_recoveries / total_recoveries
            if self.alerts.should_alert("recovery_failure_rate", failure_rate):
                return HealthStatus.WARNING

        return HealthStatus.HEALTHY

    def get_active_alerts(self) -> list[dict[str, Any]]:
        """Get list of active alerts."""
        alerts = []

        # Check error rate alerts
        current_error_rate = self.metrics.get_total_error_rate(5)
        if self.alerts.should_alert("error_rate_per_minute", current_error_rate):
            alerts.append(
                {
                    "type": "high_error_rate",
                    "message": f"High error rate: {current_error_rate:.2f} errors/min",
                    "severity": "warning",
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            )

        # Check critical errors
        critical_count = self.metrics.get_critical_errors_count(5)
        if critical_count > 0:
            alerts.append(
                {
                    "type": "critical_errors",
                    "message": f"{critical_count} critical errors in last 5 minutes",
                    "severity": "critical",
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            )

        return alerts

    def get_recommendations(self) -> list[str]:
        """Get actionable recommendations based on current system state."""
        recommendations = []

        # Analyze error patterns
        error_summary = self.metrics.get_error_summary()

        if error_summary["critical_errors_5min"] > 0:
            recommendations.append(
                "Investigate critical errors immediately - check logs and system status"
            )

        if error_summary["recent_error_rate_5min"] > 1.0:
            recommendations.append("High error rate detected - consider reducing system load")

        # Check recovery performance
        poor_recovery_types = []
        for error_type, stats in self.metrics.recovery_stats.items():
            if stats.total_attempts > 5 and stats.success_rate < 0.7:
                poor_recovery_types.append(error_type)

        if poor_recovery_types:
            recommendations.append(
                f"Poor recovery rates for: {', '.join(poor_recovery_types)} - review recovery strategies"
            )

        # Check for repetitive errors
        most_common = error_summary["most_common_errors"][:3]
        if most_common and most_common[0][1] > 10:
            recommendations.append(
                f"Frequent error pattern detected: {most_common[0][0]} ({most_common[0][1]} occurrences) - investigate root cause"
            )

        if not recommendations:
            recommendations.append("System operating normally - continue monitoring")

        return recommendations

    def generate_health_report(self) -> HealthReport:
        """Generate comprehensive health report."""
        return HealthReport(
            status=self.get_health_status(),
            timestamp=datetime.now(UTC),
            error_summary=self.metrics.get_error_summary(),
            active_alerts=self.get_active_alerts(),
            recovery_stats=self.metrics.recovery_stats,
            recommendations=self.get_recommendations(),
        )

    def update_monitoring_baselines(self) -> None:
        """Update baseline data for dynamic threshold calculation."""
        summary = self.metrics.get_error_summary()

        # Update baselines for key metrics
        self.alerts.update_baseline("error_rate_per_minute", summary["recent_error_rate_5min"])
        self.alerts.update_baseline("critical_errors_5min", summary["critical_errors_5min"])

        # Update recovery failure rate
        total_attempts = sum(stats.total_attempts for stats in self.metrics.recovery_stats.values())
        total_failures = sum(
            stats.failed_recoveries for stats in self.metrics.recovery_stats.values()
        )
        if total_attempts > 0:
            failure_rate = total_failures / total_attempts
            self.alerts.update_baseline("recovery_failure_rate", failure_rate)


class ProductionMonitor:
    """Central production monitoring system."""

    def __init__(self) -> None:
        self.metrics = ErrorMetricsCollector()
        self.dashboard = ErrorHealthDashboard(self.metrics)
        self.monitoring_enabled = True
        self.logger = logging.getLogger(__name__)

    def record_error(self, error: Exception, context: ErrorContextData | None = None) -> None:
        """Record an error for monitoring."""
        if not self.monitoring_enabled:
            return

        try:
            self.metrics.record_error(error, context)
            self.logger.debug(f"Recorded error for monitoring: {error.__class__.__name__}")
        except Exception as e:
            self.logger.error(f"Failed to record error for monitoring: {e}")

    def record_recovery(self, error_type: str, success: bool, recovery_time: float = 0.0) -> None:
        """Record a recovery attempt."""
        if not self.monitoring_enabled:
            return

        try:
            self.metrics.record_recovery_attempt(error_type, success, recovery_time)
            self.logger.debug(f"Recorded recovery attempt: {error_type}, success={success}")
        except Exception as e:
            self.logger.error(f"Failed to record recovery attempt: {e}")

    def get_dashboard_data(self) -> dict[str, Any]:
        """Get current dashboard data."""
        try:
            health_report = self.dashboard.generate_health_report()
            return {
                "health_report": health_report.to_dict(),
                "threshold_summary": self.dashboard.alerts.get_threshold_summary(),
                "hourly_trend": self.metrics.get_hourly_trend(24),
            }
        except Exception as e:
            self.logger.error(f"Failed to generate dashboard data: {e}")
            return {
                "error": str(e),
                "status": HealthStatus.UNKNOWN.value,
                "timestamp": datetime.now(UTC).isoformat(),
            }

    def update_baselines(self) -> None:
        """Update monitoring baselines for dynamic thresholds."""
        try:
            self.dashboard.update_monitoring_baselines()
        except Exception as e:
            self.logger.error(f"Failed to update monitoring baselines: {e}")

    def is_healthy(self) -> bool:
        """Quick health check."""
        try:
            status = self.dashboard.get_health_status()
            return status in [HealthStatus.HEALTHY, HealthStatus.WARNING]
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False

    def enable_monitoring(self) -> None:
        """Enable error monitoring."""
        self.monitoring_enabled = True
        self.logger.info("Error monitoring enabled")

    def disable_monitoring(self) -> None:
        """Disable error monitoring."""
        self.monitoring_enabled = False
        self.logger.info("Error monitoring disabled")


# Global production monitor instance
_production_monitor = ProductionMonitor()


def get_production_monitor() -> ProductionMonitor:
    """Get the global production monitor instance."""
    return _production_monitor


def record_error_for_monitoring(error: Exception, context: ErrorContextData | None = None) -> None:
    """Convenience function to record error for monitoring."""
    _production_monitor.record_error(error, context)


def record_recovery_for_monitoring(
    error_type: str, success: bool, recovery_time: float = 0.0
) -> None:
    """Convenience function to record recovery attempt for monitoring."""
    _production_monitor.record_recovery(error_type, success, recovery_time)


def get_system_health() -> HealthStatus:
    """Get current system health status."""
    return _production_monitor.dashboard.get_health_status()


def get_health_dashboard() -> dict[str, Any]:
    """Get current health dashboard data."""
    return _production_monitor.get_dashboard_data()
