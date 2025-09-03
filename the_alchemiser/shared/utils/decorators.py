#!/usr/bin/env python3
"""Business Unit: shared | Status: current..

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
        def wrapper(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401  # Decorator passthrough for any function signature
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


def translate_market_data_errors(
    default_return: Any = None,
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


def translate_trading_errors(
    default_return: Any = None,
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


def translate_streaming_errors(
    default_return: Any = None,
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


def translate_config_errors(
    default_return: Any = None,
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
