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

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.strategy_allocation import StrategyAllocation

from ..adapters.market_data_adapter import StrategyMarketDataAdapter
from ..errors import ConfigurationError, StrategyExecutionError
from ..models.context import StrategyContext

logger = get_logger(__name__)

# Constants for repeated literals
ORCHESTRATOR_COMPONENT: str = "strategy_v2.core.orchestrator"


class SingleStrategyOrchestrator:
    """Orchestrates strategy execution and schema conversion.

    Coordinates between market data adapters, strategy engines, and output
    DTO generation with proper error handling and weight normalization.
    """

    def __init__(self, market_data_adapter: StrategyMarketDataAdapter) -> None:
        """Initialize orchestrator with market data adapter.

        Args:
            market_data_adapter: Configured market data adapter

        Note:
            Market data adapter is stored for future engine integration.
            Currently unused as sample allocation doesn't require market data.

        """
        self._market_data = market_data_adapter

    def run(
        self,
        strategy_id: str,
        context: StrategyContext,
        correlation_id: str | None = None,
    ) -> StrategyAllocation:
        """Run strategy and return allocation schema.

        Args:
            strategy_id: Strategy identifier (e.g., 'nuclear', 'klm', 'tecl')
            context: Strategy execution context
            correlation_id: Optional correlation ID for idempotent retry (generates new if not provided)

        Returns:
            Strategy allocation DTO with target weights

        Raises:
            StrategyExecutionError: If strategy execution fails
            ConfigurationError: If context validation fails

        """
        correlation_id = correlation_id or str(uuid.uuid4())

        try:
            logger.info(
                "Running strategy with context",
                extra={
                    "component": ORCHESTRATOR_COMPONENT,
                    "correlation_id": correlation_id,
                    "strategy_id": strategy_id,
                    "symbols": context.symbols,
                    "timeframe": context.timeframe,
                },
            )

            # Generate sample allocation for development/testing
            # This will be replaced with actual engine execution in future phases
            target_weights = self._generate_sample_allocation(context)

            # Normalize weights to sum to 1.0
            normalized_weights = self._normalize_weights(target_weights)

            # Create allocation DTO
            allocation = StrategyAllocation(
                target_weights=normalized_weights,
                correlation_id=correlation_id,
                as_of=context.as_of or datetime.now(UTC),
                constraints={
                    "strategy_id": strategy_id,
                    "symbols": ",".join(context.symbols),
                    "timeframe": context.timeframe,
                },
            )

            logger.info(
                "Strategy completed successfully",
                extra={
                    "component": ORCHESTRATOR_COMPONENT,
                    "correlation_id": correlation_id,
                    "strategy_id": strategy_id,
                    "weights_sum": float(sum(normalized_weights.values())),
                    "symbols_count": len(normalized_weights),
                },
            )

            return allocation

        except ConfigurationError:
            # Re-raise configuration errors directly with context
            raise
        except Exception as e:
            logger.error(
                "Strategy execution failed",
                extra={
                    "component": ORCHESTRATOR_COMPONENT,
                    "correlation_id": correlation_id,
                    "strategy_id": strategy_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )
            raise StrategyExecutionError(
                f"Strategy execution failed: {e}",
                strategy_id=strategy_id,
                correlation_id=correlation_id,
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
            Handles edge cases like zero sum or negative weights by falling back
            to equal weights. This ensures robustness in strategy execution.

        """
        if not weights:
            return {}

        total = sum(weights.values())

        # Handle zero or negative total
        if total <= 0:
            logger.warning(
                "Invalid total weight, using equal weights fallback",
                extra={
                    "component": ORCHESTRATOR_COMPONENT,
                    "total_weight": float(total),
                    "symbols_count": len(weights),
                },
            )
            # Fall back to equal weights
            equal_weight = Decimal("1.0") / len(weights)
            return dict.fromkeys(weights.keys(), equal_weight)

        # Normalize to sum to 1.0
        return {symbol: weight / total for symbol, weight in weights.items()}
