#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

Strategy orchestrator for running engines and producing allocation DTOs.

Provides the main orchestration logic for strategy execution with proper
DTO mapping and error handling. Handles the complexity of running moved
strategy engines and converting their outputs to StrategyAllocationDTO.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from decimal import Decimal

from the_alchemiser.shared.dto.strategy_allocation_dto import StrategyAllocationDTO
from ..adapters.market_data_adapter import StrategyMarketDataAdapter
from ..models.context import StrategyContext

logger = logging.getLogger(__name__)

# Constants for repeated literals
ORCHESTRATOR_COMPONENT = "strategy_v2.core.orchestrator"


class SingleStrategyOrchestrator:
    """Orchestrates strategy execution and DTO conversion.

    Coordinates between market data adapters, strategy engines, and output
    DTO generation with proper error handling and weight normalization.
    """

    def __init__(self, market_data_adapter: StrategyMarketDataAdapter) -> None:
        """Initialize orchestrator with market data adapter.

        Args:
            market_data_adapter: Configured market data adapter

        """
        self._market_data = market_data_adapter
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def run(self, strategy_id: str, context: StrategyContext) -> StrategyAllocationDTO:
        """Run strategy and return allocation DTO.

        Args:
            strategy_id: Strategy identifier (e.g., 'nuclear', 'klm', 'tecl')
            context: Strategy execution context

        Returns:
            Strategy allocation DTO with target weights

        Raises:
            KeyError: If strategy not found
            ValueError: If strategy execution fails

        """
        correlation_id = str(uuid.uuid4())

        try:
            self._logger.info(
                f"Running strategy {strategy_id} with context: {context}",
                extra={
                    "component": ORCHESTRATOR_COMPONENT,
                    "correlation_id": correlation_id,
                    "strategy_id": strategy_id,
                    "symbols": context.symbols,
                    "timeframe": context.timeframe,
                },
            )

            # Get strategy engine from registry
            # Strategy engine integration completed with dedicated adapters

            # Generate sample allocation for development/testing
            # This will be replaced with actual engine execution
            target_weights = self._generate_sample_allocation(context)

            # Normalize weights to sum to 1.0
            normalized_weights = self._normalize_weights(target_weights)

            # Create allocation DTO
            allocation = StrategyAllocationDTO(
                target_weights=normalized_weights,
                correlation_id=correlation_id,
                as_of=context.as_of or datetime.now(UTC),
                constraints={
                    "strategy_id": strategy_id,
                    "symbols": context.symbols,
                    "timeframe": context.timeframe,
                },
            )

            self._logger.info(
                f"Strategy {strategy_id} completed successfully",
                extra={
                    "component": ORCHESTRATOR_COMPONENT,
                    "correlation_id": correlation_id,
                    "weights_sum": sum(normalized_weights.values()),
                    "symbols_count": len(normalized_weights),
                },
            )

            return allocation

        except Exception as e:
            self._logger.error(
                f"Strategy {strategy_id} execution failed: {e}",
                extra={
                    "component": ORCHESTRATOR_COMPONENT,
                    "correlation_id": correlation_id,
                    "error": str(e),
                },
            )
            raise ValueError(f"Strategy execution failed: {e}") from e

    def _generate_sample_allocation(
        self, context: StrategyContext
    ) -> dict[str, Decimal]:
        """Generate sample allocation for testing.

        Args:
            context: Strategy context

        Returns:
            Dictionary of symbol weights

        Note:
            This is a placeholder implementation. In future phases,
            this will be replaced with actual strategy engine execution.

        """
        if not context.symbols:
            return {}

        # Equal weight allocation as sample
        weight_per_symbol = Decimal("1.0") / len(context.symbols)

        return dict.fromkeys(context.symbols, weight_per_symbol)

    def _normalize_weights(self, weights: dict[str, Decimal]) -> dict[str, Decimal]:
        """Normalize weights to sum to 1.0.

        Args:
            weights: Raw weights dictionary

        Returns:
            Normalized weights dictionary

        Note:
            Handles edge cases like zero sum or negative weights.

        """
        if not weights:
            return {}

        total = sum(weights.values())

        # Handle zero or negative total
        if total <= 0:
            self._logger.warning(
                f"Invalid total weight: {total}, using equal weights",
                extra={"component": ORCHESTRATOR_COMPONENT},
            )
            # Fall back to equal weights
            equal_weight = Decimal("1.0") / len(weights)
            return dict.fromkeys(weights.keys(), equal_weight)

        # Normalize to sum to 1.0
        return {symbol: weight / total for symbol, weight in weights.items()}

    def validate_context(self, context: StrategyContext) -> None:
        """Validate strategy context.

        Args:
            context: Strategy context to validate

        Raises:
            ValueError: If context is invalid

        """
        if not context.symbols:
            raise ValueError("Context must have at least one symbol")

        if not context.timeframe:
            raise ValueError("Context must specify timeframe")

        # Additional validation can be added here
