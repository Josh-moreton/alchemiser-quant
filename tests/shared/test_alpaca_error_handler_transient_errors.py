"""Business Unit: shared | Status: current.

Test Alpaca error handler's ability to detect transient errors.

This test validates the error classification logic that determines
whether errors should be retried.
"""

import pytest

from the_alchemiser.shared.utils.alpaca_error_handler import AlpacaErrorHandler


class TestAlpacaErrorHandlerTransientErrors:
    """Test transient error detection for Alpaca API errors."""

    def test_detects_502_error_with_code(self):
        """Test detection of 502 error code."""
        error = Exception("502 Server Error")

        is_transient, reason = AlpacaErrorHandler.is_transient_error(error)

        assert is_transient is True
        assert reason == "502 Bad Gateway"

    def test_detects_502_error_with_message(self):
        """Test detection of 502 error from message text."""
        error = Exception("Bad Gateway returned by server")

        is_transient, reason = AlpacaErrorHandler.is_transient_error(error)

        assert is_transient is True
        assert reason == "502 Bad Gateway"

    def test_detects_503_error_with_code(self):
        """Test detection of 503 error code."""
        error = Exception("503 Service Error")

        is_transient, reason = AlpacaErrorHandler.is_transient_error(error)

        assert is_transient is True
        assert reason == "503 Service Unavailable"

    def test_detects_503_error_with_message(self):
        """Test detection of 503 error from message text."""
        error = Exception("Service Unavailable - try again later")

        is_transient, reason = AlpacaErrorHandler.is_transient_error(error)

        assert is_transient is True
        assert reason == "503 Service Unavailable"

    def test_detects_504_error(self):
        """Test detection of 504 Gateway Timeout."""
        error = Exception("504 Gateway Timeout")

        is_transient, reason = AlpacaErrorHandler.is_transient_error(error)

        assert is_transient is True
        assert reason == "Gateway Timeout/Timeout"

    def test_detects_gateway_timeout_message(self):
        """Test detection of Gateway Timeout in message."""
        error = Exception("Gateway Timeout occurred")

        is_transient, reason = AlpacaErrorHandler.is_transient_error(error)

        assert is_transient is True
        assert reason == "Gateway Timeout/Timeout"

    def test_detects_generic_timeout(self):
        """Test detection of generic timeout in message."""
        error = Exception("Request timeout after 30 seconds")

        is_transient, reason = AlpacaErrorHandler.is_transient_error(error)

        assert is_transient is True
        assert reason == "Gateway Timeout/Timeout"

    def test_detects_timeout_case_insensitive(self):
        """Test detection of timeout is case-insensitive."""
        error = Exception("CONNECTION TIMEOUT")

        is_transient, reason = AlpacaErrorHandler.is_transient_error(error)

        assert is_transient is True
        assert reason == "Gateway Timeout/Timeout"

    def test_detects_html_error_with_status_code(self):
        """Test detection of HTML error page with 5xx status code.

        Note: When HTML contains "502", it matches the 502 check first.
        This is the intended behavior - specific checks take precedence.
        """
        error = Exception(
            "<html><head><title>502 Bad Gateway</title></head><body>502 Server Error</body></html>"
        )

        is_transient, reason = AlpacaErrorHandler.is_transient_error(error)

        assert is_transient is True
        assert reason == "502 Bad Gateway"

    def test_detects_html_error_with_503_code(self):
        """Test detection of HTML error page with 503 status code.

        Note: When HTML contains "503", it matches the 503 check first.
        This is the intended behavior - specific checks take precedence.
        """
        error = Exception("<html><body>503 Service Unavailable</body></html>")

        is_transient, reason = AlpacaErrorHandler.is_transient_error(error)

        assert is_transient is True
        assert reason == "503 Service Unavailable"

    def test_detects_html_error_without_status_code(self):
        """Test detection of HTML error page without explicit status code."""
        error = Exception("<html><body>Server Error</body></html>")

        is_transient, reason = AlpacaErrorHandler.is_transient_error(error)

        assert is_transient is True
        assert reason == "HTTP 5xx HTML error"

    def test_detects_html_case_insensitive(self):
        """Test detection of HTML is case-insensitive."""
        error = Exception("<HTML><BODY>Error</BODY></HTML>")

        is_transient, reason = AlpacaErrorHandler.is_transient_error(error)

        assert is_transient is True
        assert "HTML error" in reason

    def test_non_transient_error_returns_false(self):
        """Test that non-transient errors return False."""
        error = Exception("Insufficient buying power")

        is_transient, reason = AlpacaErrorHandler.is_transient_error(error)

        assert is_transient is False
        assert reason == ""

    def test_invalid_credentials_not_transient(self):
        """Test that authentication errors are not transient."""
        error = Exception("401 Unauthorized")

        is_transient, reason = AlpacaErrorHandler.is_transient_error(error)

        assert is_transient is False
        assert reason == ""

    def test_invalid_symbol_not_transient(self):
        """Test that invalid symbol errors are not transient."""
        error = Exception("404 Symbol not found")

        is_transient, reason = AlpacaErrorHandler.is_transient_error(error)

        assert is_transient is False
        assert reason == ""

    def test_generic_error_not_transient(self):
        """Test that generic errors are not transient."""
        error = Exception("Network connection failed")

        is_transient, reason = AlpacaErrorHandler.is_transient_error(error)

        assert is_transient is False
        assert reason == ""

    def test_empty_error_message_not_transient(self):
        """Test that empty error message returns False."""
        error = Exception("")

        is_transient, reason = AlpacaErrorHandler.is_transient_error(error)

        assert is_transient is False
        assert reason == ""
