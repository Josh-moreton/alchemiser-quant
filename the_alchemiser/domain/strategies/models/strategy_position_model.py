"""Strategy position model using domain value objects."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from the_alchemiser.domain.trading.value_objects.symbol import Symbol
from the_alchemiser.domain.types import StrategyPositionData as StrategyPositionDTO


@dataclass(frozen=True)
class StrategyPositionModel:
    """Immutable strategy position model using domain value objects.

    This model uses proper domain value objects with Decimal for financial values
    and provides mapping to/from TypedDict DTOs for interface boundaries.
    """

    symbol: Symbol
    quantity: Decimal  # Using Decimal directly since positions can be fractional
    entry_price: Decimal  # Using Decimal for price precision
    current_price: Decimal  # Using Decimal for price precision
    strategy_type: str

    def __post_init__(self) -> None:  # pragma: no cover - trivial validation
        """Validate position data."""
        if self.entry_price < 0:
            raise ValueError("Entry price cannot be negative")
        if self.current_price < 0:
            raise ValueError("Current price cannot be negative")

    @classmethod
    def from_dto(cls, data: StrategyPositionDTO) -> StrategyPositionModel:
        """Create from StrategyPositionData TypedDict DTO."""
        symbol = Symbol(str(data["symbol"]))

        # Convert to Decimal for financial precision
        quantity = Decimal(str(data["quantity"]))
        entry_price = Decimal(str(data["entry_price"]))
        current_price = Decimal(str(data["current_price"]))

        return cls(
            symbol=symbol,
            quantity=quantity,
            entry_price=entry_price,
            current_price=current_price,
            strategy_type=str(data["strategy_type"]),
        )

    def to_dto(self) -> StrategyPositionDTO:
        """Convert to StrategyPositionData TypedDict DTO."""
        return {
            "symbol": self.symbol.value,
            "quantity": float(self.quantity),
            "entry_price": float(self.entry_price),
            "current_price": float(self.current_price),
            "strategy_type": self.strategy_type,
        }

    @property
    def unrealized_pnl(self) -> Decimal:
        """Calculate unrealized P&L as Decimal."""
        price_diff = self.current_price - self.entry_price
        return price_diff * self.quantity

    @property
    def unrealized_pnl_percentage(self) -> Decimal:
        """Calculate unrealized P&L percentage."""
        if self.entry_price == 0:
            return Decimal("0")
        price_diff = self.current_price - self.entry_price
        return (price_diff / self.entry_price) * Decimal("100")

    @property
    def total_value(self) -> Decimal:
        """Calculate total value at current price."""
        return abs(self.quantity) * self.current_price

    @property
    def is_long(self) -> bool:
        """Check if position is long."""
        return self.quantity > 0

    @property
    def is_short(self) -> bool:
        """Check if position is short."""
        return self.quantity < 0

    @property
    def is_profitable(self) -> bool:
        """Check if position is profitable."""
        return self.unrealized_pnl > 0

    # Convenience methods for backward compatibility
    @property
    def unrealized_pnl_float(self) -> float:
        """Get unrealized P&L as float for backward compatibility."""
        return float(self.unrealized_pnl)

    @property
    def unrealized_pnl_percentage_float(self) -> float:
        """Get unrealized P&L percentage as float for backward compatibility."""
        return float(self.unrealized_pnl_percentage)

    @property
    def total_value_float(self) -> float:
        """Get total value as float for backward compatibility."""
        return float(self.total_value)
