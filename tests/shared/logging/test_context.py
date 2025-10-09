"""Business Unit: shared | Status: current.

Tests for logging context management module.

This test suite validates context variable management for request tracking
and error tracking, ensuring async-safety, isolation, and proper lifecycle.
"""

from __future__ import annotations

import asyncio
import uuid
from unittest.mock import patch

import pytest

from the_alchemiser.shared.logging import context


@pytest.mark.unit
class TestRequestIdManagement:
    """Test request ID context variable management."""

    def test_set_and_get_request_id(self) -> None:
        """Test setting and getting request ID."""
        test_id = "test-request-123"
        context.set_request_id(test_id)
        
        try:
            result = context.get_request_id()
            assert result == test_id
        finally:
            context.set_request_id(None)

    def test_get_request_id_returns_none_by_default(self) -> None:
        """Test that get_request_id returns None when not set."""
        # Ensure clean slate
        context.set_request_id(None)
        result = context.get_request_id()
        assert result is None

    def test_set_request_id_with_none_clears_value(self) -> None:
        """Test that setting None clears the request ID."""
        context.set_request_id("test-id")
        context.set_request_id(None)
        
        result = context.get_request_id()
        assert result is None

    def test_set_request_id_is_idempotent(self) -> None:
        """Test that setting request ID multiple times is idempotent."""
        test_id = "test-request-456"
        
        try:
            context.set_request_id(test_id)
            context.set_request_id(test_id)
            context.set_request_id(test_id)
            
            result = context.get_request_id()
            assert result == test_id
        finally:
            context.set_request_id(None)

    def test_set_request_id_overwrites_previous_value(self) -> None:
        """Test that setting a new request ID overwrites the previous one."""
        first_id = "first-id"
        second_id = "second-id"
        
        try:
            context.set_request_id(first_id)
            assert context.get_request_id() == first_id
            
            context.set_request_id(second_id)
            assert context.get_request_id() == second_id
        finally:
            context.set_request_id(None)


@pytest.mark.unit
class TestErrorIdManagement:
    """Test error ID context variable management."""

    def test_set_and_get_error_id(self) -> None:
        """Test setting and getting error ID."""
        test_id = "error-789"
        context.set_error_id(test_id)
        
        try:
            result = context.get_error_id()
            assert result == test_id
        finally:
            context.set_error_id(None)

    def test_get_error_id_returns_none_by_default(self) -> None:
        """Test that get_error_id returns None when not set."""
        # Ensure clean slate
        context.set_error_id(None)
        result = context.get_error_id()
        assert result is None

    def test_set_error_id_with_none_clears_value(self) -> None:
        """Test that setting None clears the error ID."""
        context.set_error_id("test-error")
        context.set_error_id(None)
        
        result = context.get_error_id()
        assert result is None

    def test_set_error_id_is_idempotent(self) -> None:
        """Test that setting error ID multiple times is idempotent."""
        test_id = "error-999"
        
        try:
            context.set_error_id(test_id)
            context.set_error_id(test_id)
            context.set_error_id(test_id)
            
            result = context.get_error_id()
            assert result == test_id
        finally:
            context.set_error_id(None)

    def test_set_error_id_overwrites_previous_value(self) -> None:
        """Test that setting a new error ID overwrites the previous one."""
        first_id = "error-1"
        second_id = "error-2"
        
        try:
            context.set_error_id(first_id)
            assert context.get_error_id() == first_id
            
            context.set_error_id(second_id)
            assert context.get_error_id() == second_id
        finally:
            context.set_error_id(None)


@pytest.mark.unit
class TestRequestIdGeneration:
    """Test request ID generation."""

    def test_generate_request_id_returns_string(self) -> None:
        """Test that generate_request_id returns a string."""
        result = context.generate_request_id()
        assert isinstance(result, str)

    def test_generate_request_id_returns_valid_uuid(self) -> None:
        """Test that generated ID is a valid UUID format."""
        result = context.generate_request_id()
        
        # Should be parseable as UUID
        parsed = uuid.UUID(result)
        assert str(parsed) == result

    def test_generate_request_id_returns_uuid_v4(self) -> None:
        """Test that generated ID uses UUID v4 format."""
        result = context.generate_request_id()
        parsed = uuid.UUID(result)
        
        # UUID v4 has version 4
        assert parsed.version == 4

    def test_generate_request_id_returns_unique_values(self) -> None:
        """Test that multiple calls generate different IDs."""
        id1 = context.generate_request_id()
        id2 = context.generate_request_id()
        id3 = context.generate_request_id()
        
        # All IDs should be unique
        assert id1 != id2
        assert id2 != id3
        assert id1 != id3

    def test_generate_request_id_with_mock(self) -> None:
        """Test that generate_request_id can be mocked for deterministic tests."""
        mock_uuid = "12345678-1234-5678-1234-567812345678"
        
        with patch("uuid.uuid4", return_value=uuid.UUID(mock_uuid)):
            result = context.generate_request_id()
            assert result == mock_uuid


