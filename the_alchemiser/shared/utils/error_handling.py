"""Business Unit: shared | Status: current..

[DEPRECATED] Legacy error handling utilities.

This module has been deprecated and its functionality has been moved to:
- TradingSystemErrorHandler (in handler.py) for centralized error handling
- Translation decorators (in decorators.py) for exception translation
- ErrorScope (in scope.py) for context managers

This module is kept temporarily for backward compatibility but will be removed
in a future version. Please migrate to the new error handling APIs.
"""

from __future__ import annotations

import warnings
from collections.abc import Callable
from typing import Any

# Issue deprecation warning when this module is imported
warnings.warn(
    "the_alchemiser.shared.utils.error_handling is deprecated. "
    "Use TradingSystemErrorHandler, translation decorators, or ErrorScope instead.",
    DeprecationWarning,
    stacklevel=2,
)


def create_service_logger(*args: Any, **kwargs: Any) -> Any:
    """[DEPRECATED] Create a standardized logger for a service.

    This function is deprecated. Use get_service_logger from
    the_alchemiser.shared.utils.logging_utils instead.
    """
    warnings.warn(
        "create_service_logger is deprecated. "
        "Use get_service_logger from the_alchemiser.shared.logging.logging_utils instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    # Import here to avoid circular imports
    from the_alchemiser.shared.logging.logging_utils import get_service_logger

    return get_service_logger(args[0] if args else "unknown")


# Deprecated stub functions that raise errors
def _deprecated_decorator_stub(name: str) -> Callable[..., Any]:
    """Create a stub that raises deprecation error."""

    def stub(*args: Any, **kwargs: Any) -> Any:
        raise DeprecationWarning(
            f"{name} is deprecated. Use translation decorators from "
            "the_alchemiser.services.errors.decorators instead."
        )

    return stub


# Deprecated decorator stubs
handle_service_errors = _deprecated_decorator_stub("handle_service_errors")
handle_market_data_errors = _deprecated_decorator_stub("handle_market_data_errors")
handle_trading_errors = _deprecated_decorator_stub("handle_trading_errors")
handle_streaming_errors = _deprecated_decorator_stub("handle_streaming_errors")
handle_config_errors = _deprecated_decorator_stub("handle_config_errors")


# Deprecated class stubs
class ErrorHandler:
    """[DEPRECATED] Use TradingSystemErrorHandler instead."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise DeprecationWarning(
            "ErrorHandler is deprecated. Use TradingSystemErrorHandler instead."
        )


class ServiceMetrics:
    """[DEPRECATED] Service metrics functionality removed."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise DeprecationWarning(
            "ServiceMetrics is deprecated and has been removed. "
            "Use modern monitoring solutions instead."
        )


class ErrorContext:
    """[DEPRECATED] Use ErrorScope instead."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise DeprecationWarning("ErrorContext is deprecated. Use ErrorScope instead.")


# Deprecated instances
def _deprecated_instance_stub(name: str) -> Any:
    """Create a stub that raises error when accessed."""

    class DeprecatedStub:
        def __getattr__(self, item: str) -> Any:
            raise DeprecationWarning(f"{name} is deprecated and has been removed.")

    return DeprecatedStub()


service_metrics = _deprecated_instance_stub("service_metrics")


def with_metrics(*args: Any, **kwargs: Any) -> Any:
    """[DEPRECATED] Metrics decorator removed."""
    raise DeprecationWarning(
        "with_metrics decorator is deprecated and has been removed. "
        "Use modern monitoring solutions instead."
    )
