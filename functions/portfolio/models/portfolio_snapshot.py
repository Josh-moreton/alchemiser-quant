"""Business Unit: portfolio | Status: current.

Portfolio state management and rebalancing logic.

Portfolio snapshot models for immutable state representation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import TYPE_CHECKING

from the_alchemiser.shared.errors.exceptions import PortfolioError

if TYPE_CHECKING:
    from the_alchemiser.shared.config.config import MarginSafetyConfig

# Module identifier constant for error reporting
_MODULE_ID: str = "portfolio_v2.models.portfolio_snapshot"


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

    # Core margin fields
    buying_power: Decimal | None = None  # Total buying power (based on multiplier)
    initial_margin: Decimal | None = None  # Margin required to open positions
    maintenance_margin: Decimal | None = None  # Margin required to maintain positions
    equity: Decimal | None = None  # Total account equity (net liquidation value)

    # Extended fields from Alpaca for intraday vs overnight distinction
    regt_buying_power: Decimal | None = None  # Reg T overnight buying power
    daytrading_buying_power: Decimal | None = None  # Day trading buying power (4x for PDT)
    multiplier: int | None = None  # Account multiplier: 1=cash, 2=margin, 4=PDT

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
        """Calculate margin utilization as percentage of total margin capacity.

        Formula: (initial_margin / (equity * multiplier)) * 100

        This measures how much of your total margin capacity is used.
        With 2x margin and $100k equity:
        - Total capacity = $200k
        - If $110k deployed with 50% margin req: initial_margin = $55k
        - Utilization = 55k/200k = 27.5%

        Note: buying_power is what's LEFT after positions, not total capacity.

        Returns:
            Margin utilization percentage (0-100) or None if data insufficient

        Example:
            equity=$100,000, multiplier=2, initial_margin=$55,000 -> 27.5%

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

        A higher buffer means more safety margin before a margin call.
        At 0%, you're at the margin call threshold.
        Negative means margin call territory.

        Returns:
            Buffer percentage or None if data insufficient

        Example:
            equity=$10,000, maintenance_margin=$4,000 -> 150% buffer
            equity=$5,000, maintenance_margin=$4,000 -> 25% buffer (danger zone)

        """
        if self.equity is None or self.maintenance_margin is None or self.maintenance_margin <= 0:
            return None
        return ((self.equity - self.maintenance_margin) / self.maintenance_margin) * Decimal("100")

    @property
    def effective_buying_power(self) -> Decimal | None:
        """Get the effective buying power for overnight positions.

        Uses regt_buying_power (Reg T) if available for overnight safety,
        otherwise falls back to general buying_power.

        Returns:
            Conservative buying power for overnight position sizing

        """
        # Prefer RegT buying power for overnight positions (more conservative)
        if self.regt_buying_power is not None:
            return self.regt_buying_power
        return self.buying_power

    @property
    def intraday_buying_power(self) -> Decimal | None:
        """Get the effective buying power for intraday positions.

        For PDT accounts (multiplier=4), uses daytrading_buying_power which
        is the correct constraint for same-day trades. Falls back to
        effective_buying_power for non-PDT accounts.

        This is critical for capital constraint validation because Alpaca
        enforces daytrading_buying_power limits on BUY orders during the
        trading day, even if RegT buying power would allow more.

        Returns:
            Buying power applicable for intraday BUY orders

        """
        # For PDT accounts, use daytrading_buying_power if available
        if self.is_pdt_account and self.daytrading_buying_power is not None:
            return self.daytrading_buying_power
        # Fall back to effective_buying_power for non-PDT or missing data
        return self.effective_buying_power

    @property
    def is_margin_account(self) -> bool:
        """Check if this is a margin-enabled account.

        Returns:
            True if multiplier > 1 (margin or PDT)

        """
        return self.multiplier is not None and self.multiplier > 1

    @property
    def is_pdt_account(self) -> bool:
        """Check if this is a Pattern Day Trader account.

        Returns:
            True if multiplier == 4 (PDT margin)

        """
        return self.multiplier == 4

    def is_margin_available(self) -> bool:
        """Check if margin data is available.

        Returns:
            True if buying_power is available

        """
        return self.buying_power is not None

    def is_within_safety_limits(self, config: MarginSafetyConfig) -> tuple[bool, str | None]:
        """Check if current margin state is within safety limits.

        Args:
            config: MarginSafetyConfig with safety thresholds

        Returns:
            Tuple of (is_safe, reason_if_unsafe)

        """
        # Check margin utilization
        utilization = self.margin_utilization_pct
        if utilization is not None:
            max_util = Decimal(str(config.max_margin_utilization_pct))
            if utilization > max_util:
                return (
                    False,
                    f"Margin utilization {utilization:.1f}% exceeds max {max_util:.1f}%",
                )

        # Check maintenance margin buffer
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

        This ensures we don't exceed margin safety limits even if
        buying_power would allow more.

        Args:
            config: MarginSafetyConfig with safety thresholds
            current_positions_value: Current market value of positions

        Returns:
            Maximum safe deployment amount, or None if insufficient data

        """
        if self.equity is None or self.maintenance_margin is None:
            return None

        # Method 1: Cap based on max margin utilization
        # If max utilization is 75%, we can use at most 75% of equity as initial margin
        # Assuming ~50% initial margin requirement (typical for stocks),
        # we can deploy at most equity * max_util% * 2
        Decimal(str(config.max_margin_utilization_pct)) / Decimal("100")

        # Method 2: Ensure we maintain minimum buffer above maintenance margin
        # buffer = (equity - maintenance_margin) / maintenance_margin
        # We need: (equity_after - mm_after) / mm_after >= min_buffer
        # This is complex because mm_after depends on new positions

        # Simpler approach: cap at max_equity_deployment_pct * equity
        max_deployment = Decimal(str(config.max_equity_deployment_pct))
        safe_limit = self.equity * max_deployment

        # Also cap at effective buying power
        effective_bp = self.effective_buying_power
        if effective_bp is not None:
            safe_limit = min(safe_limit, effective_bp)

        return safe_limit


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
