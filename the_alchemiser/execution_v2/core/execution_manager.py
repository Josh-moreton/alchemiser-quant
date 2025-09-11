"""Business Unit: execution | Status: current.

Execution manager that coordinates Executor with AlpacaManager.
"""

from __future__ import annotations

import logging

from the_alchemiser.execution_v2.core.executor import Executor
from the_alchemiser.execution_v2.models.execution_result import ExecutionResultDTO
from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
from the_alchemiser.shared.dto.rebalance_plan_dto import RebalancePlanDTO

logger = logging.getLogger(__name__)


class ExecutionManager:
    """Execution manager that delegates to Executor."""

    def __init__(self, alpaca_manager: AlpacaManager) -> None:
        """Initialize with shared Alpaca manager."""
        self.alpaca_manager = alpaca_manager
        self.executor = Executor(alpaca_manager)

    def execute_rebalance_plan(self, plan: RebalancePlanDTO) -> ExecutionResultDTO:
        """Execute rebalance plan using executor.
        
        Args:
            plan: RebalancePlanDTO to execute
            
        Returns:
            ExecutionResultDTO with execution results

        """
        logger.info(f"🚀 NEW EXECUTION: {len(plan.items)} items (using execution_v2)")
        
        result = self.executor.execute_rebalance_plan(plan)
        
        logger.info(f"✅ Execution complete: {result.success} ({result.orders_placed} orders)")
        return result

    @classmethod
    def create_with_config(
        cls, 
        api_key: str, 
        secret_key: str, 
        *, 
        paper: bool = True
    ) -> ExecutionManager:
        """Create ExecutionManager with config.
        
        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key  
            paper: Whether to use paper trading
            
        Returns:
            ExecutionManager instance

        """
        alpaca_manager = AlpacaManager(
            api_key=api_key,
            secret_key=secret_key,
            paper=paper
        )
        return cls(alpaca_manager)