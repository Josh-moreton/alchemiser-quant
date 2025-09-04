"""Business Unit: execution | Status: current.

Infrastructure concerns separated from business logic.

This module consolidates infrastructure concerns like logging configuration,
monitoring setup, and system initialization that were previously scattered
throughout business logic components.

Phase 3 improvement addressing separation of concerns by establishing
clear boundaries between business logic and infrastructure code.
"""

from __future__ import annotations

import logging
import sys
from datetime import UTC, datetime
from typing import Any


# Infrastructure logging configuration
def configure_execution_logging(
    level: int = logging.INFO,
    *,
    enable_structured_logging: bool = True,
    enable_rich_output: bool = False,
) -> None:
    """Configure logging for the execution module.

    Separated from business logic to establish clear infrastructure boundaries.

    Args:
        level: Logging level (default: INFO)
        enable_structured_logging: Whether to use structured JSON logging
        enable_rich_output: Whether to use rich console output for development

    """
    # Create execution module logger
    execution_logger = logging.getLogger("the_alchemiser.execution")
    execution_logger.setLevel(level)

    # Prevent duplicate handlers
    if execution_logger.handlers:
        return

    if enable_rich_output:
        try:
            from rich.logging import RichHandler

            handler = RichHandler(
                show_time=True,
                show_level=True,
                show_path=True,
                markup=True,
            )
        except ImportError:
            # Fallback to standard handler if rich not available
            handler = logging.StreamHandler(sys.stdout)
    else:
        handler = logging.StreamHandler(sys.stdout)

    if enable_structured_logging:
        # Structured JSON formatter for production
        formatter = StructuredFormatter()
    else:
        # Human-readable formatter for development
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    handler.setFormatter(formatter)
    execution_logger.addHandler(handler)


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging in production environments."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON structure."""
        import json

        # Base log data
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception information if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info),
            }

        # Add any extra fields from logging context
        extra_fields = {
            key: value
            for key, value in record.__dict__.items()
            if key
            not in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "getMessage",
                "exc_info",
                "exc_text",
                "stack_info",
            }
        }

        if extra_fields:
            log_data["extra"] = extra_fields

        return json.dumps(log_data, default=str)


class SystemMetrics:
    """Infrastructure metrics collection separate from business logic."""

    def __init__(self) -> None:
        """Initialize metrics collector."""
        self._metrics: dict[str, Any] = {}
        self._start_time = datetime.now(UTC)

    def record_operation(
        self,
        operation: str,
        duration_ms: float,
        *,
        success: bool = True,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Record an operation metric.

        Args:
            operation: Operation name (e.g., "order_placement", "state_transition")
            duration_ms: Operation duration in milliseconds
            success: Whether operation succeeded
            metadata: Additional operation context

        """
        if operation not in self._metrics:
            self._metrics[operation] = {
                "count": 0,
                "success_count": 0,
                "total_duration_ms": 0.0,
                "min_duration_ms": float("inf"),
                "max_duration_ms": 0.0,
            }

        metric = self._metrics[operation]
        metric["count"] += 1
        metric["total_duration_ms"] += duration_ms
        metric["min_duration_ms"] = min(metric["min_duration_ms"], duration_ms)
        metric["max_duration_ms"] = max(metric["max_duration_ms"], duration_ms)

        if success:
            metric["success_count"] += 1

    def get_metrics_summary(self) -> dict[str, Any]:
        """Get summary of collected metrics.

        Returns:
            Dictionary containing metric summaries and system info

        """
        uptime_seconds = (datetime.now(UTC) - self._start_time).total_seconds()

        summary = {
            "system": {
                "uptime_seconds": uptime_seconds,
                "start_time": self._start_time.isoformat(),
            },
            "operations": {},
        }

        for operation, metric in self._metrics.items():
            if metric["count"] > 0:
                avg_duration = metric["total_duration_ms"] / metric["count"]
                success_rate = metric["success_count"] / metric["count"]

                summary["operations"][operation] = {
                    "count": metric["count"],
                    "success_rate": success_rate,
                    "avg_duration_ms": avg_duration,
                    "min_duration_ms": metric["min_duration_ms"],
                    "max_duration_ms": metric["max_duration_ms"],
                }

        return summary


class HealthChecker:
    """Infrastructure health checking separate from business logic."""

    def __init__(self) -> None:
        """Initialize health checker."""
        self._components: dict[str, callable] = {}

    def register_component(self, name: str, check_function: callable) -> None:
        """Register a component health check.

        Args:
            name: Component name
            check_function: Function that returns (healthy: bool, details: dict)

        """
        self._components[name] = check_function

    def check_health(self) -> dict[str, Any]:
        """Check health of all registered components.

        Returns:
            Health status summary

        """
        results = {}
        overall_healthy = True

        for component_name, check_function in self._components.items():
            try:
                is_healthy, details = check_function()
                results[component_name] = {
                    "healthy": is_healthy,
                    "details": details,
                }
                if not is_healthy:
                    overall_healthy = False
            except Exception as e:
                results[component_name] = {
                    "healthy": False,
                    "details": {"error": str(e)},
                }
                overall_healthy = False

        return {
            "overall_healthy": overall_healthy,
            "components": results,
            "timestamp": datetime.now(UTC).isoformat(),
        }


# Global infrastructure instances
_system_metrics = SystemMetrics()
_health_checker = HealthChecker()


def get_system_metrics() -> SystemMetrics:
    """Get the global system metrics instance."""
    return _system_metrics


def get_health_checker() -> HealthChecker:
    """Get the global health checker instance."""
    return _health_checker


# Utility functions for common infrastructure operations
def log_operation_timing(
    operation_name: str,
    start_time: datetime,
    *,
    success: bool = True,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Log and record timing for an operation.

    Args:
        operation_name: Name of the operation
        start_time: When the operation started
        success: Whether the operation succeeded
        metadata: Additional context

    """
    duration_ms = (datetime.now(UTC) - start_time).total_seconds() * 1000

    # Record metric
    _system_metrics.record_operation(
        operation=operation_name,
        duration_ms=duration_ms,
        success=success,
        metadata=metadata,
    )

    # Log operation
    logger = logging.getLogger("the_alchemiser.execution.infrastructure")
    logger.info(
        "Operation %s completed in %.2fms (success=%s)",
        operation_name,
        duration_ms,
        success,
        extra={
            "operation": operation_name,
            "duration_ms": duration_ms,
            "success": success,
            "metadata": metadata,
        },
    )


__all__ = [
    "HealthChecker",
    "StructuredFormatter",
    "SystemMetrics",
    "configure_execution_logging",
    "get_health_checker",
    "get_system_metrics",
    "log_operation_timing",
]
