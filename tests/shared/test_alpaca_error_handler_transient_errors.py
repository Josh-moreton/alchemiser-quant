"""Business Unit: shared | Status: current.

Test Alpaca error handler's ability to detect transient errors.

This test validates the error classification logic that determines
whether errors should be retried.
"""

from the_alchemiser.shared.utils.alpaca_error_handler import AlpacaErrorHandler


class TestAlpacaErrorHandlerTransientErrors:
    """Test transient error detection for Alpaca API errors."""

    def test_detects_502_error_with_code(self) -> None:
        """Test detection of 502 error code."""
        error = Exception("502 Server Error")

        is_transient, reason = AlpacaErrorHandler.is_transient_error(error)

        assert is_transient is True
        assert reason == "502 Bad Gateway"

    def test_detects_502_error_with_message(self) -> None:
        """Test detection of 502 error from message text."""
        error = Exception("Bad Gateway returned by server")

        is_transient, reason = AlpacaErrorHandler.is_transient_error(error)

        assert is_transient is True
        assert reason == "502 Bad Gateway"

    def test_detects_503_error_with_code(self) -> None:
        """Test detection of 503 error code."""
        error = Exception("503 Service Error")

        is_transient, reason = AlpacaErrorHandler.is_transient_error(error)

        assert is_transient is True
        assert reason == "503 Service Unavailable"

    def test_detects_503_error_with_message(self) -> None:
        """Test detection of 503 error from message text."""
        error = Exception("Service Unavailable - try again later")

        is_transient, reason = AlpacaErrorHandler.is_transient_error(error)

        assert is_transient is True
        assert reason == "503 Service Unavailable"

    def test_detects_504_error(self) -> None:
        """Test detection of 504 Gateway Timeout."""
        error = Exception("504 Gateway Timeout")

        is_transient, reason = AlpacaErrorHandler.is_transient_error(error)

        assert is_transient is True
        assert reason == "Gateway Timeout/Timeout"

    def test_detects_gateway_timeout_message(self) -> None:
        """Test detection of Gateway Timeout in message."""
        error = Exception("Gateway Timeout occurred")

        is_transient, reason = AlpacaErrorHandler.is_transient_error(error)

        assert is_transient is True
        assert reason == "Gateway Timeout/Timeout"

    def test_detects_generic_timeout(self) -> None:
        """Test detection of generic timeout in message."""
        error = Exception("Request timeout after 30 seconds")

        is_transient, reason = AlpacaErrorHandler.is_transient_error(error)

        assert is_transient is True
        assert reason == "Gateway Timeout/Timeout"

    def test_detects_timeout_case_insensitive(self) -> None:
        """Test detection of timeout is case-insensitive."""
        error = Exception("CONNECTION TIMEOUT")

        is_transient, reason = AlpacaErrorHandler.is_transient_error(error)

        assert is_transient is True
        assert reason == "Gateway Timeout/Timeout"

    def test_detects_html_error_with_status_code(self) -> None:
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

    def test_detects_html_error_with_503_code(self) -> None:
        """Test detection of HTML error page with 503 status code.

        Note: When HTML contains "503", it matches the 503 check first.
        This is the intended behavior - specific checks take precedence.
        """
        error = Exception("<html><body>503 Service Unavailable</body></html>")

        is_transient, reason = AlpacaErrorHandler.is_transient_error(error)

        assert is_transient is True
        assert reason == "503 Service Unavailable"

    def test_detects_html_error_without_status_code(self) -> None:
        """Test detection of HTML error page without explicit status code."""
        error = Exception("<html><body>Server Error</body></html>")

        is_transient, reason = AlpacaErrorHandler.is_transient_error(error)

        assert is_transient is True
        assert reason == "HTTP 5xx HTML error"

    def test_detects_html_case_insensitive(self) -> None:
        """Test detection of HTML is case-insensitive."""
        error = Exception("<HTML><BODY>Error</BODY></HTML>")

        is_transient, reason = AlpacaErrorHandler.is_transient_error(error)

        assert is_transient is True
        assert "HTML error" in reason

    def test_non_transient_error_returns_false(self) -> None:
        """Test that non-transient errors return False."""
        error = Exception("Insufficient buying power")

        is_transient, reason = AlpacaErrorHandler.is_transient_error(error)

        assert is_transient is False
        assert reason == ""

    def test_invalid_credentials_not_transient(self) -> None:
        """Test that authentication errors are not transient."""
        error = Exception("401 Unauthorized")

        is_transient, reason = AlpacaErrorHandler.is_transient_error(error)

        assert is_transient is False
        assert reason == ""

    def test_invalid_symbol_not_transient(self) -> None:
        """Test that invalid symbol errors are not transient."""
        error = Exception("404 Symbol not found")

        is_transient, reason = AlpacaErrorHandler.is_transient_error(error)

        assert is_transient is False
        assert reason == ""

    def test_generic_error_not_transient(self) -> None:
        """Test that generic errors are not transient."""
        error = Exception("Network connection failed")

        is_transient, reason = AlpacaErrorHandler.is_transient_error(error)

        assert is_transient is False
        assert reason == ""

    def test_empty_error_message_not_transient(self) -> None:
        """Test that empty error message returns False."""
        error = Exception("")

        is_transient, reason = AlpacaErrorHandler.is_transient_error(error)

        assert is_transient is False
        assert reason == ""


