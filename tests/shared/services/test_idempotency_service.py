#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Unit tests for idempotency service.

Tests cover:
- Basic idempotency checking and marking
- TTL expiration behavior
- Atomic check-and-mark operations
- In-memory backend implementation
- Protocol compliance
"""

from __future__ import annotations

import time
from unittest.mock import Mock

from the_alchemiser.shared.services.idempotency_service import (
    IdempotencyService,
    InMemoryIdempotencyBackend,
)


class TestInMemoryIdempotencyBackend:
    """Test in-memory idempotency backend implementation."""

    def test_check_and_set_new_key(self) -> None:
        """Test check_and_set returns True for new key."""
        backend = InMemoryIdempotencyBackend()
        result = backend.check_and_set("test-key-1")
        assert result is True

    def test_check_and_set_existing_key(self) -> None:
        """Test check_and_set returns False for existing key."""
        backend = InMemoryIdempotencyBackend()
        backend.check_and_set("test-key-1")
        result = backend.check_and_set("test-key-1")
        assert result is False

    def test_check_and_set_expired_key(self) -> None:
        """Test check_and_set returns True for expired key."""
        backend = InMemoryIdempotencyBackend()

        # Set key with 0 second TTL (immediately expired)
        backend.check_and_set("test-key-1", ttl_seconds=0)

        # Small delay to ensure expiration
        time.sleep(0.01)

        # Should be able to set again
        result = backend.check_and_set("test-key-1")
        assert result is True

    def test_is_processed_new_key(self) -> None:
        """Test is_processed returns False for new key."""
        backend = InMemoryIdempotencyBackend()
        result = backend.is_processed("test-key-1")
        assert result is False

    def test_is_processed_existing_key(self) -> None:
        """Test is_processed returns True for existing key."""
        backend = InMemoryIdempotencyBackend()
        backend.mark_processed("test-key-1")
        result = backend.is_processed("test-key-1")
        assert result is True

    def test_is_processed_expired_key(self) -> None:
        """Test is_processed returns False for expired key."""
        backend = InMemoryIdempotencyBackend()

        # Mark as processed with 0 second TTL
        backend.mark_processed("test-key-1", ttl_seconds=0)

        # Small delay to ensure expiration
        time.sleep(0.01)

        result = backend.is_processed("test-key-1")
        assert result is False

    def test_mark_processed_sets_key(self) -> None:
        """Test mark_processed sets key correctly."""
        backend = InMemoryIdempotencyBackend()
        backend.mark_processed("test-key-1")

        # Should be marked as processed
        assert backend.is_processed("test-key-1") is True

        # Should not allow setting again
        assert backend.check_and_set("test-key-1") is False

    def test_mark_processed_with_custom_ttl(self) -> None:
        """Test mark_processed respects custom TTL."""
        backend = InMemoryIdempotencyBackend()
        backend.mark_processed("test-key-1", ttl_seconds=3600)

        # Should be marked as processed
        assert backend.is_processed("test-key-1") is True

    def test_cleanup_expired_removes_old_entries(self) -> None:
        """Test that expired entries are cleaned up."""
        backend = InMemoryIdempotencyBackend()

        # Add many keys to trigger cleanup
        for i in range(150):
            backend.mark_processed(f"test-key-{i}", ttl_seconds=0)

        # Small delay to ensure expiration
        time.sleep(0.01)

        # Add one more key to trigger cleanup
        backend.check_and_set("trigger-cleanup")

        # Expired keys should be gone (check_and_set should return True)
        assert backend.check_and_set("test-key-0") is True

    def test_different_keys_independent(self) -> None:
        """Test that different keys are tracked independently."""
        backend = InMemoryIdempotencyBackend()

        backend.mark_processed("key-1")
        backend.mark_processed("key-2")

        assert backend.is_processed("key-1") is True
        assert backend.is_processed("key-2") is True
        assert backend.is_processed("key-3") is False


class TestIdempotencyService:
    """Test idempotency service high-level API."""

    def test_service_with_default_backend(self) -> None:
        """Test service works with default in-memory backend."""
        service = IdempotencyService()
        assert service.is_duplicate("test-key") is False

    def test_service_with_custom_backend(self) -> None:
        """Test service works with custom backend."""
        mock_backend = Mock()
        mock_backend.is_processed.return_value = False

        service = IdempotencyService(backend=mock_backend)
        result = service.is_duplicate("test-key")

        assert result is False
        mock_backend.is_processed.assert_called_once_with("test-key")

    def test_is_duplicate_new_request(self) -> None:
        """Test is_duplicate returns False for new request."""
        service = IdempotencyService()
        result = service.is_duplicate("test-key-1")
        assert result is False

    def test_is_duplicate_after_marking(self) -> None:
        """Test is_duplicate returns True after marking processed."""
        service = IdempotencyService()
        service.mark_processed("test-key-1")
        result = service.is_duplicate("test-key-1")
        assert result is True

    def test_mark_processed_with_default_ttl(self) -> None:
        """Test mark_processed uses default TTL."""
        mock_backend = Mock()
        service = IdempotencyService(backend=mock_backend)

        service.mark_processed("test-key")

        mock_backend.mark_processed.assert_called_once_with("test-key", ttl_seconds=3600)

    def test_mark_processed_with_custom_ttl(self) -> None:
        """Test mark_processed uses custom TTL."""
        mock_backend = Mock()
        service = IdempotencyService(backend=mock_backend)

        service.mark_processed("test-key", ttl_seconds=7200)

        mock_backend.mark_processed.assert_called_once_with("test-key", ttl_seconds=7200)

    def test_check_and_mark_new_request(self) -> None:
        """Test check_and_mark returns True for new request."""
        service = IdempotencyService()
        result = service.check_and_mark("test-key-1")
        assert result is True

    def test_check_and_mark_duplicate_request(self) -> None:
        """Test check_and_mark returns False for duplicate."""
        service = IdempotencyService()
        service.check_and_mark("test-key-1")
        result = service.check_and_mark("test-key-1")
        assert result is False

    def test_check_and_mark_delegates_to_backend(self) -> None:
        """Test check_and_mark delegates to backend properly."""
        mock_backend = Mock()
        mock_backend.check_and_set.return_value = True

        service = IdempotencyService(backend=mock_backend)
        result = service.check_and_mark("test-key", ttl_seconds=1800)

        assert result is True
        mock_backend.check_and_set.assert_called_once_with("test-key", ttl_seconds=1800)

    def test_multiple_keys_tracked_independently(self) -> None:
        """Test that different keys are tracked independently."""
        service = IdempotencyService()

        # Mark key-1 as processed
        service.mark_processed("key-1")

        # key-1 should be duplicate, key-2 should be new
        assert service.is_duplicate("key-1") is True
        assert service.is_duplicate("key-2") is False

    def test_workflow_check_mark_pattern(self) -> None:
        """Test typical workflow using check_and_mark pattern."""
        service = IdempotencyService()

        # First call: not a duplicate, should process
        if service.check_and_mark("workflow-123"):
            processed = True
        else:
            processed = False

        assert processed is True

        # Second call: duplicate, should skip
        if service.check_and_mark("workflow-123"):
            processed_again = True
        else:
            processed_again = False

        assert processed_again is False

    def test_workflow_separate_check_mark_pattern(self) -> None:
        """Test workflow using separate check and mark calls."""
        service = IdempotencyService()

        # Check if duplicate
        if not service.is_duplicate("event-456"):
            # Process event
            service.mark_processed("event-456")
            processed = True
        else:
            processed = False

        assert processed is True

        # Second attempt
        if not service.is_duplicate("event-456"):
            service.mark_processed("event-456")
            processed_again = True
        else:
            processed_again = False

        assert processed_again is False
