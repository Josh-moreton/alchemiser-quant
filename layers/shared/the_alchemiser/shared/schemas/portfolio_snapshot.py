"""Business Unit: shared | Status: current.

Portfolio snapshot models for immutable state representation.

Moved from portfolio_v2 to shared layer to enable reuse by
strategy workers in the per-strategy books architecture.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import TYPE_CHECKING

from the_alchemiser.shared.errors.exceptions import PortfolioError

if TYPE_CHECKING:
    from the_alchemiser.shared.config.config import MarginSafetyConfig

_MODULE_ID: str = "shared.schemas.portfolio_snapshot"


@dataclass(frozen=True)
class MarginInfo:
    """Margin-related account information with safety validation.

    Tracks margin utilization and availability for leverage-aware capital management.
    All fields are optional since margin may not be available for all account types.

    Key Fields from Alpaca:
        buying_power: Total buying power (depends on multiplier: 1x/2x/4x)
        regt_buying_power: Reg T overnight buying power (more conservative)
        daytrading_buying_power: Day trade buying power (more aggressive, PDT only)
        multiplier: 1 (cash), 2 (margin), 4 (PDT margin)

    Safety Metrics:
        margin_utilization_pct: initial_margin / (equity * multiplier) * 100
        maintenance_margin_buffer_pct: (equity - maintenance_margin) / maintenance_margin * 100
    """

    buying_power: Decimal | None = None
    initial_margin: Decimal | None = None
    maintenance_margin: Decimal | None = None
    equity: Decimal | None = None
    regt_buying_power: Decimal | None = None
    daytrading_buying_power: Decimal | None = None
    multiplier: int | None = None

    @property
    def margin_available(self) -> Decimal | None:
        """Calculate available margin (buying_power - initial_margin)."""
        if self.buying_power is None or self.initial_margin is None:
            return None
        return self.buying_power - self.initial_margin

    @property
    def margin_utilization_pct(self) -> Decimal | None:
        """Calculate margin utilization as percentage of total margin capacity.

        Formula: (initial_margin / (equity * multiplier)) * 100
        """
        if (
            self.initial_margin is None
            or self.equity is None
            or self.equity <= 0
            or self.multiplier is None
            or self.multiplier <= 0
        ):
            return None
        total_capacity = self.equity * Decimal(str(self.multiplier))
        return (self.initial_margin / total_capacity) * Decimal("100")

    @property
    def maintenance_margin_buffer_pct(self) -> Decimal | None:
        """Calculate buffer above maintenance margin as percentage.

        Formula: ((equity - maintenance_margin) / maintenance_margin) * 100
        """
        if self.equity is None or self.maintenance_margin is None or self.maintenance_margin <= 0:
            return None
        return ((self.equity - self.maintenance_margin) / self.maintenance_margin) * Decimal("100")

    @property
    def effective_buying_power(self) -> Decimal | None:
        """Get the effective buying power for overnight positions.

        Uses regt_buying_power (Reg T) if available for overnight safety,
        otherwise falls back to general buying_power.
        """
        if self.regt_buying_power is not None:
            return self.regt_buying_power
        return self.buying_power

    @property
    def intraday_buying_power(self) -> Decimal | None:
        """Get the effective buying power for intraday positions.

        For PDT accounts (multiplier=4), uses daytrading_buying_power which
        is the correct constraint for same-day trades.
        """
        if self.is_pdt_account and self.daytrading_buying_power is not None:
            return self.daytrading_buying_power
        return self.effective_buying_power

    @property
    def is_margin_account(self) -> bool:
        """Check if this is a margin-enabled account."""
        return self.multiplier is not None and self.multiplier > 1

    @property
    def is_pdt_account(self) -> bool:
        """Check if this is a Pattern Day Trader account."""
        return self.multiplier == 4

    def is_margin_available(self) -> bool:
        """Check if margin data is available."""
        return self.buying_power is not None

    def is_within_safety_limits(self, config: MarginSafetyConfig) -> tuple[bool, str | None]:
        """Check if current margin state is within safety limits.

        Args:
            config: MarginSafetyConfig with safety thresholds

        Returns:
            Tuple of (is_safe, reason_if_unsafe)

        """
        utilization = self.margin_utilization_pct
        if utilization is not None:
            max_util = Decimal(str(config.max_margin_utilization_pct))
            if utilization > max_util:
                return (
                    False,
                    f"Margin utilization {utilization:.1f}% exceeds max {max_util:.1f}%",
                )

        buffer = self.maintenance_margin_buffer_pct
        if buffer is not None:
            min_buffer = Decimal(str(config.min_maintenance_margin_buffer_pct))
            if buffer < min_buffer:
                return (
                    False,
                    f"Maintenance margin buffer {buffer:.1f}% below min {min_buffer:.1f}%",
                )

        return (True, None)

    def is_approaching_warning_threshold(
        self, config: MarginSafetyConfig
    ) -> tuple[bool, str | None]:
        """Check if margin utilization is approaching warning threshold.

        Args:
            config: MarginSafetyConfig with warning thresholds

        Returns:
            Tuple of (is_warning, warning_message)

        """
        utilization = self.margin_utilization_pct
        if utilization is not None:
            warning_threshold = Decimal(str(config.margin_warning_threshold_pct))
            if utilization > warning_threshold:
                return (
                    True,
                    f"Margin utilization {utilization:.1f}% exceeds warning threshold {warning_threshold:.1f}%",
                )

        return (False, None)

    def calculate_safe_deployment_limit(
        self,
        config: MarginSafetyConfig,
        current_positions_value: Decimal,
    ) -> Decimal | None:
        """Calculate maximum safe deployment based on margin constraints.

        Args:
            config: MarginSafetyConfig with safety thresholds
            current_positions_value: Current market value of positions

        Returns:
            Maximum safe deployment amount, or None if insufficient data

        """
        if self.equity is None or self.maintenance_margin is None:
            return None

        Decimal(str(config.max_margin_utilization_pct)) / Decimal("100")

        max_deployment = Decimal(str(config.max_equity_deployment_pct))
        safe_limit = self.equity * max_deployment

        effective_bp = self.effective_buying_power
        if effective_bp is not None:
            safe_limit = min(safe_limit, effective_bp)

        return safe_limit


@dataclass(frozen=True)
class PortfolioSnapshot:
    """Represent an immutable snapshot of portfolio state.

    Contains current positions, prices, cash, and margin information for
    rebalancing calculations. All monetary values use Decimal for precision.
    """

    positions: dict[str, Decimal]  # symbol -> quantity (shares)
    prices: dict[str, Decimal]  # symbol -> current price per share
    cash: Decimal  # available cash balance (settled)
    total_value: Decimal  # total portfolio value (positions + cash)
    margin: MarginInfo = field(default_factory=MarginInfo)

    def __post_init__(self) -> None:
        """Validate snapshot consistency."""
        missing_prices = set(self.positions.keys()) - set(self.prices.keys())
        if missing_prices:
            raise PortfolioError(
                f"Missing prices for positions: {sorted(missing_prices)}",
                module=_MODULE_ID,
                operation="validation",
            )

        if self.total_value < 0:
            raise PortfolioError(
                f"Total value cannot be negative: {self.total_value}",
                module=_MODULE_ID,
                operation="validation",
            )

        for symbol, quantity in self.positions.items():
            if quantity < 0:
                raise PortfolioError(
                    f"Position quantity cannot be negative for {symbol}: {quantity}",
                    module=_MODULE_ID,
                    operation="validation",
                )

        for symbol, price in self.prices.items():
            if price <= 0:
                raise PortfolioError(
                    f"Price must be positive for {symbol}: {price}",
                    module=_MODULE_ID,
                    operation="validation",
                )

    def get_position_value(self, symbol: str) -> Decimal:
        """Get the market value of a position."""
        if symbol not in self.positions:
            raise KeyError(f"Symbol {symbol} not found in positions")
        if symbol not in self.prices:
            raise KeyError(f"Symbol {symbol} not found in prices")
        return self.positions[symbol] * self.prices[symbol]

    def get_all_position_values(self) -> dict[str, Decimal]:
        """Get market values for all positions."""
        return {symbol: self.get_position_value(symbol) for symbol in self.positions}

    def get_total_position_value(self) -> Decimal:
        """Get total market value of all positions."""
        values = list(self.get_all_position_values().values())
        if not values:
            return Decimal("0")
        total = Decimal("0")
        for value in values:
            total += value
        return total

    def validate_total_value(self, tolerance: Decimal = Decimal("0.01")) -> bool:
        """Validate that total_value equals positions + cash within tolerance."""
        calculated_total = self.get_total_position_value() + self.cash
        diff = abs(self.total_value - calculated_total)
        return diff <= tolerance
