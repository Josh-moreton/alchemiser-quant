#!/usr/bin/env python3
"""Application-layer rebalancing orchestrator facade.

This module provides a clean application-layer interface for portfolio rebalancing
orchestration, reusing existing domain and infrastructure components while providing
a single entry point for the TradingEngine to delegate rebalancing concerns.

This facade wraps the existing RebalancingOrchestrator and PortfolioManagementFacade
to provide a typed, clean interface for application-layer usage.
"""

import logging
from typing import Any

from the_alchemiser.application.portfolio.rebalancing_orchestrator import RebalancingOrchestrator
from the_alchemiser.application.portfolio.services.portfolio_management_facade import (
    PortfolioManagementFacade,
)
from the_alchemiser.domain.registry.strategy_registry import StrategyType
from the_alchemiser.domain.types import OrderDetails
from the_alchemiser.services.errors.context import create_error_context
from the_alchemiser.services.errors.exceptions import StrategyExecutionError
from the_alchemiser.services.errors.handler import TradingSystemErrorHandler


class RebalancingOrchestratorFacade:
    """Application-layer facade for portfolio rebalancing orchestration.

    Provides a clean, typed interface for rebalancing operations while delegating
    to existing domain and infrastructure components. This facade encapsulates
    the complexity of sequential SELL→settle→BUY execution patterns.

    Reuses:
    - RebalancingOrchestrator for settlement timing and WebSocket monitoring
    - PortfolioManagementFacade for phase-specific execution
    - TradingSystemErrorHandler for consistent error handling
    """

    def __init__(
        self,
        portfolio_facade: PortfolioManagementFacade,
        trading_client: Any,
        paper_trading: bool = True,
        account_info_provider: object = None,
    ) -> None:
        """Initialize the rebalancing orchestrator facade.

        Args:
            portfolio_facade: Existing PortfolioManagementFacade for operations
            trading_client: Alpaca trading client for WebSocket monitoring
            paper_trading: Whether using paper trading mode
            account_info_provider: Provider for account information

        """
        self.logger = logging.getLogger(__name__)
        self.error_handler = TradingSystemErrorHandler()

        # Reuse existing RebalancingOrchestrator
        self._orchestrator = RebalancingOrchestrator(
            portfolio_facade=portfolio_facade,
            trading_client=trading_client,
            paper_trading=paper_trading,
            account_info_provider=account_info_provider,
        )

        # Store facade for direct access to phase operations
        self._portfolio_facade = portfolio_facade

    def execute_full_rebalance_cycle(
        self,
        target_portfolio: dict[str, float],
        strategy_attribution: dict[str, list[StrategyType]] | None = None,
    ) -> list[OrderDetails]:
        """Execute complete rebalancing cycle with sequential SELL→settle→BUY.

        This method delegates to the existing RebalancingOrchestrator while providing
        consistent error handling and logging at the application layer.

        Args:
            target_portfolio: Target allocation weights (0.0-1.0) by symbol
            strategy_attribution: Mapping of symbols to contributing strategies

        Returns:
            List of all executed orders from both SELL and BUY phases

        Raises:
            StrategyExecutionError: If rebalancing fails

        """
        try:
            self.logger.info(f"Starting full rebalancing cycle for {len(target_portfolio)} symbols")

            # Delegate to existing orchestrator
            orders = self._orchestrator.execute_full_rebalance_cycle(
                target_portfolio, strategy_attribution
            )

            self.logger.info(f"Rebalancing cycle completed with {len(orders)} total orders")
            return orders

        except Exception as e:
            context = create_error_context(
                operation="execute_full_rebalance_cycle",
                component="RebalancingOrchestratorFacade.execute_full_rebalance_cycle",
                function_name="execute_full_rebalance_cycle",
                additional_data={
                    "target_symbols": list(target_portfolio.keys()),
                    "target_portfolio_size": len(target_portfolio),
                    "has_strategy_attribution": strategy_attribution is not None,
                },
            )
            self.error_handler.handle_error_with_context(
                error=e, context=context, should_continue=False
            )
            raise StrategyExecutionError(f"Rebalancing cycle failed: {e}") from e

    def execute_rebalance_phase(
        self,
        target_portfolio: dict[str, float],
        phase: str,
    ) -> list[OrderDetails]:
        """Execute a single phase of rebalancing (SELL or BUY).

        This method delegates to the existing PortfolioManagementFacade.rebalance_portfolio_phase
        while providing consistent error handling and logging.

        Args:
            target_portfolio: Target allocation weights by symbol
            phase: Either "sell" or "buy"

        Returns:
            List of executed orders for the specified phase

        Raises:
            StrategyExecutionError: If phase execution fails

        """
        try:
            phase_normalized = phase.lower().strip()
            self.logger.info(f"Executing {phase_normalized} phase for rebalancing")

            # Delegate to existing facade method
            orders = self._portfolio_facade.rebalance_portfolio_phase(
                target_portfolio, phase_normalized
            )

            self.logger.info(f"Phase {phase_normalized} completed with {len(orders)} orders")
            return orders

        except Exception as e:
            context = create_error_context(
                operation="execute_rebalance_phase",
                component="RebalancingOrchestratorFacade.execute_rebalance_phase",
                function_name="execute_rebalance_phase",
                additional_data={
                    "phase": phase,
                    "target_symbols": list(target_portfolio.keys()),
                },
            )
            self.error_handler.handle_error_with_context(
                error=e, context=context, should_continue=False
            )
            raise StrategyExecutionError(f"Rebalancing phase {phase} failed: {e}") from e