@pytest.mark.unit
class TestContextIsolation:
    """Test context isolation between different contexts."""

    def test_request_id_and_error_id_are_independent(self) -> None:
        """Test that request_id and error_id are independent."""
        request_id = "req-123"
        error_id = "err-456"
        
        try:
            context.set_request_id(request_id)
            context.set_error_id(error_id)
            
            assert context.get_request_id() == request_id
            assert context.get_error_id() == error_id
            
            # Clear one, the other should remain
            context.set_request_id(None)
            assert context.get_request_id() is None
            assert context.get_error_id() == error_id
        finally:
            context.set_request_id(None)
            context.set_error_id(None)

    @pytest.mark.asyncio
    async def test_context_isolation_in_async_tasks(self) -> None:
        """Test that context variables are isolated between async tasks."""
        results: dict[str, str | None] = {}
        
        async def task_a() -> None:
            context.set_request_id("task-a-id")
            await asyncio.sleep(0.01)  # Yield control
            results["a"] = context.get_request_id()
            context.set_request_id(None)
        
        async def task_b() -> None:
            context.set_request_id("task-b-id")
            await asyncio.sleep(0.01)  # Yield control
            results["b"] = context.get_request_id()
            context.set_request_id(None)
        
        # Run tasks concurrently
        await asyncio.gather(task_a(), task_b())
        
        # Each task should see its own context value
        assert results["a"] == "task-a-id"
        assert results["b"] == "task-b-id"


@pytest.mark.unit
class TestEdgeCases:
    """Test edge cases and special inputs."""

    def test_set_request_id_with_empty_string(self) -> None:
        """Test setting request ID to empty string."""
        try:
            context.set_request_id("")
            result = context.get_request_id()
            assert result == ""
        finally:
            context.set_request_id(None)

    def test_set_error_id_with_empty_string(self) -> None:
        """Test setting error ID to empty string."""
        try:
            context.set_error_id("")
            result = context.get_error_id()
            assert result == ""
        finally:
            context.set_error_id(None)

    def test_set_request_id_with_very_long_string(self) -> None:
        """Test setting request ID to a very long string."""
        long_id = "x" * 10000
        
        try:
            context.set_request_id(long_id)
            result = context.get_request_id()
            assert result == long_id
            assert len(result) == 10000
        finally:
            context.set_request_id(None)

    def test_set_request_id_with_special_characters(self) -> None:
        """Test setting request ID with special characters."""
        special_id = "req-123!@#$%^&*(){}[]|\\:;\"'<>,.?/~`"
        
        try:
            context.set_request_id(special_id)
            result = context.get_request_id()
            assert result == special_id
        finally:
            context.set_request_id(None)

    def test_set_request_id_with_unicode(self) -> None:
        """Test setting request ID with unicode characters."""
        unicode_id = "req-测试-🎯-αβγ"
        
        try:
            context.set_request_id(unicode_id)
            result = context.get_request_id()
            assert result == unicode_id
        finally:
            context.set_request_id(None)


@pytest.mark.unit
class TestContextLifecycle:
    """Test context variable lifecycle and cleanup."""

    def test_multiple_set_get_cycles(self) -> None:
        """Test multiple set/get cycles work correctly."""
        ids = ["id-1", "id-2", "id-3", "id-4", "id-5"]
        
        try:
            for test_id in ids:
                context.set_request_id(test_id)
                result = context.get_request_id()
                assert result == test_id
        finally:
            context.set_request_id(None)

    def test_cleanup_restores_default_state(self) -> None:
        """Test that cleanup (set None) restores default state."""
        # Set values
        context.set_request_id("req-cleanup")
        context.set_error_id("err-cleanup")
        
        # Cleanup
        context.set_request_id(None)
        context.set_error_id(None)
        
        # Should return to default None state
        assert context.get_request_id() is None
        assert context.get_error_id() is None

    def test_context_survives_across_function_calls(self) -> None:
        """Test that context persists across function boundaries."""
        def set_context() -> None:
            context.set_request_id("persistent-id")
        
        def get_context() -> str | None:
            return context.get_request_id()
        
        try:
            set_context()
            result = get_context()
            assert result == "persistent-id"
        finally:
            context.set_request_id(None)


@pytest.mark.unit
class TestTypeAnnotations:
    """Test that type annotations are correct and enforced."""

    def test_get_request_id_return_type(self) -> None:
        """Test that get_request_id returns str or None."""
        context.set_request_id(None)
        result = context.get_request_id()
        assert result is None or isinstance(result, str)

    def test_get_error_id_return_type(self) -> None:
        """Test that get_error_id returns str or None."""
        context.set_error_id(None)
        result = context.get_error_id()
        assert result is None or isinstance(result, str)

    def test_generate_request_id_return_type(self) -> None:
        """Test that generate_request_id always returns str."""
        result = context.generate_request_id()
        assert isinstance(result, str)
        assert len(result) > 0
