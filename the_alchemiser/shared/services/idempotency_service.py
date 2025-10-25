#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Idempotency Service for preventing duplicate request processing.

This module provides an abstraction for idempotency checking across
Lambda invocations and event handlers. It supports both in-memory
(for testing/single-instance) and distributed cache backends
(DynamoDB, Redis, etc.) for production use.

Key Features:
- Abstract interface for pluggable backends
- In-memory implementation for development/testing
- DynamoDB-ready design for production deployment
- Automatic TTL support for cache expiration
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Protocol


class IdempotencyBackend(Protocol):
    """Protocol for idempotency backend implementations.

    Defines the interface that all idempotency backends must implement.
    This allows for pluggable backends (in-memory, DynamoDB, Redis, etc.)
    without changing consumer code.
    """

    def check_and_set(self, key: str, ttl_seconds: int = 3600) -> bool:
        """Check if key exists and set it atomically if not.

        Args:
            key: Idempotency key to check/set
            ttl_seconds: Time-to-live in seconds (default: 1 hour)

        Returns:
            True if key was newly set (first time seeing this key),
            False if key already exists (duplicate request)

        """
        ...

    def is_processed(self, key: str) -> bool:
        """Check if a key has been processed.

        Args:
            key: Idempotency key to check

        Returns:
            True if key exists (already processed), False otherwise

        """
        ...

    def mark_processed(self, key: str, ttl_seconds: int = 3600) -> None:
        """Mark a key as processed.

        Args:
            key: Idempotency key to mark as processed
            ttl_seconds: Time-to-live in seconds (default: 1 hour)

        """
        ...


class InMemoryIdempotencyBackend:
    """In-memory idempotency backend for development and testing.

    This implementation uses a simple in-memory dictionary to track
    processed keys. It includes basic TTL support by storing expiration
    times alongside keys.

    Note:
        This implementation is NOT suitable for production use with
        AWS Lambda due to stateless invocations. Use DynamoDB or
        Redis-backed implementation for production.

    Thread Safety:
        This implementation is NOT thread-safe. For multi-threaded
        environments, add appropriate locking mechanisms.

    """

    def __init__(self) -> None:
        """Initialize in-memory backend with empty cache."""
        # Dictionary mapping keys to expiration timestamps
        self._cache: dict[str, datetime] = {}

    def _cleanup_expired(self) -> None:
        """Remove expired entries from cache.

        This is called opportunistically during operations to prevent
        unbounded memory growth. Not guaranteed to run on every operation.
        """
        now = datetime.now(UTC)
        expired_keys = [key for key, expiry in self._cache.items() if expiry < now]
        for key in expired_keys:
            del self._cache[key]

    def check_and_set(self, key: str, ttl_seconds: int = 3600) -> bool:
        """Check if key exists and set it atomically if not.

        Args:
            key: Idempotency key to check/set
            ttl_seconds: Time-to-live in seconds (default: 1 hour)

        Returns:
            True if key was newly set (first time seeing this key),
            False if key already exists (duplicate request)

        """
        # Cleanup expired entries opportunistically
        if len(self._cache) > 100:  # Only cleanup periodically
            self._cleanup_expired()

        now = datetime.now(UTC)

        # Check if key exists and is not expired
        if key in self._cache:
            if self._cache[key] > now:
                return False  # Key exists and hasn't expired - duplicate
            # Key expired, remove it
            del self._cache[key]

        # Set new key with TTL
        expiry = now + timedelta(seconds=ttl_seconds)
        self._cache[key] = expiry
        return True  # Key was newly set

    def is_processed(self, key: str) -> bool:
        """Check if a key has been processed.

        Args:
            key: Idempotency key to check

        Returns:
            True if key exists (already processed), False otherwise

        """
        now = datetime.now(UTC)

        if key not in self._cache:
            return False

        # Check if key has expired
        if self._cache[key] < now:
            del self._cache[key]
            return False

        return True

    def mark_processed(self, key: str, ttl_seconds: int = 3600) -> None:
        """Mark a key as processed.

        Args:
            key: Idempotency key to mark as processed
            ttl_seconds: Time-to-live in seconds (default: 1 hour)

        """
        expiry = datetime.now(UTC) + timedelta(seconds=ttl_seconds)
        self._cache[key] = expiry


class IdempotencyService:
    """Service for checking request/event idempotency.

    This service provides a high-level API for idempotency checking
    that abstracts over different backend implementations. Consumers
    should use this service rather than backends directly.

    Example:
        >>> service = IdempotencyService()
        >>> key = "event-123-correlation-456"
        >>>
        >>> # First request
        >>> if service.is_duplicate(key):
        >>>     print("Duplicate - skip processing")
        >>> else:
        >>>     print("New request - process it")
        >>>     # ... do work ...
        >>>     service.mark_processed(key)

    Production Deployment:
        For AWS Lambda production use, replace the default in-memory
        backend with a DynamoDB-backed implementation:

        >>> from .dynamodb_backend import DynamoDBIdempotencyBackend
        >>> backend = DynamoDBIdempotencyBackend(table_name="idempotency-keys")
        >>> service = IdempotencyService(backend=backend)

    """

    def __init__(self, backend: IdempotencyBackend | None = None) -> None:
        """Initialize idempotency service.

        Args:
            backend: Backend implementation for idempotency storage.
                    Defaults to in-memory backend if not provided.

        """
        self._backend = backend if backend is not None else InMemoryIdempotencyBackend()

    def is_duplicate(self, key: str) -> bool:
        """Check if a request/event has already been processed.

        Args:
            key: Idempotency key (typically event_id + correlation_id)

        Returns:
            True if this is a duplicate (already processed), False if new

        """
        return self._backend.is_processed(key)

    def mark_processed(self, key: str, ttl_seconds: int = 3600) -> None:
        """Mark a request/event as processed.

        Args:
            key: Idempotency key to mark
            ttl_seconds: How long to remember this key (default: 1 hour)

        Note:
            TTL should be set based on your retry/replay window.
            For Lambda with EventBridge, consider 24 hours.
            For high-frequency events, shorter TTLs are acceptable.

        """
        self._backend.mark_processed(key, ttl_seconds=ttl_seconds)

    def check_and_mark(self, key: str, ttl_seconds: int = 3600) -> bool:
        """Atomic check-and-mark operation.

        This is the recommended method for most use cases as it
        combines checking and marking in a single operation.

        Args:
            key: Idempotency key to check/mark
            ttl_seconds: How long to remember this key (default: 1 hour)

        Returns:
            True if this is a new request (not duplicate),
            False if this is a duplicate (already processed)

        Example:
            >>> if service.check_and_mark(key):
            >>>     # New request - safe to process
            >>>     process_event()
            >>> else:
            >>>     # Duplicate - skip processing
            >>>     log.warning("Duplicate event detected")

        """
        return self._backend.check_and_set(key, ttl_seconds=ttl_seconds)


# Public API
__all__ = [
    "IdempotencyBackend",
    "IdempotencyService",
    "InMemoryIdempotencyBackend",
]
