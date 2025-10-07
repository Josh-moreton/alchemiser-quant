"""Business Unit: portfolio | Status: current.

Portfolio state management and rebalancing logic.

Portfolio service V2 - orchestration facade for rebalance plan creation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlan
from the_alchemiser.shared.errors.exceptions import PortfolioError

if TYPE_CHECKING:
    from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
    from the_alchemiser.shared.schemas.strategy_allocation import StrategyAllocation

from ..adapters.alpaca_data_adapter import AlpacaDataAdapter
from .planner import RebalancePlanCalculator
from .state_reader import PortfolioStateReader

logger = get_logger(__name__)

# Module name constant for consistent logging
MODULE_NAME = "portfolio_v2.core.portfolio_service"


class PortfolioServiceV2:
    """Portfolio service V2 - main facade for portfolio rebalancing.

    Orchestrates the portfolio rebalancing process by:
    1. Reading current portfolio state via AlpacaDataAdapter
    2. Building portfolio snapshot via PortfolioStateReader
    3. Calculating rebalance plan via RebalancePlanCalculator
    4. Returning clean RebalancePlan for execution module
    """

    def __init__(self, alpaca_manager: AlpacaManager) -> None:
        """Initialize portfolio service with dependencies.

        Args:
            alpaca_manager: Shared AlpacaManager for market data access

        """
        self._data_adapter = AlpacaDataAdapter(alpaca_manager)
        self._state_reader = PortfolioStateReader(self._data_adapter)
        self._planner = RebalancePlanCalculator()

    def create_rebalance_plan(
        self, strategy: StrategyAllocation, correlation_id: str
    ) -> RebalancePlan:
        """Create rebalance plan DTO from strategy allocation.

        This is the main entry point for portfolio rebalancing. It orchestrates
        the entire process from reading current state to producing a trade plan.

        Args:
            strategy: Strategy allocation with target weights and constraints
            correlation_id: Correlation ID for tracking this operation

        Returns:
            RebalancePlan with trade items ready for execution

        Raises:
            PortfolioError: If rebalance plan cannot be created

        """
        logger.info(
            "Creating rebalance plan",
            module=MODULE_NAME,
            action="create_rebalance_plan",
            correlation_id=correlation_id,
            target_symbols=sorted(strategy.target_weights.keys()),
            strategy_portfolio_value=str(strategy.portfolio_value)
            if strategy.portfolio_value
            else None,
        )

        try:
            # Step 1: Build current portfolio snapshot
            # Include all symbols from strategy target weights to ensure we have prices
            target_symbols = set(strategy.target_weights.keys())

            logger.debug(
                "Building portfolio snapshot",
                module=MODULE_NAME,
                action="build_snapshot",
                correlation_id=correlation_id,
                target_symbols=sorted(target_symbols),
            )

            snapshot = self._state_reader.build_portfolio_snapshot(symbols=target_symbols)

            # Step 2: Calculate rebalance plan
            logger.debug(
                "Calculating rebalance plan",
                module=MODULE_NAME,
                action="calculate_plan",
                correlation_id=correlation_id,
                snapshot_total_value=str(snapshot.total_value),
                snapshot_cash=str(snapshot.cash),
                snapshot_position_count=len(snapshot.positions),
            )

            plan = self._planner.build_plan(strategy, snapshot, correlation_id)

            # Step 3: Log successful completion
            trade_count = len([item for item in plan.items if item.action != "HOLD"])
            hold_count = len([item for item in plan.items if item.action == "HOLD"])

            logger.info(
                "Rebalance plan created successfully",
                module=MODULE_NAME,
                action="create_rebalance_plan",
                correlation_id=correlation_id,
                total_items=len(plan.items),
                trade_items=trade_count,
                hold_items=hold_count,
                total_trade_value=str(plan.total_trade_value),
            )

            return plan

        except Exception as e:
            logger.error(
                f"Failed to create rebalance plan: {e}",
                module=MODULE_NAME,
                action="create_rebalance_plan",
                correlation_id=correlation_id,
                error=str(e),
            )
            raise PortfolioError(f"Failed to create rebalance plan: {e}") from e
