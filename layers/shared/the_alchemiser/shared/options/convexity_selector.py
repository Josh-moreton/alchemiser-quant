"""Business Unit: shared | Status: current.

Convexity-based option selection for hedging.

Selects strikes based on:
- Effective convexity per premium dollar
- Scenario payoff contribution at -20% move
- Delta-anchored selection (not fixed strike bands)
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.options.schemas import OptionContract

logger = get_logger(__name__)


@dataclass(frozen=True)
class ConvexityMetrics:
    """Convexity analysis for an option contract."""

    contract: OptionContract
    convexity_per_dollar: Decimal  # Gamma / (mid_price * 100)
    scenario_payoff_multiple: Decimal  # Payoff at -20% as multiple of premium (e.g., 3.0 = 3x)
    effective_score: Decimal  # Combined score (higher is better)


class ConvexitySelector:
    """Selects options based on convexity per premium and scenario payoffs."""

    def __init__(
        self,
        scenario_move: Decimal = Decimal("-0.20"),
        min_payoff_contribution: Decimal = Decimal("3.0"),
    ) -> None:
        """Initialize convexity selector.

        Args:
            scenario_move: Target scenario move (e.g., -0.20 for -20%)
            min_payoff_contribution: Minimum payoff as multiple of premium (e.g., 3x)

        """
        self._scenario_move = scenario_move
        self._min_payoff_contribution = min_payoff_contribution

    def calculate_convexity_metrics(
        self,
        contract: OptionContract,
        underlying_price: Decimal,
    ) -> ConvexityMetrics | None:
        """Calculate convexity metrics for a contract.

        Args:
            contract: Option contract
            underlying_price: Current underlying price

        Returns:
            ConvexityMetrics if calculable, None if data missing

        """
        # Need mid price and gamma
        mid_price = contract.mid_price
        gamma = contract.gamma

        if mid_price is None or mid_price <= 0 or gamma is None:
            return None

        # Convexity per dollar = gamma / (mid_price * 100 shares)
        premium_per_contract = mid_price * 100
        convexity_per_dollar = gamma / premium_per_contract

        # Scenario payoff at target move (e.g., -20%)
        # Simplified: intrinsic value at scenario price
        scenario_price = underlying_price * (1 + self._scenario_move)
        strike = contract.strike_price

        # Put payoff = max(strike - scenario_price, 0)
        scenario_payoff = max(strike - scenario_price, Decimal("0"))

        # Payoff per contract = scenario_payoff * 100 shares
        scenario_payoff_per_contract = scenario_payoff * 100

        # Payoff as multiple of premium
        if premium_per_contract > 0:
            payoff_multiple = scenario_payoff_per_contract / premium_per_contract
        else:
            payoff_multiple = Decimal("0")

        # Effective score: combine convexity and payoff
        # Higher convexity = better protection curve
        # Higher payoff = better value in crash scenario
        # Weight both equally
        effective_score = (convexity_per_dollar * 1000) + payoff_multiple

        return ConvexityMetrics(
            contract=contract,
            convexity_per_dollar=convexity_per_dollar,
            scenario_payoff_multiple=payoff_multiple,
            effective_score=effective_score,
        )

    def filter_by_payoff_contribution(
        self,
        metrics_list: list[ConvexityMetrics],
    ) -> list[ConvexityMetrics]:
        """Filter contracts by minimum payoff contribution.

        Args:
            metrics_list: List of convexity metrics

        Returns:
            Filtered list meeting minimum payoff threshold

        """
        filtered = [
            m for m in metrics_list if m.scenario_payoff_multiple >= self._min_payoff_contribution
        ]

        logger.info(
            "Filtered by payoff contribution",
            total_contracts=len(metrics_list),
            passed_filter=len(filtered),
            min_payoff_multiple=str(self._min_payoff_contribution),
        )

        return filtered

    def rank_by_convexity(
        self,
        metrics_list: list[ConvexityMetrics],
    ) -> list[ConvexityMetrics]:
        """Rank contracts by effective convexity score.

        Args:
            metrics_list: List of convexity metrics

        Returns:
            Sorted list (best first)

        """
        # Sort by effective score (descending)
        ranked = sorted(metrics_list, key=lambda m: m.effective_score, reverse=True)

        if ranked:
            best = ranked[0]
            logger.info(
                "Top convexity candidate",
                symbol=best.contract.symbol,
                strike=str(best.contract.strike_price),
                delta=str(best.contract.delta) if best.contract.delta else "N/A",
                convexity_per_dollar=str(best.convexity_per_dollar),
                payoff_multiple=str(best.scenario_payoff_multiple),
                effective_score=str(best.effective_score),
            )

        return ranked
