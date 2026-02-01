"""Business Unit: shared | Status: current.

Hedge report generator for options hedging activity.

Generates daily, weekly, and inventory reports with scenario projections
and post-event performance attribution.
"""

from __future__ import annotations

import os
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from ..logging import get_logger
from .adapters.hedge_history_repository import HedgeHistoryRepository
from .adapters.hedge_positions_repository import HedgePositionsRepository
from .constants import MAX_ANNUAL_PREMIUM_SPEND_PCT
from .schemas.hedge_history_record import HedgeAction
from .schemas.hedge_report import (
    AttributionReport,
    DailyHedgeReport,
    HedgeInventoryReport,
    HedgePositionSummary,
    PositionAttribution,
    PremiumSpendSummary,
    ScenarioPayoff,
    ScenarioProjection,
    WeeklyHedgeReport,
)

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)

# Threshold for triggering attribution report (5% underlying move)
SIGNIFICANT_MOVE_THRESHOLD_PCT = Decimal("5")


class HedgeReportGenerator:
    """Generates hedge reports from DynamoDB data.

    Queries HedgePositionsTable and HedgeHistoryTable to generate
    daily, weekly, and inventory reports with scenario projections.
    """

    def __init__(
        self,
        positions_repo: HedgePositionsRepository,
        history_repo: HedgeHistoryRepository,
        account_id: str,
    ) -> None:
        """Initialize report generator.

        Args:
            positions_repo: Repository for hedge positions
            history_repo: Repository for hedge history
            account_id: Account ID for querying history

        """
        self._positions_repo = positions_repo
        self._history_repo = history_repo
        self._account_id = account_id

    @classmethod
    def from_environment(cls, account_id: str) -> HedgeReportGenerator:
        """Create generator from environment variables.

        Args:
            account_id: Account ID

        Returns:
            HedgeReportGenerator instance

        """
        positions_table = os.environ.get("HEDGE_POSITIONS_TABLE_NAME", "")
        history_table = os.environ.get("HEDGE_HISTORY_TABLE_NAME", "")

        if not positions_table or not history_table:
            raise ValueError("HEDGE_POSITIONS_TABLE_NAME and HEDGE_HISTORY_TABLE_NAME must be set")

        return cls(
            positions_repo=HedgePositionsRepository(positions_table),
            history_repo=HedgeHistoryRepository(history_table),
            account_id=account_id,
        )

    def generate_daily_report(
        self,
        report_date: date | None = None,
        current_nav: Decimal | None = None,
        underlying_prices: dict[str, Decimal] | None = None,
    ) -> DailyHedgeReport:
        """Generate daily hedge activity report.

        Args:
            report_date: Date of report (defaults to today)
            current_nav: Current portfolio NAV (for scenario projections)
            underlying_prices: Current prices by underlying symbol

        Returns:
            DailyHedgeReport

        """
        if report_date is None:
            report_date = datetime.now(UTC).date()

        now = datetime.now(UTC)

        logger.info(
            "Generating daily hedge report",
            report_date=report_date.isoformat(),
            account_id=self._account_id,
        )

        # Query today's activity from history
        day_start = datetime.combine(report_date, datetime.min.time()).replace(tzinfo=UTC)
        day_end = datetime.combine(report_date, datetime.max.time()).replace(tzinfo=UTC)

        history_records = self._history_repo.query_history(
            account_id=self._account_id,
            start_time=day_start,
            end_time=day_end,
            limit=1000,
        )

        # Count activity by type
        hedges_placed = sum(1 for r in history_records if r.action == HedgeAction.HEDGE_OPENED)
        hedges_rolled = sum(1 for r in history_records if r.action == HedgeAction.HEDGE_ROLLED)
        hedges_closed = sum(1 for r in history_records if r.action == HedgeAction.HEDGE_CLOSED)
        hedges_expired = sum(1 for r in history_records if r.action == HedgeAction.HEDGE_EXPIRED)

        # Get active positions
        active_positions_raw = self._positions_repo.query_active_positions()
        active_positions = [self._position_dict_to_summary(pos) for pos in active_positions_raw]

        # Calculate premium spend summary
        premium_spend = self._calculate_premium_spend_summary(
            history_records=history_records,
            nav=current_nav or Decimal("100000"),  # Default if not provided
            report_date=report_date,
        )

        # Generate scenario projection if positions exist and nav provided
        scenario_projection = None
        if active_positions and current_nav and underlying_prices:
            # Group by underlying
            for underlying, price in underlying_prices.items():
                scenario_projection = self._generate_scenario_projection(
                    positions=[p for p in active_positions if p.underlying_symbol == underlying],
                    current_nav=current_nav,
                    underlying_symbol=underlying,
                    underlying_price=price,
                )
                break  # Use first underlying for now

        # Check for significant market moves and generate attribution if needed
        attribution_report = None
        if underlying_prices:
            attribution_report = self._check_and_generate_attribution(
                active_positions=active_positions_raw,
                underlying_prices=underlying_prices,
                current_nav=current_nav or Decimal("100000"),
            )

        # Generate alerts
        alerts = self._generate_alerts(
            active_positions=active_positions,
            premium_spend=premium_spend,
        )

        return DailyHedgeReport(
            report_date=report_date,
            generated_at=now,
            hedges_placed_today=hedges_placed,
            hedges_rolled_today=hedges_rolled,
            hedges_closed_today=hedges_closed,
            hedges_expired_today=hedges_expired,
            total_active_hedges=len(active_positions),
            premium_spend=premium_spend,
            active_positions=active_positions,
            scenario_projection=scenario_projection,
            attribution_report=attribution_report,
            alerts=alerts,
        )

    def generate_weekly_report(
        self,
        week_end_date: date | None = None,
        current_nav: Decimal | None = None,
        underlying_prices: dict[str, Decimal] | None = None,
    ) -> WeeklyHedgeReport:
        """Generate weekly aggregated hedge report.

        Args:
            week_end_date: End date of the week (defaults to today/Friday)
            current_nav: Current portfolio NAV
            underlying_prices: Current prices by underlying symbol

        Returns:
            WeeklyHedgeReport

        """
        if week_end_date is None:
            week_end_date = datetime.now(UTC).date()

        # Calculate week start (Monday)
        days_since_monday = week_end_date.weekday()
        week_start_date = week_end_date - timedelta(days=days_since_monday)

        now = datetime.now(UTC)

        logger.info(
            "Generating weekly hedge report",
            week_start=week_start_date.isoformat(),
            week_end=week_end_date.isoformat(),
            account_id=self._account_id,
        )

        # Query week's activity from history
        week_start = datetime.combine(week_start_date, datetime.min.time()).replace(tzinfo=UTC)
        week_end = datetime.combine(week_end_date, datetime.max.time()).replace(tzinfo=UTC)

        history_records = self._history_repo.query_history(
            account_id=self._account_id,
            start_time=week_start,
            end_time=week_end,
            limit=10000,
        )

        # Count activity
        total_placed = sum(1 for r in history_records if r.action == HedgeAction.HEDGE_OPENED)
        total_rolled = sum(1 for r in history_records if r.action == HedgeAction.HEDGE_ROLLED)
        total_closed = sum(1 for r in history_records if r.action == HedgeAction.HEDGE_CLOSED)
        total_expired = sum(1 for r in history_records if r.action == HedgeAction.HEDGE_EXPIRED)

        # Calculate premium spent this week
        premium_this_week = sum(
            (r.premium for r in history_records if r.action == HedgeAction.HEDGE_OPENED),
            Decimal("0"),
        )

        # Get active positions
        active_positions_raw = self._positions_repo.query_active_positions()
        active_positions = [self._position_dict_to_summary(pos) for pos in active_positions_raw]

        # Calculate MTD and YTD premium
        premium_mtd = self._calculate_premium_mtd(week_end_date)
        premium_ytd = self._calculate_premium_ytd(week_end_date)

        # Generate scenario projection
        scenario_projection = None
        if active_positions and current_nav and underlying_prices:
            for underlying, price in underlying_prices.items():
                scenario_projection = self._generate_scenario_projection(
                    positions=[p for p in active_positions if p.underlying_symbol == underlying],
                    current_nav=current_nav,
                    underlying_symbol=underlying,
                    underlying_price=price,
                )
                break

        return WeeklyHedgeReport(
            report_week_start=week_start_date,
            report_week_end=week_end_date,
            generated_at=now,
            total_hedges_placed=total_placed,
            total_hedges_rolled=total_rolled,
            total_hedges_closed=total_closed,
            total_hedges_expired=total_expired,
            premium_spent_this_week=premium_this_week,
            premium_spent_mtd=premium_mtd,
            premium_spent_ytd=premium_ytd,
            average_fill_slippage_pct=None,  # TODO: Calculate from execution data
            active_positions_count=len(active_positions),
            active_positions=active_positions,
            scenario_projection=scenario_projection,
            position_count_change=0,  # TODO: Compare with previous week
            premium_spend_change=Decimal("0"),  # TODO: Compare with previous week
        )

    def generate_inventory_report(
        self,
        current_nav: Decimal,
    ) -> HedgeInventoryReport:
        """Generate detailed current hedge inventory report.

        Args:
            current_nav: Current portfolio NAV

        Returns:
            HedgeInventoryReport

        """
        now = datetime.now(UTC)

        logger.info(
            "Generating hedge inventory report",
            account_id=self._account_id,
        )

        # Get all active positions
        active_positions_raw = self._positions_repo.query_active_positions()
        positions = [self._position_dict_to_summary(pos) for pos in active_positions_raw]

        # Calculate totals
        total_contracts = sum(p.contracts for p in positions)
        total_premium = sum((p.entry_price * p.contracts * 100 for p in positions), Decimal("0"))
        total_current_value = sum(
            ((p.current_price or p.entry_price) * p.contracts * 100 for p in positions),
            Decimal("0"),
        )
        total_unrealized_pnl = total_current_value - total_premium

        # Aggregate portfolio Greeks
        portfolio_delta = sum(
            ((p.current_delta or p.entry_delta) * p.contracts * 100 for p in positions),
            Decimal("0"),
        )
        portfolio_gamma = sum((p.gamma or Decimal("0")) * p.contracts * 100 for p in positions)
        portfolio_theta = sum((p.theta or Decimal("0")) * p.contracts * 100 for p in positions)
        portfolio_vega = sum((p.vega or Decimal("0")) * p.contracts * 100 for p in positions)

        # Group by underlying
        positions_by_underlying: dict[str, list[HedgePositionSummary]] = {}
        for pos in positions:
            underlying = pos.underlying_symbol
            if underlying not in positions_by_underlying:
                positions_by_underlying[underlying] = []
            positions_by_underlying[underlying].append(pos)

        # Count by template
        tail_count = sum(1 for p in positions if p.hedge_template == "tail_first")
        spread_count = sum(1 for p in positions if p.is_spread)

        # DTE distribution
        dte_under_30 = sum(1 for p in positions if p.days_to_expiry < 30)
        dte_30_to_60 = sum(1 for p in positions if 30 <= p.days_to_expiry < 60)
        dte_60_to_90 = sum(1 for p in positions if 60 <= p.days_to_expiry < 90)
        dte_over_90 = sum(1 for p in positions if p.days_to_expiry >= 90)

        return HedgeInventoryReport(
            as_of=now,
            current_nav=current_nav,
            total_positions=len(positions),
            total_contracts=total_contracts,
            total_premium_invested=total_premium,
            total_current_value=total_current_value,
            total_unrealized_pnl=total_unrealized_pnl,
            portfolio_delta=portfolio_delta,
            portfolio_gamma=portfolio_gamma if portfolio_gamma else None,
            portfolio_theta=portfolio_theta if portfolio_theta else None,
            portfolio_vega=portfolio_vega if portfolio_vega else None,
            positions_by_underlying=positions_by_underlying,
            tail_positions_count=tail_count,
            spread_positions_count=spread_count,
            positions_dte_under_30=dte_under_30,
            positions_dte_30_to_60=dte_30_to_60,
            positions_dte_60_to_90=dte_60_to_90,
            positions_dte_over_90=dte_over_90,
        )

    def generate_attribution_report(
        self,
        underlying_symbol: str,
        move_start_price: Decimal,
        move_end_price: Decimal,
        nav_start: Decimal,
        nav_end: Decimal,
        event_start_date: date,
        event_end_date: date,
        positions: list[dict[str, Any]],
    ) -> AttributionReport:
        """Generate post-event performance attribution report.

        Args:
            underlying_symbol: Underlying ETF that moved
            move_start_price: Price at start of move
            move_end_price: Price at end of move
            nav_start: NAV at start
            nav_end: NAV at end
            event_start_date: When move started
            event_end_date: When move ended
            positions: Position data with entry and event prices

        Returns:
            AttributionReport

        """
        now = datetime.now(UTC)

        move_pct = (move_end_price - move_start_price) / move_start_price * 100
        nav_change_pct = (nav_end - nav_start) / nav_start * 100

        # Calculate expected vs actual payoff per position
        position_attributions: list[PositionAttribution] = []
        total_expected = Decimal("0")
        total_actual = Decimal("0")

        for pos in positions:
            hedge_id = pos.get("hedge_id", "")
            option_symbol = pos.get("option_symbol", "")
            contracts = int(pos.get("contracts", 0))
            entry_price = Decimal(str(pos.get("entry_price", 0)))
            price_at_start = Decimal(str(pos.get("price_at_event_start", entry_price)))
            price_at_end = Decimal(str(pos.get("price_at_event_end", price_at_start)))

            # Expected payoff based on delta approximation
            expected_payoff = Decimal("0")  # Simplified - would use actual scenario calc

            # Actual payoff
            actual_payoff = (price_at_end - price_at_start) * contracts * 100

            total_expected += expected_payoff
            total_actual += actual_payoff

            position_attributions.append(
                PositionAttribution(
                    hedge_id=hedge_id,
                    option_symbol=option_symbol,
                    underlying_symbol=underlying_symbol,
                    contracts=contracts,
                    entry_price=entry_price,
                    price_at_event_start=price_at_start,
                    price_at_event_end=price_at_end,
                    expected_payoff=expected_payoff,
                    actual_payoff=actual_payoff,
                    variance=actual_payoff - expected_payoff,
                )
            )

        expected_nav_pct = (total_expected / nav_start) * 100 if nav_start else Decimal("0")
        actual_nav_pct = (total_actual / nav_start) * 100 if nav_start else Decimal("0")
        variance_pct = actual_nav_pct - expected_nav_pct
        variance_dollars = total_actual - total_expected

        # Generate summary text
        summary = (
            f"During the {move_pct:+.1f}% {underlying_symbol} move from "
            f"{event_start_date} to {event_end_date}, hedges returned "
            f"{actual_nav_pct:.2f}% NAV (expected {expected_nav_pct:.2f}% NAV, "
            f"variance {variance_pct:+.2f}%)"
        )

        return AttributionReport(
            generated_at=now,
            event_start_date=event_start_date,
            event_end_date=event_end_date,
            underlying_symbol=underlying_symbol,
            underlying_price_start=move_start_price,
            underlying_price_end=move_end_price,
            underlying_move_pct=move_pct,
            nav_start=nav_start,
            nav_end=nav_end,
            nav_change_pct=nav_change_pct,
            expected_payoff_nav_pct=expected_nav_pct,
            actual_payoff_nav_pct=actual_nav_pct,
            attribution_variance_pct=variance_pct,
            attribution_variance_dollars=variance_dollars,
            position_attributions=position_attributions,
            summary=summary,
        )

    def _position_dict_to_summary(self, pos: dict[str, Any]) -> HedgePositionSummary:
        """Convert position dict to HedgePositionSummary."""
        expiration_date = pos.get("expiration_date")
        if isinstance(expiration_date, str):
            expiration_date = date.fromisoformat(expiration_date)

        dte = (expiration_date - datetime.now(UTC).date()).days if expiration_date else 0

        return HedgePositionSummary(
            hedge_id=pos.get("hedge_id", ""),
            option_symbol=pos.get("option_symbol", ""),
            underlying_symbol=pos.get("underlying_symbol", ""),
            strike_price=Decimal(str(pos.get("strike_price", 0))),
            expiration_date=expiration_date or datetime.now(UTC).date(),
            days_to_expiry=dte,
            contracts=int(pos.get("contracts", 0)),
            entry_price=Decimal(str(pos.get("entry_price", 0))),
            current_price=Decimal(str(pos["current_price"])) if pos.get("current_price") else None,
            entry_delta=Decimal(str(pos.get("entry_delta", 0))),
            current_delta=Decimal(str(pos["current_delta"])) if pos.get("current_delta") else None,
            hedge_template=pos.get("hedge_template", "tail_first"),
            is_spread=pos.get("is_spread", False),
            short_leg_symbol=pos.get("short_leg_symbol"),
            short_leg_strike=Decimal(str(pos["short_leg_strike"]))
            if pos.get("short_leg_strike")
            else None,
        )

    def _calculate_premium_spend_summary(
        self,
        history_records: list[Any],
        nav: Decimal,
        report_date: date,
    ) -> PremiumSpendSummary:
        """Calculate premium spend summary from history records."""
        # Today's spend
        spend_today = sum(
            r.premium for r in history_records if r.action == HedgeAction.HEDGE_OPENED
        )

        # MTD spend
        mtd_spend = self._calculate_premium_mtd(report_date)

        # YTD spend
        ytd_spend = self._calculate_premium_ytd(report_date)

        # Rolling 12-month spend
        rolling_12mo = self._calculate_premium_rolling_12mo(report_date)

        # Annual cap
        annual_cap = nav * MAX_ANNUAL_PREMIUM_SPEND_PCT
        remaining_capacity = max(Decimal("0"), annual_cap - ytd_spend)
        ytd_pct_of_cap = (ytd_spend / annual_cap * 100) if annual_cap else Decimal("0")

        return PremiumSpendSummary(
            spend_today=spend_today,
            spend_mtd=mtd_spend,
            spend_ytd=ytd_spend,
            spend_rolling_12mo=rolling_12mo,
            annual_cap=annual_cap,
            remaining_capacity=remaining_capacity,
            spend_ytd_pct_of_cap=ytd_pct_of_cap,
            nav=nav,
        )

    def _calculate_premium_mtd(self, as_of: date) -> Decimal:
        """Calculate month-to-date premium spend."""
        month_start = as_of.replace(day=1)
        month_start_dt = datetime.combine(month_start, datetime.min.time()).replace(tzinfo=UTC)
        month_end_dt = datetime.combine(as_of, datetime.max.time()).replace(tzinfo=UTC)

        records = self._history_repo.query_history(
            account_id=self._account_id,
            start_time=month_start_dt,
            end_time=month_end_dt,
            limit=10000,
        )

        return sum(
            (r.premium for r in records if r.action == HedgeAction.HEDGE_OPENED),
            Decimal("0"),
        )

    def _calculate_premium_ytd(self, as_of: date) -> Decimal:
        """Calculate year-to-date premium spend."""
        year_start = as_of.replace(month=1, day=1)
        year_start_dt = datetime.combine(year_start, datetime.min.time()).replace(tzinfo=UTC)
        year_end_dt = datetime.combine(as_of, datetime.max.time()).replace(tzinfo=UTC)

        records = self._history_repo.query_history(
            account_id=self._account_id,
            start_time=year_start_dt,
            end_time=year_end_dt,
            limit=100000,
        )

        return sum(
            (r.premium for r in records if r.action == HedgeAction.HEDGE_OPENED),
            Decimal("0"),
        )

    def _calculate_premium_rolling_12mo(self, as_of: date) -> Decimal:
        """Calculate rolling 12-month premium spend."""
        twelve_months_ago = as_of - timedelta(days=365)
        start_dt = datetime.combine(twelve_months_ago, datetime.min.time()).replace(tzinfo=UTC)
        end_dt = datetime.combine(as_of, datetime.max.time()).replace(tzinfo=UTC)

        records = self._history_repo.query_history(
            account_id=self._account_id,
            start_time=start_dt,
            end_time=end_dt,
            limit=100000,
        )

        return sum(
            (r.premium for r in records if r.action == HedgeAction.HEDGE_OPENED),
            Decimal("0"),
        )

    def _generate_scenario_projection(
        self,
        positions: list[HedgePositionSummary],
        current_nav: Decimal,
        underlying_symbol: str,
        underlying_price: Decimal,
    ) -> ScenarioProjection:
        """Generate scenario payoff projections at -10%, -20%, -30%."""
        scenarios = [Decimal("-10"), Decimal("-20"), Decimal("-30")]
        projections: list[ScenarioPayoff] = []

        totals = {s: Decimal("0") for s in scenarios}

        for pos in positions:
            for scenario in scenarios:
                scenario_price = underlying_price * (1 + scenario / 100)
                # Simplified payoff calculation - intrinsic value only
                intrinsic = max(pos.strike_price - scenario_price, Decimal("0"))
                payoff = intrinsic * pos.contracts * 100

                projections.append(
                    ScenarioPayoff(
                        scenario_move_pct=scenario,
                        underlying_price_at_scenario=scenario_price,
                        projected_payoff_dollars=payoff,
                        projected_payoff_nav_pct=(payoff / current_nav * 100),
                        hedge_id=pos.hedge_id,
                    )
                )
                totals[scenario] += payoff

        return ScenarioProjection(
            current_nav=current_nav,
            current_underlying_price=underlying_price,
            underlying_symbol=underlying_symbol,
            projections=projections,
            total_payoff_at_minus_10=totals[Decimal("-10")],
            total_payoff_at_minus_20=totals[Decimal("-20")],
            total_payoff_at_minus_30=totals[Decimal("-30")],
            total_payoff_nav_pct_at_minus_10=(totals[Decimal("-10")] / current_nav * 100),
            total_payoff_nav_pct_at_minus_20=(totals[Decimal("-20")] / current_nav * 100),
            total_payoff_nav_pct_at_minus_30=(totals[Decimal("-30")] / current_nav * 100),
        )

    def _check_and_generate_attribution(
        self,
        active_positions: list[dict[str, Any]],
        underlying_prices: dict[str, Decimal],
        current_nav: Decimal,
    ) -> AttributionReport | None:
        """Check for significant market moves and generate attribution if needed."""
        # Check each position for significant move from entry
        for pos in active_positions:
            underlying = pos.get("underlying_symbol", "")
            if underlying not in underlying_prices:
                continue

            # Get entry data (would need to store entry underlying price)
            nav_at_entry = pos.get("nav_at_entry")
            if not nav_at_entry:
                continue

            nav_at_entry = Decimal(str(nav_at_entry))

            # For now, skip attribution - would need entry underlying price stored
            # This is a placeholder for the attribution detection logic

        return None

    def _generate_alerts(
        self,
        active_positions: list[HedgePositionSummary],
        premium_spend: PremiumSpendSummary,
    ) -> list[str]:
        """Generate alerts based on current state."""
        alerts = []

        # Check for positions approaching expiry
        for pos in active_positions:
            if pos.days_to_expiry < 14:
                alerts.append(
                    f"Position {pos.option_symbol} expires in {pos.days_to_expiry} days - "
                    "consider rolling"
                )

        # Check YTD spend approaching cap
        if premium_spend.spend_ytd_pct_of_cap > 80:
            alerts.append(
                f"YTD premium spend at {premium_spend.spend_ytd_pct_of_cap:.1f}% of annual cap"
            )

        # Check if no active hedges
        if not active_positions:
            alerts.append("No active hedge positions - portfolio may be unhedged")

        return alerts
