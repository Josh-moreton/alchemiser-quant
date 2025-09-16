"""Business Unit: execution | Status: current.

Execution manager that coordinates Executor with AlpacaManager.
"""

from __future__ import annotations

import logging

from the_alchemiser.execution_v2.core.executor import Executor
from the_alchemiser.execution_v2.core.smart_execution_strategy import ExecutionConfig
from the_alchemiser.execution_v2.models.execution_result import ExecutionResultDTO
from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
from the_alchemiser.shared.dto.rebalance_plan_dto import RebalancePlanDTO

logger = logging.getLogger(__name__)


class ExecutionManager:
    """Execution manager that delegates to Executor with smart execution capabilities."""

    def __init__(
        self,
        alpaca_manager: AlpacaManager,
        execution_config: ExecutionConfig | None = None,
        *,
        enable_smart_execution: bool = True,
    ) -> None:
        """Initialize the execution manager.

        Args:
            alpaca_manager: The Alpaca broker manager
            execution_config: Configuration for smart execution strategies
            enable_smart_execution: Whether to enable smart execution features

        """
        self.alpaca_manager = alpaca_manager
        self.enable_smart_execution = enable_smart_execution

        # Delegate all execution (and smart execution setup) to Executor
        self.executor = Executor(
            alpaca_manager=alpaca_manager,
            execution_config=execution_config,
            enable_smart_execution=enable_smart_execution,
        )

    def execute_rebalance_plan(self, plan: RebalancePlanDTO) -> ExecutionResultDTO:
        """Execute rebalance plan using executor.

        Args:
            plan: RebalancePlanDTO to execute

        Returns:
            ExecutionResultDTO with execution results

        """
        logger.info(f"🚀 NEW EXECUTION: {len(plan.items)} items (using execution_v2)")

        # Run the async executor in a new event loop
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're in an async context, use async directly
                raise RuntimeError("Cannot run asyncio.run() in an existing event loop")
        except RuntimeError:
            # No event loop running, safe to use asyncio.run
            result = asyncio.run(self.executor.execute_rebalance_plan(plan))
        else:
            # Event loop exists but not running, safe to use asyncio.run
            result = asyncio.run(self.executor.execute_rebalance_plan(plan))

        logger.info(
            f"✅ Execution complete: {result.success} ({result.orders_placed} orders)"
        )
        return result

    @classmethod
    def create_with_config(
        cls,
        api_key: str,
        secret_key: str,
        *,
        paper: bool = True,
        execution_config: ExecutionConfig | None = None,
        enable_smart_execution: bool = True,
    ) -> ExecutionManager:
        """Create ExecutionManager with config and smart execution options.

        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key
            paper: Whether to use paper trading
            execution_config: Configuration for smart execution strategies
            enable_smart_execution: Whether to enable smart limit order execution

        Returns:
            ExecutionManager instance with configured smart execution

        """
        alpaca_manager = AlpacaManager(
            api_key=api_key, secret_key=secret_key, paper=paper
        )
        return cls(
            alpaca_manager=alpaca_manager,
            execution_config=execution_config,
            enable_smart_execution=enable_smart_execution,
        )
