"""Business Unit: order execution/placement; Status: current.

Trading Repository Interface.

This interface defines the contract for all trading operations including order
placement, position management, and portfolio operations.

This interface is designed to support typed DTO returns while maintaining
compatibility with current AlpacaManager usage patterns.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from the_alchemiser.shared_kernel.interfaces.orders import RawOrderEnvelope


class TradingRepository(Protocol):
    """Protocol defining trading operations interface.

    This interface abstracts all trading-related operations, allowing us to
    swap implementations (Alpaca, other brokers, mocks for testing) without
    changing dependent code.

    Designed to be compatible with current AlpacaManager methods while
    providing the foundation for our eventual infrastructure layer.
    """

    def get_positions_dict(self) -> dict[str, float]:
        """Get all current positions as dict.

        Returns:
            Dictionary mapping symbol to quantity owned. Only includes non-zero positions.

        """
        ...

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

    def place_order(self, order_request: Any) -> RawOrderEnvelope:
        """Place an order.

        Args:
            order_request: Order request object (currently Alpaca order request)

        Returns:
            RawOrderEnvelope with execution details and status.

        """
        ...

    def place_market_order(
        self,
        symbol: str,
        side: str,
        qty: float | None = None,
        notional: float | None = None,
    ) -> RawOrderEnvelope:
        """Place a market order.

        Args:
            symbol: Stock symbol
            side: "buy" or "sell"
            qty: Quantity to trade (use either qty OR notional)
            notional: Dollar amount to trade (use either qty OR notional)

        Returns:
            RawOrderEnvelope with execution details and status.

        """
        ...

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order.

        Args:
            order_id: Order ID to cancel

        Returns:
            True if successful, False otherwise.

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
    def trading_client(self) -> Any:
        """Access to underlying trading client for backward compatibility.

        Note: This property is for backward compatibility during migration.
        Eventually, this should be removed as dependent code migrates to
        use the interface methods directly.

        Returns:
            Underlying trading client instance.

        """
        ...
