"""Business Unit: shared | Status: current.

Metrics and observability utilities for event-driven architecture.

Provides metrics collection, event counters, and OpenTelemetry integration stubs.
"""

from __future__ import annotations

import time
from collections import defaultdict
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Any, Dict, Generator, Optional

from .logging_utils import get_logger

# Global metrics storage (in-memory for now, can be extended to external systems)
_metrics_store: Dict[str, Any] = {
    "counters": defaultdict(int),
    "gauges": defaultdict(float),
    "histograms": defaultdict(list),
    "timers": defaultdict(list),
}

logger = get_logger(__name__)


class MetricsCollector:
    """Collects and manages metrics for the trading system."""

    def __init__(self):
        """Initialize metrics collector."""
        self.start_time = datetime.now(UTC)
        self.event_start_times: Dict[str, float] = {}

    def increment_counter(self, name: str, value: int = 1, labels: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric.
        
        Args:
            name: Name of the counter
            value: Value to increment by (default: 1)
            labels: Optional labels for the metric
        """
        metric_key = self._build_metric_key(name, labels)
        _metrics_store["counters"][metric_key] += value
        
        logger.debug(f"Counter incremented: {metric_key} +{value} (total: {_metrics_store['counters'][metric_key]})")

    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Set a gauge metric value.
        
        Args:
            name: Name of the gauge
            value: Value to set
            labels: Optional labels for the metric
        """
        metric_key = self._build_metric_key(name, labels)
        _metrics_store["gauges"][metric_key] = value
        
        logger.debug(f"Gauge set: {metric_key} = {value}")

    def record_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Record a value in a histogram.
        
        Args:
            name: Name of the histogram
            value: Value to record
            labels: Optional labels for the metric
        """
        metric_key = self._build_metric_key(name, labels)
        _metrics_store["histograms"][metric_key].append(value)
        
        logger.debug(f"Histogram recorded: {metric_key} = {value}")

    def start_timer(self, name: str, labels: Optional[Dict[str, str]] = None) -> str:
        """Start a timer for measuring duration.
        
        Args:
            name: Name of the timer
            labels: Optional labels for the metric
            
        Returns:
            Timer ID for stopping the timer
        """
        metric_key = self._build_metric_key(name, labels)
        timer_id = f"{metric_key}_{time.time()}"
        self.event_start_times[timer_id] = time.time()
        
        logger.debug(f"Timer started: {timer_id}")
        return timer_id

    def stop_timer(self, timer_id: str) -> float:
        """Stop a timer and record the duration.
        
        Args:
            timer_id: Timer ID returned from start_timer
            
        Returns:
            Duration in seconds
        """
        if timer_id not in self.event_start_times:
            logger.warning(f"Timer not found: {timer_id}")
            return 0.0
            
        start_time = self.event_start_times.pop(timer_id)
        duration = time.time() - start_time
        
        # Extract metric name from timer_id
        metric_key = timer_id.rsplit("_", 1)[0]
        _metrics_store["timers"][metric_key].append(duration)
        
        logger.debug(f"Timer stopped: {timer_id} = {duration:.3f}s")
        return duration

    @contextmanager
    def timer_context(self, name: str, labels: Optional[Dict[str, str]] = None) -> Generator[None, None, None]:
        """Context manager for measuring duration.
        
        Args:
            name: Name of the timer
            labels: Optional labels for the metric
        """
        timer_id = self.start_timer(name, labels)
        try:
            yield
        finally:
            self.stop_timer(timer_id)

    def _build_metric_key(self, name: str, labels: Optional[Dict[str, str]] = None) -> str:
        """Build a metric key including labels.
        
        Args:
            name: Base metric name
            labels: Optional labels
            
        Returns:
            Formatted metric key
        """
        if not labels:
            return name
            
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of all collected metrics.
        
        Returns:
            Dictionary containing all metrics
        """
        summary = {
            "collection_start": self.start_time.isoformat(),
            "counters": dict(_metrics_store["counters"]),
            "gauges": dict(_metrics_store["gauges"]),
            "histograms": {},
            "timers": {},
        }
        
        # Calculate histogram statistics
        for key, values in _metrics_store["histograms"].items():
            if values:
                summary["histograms"][key] = {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values),
                }
                
        # Calculate timer statistics
        for key, durations in _metrics_store["timers"].items():
            if durations:
                summary["timers"][key] = {
                    "count": len(durations),
                    "min_seconds": min(durations),
                    "max_seconds": max(durations),
                    "avg_seconds": sum(durations) / len(durations),
                    "total_seconds": sum(durations),
                }
                
        return summary

    def reset_metrics(self) -> None:
        """Reset all collected metrics."""
        _metrics_store["counters"].clear()
        _metrics_store["gauges"].clear()
        _metrics_store["histograms"].clear()
        _metrics_store["timers"].clear()
        self.event_start_times.clear()
        self.start_time = datetime.now(UTC)
        
        logger.info("Metrics reset")


