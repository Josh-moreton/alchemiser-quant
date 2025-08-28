"""Business Unit: utilities; Status: current.

Account Repository Interface.

This interface defines the contract for all account-related operations including
account information, portfolio data, and balance management.

This interface is designed to match our current AlpacaManager usage patterns
while providing the abstraction needed for the eventual architecture.
"""
from __future__ import annotations


from typing import Any, Protocol


class AccountRepository(Protocol):
    """Protocol defining account operations interface.

    This interface abstracts all account-related operations, allowing us to
    swap implementations (Alpaca, other brokers, mocks for testing) without
    changing dependent code.

    Designed to be compatible with current usage patterns while providing
    the foundation for our eventual infrastructure layer.
    """

    def get_account(self) -> dict[str, Any] | None:
        """Get account information.

        Returns:
            Account information as dictionary, or None if failed.

        """
        ...

    def get_buying_power(self) -> float | None:
        """Get current buying power.

        Returns:
            Available buying power in dollars, or None if failed.

        """
        ...

    def get_portfolio_value(self) -> float | None:
        """Get total portfolio value.

        Returns:
            Total portfolio value in dollars, or None if failed.

        """
        ...

    def get_positions(self) -> list[Any]:
        """Get all current positions.

        Returns:
            List of position objects with attributes like symbol, qty, market_value, etc.

        """
        ...

    def get_positions_dict(self) -> dict[str, float]:
        """Get all current positions as simple dict.

        Returns:
            Dictionary mapping symbol to quantity owned. Only includes non-zero positions.

        """
        ...

    def get_portfolio_history(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        timeframe: str = "1Day",
    ) -> dict[str, Any] | None:
        """Get portfolio performance history.

        Args:
            start_date: Start date (ISO format), defaults to 1 month ago
            end_date: End date (ISO format), defaults to today
            timeframe: Timeframe for data points

        Returns:
            Portfolio history data, or None if failed.

        """
        ...

    def get_activities(
        self,
        activity_type: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get account activities (trades, dividends, etc.).

        Args:
            activity_type: Filter by activity type (optional)
            start_date: Start date (ISO format), defaults to 1 week ago
            end_date: End date (ISO format), defaults to today

        Returns:
            List of activity records.

        """
        ...

    def validate_connection(self) -> bool:
        """Validate connection to account service.

        Returns:
            True if connection is valid, False otherwise.

        """
        ...

    @property
    def is_paper_trading(self) -> bool:
        """Check if this is paper trading.

        Returns:
            True if paper trading, False if live trading.

        """
        ...
