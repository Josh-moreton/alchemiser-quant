"""Business Unit: portfolio assessment & management; Status: current.

Portfolio rebalancing service - main application orchestrator.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from the_alchemiser.application.mapping.portfolio_rebalancing_mapping import (
    rebalance_plans_dict_to_collection_dto,
)
from the_alchemiser.domain.portfolio.position.position_analyzer import PositionAnalyzer
from the_alchemiser.domain.portfolio.position.position_delta import PositionDelta
from the_alchemiser.domain.portfolio.rebalancing.rebalance_calculator import RebalanceCalculator
from the_alchemiser.domain.portfolio.rebalancing.rebalance_plan import RebalancePlan
from the_alchemiser.domain.portfolio.strategy_attribution.attribution_engine import (
    StrategyAttributionEngine,
)
from the_alchemiser.interfaces.schemas.portfolio_rebalancing import (
    RebalancePlanCollectionDTO,
    RebalancingImpactDTO,
    RebalancingSummaryDTO,
)
from the_alchemiser.services.errors.handler import TradingSystemErrorHandler
from the_alchemiser.services.trading.trading_service_manager import TradingServiceManager


class PortfolioRebalancingService:
    """Main application service for portfolio rebalancing operations.

    Orchestrates domain objects to provide high-level rebalancing functionality
    while maintaining clean separation from infrastructure concerns.
    """

    def __init__(
        self,
        trading_manager: TradingServiceManager,
        rebalance_calculator: RebalanceCalculator | None = None,
        position_analyzer: PositionAnalyzer | None = None,
        attribution_engine: StrategyAttributionEngine | None = None,
        min_trade_threshold: Decimal = Decimal("0.01"),
    ) -> None:
        """Initialize the portfolio rebalancing service.

        Args:
            trading_manager: Service for trading operations and market data
            rebalance_calculator: Calculator for rebalancing plans (optional)
            position_analyzer: Analyzer for position deltas (optional)
            attribution_engine: Engine for strategy attribution (optional)
            min_trade_threshold: Minimum threshold for trade execution

        """
        self.trading_manager = trading_manager
        self.rebalance_calculator = rebalance_calculator or RebalanceCalculator(min_trade_threshold)
        self.position_analyzer = position_analyzer or PositionAnalyzer()
        self.attribution_engine = attribution_engine or StrategyAttributionEngine()

    def _calculate_rebalancing_plan_domain(
        self,
        target_weights: dict[str, Decimal],
        current_positions: dict[str, Decimal] | None = None,
        portfolio_value: Decimal | None = None,
    ) -> dict[str, RebalancePlan]:
        """Internal method to calculate rebalancing plan as domain objects.

        Used by methods that need to work with domain objects internally.
        """
        # Fetch current data if not provided
        if current_positions is None:
            current_positions = self._get_current_position_values()

        if portfolio_value is None:
            portfolio_value = self._get_portfolio_value()

        # Calculate rebalancing plan using domain logic
        return self.rebalance_calculator.calculate_rebalance_plan(
            target_weights, current_positions, portfolio_value
        )

    def calculate_rebalancing_plan(
        self,
        target_weights: dict[str, Decimal],
        current_positions: dict[str, Decimal] | None = None,
        portfolio_value: Decimal | None = None,
    ) -> RebalancePlanCollectionDTO:
        """Calculate a complete rebalancing plan for the portfolio.

        Args:
            target_weights: Target allocation weights by symbol
            current_positions: Current position values (fetched if None)
            portfolio_value: Total portfolio value (calculated if None)

        Returns:
            RebalancePlanCollectionDTO with rebalancing plans for all symbols

        """
        try:
            # Use internal domain method
            domain_plans = self._calculate_rebalancing_plan_domain(
                target_weights, current_positions, portfolio_value
            )

            # Convert to DTO
            return rebalance_plans_dict_to_collection_dto(domain_plans)
        except Exception as e:
            return RebalancePlanCollectionDTO(
                success=False,
                plans={},
                total_symbols=0,
                symbols_needing_rebalance=0,
                total_trade_value=Decimal("0"),
                error=f"Failed to calculate rebalancing plan: {e}",
            )

    def analyze_position_deltas(
        self,
        target_weights: dict[str, Decimal],
        current_positions: dict[str, Decimal] | None = None,
        portfolio_value: Decimal | None = None,
    ) -> dict[str, PositionDelta]:
        """Analyze position deltas between current and target allocations.

        Args:
            target_weights: Target allocation weights by symbol
            current_positions: Current position values (fetched if None)
            portfolio_value: Total portfolio value (calculated if None)

        Returns:
            Dictionary mapping symbols to their position deltas

        """
        # Fetch current data if not provided
        if current_positions is None:
            current_positions = self._get_current_position_values()

        if portfolio_value is None:
            portfolio_value = self._get_portfolio_value()

        # Calculate target position values
        target_positions = {
            symbol: portfolio_value * weight for symbol, weight in target_weights.items()
        }

        # Analyze deltas using domain logic
        return self.position_analyzer.analyze_all_positions(current_positions, target_positions)

    def get_rebalancing_summary(self, target_weights: dict[str, Decimal]) -> RebalancingSummaryDTO:
        """Get a comprehensive summary of rebalancing requirements.

        Args:
            target_weights: Target allocation weights by symbol

        Returns:
            RebalancingSummaryDTO with summary analysis

        """
        try:
            current_positions = self._get_current_position_values()
            portfolio_value = self._get_portfolio_value()

            # Calculate rebalancing plan
            rebalance_plan_result = self.calculate_rebalancing_plan(
                target_weights, current_positions, portfolio_value
            )

            if not rebalance_plan_result.success:
                return RebalancingSummaryDTO(
                    success=False,
                    total_portfolio_value=portfolio_value,
                    total_symbols=0,
                    symbols_needing_rebalance=0,
                    total_trade_value=Decimal("0"),
                    largest_trade_symbol=None,
                    largest_trade_value=Decimal("0"),
                    rebalance_threshold_pct=self.rebalance_calculator.min_trade_threshold,
                    execution_feasible=False,
                    estimated_costs=Decimal("0"),
                    error=rebalance_plan_result.error,
                )

            # Extract rebalancing metrics from the plan collection
            plans = rebalance_plan_result.plans
            largest_trade_value = Decimal("0")
            largest_trade_symbol = None

            for symbol, plan in plans.items():
                if plan.trade_amount_abs > largest_trade_value:
                    largest_trade_value = plan.trade_amount_abs
                    largest_trade_symbol = symbol

            # Estimate basic costs (simplified for this phase)
            estimated_costs = rebalance_plan_result.total_trade_value * Decimal(
                "0.005"
            )  # 0.5% cost estimate

            return RebalancingSummaryDTO(
                success=True,
                total_portfolio_value=portfolio_value,
                total_symbols=rebalance_plan_result.total_symbols,
                symbols_needing_rebalance=rebalance_plan_result.symbols_needing_rebalance,
                total_trade_value=rebalance_plan_result.total_trade_value,
                largest_trade_symbol=largest_trade_symbol,
                largest_trade_value=largest_trade_value,
                rebalance_threshold_pct=self.rebalance_calculator.min_trade_threshold,
                execution_feasible=rebalance_plan_result.symbols_needing_rebalance > 0,
                estimated_costs=estimated_costs,
            )
        except Exception as e:
            return RebalancingSummaryDTO(
                success=False,
                total_portfolio_value=Decimal("0"),
                total_symbols=0,
                symbols_needing_rebalance=0,
                total_trade_value=Decimal("0"),
                largest_trade_symbol=None,
                largest_trade_value=Decimal("0"),
                rebalance_threshold_pct=Decimal("0"),
                execution_feasible=False,
                estimated_costs=Decimal("0"),
                error=f"Failed to generate rebalancing summary: {e}",
            )

    def get_symbols_requiring_sells(self, target_weights: dict[str, Decimal]) -> list[str]:
        """Get list of symbols that need to be sold for rebalancing.

        Args:
            target_weights: Target allocation weights by symbol

        Returns:
            List of symbols requiring sell orders

        """
        rebalance_plan = self._calculate_rebalancing_plan_domain(target_weights)
        sell_plans = self.rebalance_calculator.get_sell_plans(rebalance_plan)
        return list(sell_plans.keys())

    def get_symbols_requiring_buys(self, target_weights: dict[str, Decimal]) -> list[str]:
        """Get list of symbols that need to be bought for rebalancing.

        Args:
            target_weights: Target allocation weights by symbol

        Returns:
            List of symbols requiring buy orders

        """
        rebalance_plan = self._calculate_rebalancing_plan_domain(target_weights)
        buy_plans = self.rebalance_calculator.get_buy_plans(rebalance_plan)
        return list(buy_plans.keys())

    def estimate_rebalancing_impact(
        self, target_weights: dict[str, Decimal]
    ) -> RebalancingImpactDTO:
        """Estimate the impact of rebalancing on the portfolio.

        Args:
            target_weights: Target allocation weights by symbol

        Returns:
            RebalancingImpactDTO with impact analysis

        """
        try:
            current_positions = self._get_current_position_values()
            portfolio_value = self._get_portfolio_value()

            # Calculate position deltas
            position_deltas = self.analyze_position_deltas(
                target_weights, current_positions, portfolio_value
            )

            # Calculate turnover and trade metrics
            portfolio_turnover = self.position_analyzer.calculate_portfolio_turnover(
                position_deltas, portfolio_value
            )
            positions_to_sell = self.position_analyzer.get_positions_to_sell(position_deltas)
            positions_to_buy = self.position_analyzer.get_positions_to_buy(position_deltas)

            # Calculate estimated costs and impact (simplified for this phase)
            total_trade_value = sum(abs(delta.quantity) for delta in position_deltas.values())
            estimated_transaction_costs = total_trade_value * Decimal(
                "0.002"
            )  # 0.2% transaction cost
            estimated_slippage = total_trade_value * Decimal("0.001")  # 0.1% slippage
            total_estimated_costs = estimated_transaction_costs + estimated_slippage

            # Risk analysis (simplified)
            num_trades = len(positions_to_sell) + len(positions_to_buy)
            portfolio_risk_change = Decimal(str(portfolio_turnover)) * Decimal(
                "0.1"
            )  # Simplified risk calculation
            concentration_risk_change = Decimal("0")  # Placeholder

            # Execution analysis
            if num_trades <= 3:
                execution_complexity = "LOW"
                recommended_time = 15
                market_impact_risk = "LOW"
            elif num_trades <= 6:
                execution_complexity = "MEDIUM"
                recommended_time = 30
                market_impact_risk = "MEDIUM"
            else:
                execution_complexity = "HIGH"
                recommended_time = 60
                market_impact_risk = "HIGH"

            # Net benefit calculation (simplified)
            net_benefit_estimate = -total_estimated_costs  # Conservative approach

            # Recommendation logic
            if (
                total_estimated_costs > portfolio_value * Decimal("0.01") or num_trades > 10
            ):  # > 1% of portfolio
                recommendation = "DEFER"
            else:
                recommendation = "EXECUTE"

            return RebalancingImpactDTO(
                success=True,
                portfolio_risk_change=portfolio_risk_change,
                concentration_risk_change=concentration_risk_change,
                estimated_transaction_costs=estimated_transaction_costs,
                estimated_slippage=estimated_slippage,
                total_estimated_costs=total_estimated_costs,
                execution_complexity=execution_complexity,
                recommended_execution_time=recommended_time,
                market_impact_risk=market_impact_risk,
                net_benefit_estimate=net_benefit_estimate,
                recommendation=recommendation,
            )
        except Exception as e:
            return RebalancingImpactDTO(
                success=False,
                portfolio_risk_change=Decimal("0"),
                concentration_risk_change=Decimal("0"),
                estimated_transaction_costs=Decimal("0"),
                estimated_slippage=Decimal("0"),
                total_estimated_costs=Decimal("0"),
                execution_complexity="UNKNOWN",
                recommended_execution_time=0,
                market_impact_risk="UNKNOWN",
                net_benefit_estimate=Decimal("0"),
                recommendation="CANCEL",
                error=f"Failed to estimate rebalancing impact: {e}",
            )

    def _get_current_position_values(self) -> dict[str, Decimal]:
        """Get current position values from trading manager."""
        positions = self.trading_manager.get_all_positions()
        values: dict[str, Decimal] = {}
        for pos in positions:
            try:
                mv = Decimal(str(getattr(pos, "market_value", 0) or 0))
            except Exception:
                mv = Decimal("0")
            if mv > Decimal("0"):
                values[getattr(pos, "symbol", "")] = mv
        return values

    def _get_portfolio_value(self) -> Decimal:
        """Get total portfolio value from trading manager.

        Returns:
            Decimal: The portfolio value

        Raises:
            ValueError: If portfolio_dto is None or portfolio_dto.value is not a valid Decimal

        """
        try:
            portfolio_dto = self.trading_manager.get_portfolio_value()

            # Defensive validation: ensure we got a valid PortfolioValueDTO
            if portfolio_dto is None:
                error_handler = TradingSystemErrorHandler()
                error = ValueError("Portfolio DTO is None - potential upstream schema drift")
                error_handler.handle_error(
                    error=error,
                    component="PortfolioRebalancingService._get_portfolio_value",
                    context="portfolio value retrieval",
                    additional_data={"portfolio_dto": None},
                )
                raise error

            # Defensive validation: ensure portfolio_dto.value is a valid Decimal
            if not isinstance(portfolio_dto.value, Decimal):
                error_handler = TradingSystemErrorHandler()
                error = ValueError(
                    f"Portfolio value is not a Decimal: {type(portfolio_dto.value)} - "
                    f"potential upstream schema drift"
                )
                error_handler.handle_error(
                    error=error,
                    component="PortfolioRebalancingService._get_portfolio_value",
                    context="portfolio value validation",
                    additional_data={
                        "portfolio_dto_type": str(type(portfolio_dto)),
                        "value_type": str(type(portfolio_dto.value)),
                        "value_repr": repr(portfolio_dto.value),
                    },
                )
                raise error

            return portfolio_dto.value

        except Exception as e:
            # Re-raise if already handled above, otherwise handle and re-raise
            if isinstance(e, ValueError) and "schema drift" in str(e):
                raise

            error_handler = TradingSystemErrorHandler()
            error_handler.handle_error(
                error=e,
                component="PortfolioRebalancingService._get_portfolio_value",
                context="portfolio value retrieval - unexpected error",
                additional_data={"error_type": str(type(e))},
            )
            raise

    def _calculate_strategy_changes(
        self, current_exposures: dict[str, Any], target_exposures: dict[str, Any]
    ) -> dict[str, Decimal]:
        """Calculate changes in strategy allocations."""
        changes = {}

        # Get all strategies from both current and target
        all_strategies = set(current_exposures.keys()) | set(target_exposures.keys())

        for strategy in all_strategies:
            current_allocation = current_exposures.get(strategy, {}).get(
                "allocation_percentage", Decimal("0")
            )
            target_allocation = target_exposures.get(strategy, {}).get(
                "allocation_percentage", Decimal("0")
            )
            changes[strategy] = target_allocation - current_allocation

        return changes
