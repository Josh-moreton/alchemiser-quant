"""Business Unit: shared | Status: current.

Alpaca exception definitions.

Normalized exception hierarchy for Alpaca broker operations,
providing consistent error handling across all modules.
"""

from __future__ import annotations


class AlpacaError(Exception):
    """Base exception for Alpaca broker operations."""

    def __init__(self, message: str, *, original_error: Exception | None = None) -> None:
        """Initialize with message and optional original error.
        
        Args:
            message: Error message
            original_error: Original exception that caused this error

        """
        super().__init__(message)
        self.original_error = original_error


class AlpacaConnectionError(AlpacaError):
    """Error connecting to Alpaca API."""


class AlpacaAuthenticationError(AlpacaError):
    """Error authenticating with Alpaca API."""


class AlpacaOrderError(AlpacaError):
    """Error with order operations."""


class AlpacaDataError(AlpacaError):
    """Error retrieving market data."""


class AlpacaPositionError(AlpacaError):
    """Error with position operations."""


class AlpacaAccountError(AlpacaError):
    """Error with account operations."""


def normalize_alpaca_error(error: Exception, context: str = "Operation") -> AlpacaError:
    """Normalize an exception into an appropriate AlpacaError subclass.
    
    Args:
        error: Original exception
        context: Context string for error message
        
    Returns:
        Appropriate AlpacaError subclass

    """
    error_str = str(error).lower()
    message = f"{context} failed: {error}"
    
    # Map common error patterns to specific exception types
    if "auth" in error_str or "unauthorized" in error_str or "forbidden" in error_str:
        return AlpacaAuthenticationError(message, original_error=error)
    if "connection" in error_str or "timeout" in error_str or "network" in error_str:
        return AlpacaConnectionError(message, original_error=error)
    if "order" in error_str:
        return AlpacaOrderError(message, original_error=error)
    if "position" in error_str:
        return AlpacaPositionError(message, original_error=error)
    if "account" in error_str:
        return AlpacaAccountError(message, original_error=error)
    if "data" in error_str or "quote" in error_str or "bar" in error_str:
        return AlpacaDataError(message, original_error=error)
    return AlpacaError(message, original_error=error)