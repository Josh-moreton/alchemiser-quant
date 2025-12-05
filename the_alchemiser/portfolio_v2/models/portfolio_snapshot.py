"""Business Unit: portfolio | Status: current.

Portfolio state management and rebalancing logic.

Portfolio snapshot models for immutable state representation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from the_alchemiser.shared.errors.exceptions import PortfolioError

# Module identifier constant for error reporting
_MODULE_ID: str = "portfolio_v2.models.portfolio_snapshot"


@dataclass(frozen=True)
class MarginInfo:
    """Margin-related account information.

    Tracks margin utilization and availability for leverage-aware capital management.
    All fields are optional since margin may not be available for all account types.
    """

    buying_power: Decimal | None = None  # Total buying power (cash + margin)
    initial_margin: Decimal | None = None  # Margin required to open positions
    maintenance_margin: Decimal | None = None  # Margin required to maintain positions
    equity: Decimal | None = None  # Total account equity (net liquidation value)

    @property
    def margin_available(self) -> Decimal | None:
        """Calculate available margin (buying_power - initial_margin).

        Returns:
            Available margin or None if data insufficient

        """
        if self.buying_power is None or self.initial_margin is None:
            return None
        return self.buying_power - self.initial_margin

    @property
    def margin_utilization_pct(self) -> Decimal | None:
        """Calculate margin utilization as percentage of equity.

        Returns:
            Margin utilization percentage (0-100+) or None if data insufficient

        """
        if self.initial_margin is None or self.equity is None or self.equity <= 0:
            return None
        return (self.initial_margin / self.equity) * Decimal("100")

    @property
    def maintenance_margin_buffer_pct(self) -> Decimal | None:
        """Calculate buffer above maintenance margin as percentage.

        A higher buffer means more safety margin before a margin call.

        Returns:
            Buffer percentage or None if data insufficient

        """
        if self.equity is None or self.maintenance_margin is None or self.maintenance_margin <= 0:
            return None
        return ((self.equity - self.maintenance_margin) / self.maintenance_margin) * Decimal("100")

    def is_margin_available(self) -> bool:
        """Check if margin data is available.

        Returns:
            True if buying_power is available

        """
        return self.buying_power is not None


@dataclass(frozen=True)
class PortfolioSnapshot:
    """Represent an immutable snapshot of portfolio state.

    Contains current positions, prices, cash, and margin information for
    rebalancing calculations. All monetary values use Decimal for precision.

    Capital Management:
        - cash: Actual settled cash in account
        - total_value: Portfolio equity (positions + cash)
        - margin: Optional margin info for leverage-enabled accounts

    The planner uses cash as the primary capital source, with buying_power
    from margin info used for validation in leverage mode.
    """

    positions: dict[str, Decimal]  # symbol -> quantity (shares)
    prices: dict[str, Decimal]  # symbol -> current price per share
    cash: Decimal  # available cash balance (settled)
    total_value: Decimal  # total portfolio value (positions + cash)
    margin: MarginInfo = field(default_factory=MarginInfo)  # Optional margin info

    def __post_init__(self) -> None:
        """Validate snapshot consistency."""
        # Validate all positions have prices
        missing_prices = set(self.positions.keys()) - set(self.prices.keys())
        if missing_prices:
            raise PortfolioError(
                f"Missing prices for positions: {sorted(missing_prices)}",
                module=_MODULE_ID,
                operation="validation",
            )

        # Validate total value is non-negative
        if self.total_value < 0:
            raise PortfolioError(
                f"Total value cannot be negative: {self.total_value}",
                module=_MODULE_ID,
                operation="validation",
            )

        # Validate position quantities are non-negative
        for symbol, quantity in self.positions.items():
            if quantity < 0:
                raise PortfolioError(
                    f"Position quantity cannot be negative for {symbol}: {quantity}",
                    module=_MODULE_ID,
                    operation="validation",
                )

        # Validate prices are positive
        for symbol, price in self.prices.items():
            if price <= 0:
                raise PortfolioError(
                    f"Price must be positive for {symbol}: {price}",
                    module=_MODULE_ID,
                    operation="validation",
                )

    def get_position_value(self, symbol: str) -> Decimal:
        """Get the market value of a position.

        Args:
            symbol: Trading symbol

        Returns:
            Market value (quantity * price)

        Raises:
            KeyError: If symbol not found in positions or prices

        """
        if symbol not in self.positions:
            raise KeyError(f"Symbol {symbol} not found in positions")
        if symbol not in self.prices:
            raise KeyError(f"Symbol {symbol} not found in prices")

        return self.positions[symbol] * self.prices[symbol]

    def get_all_position_values(self) -> dict[str, Decimal]:
        """Get market values for all positions.

        Returns:
            Dictionary mapping symbol to market value

        """
        return {symbol: self.get_position_value(symbol) for symbol in self.positions}

    def get_total_position_value(self) -> Decimal:
        """Get total market value of all positions.

        Returns:
            Sum of all position market values

        """
        values = list(self.get_all_position_values().values())
        if not values:
            return Decimal("0")
        total = Decimal("0")
        for value in values:
            total += value
        return total

    def validate_total_value(self, tolerance: Decimal = Decimal("0.01")) -> bool:
        """Validate that total_value equals positions + cash within tolerance.

        Args:
            tolerance: Maximum allowed difference

        Returns:
            True if values match within tolerance

        """
        calculated_total = self.get_total_position_value() + self.cash
        diff = abs(self.total_value - calculated_total)
        return diff <= tolerance
