#!/usr/bin/env python3
"""Business Unit: shared | Status: current..retry_count = attempt
                        raise

                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (backoff_factor**attempt), max_delay)
                    if jitter:
                        delay *= 0.5 + random.random() * 0.5  # Add 50% jitter

                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    time.sleep(delay)

            # This should never be reached due to the raise in the except block
            if last_exception:
                raise last_exception
            raise RuntimeError("Unexpected state in retry logic")

        return wrapper

    return decorator


# Common retry configurations for different scenarios


def retry_api_call(
    max_retries: int = 3, base_delay: float = 1.0
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Retry decorator for API calls with common exceptions."""
    from the_alchemiser.shared.types.exceptions import DataProviderError, TradingClientError

    return retry_with_backoff(
        exceptions=(DataProviderError, TradingClientError, ConnectionError, TimeoutError),
        max_retries=max_retries,
        base_delay=base_delay,
    )


def retry_data_fetch(
    max_retries: int = 3, base_delay: float = 0.5
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Retry decorator for data fetching operations."""
    from the_alchemiser.shared.types.exceptions import DataProviderError

    return retry_with_backoff(
        exceptions=(DataProviderError, ConnectionError, TimeoutError),
        max_retries=max_retries,
        base_delay=base_delay,
    )


def retry_order_execution(
    max_retries: int = 2, base_delay: float = 0.5
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Retry decorator for order execution with limited retries."""
    from the_alchemiser.shared.types.exceptions import OrderExecutionError

    return retry_with_backoff(
        exceptions=(OrderExecutionError,),
        max_retries=max_retries,
        base_delay=base_delay,
    )
