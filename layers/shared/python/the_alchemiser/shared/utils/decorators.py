#!/usr/bin/env python3
"""Business Unit: utilities; Status: current.

Exception translation decorators for The Alchemiser Trading System.

This module provides decorators that only translate exceptions without logging.
The logging is handled explicitly by orchestrators/services using the handler.
"""

from __future__ import annotations

import functools
from collections.abc import Callable

from the_alchemiser.shared.errors.exceptions import (
    ConfigurationError,
    DataProviderError,
    MarketDataError,
    StreamingError,
    TradingClientError,
)

# Type alias for flexible default return values in decorators
DefaultReturn = (
    str | int | float | bool | dict[str, object] | list[object] | None
)  # Generic function type for decorators


def translate_service_errors[F: Callable[..., object]](
    error_types: dict[type[Exception], type[Exception]] | None = None,
    default_return: DefaultReturn = None,
) -> Callable[[F], F]:
    """Translate service errors without logging.

    This decorator only translates exceptions - no logging is performed.
    Orchestrators/services should use the handler explicitly for logging.

    Args:
        error_types: Mapping of original exceptions to custom exceptions
        default_return: Default return value on error (if provided, suppresses exception)

    Returns:
        Decorated function

    """
    if error_types is None:
        error_types = {
            ConnectionError: DataProviderError,
            TimeoutError: DataProviderError,
            ValueError: DataProviderError,
            KeyError: DataProviderError,
        }

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: object, **kwargs: object) -> object:
            try:
                return func(*args, **kwargs)
            except tuple(error_types.keys()) as e:
                # Convert to custom exception type
                custom_error_type = error_types.get(type(e), DataProviderError)
                translated_error = custom_error_type(f"Service error in {func.__name__}: {e}")
                translated_error.__cause__ = e

                if default_return is not None:
                    return default_return
                raise translated_error
            except Exception as e:
                # Handle unexpected errors
                translated_error = DataProviderError(f"Unexpected error in {func.__name__}: {e}")
                translated_error.__cause__ = e

                if default_return is not None:
                    return default_return
                raise translated_error

        return wrapper  # type: ignore[return-value]

    return decorator


def translate_market_data_errors[F: Callable[..., object]](
    default_return: DefaultReturn = None,
) -> Callable[[F], F]:  # Flexible default return for any function type
    """Translate market data service error translation."""
    return translate_service_errors(
        error_types={
            ConnectionError: MarketDataError,
            TimeoutError: MarketDataError,
            ValueError: MarketDataError,
            KeyError: MarketDataError,
        },
        default_return=default_return,
    )


def translate_trading_errors[F: Callable[..., object]](
    default_return: DefaultReturn = None,
) -> Callable[[F], F]:  # Flexible default return for any function type
    """Translate trading service error translation."""
    return translate_service_errors(
        error_types={
            ConnectionError: TradingClientError,
            TimeoutError: TradingClientError,
            ValueError: TradingClientError,
            KeyError: TradingClientError,
        },
        default_return=default_return,
    )


def translate_streaming_errors[F: Callable[..., object]](
    default_return: DefaultReturn = None,
) -> Callable[[F], F]:  # Flexible default return for any function type
    """Translate streaming service error translation."""
    return translate_service_errors(
        error_types={
            ConnectionError: StreamingError,
            TimeoutError: StreamingError,
            ValueError: StreamingError,
        },
        default_return=default_return,
    )


def translate_config_errors[F: Callable[..., object]](
    default_return: DefaultReturn = None,
) -> Callable[[F], F]:  # Flexible default return for any function type
    """Translate configuration error translation."""
    return translate_service_errors(
        error_types={
            FileNotFoundError: ConfigurationError,
            ValueError: ConfigurationError,
            KeyError: ConfigurationError,
        },
        default_return=default_return,
    )
