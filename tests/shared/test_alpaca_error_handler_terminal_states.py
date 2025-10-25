"""Business Unit: shared | Status: current.

Test Alpaca error handler's ability to detect terminal order states.

This test validates the error classification logic that prevents duplicate
order placement when an order has already been filled or reached another
terminal state.
"""

from the_alchemiser.shared.schemas.operations import TerminalOrderError
from the_alchemiser.shared.utils.alpaca_error_handler import AlpacaErrorHandler


class TestAlpacaErrorHandlerTerminalStates:
    """Test terminal state detection for Alpaca API errors."""

    def test_detects_order_already_filled_with_error_code(self):
        """Test detection of Alpaca error code 42210000 for filled orders."""
        # This is the actual error from the issue
        error = Exception('{"code":42210000,"message":"order is already in \\"filled\\" state"}')

        is_terminal, terminal_error = AlpacaErrorHandler.is_order_already_in_terminal_state(error)

        assert is_terminal is True
        assert terminal_error == TerminalOrderError.ALREADY_FILLED

    def test_detects_order_already_filled_without_error_code(self):
        """Test detection of filled state from message alone."""
        error = Exception('order is already in "filled" state')

        is_terminal, terminal_error = AlpacaErrorHandler.is_order_already_in_terminal_state(error)

        assert is_terminal is True
        assert terminal_error == TerminalOrderError.ALREADY_FILLED

    def test_detects_order_already_cancelled(self):
        """Test detection of cancelled state."""
        error = Exception('order is already in "canceled" state')

        is_terminal, terminal_error = AlpacaErrorHandler.is_order_already_in_terminal_state(error)

        assert is_terminal is True
        assert terminal_error == TerminalOrderError.ALREADY_CANCELLED

    def test_detects_order_already_cancelled_uk_spelling(self):
        """Test detection of cancelled state with UK spelling."""
        error = Exception('order is already in "cancelled" state')

        is_terminal, terminal_error = AlpacaErrorHandler.is_order_already_in_terminal_state(error)

        assert is_terminal is True
        assert terminal_error == TerminalOrderError.ALREADY_CANCELLED

    def test_detects_order_already_rejected(self):
        """Test detection of rejected state."""
        error = Exception('order is already in "rejected" state')

        is_terminal, terminal_error = AlpacaErrorHandler.is_order_already_in_terminal_state(error)

        assert is_terminal is True
        assert terminal_error == TerminalOrderError.ALREADY_REJECTED

    def test_detects_order_already_expired(self):
        """Test detection of expired state."""
        error = Exception('order is already in "expired" state')

        is_terminal, terminal_error = AlpacaErrorHandler.is_order_already_in_terminal_state(error)

        assert is_terminal is True
        assert terminal_error == TerminalOrderError.ALREADY_EXPIRED

    def test_non_terminal_error_returns_false(self):
        """Test that non-terminal errors are not classified as terminal."""
        error = Exception("Insufficient buying power")

        is_terminal, terminal_error = AlpacaErrorHandler.is_order_already_in_terminal_state(error)

        assert is_terminal is False
        assert terminal_error is None

    def test_generic_error_returns_false(self):
        """Test that generic errors are not classified as terminal."""
        error = Exception("Network timeout")

        is_terminal, terminal_error = AlpacaErrorHandler.is_order_already_in_terminal_state(error)

        assert is_terminal is False
        assert terminal_error is None

    def test_order_pending_not_terminal(self):
        """Test that pending order state is not classified as terminal."""
        error = Exception('order is in "pending_new" state')

        is_terminal, terminal_error = AlpacaErrorHandler.is_order_already_in_terminal_state(error)

        assert is_terminal is False
        assert terminal_error is None

    def test_case_insensitive_matching(self):
        """Test that state detection is case-insensitive."""
        error = Exception('Order is already in "FILLED" state')

        is_terminal, terminal_error = AlpacaErrorHandler.is_order_already_in_terminal_state(error)

        assert is_terminal is True
        assert terminal_error == TerminalOrderError.ALREADY_FILLED
