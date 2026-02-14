"""Business Unit: shared | Status: current.

Payoff-based contract sizing calculator for options hedging.

Implements scenario-based sizing where contracts are determined by:
1. Target payoff at specific scenario moves (e.g., +8% NAV at -20% market move)
2. Option delta and strike estimation
3. Expected payoff per contract

This replaces budget-first sizing with payoff-first sizing.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from ..logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class PayoffScenario:
    """Scenario definition for payoff calculation.

    Defines a market move scenario and target hedge payoff.
    """

    scenario_move_pct: Decimal  # Market move as decimal (e.g., -0.20 for -20%)
    target_payoff_pct: Decimal  # Target payoff as % of NAV (e.g., 0.08 for 8%)
    description: str  # Human-readable description


@dataclass(frozen=True)
class PayoffCalculationResult:
    """Result of payoff-based contract sizing calculation.

    Contains detailed breakdown of the calculation for transparency.
    """

    contracts_required: int  # Number of contracts needed
    scenario_move_pct: Decimal  # Scenario market move
    target_payoff_dollars: Decimal  # Target payoff in dollars
    estimated_strike: Decimal  # Estimated strike price
    scenario_price: Decimal  # Underlying price at scenario move
    payoff_per_contract: Decimal  # Expected payoff per contract
    target_payoff_pct: Decimal  # Target payoff as % of NAV
    underlying_price: Decimal  # Current underlying price
    option_delta: Decimal  # Option delta used


class PayoffCalculator:
    """Calculator for scenario-based option contract sizing.

    Sizes option contracts to achieve specific payoff targets at defined
    scenario moves, independent of premium budget constraints.
    """

    def calculate_contracts_for_scenario(
        self,
        underlying_price: Decimal,
        option_delta: Decimal,
        scenario: PayoffScenario,
        nav: Decimal,
        *,
        leverage_factor: Decimal = Decimal("1.0"),
    ) -> PayoffCalculationResult:
        """Calculate contracts required to achieve target payoff at scenario move.

        Args:
            underlying_price: Current price of underlying asset
            option_delta: Target put delta (e.g., 0.15 for 15-delta)
            scenario: Scenario definition with move and target payoff
            nav: Portfolio net asset value
            leverage_factor: Portfolio leverage multiplier (default: 1.0)

        Returns:
            PayoffCalculationResult with sizing details

        Examples:
            >>> calc = PayoffCalculator()
            >>> scenario = PayoffScenario(
            ...     scenario_move_pct=Decimal("-0.20"),
            ...     target_payoff_pct=Decimal("0.08"),
            ...     description="-20% crash"
            ... )
            >>> result = calc.calculate_contracts_for_scenario(
            ...     underlying_price=Decimal("500"),
            ...     option_delta=Decimal("0.15"),
            ...     scenario=scenario,
            ...     nav=Decimal("100000"),
            ...     leverage_factor=Decimal("2.0")
            ... )
            >>> result.contracts_required
            3

        """
        # Calculate target payoff in dollars
        # Leverage factor scales the target proportionally
        adjusted_target_pct = scenario.target_payoff_pct * leverage_factor
        target_payoff_dollars = nav * adjusted_target_pct

        # Calculate scenario price after the move
        scenario_price = underlying_price * (Decimal("1") + scenario.scenario_move_pct)

        # Estimate strike from delta
        # For puts: delta approximates OTM percentage
        # 15-delta ≈ 15% OTM, so strike ≈ underlying * (1 - delta)
        estimated_strike = underlying_price * (Decimal("1") - option_delta)

        # Calculate option payoff per contract at scenario
        # For puts: max(0, strike - scenario_price) * 100 shares
        payoff_per_contract = max(Decimal("0"), estimated_strike - scenario_price) * 100

        # Handle edge case where option expires worthless in scenario
        if payoff_per_contract <= 0:
            logger.warning(
                "Option would expire worthless at scenario move",
                scenario_move=str(scenario.scenario_move_pct),
                strike=str(estimated_strike),
                scenario_price=str(scenario_price),
                option_delta=str(option_delta),
            )
            # Return minimum 1 contract
            return PayoffCalculationResult(
                contracts_required=1,
                scenario_move_pct=scenario.scenario_move_pct,
                target_payoff_dollars=target_payoff_dollars,
                estimated_strike=estimated_strike,
                scenario_price=scenario_price,
                payoff_per_contract=Decimal("0"),
                target_payoff_pct=adjusted_target_pct,
                underlying_price=underlying_price,
                option_delta=option_delta,
            )

        # Calculate required contracts
        contracts_float = target_payoff_dollars / payoff_per_contract

        # Round up to ensure we meet or exceed target
        # Use ceiling logic: int(x + 0.999...) ensures rounding up
        contracts_required = max(1, int(contracts_float + Decimal("0.999999")))

        logger.info(
            "Calculated contracts for payoff target",
            scenario_description=scenario.description,
            scenario_move=str(scenario.scenario_move_pct),
            target_payoff_pct=str(adjusted_target_pct),
            target_payoff_dollars=str(target_payoff_dollars),
            underlying_price=str(underlying_price),
            option_delta=str(option_delta),
            estimated_strike=str(estimated_strike),
            scenario_price=str(scenario_price),
            payoff_per_contract=str(payoff_per_contract),
            contracts_required=contracts_required,
            leverage_factor=str(leverage_factor),
        )

        return PayoffCalculationResult(
            contracts_required=contracts_required,
            scenario_move_pct=scenario.scenario_move_pct,
            target_payoff_dollars=target_payoff_dollars,
            estimated_strike=estimated_strike,
            scenario_price=scenario_price,
            payoff_per_contract=payoff_per_contract,
            target_payoff_pct=adjusted_target_pct,
            underlying_price=underlying_price,
            option_delta=option_delta,
        )

    def estimate_premium_cost(
        self,
        contracts: int,
        underlying_price: Decimal,
        option_delta: Decimal,
        days_to_expiry: int,
        *,
        is_spread: bool = False,
    ) -> Decimal:
        """Estimate premium cost for a given number of contracts.

        Uses rule-of-thumb estimates based on delta and DTE.
        This is a rough estimate - actual cost will be determined at execution.

        Args:
            contracts: Number of contracts
            underlying_price: Current price of underlying
            option_delta: Target put delta
            days_to_expiry: Days to expiration
            is_spread: Whether this is a spread (reduces net premium)

        Returns:
            Estimated total premium cost in dollars

        """
        # Rule of thumb estimates:
        # - 15-delta put at 90 DTE: ~1.5% of underlying
        # - 30-delta put at 60 DTE: ~2.5% of underlying
        # - 10-delta put at 60 DTE: ~0.8% of underlying
        # - Put spread (30-10): ~1.5% of underlying

        if is_spread:
            # Put spread: buy 30-delta, sell 10-delta
            # Net premium is roughly 1.5% of underlying at 60 DTE
            premium_pct = Decimal("0.015")
        else:
            # Single put: scale by delta
            # Base on 15-delta at 90 DTE = 1.5%
            # Adjust for different deltas and DTE
            delta_factor = option_delta / Decimal("0.15")
            dte_factor = Decimal(str(days_to_expiry)) / Decimal("90")
            # Premium scales with delta and sqrt(time)
            time_adjustment = dte_factor.sqrt() if dte_factor > 0 else Decimal("1")
            premium_pct = Decimal("0.015") * delta_factor * time_adjustment

        # Calculate total premium
        premium_per_contract = premium_pct * underlying_price * 100
        total_premium = premium_per_contract * contracts

        logger.debug(
            "Estimated premium cost",
            contracts=contracts,
            underlying_price=str(underlying_price),
            option_delta=str(option_delta),
            days_to_expiry=days_to_expiry,
            is_spread=is_spread,
            premium_pct=str(premium_pct),
            premium_per_contract=str(premium_per_contract),
            total_premium=str(total_premium),
        )

        return total_premium
