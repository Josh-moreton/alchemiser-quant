#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Unit tests for event-specific error classes.

Tests EventPublishError exception with various configurations
and error message formatting.
"""

import pytest

from the_alchemiser.shared.events.errors import EventPublishError


class TestEventPublishError:
    """Test EventPublishError exception class."""

    def test_basic_error_message(self) -> None:
        """Test basic error without context."""
        error = EventPublishError("Service unavailable")
        
        assert str(error) == "Service unavailable"
        assert error.event_id is None
        assert error.correlation_id is None
        assert error.error_code is None

    def test_error_with_event_id(self) -> None:
        """Test error with event_id context."""
        error = EventPublishError("Publish failed", event_id="evt-123")
        
        assert "Publish failed" in str(error)
        assert "event_id=evt-123" in str(error)
        assert error.event_id == "evt-123"

    def test_error_with_correlation_id(self) -> None:
        """Test error with correlation_id context."""
        error = EventPublishError("Publish failed", correlation_id="corr-456")
        
        assert "Publish failed" in str(error)
        assert "correlation_id=corr-456" in str(error)
        assert error.correlation_id == "corr-456"

    def test_error_with_error_code(self) -> None:
        """Test error with AWS error code."""
        error = EventPublishError(
            "InternalException: Service error",
            error_code="InternalException"
        )
        
        assert "Service error" in str(error)
        assert "error_code=InternalException" in str(error)
        assert error.error_code == "InternalException"

    def test_error_with_all_context(self) -> None:
        """Test error with full context information."""
        error = EventPublishError(
            "Throttling: Request rate exceeded",
            event_id="evt-789",
            correlation_id="corr-012",
            error_code="ThrottlingException"
        )
        
        error_str = str(error)
        assert "Throttling: Request rate exceeded" in error_str
        assert "event_id=evt-789" in error_str
        assert "correlation_id=corr-012" in error_str
        assert "error_code=ThrottlingException" in error_str

    def test_error_is_raiseable(self) -> None:
        """Test that error can be raised and caught."""
        with pytest.raises(EventPublishError) as exc_info:
            raise EventPublishError("Test error", event_id="test-123")
        
        assert "Test error" in str(exc_info.value)
        assert exc_info.value.event_id == "test-123"

    def test_error_inheritance(self) -> None:
        """Test that EventPublishError inherits from Exception."""
        error = EventPublishError("Test")
        
        assert isinstance(error, Exception)
        assert isinstance(error, EventPublishError)
