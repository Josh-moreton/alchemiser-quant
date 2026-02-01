"""Business Unit: shared | Status: current.

Hedge report data transfer objects.

Schemas for daily, weekly, and inventory reports on options hedging activity.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ...constants import CONTRACT_VERSION


class HedgePositionSummary(BaseModel):
    """Summary of a single hedge position for reporting."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    hedge_id: str
    option_symbol: str
    underlying_symbol: str
    strike_price: Decimal
    expiration_date: date
    days_to_expiry: int
    contracts: int
    entry_price: Decimal
    current_price: Decimal | None = None
    entry_delta: Decimal
    current_delta: Decimal | None = None
    gamma: Decimal | None = None
    theta: Decimal | None = None
    vega: Decimal | None = None
    unrealized_pnl: Decimal | None = None
    hedge_template: str
    # Spread details (if applicable)
    is_spread: bool = False
    short_leg_symbol: str | None = None
    short_leg_strike: Decimal | None = None


class ScenarioPayoff(BaseModel):
    """Projected payoff at a specific scenario move."""

    model_config = ConfigDict(strict=True, frozen=True)

    scenario_move_pct: Decimal  # e.g., -10, -20, -30
    underlying_price_at_scenario: Decimal
    projected_payoff_dollars: Decimal
    projected_payoff_nav_pct: Decimal
    hedge_id: str  # Which hedge position this is for


class ScenarioProjection(BaseModel):
    """Aggregated scenario projections across all hedges."""

    model_config = ConfigDict(strict=True, frozen=True)

    current_nav: Decimal
    current_underlying_price: Decimal
    underlying_symbol: str
    projections: list[ScenarioPayoff]
    # Summary by scenario move
    total_payoff_at_minus_10: Decimal
    total_payoff_at_minus_20: Decimal
    total_payoff_at_minus_30: Decimal
    total_payoff_nav_pct_at_minus_10: Decimal
    total_payoff_nav_pct_at_minus_20: Decimal
    total_payoff_nav_pct_at_minus_30: Decimal


class PremiumSpendSummary(BaseModel):
    """Summary of premium spend over various periods."""

    model_config = ConfigDict(strict=True, frozen=True)

    spend_today: Decimal
    spend_mtd: Decimal
    spend_ytd: Decimal
    spend_rolling_12mo: Decimal
    annual_cap: Decimal
    remaining_capacity: Decimal
    spend_ytd_pct_of_cap: Decimal
    nav: Decimal


class DailyHedgeReport(BaseModel):
    """Daily hedge activity report."""

    model_config = ConfigDict(strict=True, frozen=True)

    __schema_version__: str = CONTRACT_VERSION

    report_date: date
    generated_at: datetime

    # Summary metrics
    hedges_placed_today: int
    hedges_rolled_today: int
    hedges_closed_today: int
    hedges_expired_today: int
    total_active_hedges: int

    # Premium tracking
    premium_spend: PremiumSpendSummary

    # Current inventory
    active_positions: list[HedgePositionSummary]

    # Scenario projections (optional, if positions exist)
    scenario_projection: ScenarioProjection | None = None

    # Market move attribution (if significant move detected)
    attribution_report: AttributionReport | None = None

    # Alerts/warnings
    alerts: list[str] = Field(default_factory=list)


class WeeklyHedgeReport(BaseModel):
    """Weekly aggregated hedge report."""

    model_config = ConfigDict(strict=True, frozen=True)

    __schema_version__: str = CONTRACT_VERSION

    report_week_start: date
    report_week_end: date
    generated_at: datetime

    # Activity summary
    total_hedges_placed: int
    total_hedges_rolled: int
    total_hedges_closed: int
    total_hedges_expired: int

    # Premium tracking
    premium_spent_this_week: Decimal
    premium_spent_mtd: Decimal
    premium_spent_ytd: Decimal
    average_fill_slippage_pct: Decimal | None = None

    # End-of-week inventory
    active_positions_count: int
    active_positions: list[HedgePositionSummary]

    # Scenario projections
    scenario_projection: ScenarioProjection | None = None

    # Week-over-week changes
    position_count_change: int  # vs previous week
    premium_spend_change: Decimal  # vs previous week


class AttributionReport(BaseModel):
    """Post-event performance attribution report.

    Generated when a significant market move occurs to compare
    actual hedge performance vs expected.
    """

    model_config = ConfigDict(strict=True, frozen=True)

    __schema_version__: str = CONTRACT_VERSION

    generated_at: datetime
    event_start_date: date
    event_end_date: date

    # Market move details
    underlying_symbol: str
    underlying_price_start: Decimal
    underlying_price_end: Decimal
    underlying_move_pct: Decimal

    # NAV tracking
    nav_start: Decimal
    nav_end: Decimal
    nav_change_pct: Decimal

    # Hedge performance
    expected_payoff_nav_pct: Decimal  # What we expected from scenario projections
    actual_payoff_nav_pct: Decimal  # What we actually got
    attribution_variance_pct: Decimal  # Difference
    attribution_variance_dollars: Decimal

    # Per-position breakdown
    position_attributions: list[PositionAttribution]

    # Summary text
    summary: str  # "During the -X% move, hedges returned Y% NAV (expected Z% NAV)"


class PositionAttribution(BaseModel):
    """Attribution for a single hedge position."""

    model_config = ConfigDict(strict=True, frozen=True)

    hedge_id: str
    option_symbol: str
    underlying_symbol: str
    contracts: int

    # Price changes
    entry_price: Decimal
    price_at_event_start: Decimal
    price_at_event_end: Decimal

    # Payoff
    expected_payoff: Decimal
    actual_payoff: Decimal
    variance: Decimal
    variance_explanation: str | None = None


class HedgeInventoryReport(BaseModel):
    """Current hedge inventory with full Greeks.

    Detailed snapshot of all active positions.
    """

    model_config = ConfigDict(strict=True, frozen=True)

    __schema_version__: str = CONTRACT_VERSION

    as_of: datetime
    current_nav: Decimal

    # Summary
    total_positions: int
    total_contracts: int
    total_premium_invested: Decimal
    total_current_value: Decimal
    total_unrealized_pnl: Decimal

    # Aggregate Greeks
    portfolio_delta: Decimal  # Sum of position deltas
    portfolio_gamma: Decimal | None = None
    portfolio_theta: Decimal | None = None  # Daily theta bleed
    portfolio_vega: Decimal | None = None

    # By underlying
    positions_by_underlying: dict[str, list[HedgePositionSummary]]

    # By template
    tail_positions_count: int
    spread_positions_count: int

    # DTE distribution
    positions_dte_under_30: int
    positions_dte_30_to_60: int
    positions_dte_60_to_90: int
    positions_dte_over_90: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = self.model_dump()
        data["as_of"] = self.as_of.isoformat()
        return data
