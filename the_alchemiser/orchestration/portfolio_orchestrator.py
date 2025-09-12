"""Business Unit: orchestration | Status: current

Portfolio rebalancing orchestration workflow.

Coordinates portfolio state analysis and rebalancing plan generation using the
portfolio_v2 module. This orchestrator focuses on portfolio optimization logic
without trading execution.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer

from the_alchemiser.shared.config.config import Settings
from the_alchemiser.shared.logging.logging_utils import get_logger


class PortfolioOrchestrator:
    """Orchestrates portfolio rebalancing workflow."""

    def __init__(self, settings: Settings, container: ApplicationContainer) -> None:
        self.settings = settings
        self.container = container
        self.logger = get_logger(__name__)

    def analyze_portfolio_state(self) -> dict[str, Any] | None:
        """Analyze current portfolio state and generate rebalancing recommendations.

        Returns:
            Portfolio analysis result or None if analysis failed

        """
        try:
            # Use portfolio_v2 for modern portfolio analysis
            from the_alchemiser.portfolio_v2 import PortfolioServiceV2

            # Get portfolio service from container
            portfolio_service = PortfolioServiceV2(
                data_adapter=self.container.infrastructure.alpaca_manager()
            )

            # Get current portfolio snapshot
            portfolio_snapshot = portfolio_service.get_portfolio_snapshot()

            if not portfolio_snapshot:
                self.logger.warning("Could not retrieve portfolio snapshot")
                return None

            self.logger.info(
                f"Portfolio analysis: {len(portfolio_snapshot.positions)} positions, "
                f"${portfolio_snapshot.total_value:.2f} total value"
            )

            return {
                "snapshot": portfolio_snapshot,
                "analysis_timestamp": portfolio_snapshot.timestamp,
                "position_count": len(portfolio_snapshot.positions),
                "total_value": float(portfolio_snapshot.total_value),
            }

        except Exception as e:
            self.logger.error(f"Portfolio analysis failed: {e}")
            return None

    def generate_rebalancing_plan(
        self, target_allocations: dict[str, float]
    ) -> dict[str, Any] | None:
        """Generate rebalancing plan based on target allocations.

        Args:
            target_allocations: Target allocation percentages by symbol

        Returns:
            Rebalancing plan or None if generation failed

        """
        try:
            # Use portfolio_v2 for rebalancing plan calculation
            from datetime import datetime
            from decimal import Decimal

            from the_alchemiser.portfolio_v2 import RebalancePlanCalculator
            from the_alchemiser.shared.dto.strategy_allocation_dto import StrategyAllocationDTO

            # Convert float allocations to Decimal for portfolio_v2
            target_weights = {
                symbol: Decimal(str(allocation))
                for symbol, allocation in target_allocations.items()
            }

            # Create strategy allocation DTO
            allocation_dto = StrategyAllocationDTO(
                target_weights=target_weights,
                correlation_id="portfolio_orchestrator",
                as_of=datetime.now(),
                constraints={"orchestrator": "portfolio"},
            )

            # Get data adapter
            data_adapter = self.container.infrastructure.alpaca_manager()

            # Create rebalance plan calculator
            calculator = RebalancePlanCalculator(data_adapter)

            # Generate rebalancing plan
            rebalance_plan = calculator.calculate_rebalance_plan(allocation_dto)

            if not rebalance_plan:
                self.logger.warning("Could not generate rebalancing plan")
                return None

            self.logger.info(
                f"Generated rebalancing plan: {len(rebalance_plan.trades)} trades, "
                f"${rebalance_plan.total_trade_value:.2f} total trade value"
            )

            return {
                "plan": rebalance_plan,
                "trade_count": len(rebalance_plan.trades),
                "total_trade_value": float(rebalance_plan.total_trade_value),
                "target_allocations": target_allocations,
                "plan_timestamp": rebalance_plan.timestamp,
            }

        except Exception as e:
            self.logger.error(f"Rebalancing plan generation failed: {e}")
            return None

    def analyze_allocation_comparison(
        self, consolidated_portfolio: dict[str, float]
    ) -> dict[str, Any] | None:
        """Analyze target vs current allocations.

        Args:
            consolidated_portfolio: Target portfolio allocation

        Returns:
            Allocation comparison analysis or None if failed

        """
        try:
            # Get current account info and positions
            alpaca_manager = self.container.infrastructure.alpaca_manager()

            # Get account information
            account_info = alpaca_manager.get_account()
            if not account_info:
                self.logger.warning("Could not retrieve account information")
                return None

            # Get current positions
            current_positions = alpaca_manager.get_positions()
            positions_dict = {pos.symbol: float(pos.market_value) for pos in current_positions}

            # Use portfolio calculations for comparison
            from the_alchemiser.portfolio_v2.calculations.portfolio_calculations import (
                build_allocation_comparison,
            )

            # Convert account info to dict format expected by calculation
            account_dict = {
                "equity": account_info.equity,
                "portfolio_value": account_info.portfolio_value,
                "buying_power": account_info.buying_power,
            }

            allocation_comparison = build_allocation_comparison(
                consolidated_portfolio, account_dict, positions_dict
            )

            self.logger.info("Generated allocation comparison analysis")

            return {
                "comparison": allocation_comparison,
                "current_positions": positions_dict,
                "target_allocations": consolidated_portfolio,
                "account_info": account_dict,
            }

        except Exception as e:
            self.logger.error(f"Allocation comparison analysis failed: {e}")
            return None

    def execute_portfolio_workflow(
        self, target_allocations: dict[str, float]
    ) -> dict[str, Any] | None:
        """Execute complete portfolio analysis workflow.

        Args:
            target_allocations: Target allocation percentages by symbol

        Returns:
            Complete portfolio analysis result or None if failed

        """
        try:
            # Analyze current portfolio state
            portfolio_state = self.analyze_portfolio_state()
            if not portfolio_state:
                return None

            # Generate rebalancing plan
            rebalancing_plan = self.generate_rebalancing_plan(target_allocations)
            if not rebalancing_plan:
                return None

            # Analyze allocation comparison
            allocation_analysis = self.analyze_allocation_comparison(target_allocations)
            if not allocation_analysis:
                return None

            return {
                "portfolio_state": portfolio_state,
                "rebalancing_plan": rebalancing_plan,
                "allocation_analysis": allocation_analysis,
                "workflow_success": True,
            }

        except Exception as e:
            self.logger.error(f"Portfolio workflow execution failed: {e}")
            return None
