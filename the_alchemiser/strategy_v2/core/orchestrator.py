#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

Strategy orchestrator for running engines and producing allocation DTOs.

Provides the main orchestration logic for strategy execution with proper
DTO mapping and error handling. Handles the complexity of running moved
strategy engines and converting their outputs to StrategyAllocation.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from the_alchemiser.shared.errors import EnhancedTradingError
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.strategy_allocation import StrategyAllocation

from ..adapters.market_data_adapter import StrategyMarketDataAdapter
from ..models.context import StrategyContext

logger = get_logger(__name__)

# Constants for repeated literals
ORCHESTRATOR_COMPONENT = "strategy_v2.core.orchestrator"


class SingleStrategyOrchestrator:
    """Orchestrates strategy execution and schema conversion.

    Coordinates between market data adapters, strategy engines, and output
    DTO generation with proper error handling and weight normalization.
    """

    def __init__(self, market_data_adapter: StrategyMarketDataAdapter) -> None:
        """Initialize orchestrator with market data adapter.

        Args:
            market_data_adapter: Configured market data adapter

        """
        self._market_data = market_data_adapter

    def run(self, strategy_id: str, context: StrategyContext, causation_id: str | None = None) -> StrategyAllocation:
        """Run strategy and return allocation schema.

        Args:
            strategy_id: Strategy identifier (e.g., 'nuclear', 'klm', 'tecl')
            context: Strategy execution context
            causation_id: Optional causation ID from triggering event for correlation tracking

        Returns:
            Strategy allocation DTO with target weights

        Raises:
            EnhancedTradingError: If strategy execution fails

        """
        # Validate context before execution
        self.validate_context(context)
        
        correlation_id = str(uuid.uuid4())

        try:
            logger.info(
                f"Running strategy {strategy_id} with context: {context}",
                extra={
                    "component": ORCHESTRATOR_COMPONENT,
                    "correlation_id": correlation_id,
                    "causation_id": causation_id,
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
            allocation = StrategyAllocation(
                target_weights=normalized_weights,
                correlation_id=correlation_id,
                causation_id=causation_id,
                as_of=context.as_of or datetime.now(UTC),
                constraints={
                    "strategy_id": strategy_id,
                    "symbols": context.symbols,
                    "timeframe": context.timeframe,
                },
            )

            logger.info(
                f"Strategy {strategy_id} completed successfully",
                extra={
                    "component": ORCHESTRATOR_COMPONENT,
                    "correlation_id": correlation_id,
                    "causation_id": causation_id,
                    "weights_sum": sum(normalized_weights.values()),
                    "symbols_count": len(normalized_weights),
                    "target_weights": {k: str(v) for k, v in normalized_weights.items()},
                },
            )

            return allocation

        except Exception as e:
            logger.error(
                f"Strategy {strategy_id} execution failed: {e}",
                extra={
                    "component": ORCHESTRATOR_COMPONENT,
                    "correlation_id": correlation_id,
                    "causation_id": causation_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )
            raise EnhancedTradingError(
                f"Strategy execution failed: {e}",
                context={
                    "strategy_id": strategy_id,
                    "correlation_id": correlation_id,
                    "causation_id": causation_id,
                    "symbols": context.symbols,
                    "timeframe": context.timeframe,
                },
            ) from e

    def _generate_sample_allocation(self, context: StrategyContext) -> dict[str, Decimal]:
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

        # Handle zero or negative total (use explicit Decimal comparison)
        if total <= Decimal("0"):
            logger.warning(
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