# Global metrics collector instance
metrics_collector = MetricsCollector()


def increment_event_counter(event_type: str, status: str = "published") -> None:
    """Increment event counter with type and status labels.
    
    Args:
        event_type: Type of event
        status: Status (published, handled, failed)
    """
    metrics_collector.increment_counter(
        "event_total",
        labels={"event_type": event_type, "status": status}
    )


def record_event_handler_latency(event_type: str, handler_name: str, latency_ms: float) -> None:
    """Record event handler latency.
    
    Args:
        event_type: Type of event handled
        handler_name: Name of the handler
        latency_ms: Latency in milliseconds
    """
    metrics_collector.record_histogram(
        "event_handler_latency_ms",
        latency_ms,
        labels={"event_type": event_type, "handler": handler_name}
    )


def set_workflow_gauge(workflow_type: str, status: str, count: int) -> None:
    """Set workflow status gauge.
    
    Args:
        workflow_type: Type of workflow (trading, signal_generation, etc.)
        status: Status (active, completed, failed)
        count: Current count
    """
    metrics_collector.set_gauge(
        "workflow_status",
        count,
        labels={"type": workflow_type, "status": status}
    )


@contextmanager
def measure_event_handling(event_type: str, handler_name: str) -> Generator[None, None, None]:
    """Context manager to measure event handling duration.
    
    Args:
        event_type: Type of event being handled
        handler_name: Name of the handler
    """
    start_time = time.time()
    try:
        yield
        # Success case
        increment_event_counter(event_type, "handled")
    except Exception:
        # Failure case
        increment_event_counter(event_type, "failed")
        raise
    finally:
        # Always record latency
        latency_ms = (time.time() - start_time) * 1000
        record_event_handler_latency(event_type, handler_name, latency_ms)


def log_metrics_summary() -> None:
    """Log a summary of current metrics."""
    summary = metrics_collector.get_metrics_summary()
    logger.info("=== METRICS SUMMARY ===")
    logger.info(f"Collection started: {summary['collection_start']}")
    
    if summary["counters"]:
        logger.info("Counters:")
        for key, value in summary["counters"].items():
            logger.info(f"  {key}: {value}")
    
    if summary["gauges"]:
        logger.info("Gauges:")
        for key, value in summary["gauges"].items():
            logger.info(f"  {key}: {value}")
    
    if summary["timers"]:
        logger.info("Timers:")
        for key, stats in summary["timers"].items():
            logger.info(f"  {key}: {stats['count']} calls, avg={stats['avg_seconds']:.3f}s")
    
    logger.info("=== END METRICS SUMMARY ===")


# OpenTelemetry integration stubs for future implementation
class OpenTelemetryStubs:
    """Stubs for OpenTelemetry integration."""
    
    @staticmethod
    def create_span(name: str, attributes: Optional[Dict[str, Any]] = None) -> Any:
        """Create a tracing span (stub implementation).
        
        Args:
            name: Span name
            attributes: Span attributes
            
        Returns:
            Mock span object
        """
        logger.debug(f"OpenTelemetry span created: {name} {attributes or {}}")
        return MockSpan(name, attributes or {})
    
    @staticmethod
    def add_event_to_span(span: Any, event_name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        """Add event to span (stub implementation).
        
        Args:
            span: Span object
            event_name: Event name
            attributes: Event attributes
        """
        logger.debug(f"OpenTelemetry event added to span: {event_name} {attributes or {}}")
        if hasattr(span, 'add_event'):
            span.add_event(event_name, attributes or {})


class MockSpan:
    """Mock span for OpenTelemetry stub."""
    
    def __init__(self, name: str, attributes: Dict[str, Any]):
        """Initialize mock span.
        
        Args:
            name: Span name
            attributes: Span attributes
        """
        self.name = name
        self.attributes = attributes
        self.events: list[Dict[str, Any]] = []
        
    def add_event(self, event_name: str, attributes: Dict[str, Any]) -> None:
        """Add event to span.
        
        Args:
            event_name: Event name
            attributes: Event attributes
        """
        self.events.append({"name": event_name, "attributes": attributes})
        
    def __enter__(self):
        """Enter context manager."""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        pass


# Global OpenTelemetry stubs instance
otel_stubs = OpenTelemetryStubs()