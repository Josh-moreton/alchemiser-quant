#!/usr/bin/env python3
"""Business Unit: shared | Status: current.."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    order_id: str | None = None


class OrderStatusResult(Result):
    """DTO for order status query results."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    order_id: str | None = None
    status: str | None = None


# Backward compatibility aliases - will be removed in future version
OperationResultDTO = OperationResult
OrderCancellationDTO = OrderCancellationResult
OrderStatusDTO = OrderStatusResult
