"""Async utilities for concurrent task execution.

Business Unit: shared
Status: current
"""

import asyncio
from collections.abc import Awaitable, Iterator


async def gather_with_concurrency[T](
    semaphore: asyncio.Semaphore, awaitables: list[Awaitable[T]]
) -> list[T]:
    """Execute awaitables concurrently with limited concurrency.

    This function takes a list of awaitable objects and executes them concurrently,
    using a semaphore to limit the number of concurrent executions. This is useful
    for controlling resource usage when processing many async operations.

    Args:
        semaphore: Asyncio semaphore to control concurrency limits
        awaitables: List of awaitable objects to execute concurrently

    Returns:
        List of results from the awaitable objects in the same order as input

    Example:
        >>> semaphore = asyncio.Semaphore(5)  # Limit to 5 concurrent operations
        >>> tasks = [fetch_data(url) for url in urls]
        >>> results = await gather_with_concurrency(semaphore, tasks)

    """
    async def _limited_awaitable(awaitable: Awaitable[T]) -> T:
        async with semaphore:
            return await awaitable

    limited_awaitables = [_limited_awaitable(aw) for aw in awaitables]
    return await asyncio.gather(*limited_awaitables)


async def limited_as_completed[T](
    semaphore: asyncio.Semaphore, awaitables: list[Awaitable[T]]
) -> Iterator[Awaitable[T]]:
    """Yield tasks as they complete with limited concurrency.

    This function takes a list of awaitable objects and yields them as they complete,
    using a semaphore to limit the number of concurrent executions. Unlike gather_with_concurrency,
    this allows processing results as soon as they become available rather than waiting
    for all tasks to complete.

    Args:
        semaphore: Asyncio semaphore to control concurrency limits
        awaitables: List of awaitable objects to execute concurrently

    Yields:
        Awaitable objects as they complete, wrapped to respect concurrency limits

    Example:
        >>> semaphore = asyncio.Semaphore(3)  # Limit to 3 concurrent operations
        >>> tasks = [fetch_data(url) for url in urls]
        >>> async for completed_task in limited_as_completed(semaphore, tasks):
        ...     result = await completed_task
        ...     process_result(result)

    """
    async def _limited_awaitable(awaitable: Awaitable[T]) -> T:
        async with semaphore:
            return await awaitable

    limited_awaitables = [_limited_awaitable(aw) for aw in awaitables]
    for completed in asyncio.as_completed(limited_awaitables):
        yield completed