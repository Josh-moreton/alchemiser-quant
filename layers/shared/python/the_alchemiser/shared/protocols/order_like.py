"""Business Unit: shared | Status: current.

Order-like Object Protocol.

Defines minimal interfaces for objects that have order-like attributes.
Used in mapping functions to provide type safety while maintaining flexibility
for different order object implementations (domain entities, Alpaca SDK objects, etc.).

These protocols enable duck typing validation without requiring inheritance,
making them ideal for adapter patterns and boundary normalization.

Usage Examples
--------------
These protocols are typically used in mapping/normalization functions:

    >>> from alpaca.trading import Order as AlpacaOrder
    >>> from the_alchemiser.shared.protocols.order_like import OrderLikeProtocol
    >>>
    >>> def normalize_order(order: OrderLikeProtocol) -> dict:
    ...     '''Convert any order-like object to standard dict.'''
    ...     return {
    ...         'id': order.id,
    ...         'symbol': order.symbol,
    ...         'qty': order.qty,
    ...         'side': order.side,
    ...     }
    >>>
    >>> # Works with Alpaca SDK objects
    >>> alpaca_order = AlpacaOrder(...)  # from broker
    >>> result = normalize_order(alpaca_order)
    >>>
    >>> # Works with domain entities
    >>> domain_order = DomainOrder(...)
    >>> result = normalize_order(domain_order)
    >>>
    >>> # Works with test mocks
    >>> mock_order = Mock(spec=OrderLikeProtocol)
    >>> result = normalize_order(mock_order)

Type Flexibility
----------------
Quantity fields (qty, filled_qty) accept `float | int | str | None` to support:
- **Strings**: Alpaca SDK returns quantities as strings (e.g., "100.5")
- **Decimals/Floats**: Domain models may use Decimal or float for calculations
- **Ints**: Whole share quantities
- **None**: Orders before submission or optional fields

When working with string quantities, ensure they are convertible to numeric types
at boundary validation points.

Related Protocols
-----------------
- `AlpacaOrderProtocol` (alpaca.py): More specific protocol with Alpaca-specific fields
- `StrategyOrderProtocol` (strategy_tracking.py): Strategy-level order tracking
- `PositionLikeProtocol`: Related protocol for position objects

Error Handling
--------------
Property access may raise AttributeError if object doesn't implement the protocol.
Use `isinstance(obj, OrderLikeProtocol)` to check conformance at runtime.

None values in optional fields (id, order_type, status, filled_qty) should be
handled explicitly by consumers.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class OrderLikeProtocol(Protocol):
    """Protocol for objects that have basic order attributes.

    Used in mapping functions where order objects from different sources
    (domain entities, broker SDK objects, dicts) need to be normalized.

    This protocol uses structural typing (duck typing) which means any object
    with matching properties will satisfy the protocol, regardless of inheritance.

    Example implementations:
        - Alpaca SDK Order objects (alpaca.trading.Order)
        - Domain order entities (the_alchemiser.execution_v2.domain.Order)
        - Dictionary representations from APIs
        - Test mocks and fixtures

    Type Constraints:
        Quantity fields accept float|int|str to accommodate different sources:
        - Alpaca SDK uses strings (e.g., "100.5")
        - Domain models may use Decimal or float
        - Integer quantities for whole shares

        Side field accepts any string but should be validated to:
        - "buy" or "sell" for most brokers
        - Possibly "sell_short" depending on broker

    Error Handling:
        - Property access raises AttributeError if not implemented
        - None values must be handled by consumers for optional fields
        - String quantities should be validated/converted at boundaries
    """

    @property
    def id(self) -> str | None:
        """Order identifier.

        Returns:
            Unique order ID assigned by broker, or None for orders
            not yet submitted.

        Examples:
            "4fe538e7-6b13-4e7e-91a1-1234567890ab"  # UUID from Alpaca
            None  # New order before submission

        """
        ...

    @property
    def symbol(self) -> str:
        """Trading symbol.

        Returns:
            Symbol/ticker of the security (e.g., "AAPL", "SPY").
            Always required; never None.

        Examples:
            "AAPL"  # Stock
            "SPY"   # ETF
            "BTC/USD"  # Crypto (broker-dependent format)

        """
        ...

    @property
    def qty(self) -> float | int | str | None:
        """Order quantity.

        Returns:
            Number of shares/units to trade. May be string (Alpaca SDK),
            numeric (domain models), or None (unspecified).

        Type Guidance:
            - String: From Alpaca SDK, e.g., "100.5"
            - Float/Decimal: Domain calculations, e.g., 100.5
            - Int: Whole shares, e.g., 100
            - None: Not yet specified (rare)

        Examples:
            "100.5"  # Fractional shares from Alpaca
            100      # Whole shares
            100.5    # Calculated quantity
            None     # Notional order (dollar-based)

        """
        ...

    @property
    def side(self) -> str:
        """Order side (buy/sell).

        Returns:
            Direction of the trade. Expected values are broker-specific
            but typically "buy" or "sell".

        Expected Values:
            - "buy": Long/increase position
            - "sell": Reduce/close long position
            - "sell_short": Short selling (broker-dependent)

        Note:
            No validation is enforced at protocol level. Consumers must
            validate against broker-specific allowed values.

        Examples:
            "buy"
            "sell"

        """
        ...

    @property
    def order_type(self) -> str | None:
        """Order type (market/limit).

        Returns:
            Type of order execution, or None if not specified.

        Expected Values:
            - "market": Execute at current market price
            - "limit": Execute at specified limit price or better
            - "stop": Stop loss order
            - "stop_limit": Stop with limit price
            - None: Default to market (implementation-specific)

        Examples:
            "market"
            "limit"
            None

        """
        ...

    @property
    def status(self) -> str | None:
        """Order status.

        Returns:
            Current lifecycle status of the order, or None if
            not yet assigned (pre-submission).

        Expected Values (Alpaca):
            - "new": Just submitted
            - "accepted": Accepted by broker
            - "pending_new": Pending acceptance
            - "partially_filled": Partial execution
            - "filled": Fully executed
            - "canceled": Canceled by user/system
            - "rejected": Rejected by broker
            - None: Not yet submitted

        Examples:
            "filled"
            "pending_new"
            None  # Pre-submission

        """
        ...

    @property
    def filled_qty(self) -> float | int | str | None:
        """Filled quantity.

        Returns:
            Number of shares/units actually executed, or None/0 if
            no fills yet.

        Type Guidance:
            Same as qty field - may be string (SDK), numeric (domain),
            or None/0 (no fills).

        Examples:
            "50.5"  # Partial fill (Alpaca SDK)
            100     # Fully filled
            0       # No fills
            None    # No fills

        """
        ...


@runtime_checkable
class PositionLikeProtocol(Protocol):
    """Protocol for objects that have basic position attributes.

    Used in mapping functions where position objects from different sources
    need to be normalized.

    Similar to OrderLikeProtocol but focused on position/holding state rather
    than transactional order data.

    Example implementations:
        - Alpaca SDK Position objects (alpaca.trading.Position)
        - Domain position entities
        - Portfolio tracking objects
        - Test mocks and fixtures

    Key Difference from OrderLikeProtocol:
        Position quantity is always present (never None) since positions
        represent actual holdings, not pending orders.

    Type Constraints:
        Quantity/monetary fields accept float|int|str to accommodate:
        - Alpaca SDK uses strings for all numeric fields
        - Domain models may use Decimal for precision
        - Legacy code may use float/int

    Error Handling:
        - Property access raises AttributeError if not implemented
        - None values in market_value/avg_entry_price should be handled
          (may occur for newly opened positions before market data updates)
    """

    @property
    def symbol(self) -> str:
        """Trading symbol.

        Returns:
            Symbol/ticker of the security held in position.
            Always required; never None.

        Examples:
            "AAPL"
            "SPY"

        """
        ...

    @property
    def qty(self) -> float | int | str:
        """Position quantity.

        Returns:
            Number of shares/units currently held. Always present
            for positions (never None).

            Positive values = long position
            Negative values = short position (if supported)

        Type Guidance:
            - String: From Alpaca SDK, e.g., "100.5"
            - Float/Decimal: Domain calculations, e.g., 100.5
            - Int: Whole shares, e.g., 100

        Examples:
            "100.5"  # Fractional position from Alpaca
            100      # Whole shares
            -50      # Short position (if supported)

        """
        ...

    @property
    def market_value(self) -> float | int | str | None:
        """Current market value.

        Returns:
            Total current value of the position at market prices,
            or None if not yet calculated/available.

        Calculation:
            qty * current_price

        Type Guidance:
            Should use Decimal in domain logic for monetary precision.
            May be string from SDK or numeric from calculations.

        Examples:
            "10500.50"  # From Alpaca SDK
            10500.50    # Calculated value
            None        # Not yet available

        """
        ...

    @property
    def avg_entry_price(self) -> float | int | str | None:
        """Average entry price.

        Returns:
            Average price paid per share/unit, or None if not
            yet calculated/available.

        Calculation:
            total_cost / qty

        Used For:
            - P&L calculations: (current_price - avg_entry_price) * qty
            - Cost basis tracking
            - Tax reporting

        Type Guidance:
            Should use Decimal in domain logic for monetary precision.
            May be string from SDK or numeric from calculations.

        Examples:
            "105.50"  # From Alpaca SDK
            105.50    # Calculated average
            None      # Not yet available

        """
        ...
