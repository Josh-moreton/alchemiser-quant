"""Business Unit: utilities; Status: current.

Policy mapping utilities for converting between DTOs and domain objects.

This module is part of the anti-corruption layer, converting between interface
DTOs (Pydantic models) and pure domain objects for policy processing. This
maintains domain layer purity while providing type-safe boundaries.
"""

from __future__ import annotations

from decimal import Decimal

from the_alchemiser.execution.domain.policy_result import PolicyResult, PolicyWarning
from the_alchemiser.shared_kernel.value_objects.money import Money
from the_alchemiser.execution.domain.value_objects.order_request import OrderRequest
from the_alchemiser.execution.domain.value_objects.order_type import OrderType
from the_alchemiser.execution.domain.value_objects.quantity import Quantity
from the_alchemiser.execution.domain.value_objects.side import Side
from the_alchemiser.execution.domain.value_objects.symbol import Symbol
from the_alchemiser.execution.domain.value_objects.time_in_force import TimeInForce
from the_alchemiser.shared_kernel.interfaces.orders import (
    AdjustedOrderRequestDTO,
    OrderRequestDTO,
    PolicyWarningDTO,
)


def dto_to_domain_order_request(dto: OrderRequestDTO) -> OrderRequest:
    """Convert OrderRequestDTO to domain OrderRequest."""
    # Convert limit_price with default currency handling
    limit_price = None
    if dto.limit_price is not None:
        # TODO: Make currency configurable rather than hardcoded
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


def domain_order_request_to_dto(order_request: OrderRequest) -> OrderRequestDTO:
    """Convert domain OrderRequest to OrderRequestDTO."""
    # Extract limit price amount if present
    limit_price = None
    if order_request.limit_price is not None:
        limit_price = order_request.limit_price.amount

    return OrderRequestDTO(
        symbol=order_request.symbol.value,
        side=order_request.side.value,
        quantity=order_request.quantity.value,
        order_type=order_request.order_type.value,
        time_in_force=order_request.time_in_force.value,
        limit_price=limit_price,
        client_order_id=order_request.client_order_id,
    )


def domain_warning_to_dto(warning: PolicyWarning) -> PolicyWarningDTO:
    """Convert domain PolicyWarning to PolicyWarningDTO."""
    return PolicyWarningDTO(
        policy_name=warning.policy_name,
        action=warning.action,
        message=warning.message,
        original_value=warning.original_value,
        adjusted_value=warning.adjusted_value,
        risk_level=warning.risk_level,
    )


def dto_warning_to_domain(dto: PolicyWarningDTO) -> PolicyWarning:
    """Convert PolicyWarningDTO to domain PolicyWarning."""
    # Handle None values by providing defaults that match the domain constraints
    action = dto.action if dto.action in ["adjust", "allow", "reject"] else "allow"
    risk_level = dto.risk_level if dto.risk_level in ["low", "medium", "high"] else "low"

    return PolicyWarning(
        policy_name=dto.policy_name,
        action=action,  # type: ignore[arg-type]
        message=dto.message,
        original_value=dto.original_value,
        adjusted_value=dto.adjusted_value,
        risk_level=risk_level,  # type: ignore[arg-type]
    )


def domain_result_to_dto(result: PolicyResult) -> AdjustedOrderRequestDTO:
    """Convert domain PolicyResult to AdjustedOrderRequestDTO."""
    # Convert order request
    order_dto = domain_order_request_to_dto(result.order_request)

    # Convert warnings
    warning_dtos = [domain_warning_to_dto(warning) for warning in result.warnings]

    # Create DTO with new collections to avoid mutable defaults
    return AdjustedOrderRequestDTO(
        symbol=order_dto.symbol,
        side=order_dto.side,
        quantity=order_dto.quantity,
        order_type=order_dto.order_type,
        time_in_force=order_dto.time_in_force,
        limit_price=order_dto.limit_price,
        client_order_id=order_dto.client_order_id,
        is_approved=result.is_approved,
        original_quantity=result.original_quantity,
        adjustment_reason=result.adjustment_reason,
        warnings=warning_dtos,
        policy_metadata=result.policy_metadata or {},
        total_risk_score=result.total_risk_score,
        rejection_reason=result.rejection_reason,
    )


def dto_to_domain_result(dto: AdjustedOrderRequestDTO) -> PolicyResult:
    """Convert AdjustedOrderRequestDTO to domain PolicyResult."""
    # Convert order request
    order_request = OrderRequest(
        symbol=Symbol(dto.symbol),
        side=Side(dto.side),
        quantity=Quantity(dto.quantity),
        order_type=OrderType(dto.order_type),
        time_in_force=TimeInForce(dto.time_in_force),
        limit_price=Money(dto.limit_price, "USD") if dto.limit_price else None,
        client_order_id=dto.client_order_id,
    )

    # Convert warnings to immutable tuple
    warnings = tuple(dto_warning_to_domain(w) for w in dto.warnings)

    return PolicyResult(
        order_request=order_request,
        is_approved=dto.is_approved,
        original_quantity=dto.original_quantity,
        adjustment_reason=dto.adjustment_reason,
        rejection_reason=dto.rejection_reason,
        warnings=warnings,
        policy_metadata=dto.policy_metadata if dto.policy_metadata else None,
        total_risk_score=dto.total_risk_score or Decimal("0"),
    )
