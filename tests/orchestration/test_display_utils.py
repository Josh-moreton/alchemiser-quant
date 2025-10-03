"""Business Unit: orchestration | Status: current

Unit tests for display_utils deprecated module placeholder.

Tests that the module properly raises RuntimeError when imported,
as display utilities have been removed in favor of event-driven logging.
"""

import pytest


class TestDisplayUtils:
    """Test display_utils module behavior."""

    def test_display_utils_raises_runtime_error_on_import(self):
        """Test that importing display_utils raises RuntimeError with appropriate message."""
        with pytest.raises(RuntimeError) as exc_info:
            from the_alchemiser.orchestration import display_utils  # noqa: F401

        error_message = str(exc_info.value)
        assert "display_utils has been removed" in error_message
        assert "event-driven logging" in error_message

    def test_display_utils_error_message_content(self):
        """Test that the error message contains expected guidance."""
        with pytest.raises(RuntimeError) as exc_info:
            import the_alchemiser.orchestration.display_utils  # noqa: F401

        error_message = str(exc_info.value)
        # Verify the message tells users what to use instead
        assert "handlers" in error_message.lower()
        assert "the_alchemiser.orchestration.display_utils" in error_message