class TestDNSAndNetworkErrors:
    """Test DNS and network error detection."""

    def test_detects_name_resolution_error(self) -> None:
        """Test detection of DNS NameResolutionError."""
        error = Exception(
            "NameResolutionError: Failed to resolve 'data.alpaca.markets' "
            "([Errno 8] nodename nor servname provided, or not known)"
        )

        is_transient, reason = AlpacaErrorHandler.is_transient_error(error)

        assert is_transient is True
        assert reason == "DNS Resolution Error"

    def test_detects_getaddrinfo_failed(self) -> None:
        """Test detection of getaddrinfo failure."""
        error = Exception("[Errno -3] Temporary failure in name resolution")

        is_transient, reason = AlpacaErrorHandler.is_transient_error(error)

        assert is_transient is True
        assert reason == "DNS Resolution Error"

    def test_detects_failed_to_resolve(self) -> None:
        """Test detection of failed to resolve DNS error."""
        error = Exception("Failed to resolve hostname")

        is_transient, reason = AlpacaErrorHandler.is_transient_error(error)

        assert is_transient is True
        assert reason == "DNS Resolution Error"

    def test_detects_nodename_nor_servname(self) -> None:
        """Test detection of nodename nor servname error."""
        error = Exception("nodename nor servname provided, or not known")

        is_transient, reason = AlpacaErrorHandler.is_transient_error(error)

        assert is_transient is True
        assert reason == "DNS Resolution Error"

    def test_detects_name_or_service_not_known(self) -> None:
        """Test detection of name or service not known error."""
        error = Exception("[Errno -2] Name or service not known")

        is_transient, reason = AlpacaErrorHandler.is_transient_error(error)

        assert is_transient is True
        assert reason == "DNS Resolution Error"

    def test_detects_getaddrinfo_failed_pattern(self) -> None:
        """Test detection of getaddrinfo failed pattern."""
        error = Exception("getaddrinfo failed for api.alpaca.markets")

        is_transient, reason = AlpacaErrorHandler.is_transient_error(error)

        assert is_transient is True
        assert reason == "DNS Resolution Error"

    def test_detects_connection_refused(self) -> None:
        """Test detection of connection refused."""
        error = Exception("ConnectionRefusedError: [Errno 111] Connection refused")

        is_transient, reason = AlpacaErrorHandler.is_transient_error(error)

        assert is_transient is True
        assert reason == "Network Connection Error"

    def test_detects_connection_error(self) -> None:
        """Test detection of generic ConnectionError."""
        error = Exception("ConnectionError: Failed to establish connection")

        is_transient, reason = AlpacaErrorHandler.is_transient_error(error)

        assert is_transient is True
        assert reason == "Network Connection Error"

    def test_detects_max_retries_exceeded(self) -> None:
        """Test detection of urllib3 max retries exceeded."""
        error = Exception("HTTPSConnectionPool: Max retries exceeded with url: /v2/...")

        is_transient, reason = AlpacaErrorHandler.is_transient_error(error)

        assert is_transient is True
        assert reason == "Network Connection Error"

    def test_detects_network_unreachable(self) -> None:
        """Test detection of network unreachable."""
        error = Exception("[Errno 101] Network is unreachable")

        is_transient, reason = AlpacaErrorHandler.is_transient_error(error)

        assert is_transient is True
        assert reason == "Network Connection Error"

    def test_detects_connection_reset(self) -> None:
        """Test detection of connection reset."""
        error = Exception("Connection reset by peer")

        is_transient, reason = AlpacaErrorHandler.is_transient_error(error)

        assert is_transient is True
        assert reason == "Network Connection Error"

    def test_detects_connection_aborted(self) -> None:
        """Test detection of connection aborted."""
        error = Exception("Connection aborted")

        is_transient, reason = AlpacaErrorHandler.is_transient_error(error)

        assert is_transient is True
        assert reason == "Network Connection Error"

    def test_detects_no_route_to_host(self) -> None:
        """Test detection of no route to host."""
        error = Exception("[Errno 113] No route to host")

        is_transient, reason = AlpacaErrorHandler.is_transient_error(error)

        assert is_transient is True
        assert reason == "Network Connection Error"

    def test_dns_errors_case_insensitive(self) -> None:
        """Test that DNS error detection is case-insensitive."""
        error = Exception("NAMERESOLUTIONERROR: FAILED TO RESOLVE")

        is_transient, reason = AlpacaErrorHandler.is_transient_error(error)

        assert is_transient is True
        assert reason == "DNS Resolution Error"

    def test_connection_errors_case_insensitive(self) -> None:
        """Test that connection error detection is case-insensitive."""
        error = Exception("CONNECTIONERROR: CONNECTION REFUSED")

        is_transient, reason = AlpacaErrorHandler.is_transient_error(error)

        assert is_transient is True
        assert reason == "Network Connection Error"
