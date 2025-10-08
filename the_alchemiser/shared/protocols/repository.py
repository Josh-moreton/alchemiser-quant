"""Business Unit: shared | Status: current.

Shared protocols and interfaces for trading and data access.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from alpaca.trading.requests import (
        LimitOrderRequest,
        MarketOrderRequest,
        ReplaceOrderRequest,
    )

    from the_alchemiser.shared.schemas.broker import OrderExecutionResult
    from the_alchemiser.shared.schemas.execution_report import ExecutedOrder
    from the_alchemiser.shared.schemas.operations import OrderCancellationResult


class AccountRepository(Protocol):
    """Protocol defining account operations interface."""

    def get_account(self) -> dict[str, Any] | None:
        """Get account information."""
        ...

    def get_buying_power(self) -> Decimal | None:
        """Get current buying power."""
        ...

    def get_positions_dict(self) -> dict[str, Decimal]:
        """Get all current positions as dict."""
        ...


class MarketDataRepository(Protocol):
    """Protocol defining market data operations interface."""

    def get_current_price(self, symbol: str) -> float | None:
        """Get current price for a symbol."""
        ...

    def get_quote(self, symbol: str) -> dict[str, Any] | None:
        """Get quote information for a symbol."""
        ...


class TradingRepository(Protocol):
    """Protocol defining trading operations interface.

    This interface abstracts all trading-related operations, allowing us to
    swap implementations (Alpaca, other brokers, mocks for testing) without
    changing dependent code.

    Designed to be compatible with current AlpacaManager methods while
    providing the foundation for our eventual infrastructure layer.
    """

    def get_positions_dict(self) -> dict[str, Decimal]:
        """Get all current positions as dict.

        Returns:
            Dictionary mapping symbol to quantity owned (as Decimal).
            Only includes non-zero positions.

        """
        ...

    def get_account(self) -> dict[str, Any] | None:
        """Get account information.

        Returns:
            Account information as dictionary, or None if failed.

        """
        ...

    def get_buying_power(self) -> Decimal | None:
        """Get current buying power.

        Returns:
            Available buying power as Decimal, or None if failed.

        """
        ...

    def get_portfolio_value(self) -> Decimal | None:
        """Get total portfolio value.

        Returns:
            Total portfolio value as Decimal, or None if failed.

        """
        ...

    def place_order(self, order_request: LimitOrderRequest | MarketOrderRequest) -> ExecutedOrder:
        """Place an order.

        Args:
            order_request: Order request object (Alpaca LimitOrderRequest or MarketOrderRequest)

        Returns:
            ExecutedOrder with execution details and status.

        """
        ...

    def place_market_order(
        self,
        symbol: str,
        side: str,
        qty: float | None = None,
        notional: float | None = None,
        *,
        is_complete_exit: bool = False,
    ) -> ExecutedOrder:
        """Place a market order.

        Args:
            symbol: Stock symbol
            side: "buy" or "sell"
            qty: Quantity to trade (use either qty OR notional)
            notional: Dollar amount to trade (use either qty OR notional)
            is_complete_exit: If True and side is 'sell', use actual available quantity

        Returns:
            ExecutedOrder with execution details and status.

        """
        ...

    def cancel_order(self, order_id: str) -> OrderCancellationResult:
        """Cancel an order.

        Args:
            order_id: Order ID to cancel

        Returns:
            OrderCancellationResult with detailed cancellation status.

        """
        ...

    def replace_order(
        self, order_id: str, order_data: ReplaceOrderRequest | None = None
    ) -> OrderExecutionResult:
        """Replace an order with new parameters.

        Args:
            order_id: The unique order ID to replace
            order_data: The parameters to update (quantity, limit_price, etc.)

        Returns:
            OrderExecutionResult with the updated order details.

        """
        ...

    def cancel_all_orders(self, symbol: str | None = None) -> bool:
        """Cancel all orders, optionally filtered by symbol.

        Args:
            symbol: If provided, only cancel orders for this symbol

        Returns:
            True if successful, False otherwise.

        """
        ...

    def liquidate_position(self, symbol: str) -> str | None:
        """Liquidate entire position using close_position API.

        Args:
            symbol: Symbol to liquidate

        Returns:
            Order ID if successful, None if failed.

        """
        ...

    def close_all_positions(self, *, cancel_orders: bool = True) -> list[dict[str, Any]]:
        """Liquidate all positions for an account.

        Places an order for each open position to liquidate.

        Args:
            cancel_orders: If True, cancel all open orders before liquidating positions

        Returns:
            List of responses from each closed position containing status and order info

        """
        ...

    def validate_connection(self) -> bool:
        """Validate connection to trading service.

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

    @property
    def trading_client(
        self,
    ) -> Any:  # noqa: ANN401  # External broker SDK trading client object
        """Access to underlying trading client for backward compatibility.

        Note: This property is for backward compatibility during migration.
        Eventually, this should be removed as dependent code migrates to
        use the interface methods directly.

        Returns:
            Underlying trading client instance.

        """
        ...
