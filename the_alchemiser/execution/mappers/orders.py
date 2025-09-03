"""Business Unit: execution | Status: current..

    Args:
        request: The original order request
        estimated_value: Estimated order value
        is_fractional: Whether the order quantity is fractional
        normalized_quantity: Normalized quantity after validation
        risk_score: Risk score from validation

    Returns:
        ValidatedOrderDTO instance

    """
    return ValidatedOrderDTO(
        # Core order fields from request
        symbol=request.symbol,
        side=request.side,
        quantity=request.quantity,
        order_type=request.order_type,
        time_in_force=request.time_in_force,
        limit_price=request.limit_price,
        client_order_id=request.client_order_id,
        # Derived validation fields
        estimated_value=estimated_value,
        is_fractional=is_fractional,
        normalized_quantity=normalized_quantity or request.quantity,
        risk_score=risk_score,
        validation_timestamp=datetime.now(UTC),
    )


def validated_dto_to_dict(validated_order: ValidatedOrderDTO) -> dict[str, Any]:
    """Convert ValidatedOrderDTO back to dictionary for backward compatibility.

    Args:
        validated_order: ValidatedOrderDTO instance

    Returns:
        Dictionary representation for legacy systems

    """
    return {
        "symbol": validated_order.symbol,
        "side": validated_order.side,
        "quantity": float(validated_order.quantity),
        "order_type": validated_order.order_type,
        "time_in_force": validated_order.time_in_force,
        "limit_price": float(validated_order.limit_price) if validated_order.limit_price else None,
        "client_order_id": validated_order.client_order_id,
        "estimated_value": (
            float(validated_order.estimated_value) if validated_order.estimated_value else None
        ),
        "is_fractional": validated_order.is_fractional,
        "normalized_quantity": (
            float(validated_order.normalized_quantity)
            if validated_order.normalized_quantity
            else None
        ),
        "risk_score": float(validated_order.risk_score) if validated_order.risk_score else None,
        "validation_timestamp": validated_order.validation_timestamp.isoformat(),
    }


def validated_dto_to_order_handler_params(validated_order: ValidatedOrderDTO) -> dict[str, Any]:
    """Convert ValidatedOrderDTO to parameters suitable for order handlers.

    Args:
        validated_order: ValidatedOrderDTO instance

    Returns:
        Dictionary with parameters for AssetOrderHandler (LimitOrderHandler deprecated)

    """
    # Convert side to Alpaca OrderSide enum value for handler compatibility
    from alpaca.trading.enums import OrderSide

    order_side = OrderSide.BUY if validated_order.side.lower() == "buy" else OrderSide.SELL
    quantity = float(validated_order.normalized_quantity or validated_order.quantity)

    params = {
        "symbol": validated_order.symbol,
        "side": order_side,
        "qty": quantity,
        "order_type": validated_order.order_type,
        "time_in_force": validated_order.time_in_force,
    }

    # Add limit price if it's a limit order
    if validated_order.limit_price is not None:
        params["limit_price"] = float(validated_order.limit_price)

    return params


def order_request_dto_to_domain_order_params(dto: OrderRequestDTO) -> dict[str, Any]:
    """Convert OrderRequestDTO to domain Order entity creation parameters.

    Args:
        dto: OrderRequestDTO instance to convert

    Returns:
        Dictionary with parameters needed to create domain Order entity

    Raises:
        ValueError: If required domain conversions fail

    """
    # Convert DTO fields to domain value objects
    symbol = Symbol(dto.symbol)
    quantity = Quantity(dto.quantity)

    # Convert limit price to Money if present
    limit_price = None
    if dto.limit_price is not None:
        limit_price = Money(dto.limit_price, "USD")

    # Generate a new OrderId - this would typically come from infrastructure
    order_id = OrderId.generate()

    # Map order type and time in force to the format expected by domain
    order_type_mapping = {"market": "MARKET", "limit": "LIMIT"}
    order_type = order_type_mapping.get(dto.order_type, dto.order_type.upper())

    return {
        "id": order_id,
        "symbol": symbol,
        "quantity": quantity,
        "status": OrderStatus.NEW,
        "order_type": order_type,
        "limit_price": limit_price,
        # Additional context that might be useful for order creation
        "side": dto.side,
        "time_in_force": dto.time_in_force,
        "client_order_id": dto.client_order_id,
    }


def domain_order_to_execution_result_dto(order: Order) -> OrderExecutionResultDTO:
    """Convert domain Order entity to OrderExecutionResultDTO.

    Args:
        order: Domain Order entity to convert

    Returns:
        OrderExecutionResultDTO instance with execution result data

    Raises:
        ValueError: If order data cannot be converted to DTO format

    """
    # Map domain OrderStatus to DTO status literals
    status_mapping = {
        OrderStatus.NEW: "accepted",
        OrderStatus.PARTIALLY_FILLED: "partially_filled",
        OrderStatus.FILLED: "filled",
        OrderStatus.CANCELLED: "canceled",
        OrderStatus.REJECTED: "rejected",
    }

    dto_status = status_mapping.get(order.status)
    if dto_status is None:
        raise ValueError(f"Cannot map order status {order.status} to DTO format")

    # Calculate average fill price if filled quantity > 0
    avg_fill_price = None
    if order.filled_quantity.value > 0 and order.limit_price is not None:
        # For simplicity, use limit price as avg fill price
        # In real implementation, this would track actual fill prices
        avg_fill_price = order.limit_price.amount

    # Determine completion time based on status
    completed_at = None
    if order.status in (OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED):
        completed_at = order.created_at  # Simplified - would track actual completion time

    status_literal = cast(
        Literal["accepted", "filled", "partially_filled", "rejected", "canceled"], dto_status
    )
    success = status_literal not in {"rejected"}
    return OrderExecutionResultDTO(
        success=success,
        error=None if success else "Order rejected",
        order_id=str(order.id.value),
        status=status_literal,
        filled_qty=order.filled_quantity.value,
        avg_fill_price=avg_fill_price,
        submitted_at=order.created_at,
        completed_at=completed_at,
    )
