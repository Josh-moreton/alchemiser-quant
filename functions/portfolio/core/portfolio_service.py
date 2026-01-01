"""Business Unit: portfolio | Status: current.

Portfolio state management and rebalancing logic.

Portfolio service V2 - orchestration facade for rebalance plan creation.

Examples:
    Basic usage with event-driven architecture:
        >>> from the_alchemiser.portfolio_v2 import register_portfolio_handlers
        >>> register_portfolio_handlers(container)  # Registers event handlers

    Direct usage (legacy, being phased out):
        >>> from decimal import Decimal
        >>> from the_alchemiser.portfolio_v2.core.portfolio_service import PortfolioServiceV2
        >>> from the_alchemiser.shared.schemas.strategy_allocation import StrategyAllocation
        >>>
        >>> service = PortfolioServiceV2(alpaca_manager)
        >>> strategy = StrategyAllocation(
        ...     target_weights={"AAPL": Decimal("0.6"), "MSFT": Decimal("0.4")},
        ...     correlation_id="trade-123"
        ... )
        >>> plan = service.create_rebalance_plan(
        ...     strategy=strategy,
        ...     correlation_id="trade-123",
        ...     causation_id="signal-456"
        ... )

Idempotency:
    This service is designed to be idempotent and replay-tolerant when used
    through the event-driven handler (PortfolioAnalysisHandler). The handler
    ensures idempotency through:
    - Deduplication at the event bus level using correlation_id
    - Deterministic plan generation from StrategyAllocation DTOs
    - Stateless service design with no side effects

    Direct service calls (legacy) do not have built-in idempotency and should
    use the event-driven API for production workflows.

"""

from __future__ import annotations

import time
from decimal import Decimal
from typing import TYPE_CHECKING

from the_alchemiser.shared.errors.exceptions import PortfolioError
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlan

if TYPE_CHECKING:
    from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
    from the_alchemiser.shared.schemas.strategy_allocation import StrategyAllocation

from adapters.alpaca_data_adapter import AlpacaDataAdapter
from core.planner import RebalancePlanCalculator
from core.state_reader import PortfolioStateReader

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
        self,
        strategy: StrategyAllocation,
        correlation_id: str,
        causation_id: str | None = None,
        strategy_contributions: dict[str, dict[str, Decimal]] | None = None,
    ) -> RebalancePlan:
        """Create rebalance plan DTO from strategy allocation.

        This is the main entry point for portfolio rebalancing. It orchestrates
        the entire process from reading current state to producing a trade plan.

        Args:
            strategy: Strategy allocation with target weights and constraints
            correlation_id: Correlation ID for tracking this operation
            causation_id: Causation ID for event traceability (defaults to correlation_id)
            strategy_contributions: Per-strategy allocation breakdown for attribution
                Format: {strategy_id: {symbol: weight}}

        Returns:
            RebalancePlan with trade items ready for execution

        Raises:
            PortfolioError: If rebalance plan cannot be created
            ValueError: If strategy allocation is invalid

        """
        # Use correlation_id as causation_id if not provided
        if causation_id is None:
            causation_id = correlation_id

        # Input validation at entry boundary
        if not strategy.target_weights:
            raise ValueError("Strategy allocation must have at least one target weight")

        # Performance tracking
        start_time = time.perf_counter()

        logger.info(
            "Creating rebalance plan",
            module=MODULE_NAME,
            action="create_rebalance_plan",
            correlation_id=correlation_id,
            causation_id=causation_id,
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
                causation_id=causation_id,
                target_symbols=sorted(target_symbols),
            )

            snapshot_start = time.perf_counter()
            snapshot = self._state_reader.build_portfolio_snapshot(symbols=target_symbols)
            snapshot_duration = time.perf_counter() - snapshot_start

            # Step 2: Calculate rebalance plan
            logger.debug(
                "Calculating rebalance plan",
                module=MODULE_NAME,
                action="calculate_plan",
                correlation_id=correlation_id,
                causation_id=causation_id,
                snapshot_total_value=str(snapshot.total_value),
                snapshot_cash=str(snapshot.cash),
                snapshot_position_count=len(snapshot.positions),
                snapshot_build_duration_ms=round(snapshot_duration * 1000, 2),
            )

            plan_start = time.perf_counter()
            plan = self._planner.build_plan(
                strategy, snapshot, correlation_id, causation_id, strategy_contributions
            )
            plan_duration = time.perf_counter() - plan_start

            # Step 3: Log successful completion with performance metrics
            trade_count = len([item for item in plan.items if item.action != "HOLD"])
            hold_count = len([item for item in plan.items if item.action == "HOLD"])
            total_duration = time.perf_counter() - start_time

            logger.info(
                "Rebalance plan created successfully",
                module=MODULE_NAME,
                action="create_rebalance_plan",
                correlation_id=correlation_id,
                causation_id=causation_id,
                total_items=len(plan.items),
                trade_items=trade_count,
                hold_items=hold_count,
                total_trade_value=str(plan.total_trade_value),
                snapshot_build_duration_ms=round(snapshot_duration * 1000, 2),
                plan_calculation_duration_ms=round(plan_duration * 1000, 2),
                total_duration_ms=round(total_duration * 1000, 2),
            )

            return plan

        except Exception as e:
            total_duration = time.perf_counter() - start_time
            logger.error(
                "Failed to create rebalance plan",
                module=MODULE_NAME,
                action="create_rebalance_plan",
                correlation_id=correlation_id,
                causation_id=causation_id,
                error=str(e),
                error_type=type(e).__name__,
                target_symbols=sorted(strategy.target_weights.keys())
                if strategy.target_weights
                else [],
                strategy_portfolio_value=str(strategy.portfolio_value)
                if strategy.portfolio_value
                else None,
                duration_before_failure_ms=round(total_duration * 1000, 2),
            )
            raise PortfolioError(f"Failed to create rebalance plan: {e}") from e
