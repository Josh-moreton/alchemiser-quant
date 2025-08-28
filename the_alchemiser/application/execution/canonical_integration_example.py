"""Business Unit: order execution/placement; Status: legacy.

Integration example for canonical order executor.

This module demonstrates how the canonical order executor can be integrated
into existing trading workflows with shadow mode for safe rollout.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from decimal import Decimal
from typing import TYPE_CHECKING

from the_alchemiser.execution.application.canonical_executor import (
    CanonicalOrderExecutor,
)
from the_alchemiser.shared_kernel.value_objects.money import Money
from the_alchemiser.domain.trading.value_objects.order_request import OrderRequest
from the_alchemiser.domain.trading.value_objects.order_type import OrderType
from the_alchemiser.domain.trading.value_objects.quantity import Quantity
from the_alchemiser.domain.trading.value_objects.side import Side
from the_alchemiser.domain.trading.value_objects.symbol import Symbol
from the_alchemiser.domain.trading.value_objects.time_in_force import TimeInForce
from the_alchemiser.infrastructure.config import load_settings
from the_alchemiser.interfaces.schemas.orders import (
    OrderExecutionResultDTO,
    OrderRequestDTO,
)

if TYPE_CHECKING:
    from the_alchemiser.infrastructure.repositories.alpaca_manager import AlpacaManager

logger = logging.getLogger(__name__)


def dto_to_domain_order_request(dto: OrderRequestDTO) -> OrderRequest:
    """Convert OrderRequestDTO to domain OrderRequest value object.

    Args:
        dto: Pydantic DTO from interface layer

    Returns:
        OrderRequest: Domain value object

    """
    limit_price = None
    if dto.limit_price is not None:
        limit_price = Money(dto.limit_price, "USD")

    return OrderRequest(
        symbol=Symbol(dto.symbol),
        side=Side(dto.side),
        quantity=Quantity(dto.quantity),
        order_type=OrderType(dto.order_type),
        time_in_force=TimeInForce(dto.time_in_force),
        limit_price=limit_price,
        client_order_id=dto.client_order_id,
    )


def execute_order_with_canonical_path(
    order_dto: OrderRequestDTO,
    repository: AlpacaManager,
    legacy_execute_fn: (Callable[[OrderRequestDTO], OrderExecutionResultDTO] | None) = None,
) -> OrderExecutionResultDTO:
    """Execute order using canonical executor with feature flag and shadow mode.

    This function demonstrates how to integrate the canonical executor into
    existing workflows with proper feature flag checking and shadow mode.

    Args:
        order_dto: Order request DTO from interface layer
        repository: AlpacaManager instance
        legacy_execute_fn: Optional legacy execution function for fallback

    Returns:
        OrderExecutionResultDTO: Execution result

    """
    settings = load_settings()
    use_canonical = settings.execution.use_canonical_executor

    if use_canonical:
        logger.info("Using canonical order executor (feature flag enabled)")

        # Convert DTO to domain value object
        domain_order = dto_to_domain_order_request(order_dto)

        # Execute via canonical path
        executor = CanonicalOrderExecutor(repository, shadow_mode=False)
        return executor.execute(domain_order)

    # Feature flag disabled - use legacy path with optional shadow mode
    logger.info("Using legacy order execution (canonical executor disabled)")

    # Optional: Run canonical executor in shadow mode for comparison
    try:
        domain_order = dto_to_domain_order_request(order_dto)
        shadow_executor = CanonicalOrderExecutor(repository, shadow_mode=True)
        shadow_result = shadow_executor.execute(domain_order)
        logger.info(f"[SHADOW] Canonical execution would result in: {shadow_result.status}")
    except Exception as e:
        logger.warning(f"Shadow mode canonical execution failed: {e}")

    # Execute via legacy path
    if legacy_execute_fn:
        return legacy_execute_fn(order_dto)

    # Fallback to direct repository call
    # This would be replaced with actual legacy execution logic
    logger.warning("No legacy execution function provided, using repository directly")
    raw_envelope = repository.place_order(order_dto)

    # Convert RawOrderEnvelope to OrderExecutionResultDTO
    from the_alchemiser.application.mapping.order_mapping import (
        raw_order_envelope_to_execution_result_dto,
    )

    return raw_order_envelope_to_execution_result_dto(raw_envelope)


# Example usage function
def example_integration() -> OrderExecutionResultDTO:
    """Example of how to integrate canonical executor."""
    # This would normally come from your trading workflow
    order_dto = OrderRequestDTO(
        symbol="AAPL",
        side="buy",
        quantity=Decimal("100"),
        order_type="market",
        time_in_force="day",
    )

    # Mock repository (in real usage, this would be your actual AlpacaManager)
    from unittest.mock import Mock

    mock_repository = Mock()

    # Example legacy function (in real usage, this would be your actual legacy execution)
    def mock_legacy_execute(dto: OrderRequestDTO) -> OrderExecutionResultDTO:
        from datetime import UTC, datetime

        return OrderExecutionResultDTO(
            success=True,
            error=None,
            order_id="legacy_mock_id",
            status="accepted",
            filled_qty=Decimal("0"),
            avg_fill_price=None,
            submitted_at=datetime.now(UTC),
            completed_at=None,
        )

    # Execute with canonical path integration
    result = execute_order_with_canonical_path(
        order_dto=order_dto,
        repository=mock_repository,
        legacy_execute_fn=mock_legacy_execute,
    )

    logger.info(f"Order execution completed: {result.order_id}")
    return result
