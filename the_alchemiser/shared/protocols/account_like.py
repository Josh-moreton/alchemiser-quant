"""Business Unit: shared | Status: current..

Protocol for account-like objects with common account attributes.
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class AccountLikeProtocol(Protocol):
    """Protocol for objects that behave like account data.

    This covers both Alpaca account objects and account dictionaries.
    Used to replace unsafe Any usage in account handling code.
    """

    @property
    def equity(self) -> float:
        """Account equity."""
        ...

    @property
    def cash(self) -> float:
        """Available cash."""
        ...

    @property
    def buying_power(self) -> float:
        """Buying power."""
        ...

    @property
    def long_market_value(self) -> float:
        """Long market value."""
        ...

    @property
    def short_market_value(self) -> float:
        """Short market value."""
        ...

    @property
    def day_trade_count(self) -> int:
        """Number of day trades."""
        ...

    @property
    def pattern_day_trader(self) -> bool:
        """Whether marked as pattern day trader."""
        ...

    @property
    def trading_blocked(self) -> bool:
        """Whether trading is blocked."""
        ...

    @property
    def transfers_blocked(self) -> bool:
        """Whether transfers are blocked."""
        ...

    @property
    def account_blocked(self) -> bool:
        """Whether account is blocked."""
        ...

    @property
    def last_equity(self) -> float:
        """Last equity value."""
        ...
