"""Business Unit: strategy | Status: current..

    Args:
        signal: Typed domain StrategySignal with value objects
        portfolio_value: Total portfolio value for quantity calculation
        order_type: Order type (market or limit)
        time_in_force: Time in force specification
        limit_price: Limit price for limit orders
        client_order_id: Optional client order ID

    Returns:
        ValidatedOrderDTO instance ready for order execution

    Raises:
        ValueError: If signal action is HOLD or other invalid states
        ValueError: If limit order without limit_price

    """
    # Handle HOLD signals - these should not generate orders
    if signal.action == "HOLD":
        raise ValueError("HOLD signals cannot be converted to orders")

    # Convert action from strategy signal to order side with proper typing
    side: Literal["buy", "sell"]
    if signal.action == "BUY":
        side = "buy"
    elif signal.action == "SELL":
        side = "sell"
    else:
        raise ValueError(f"Invalid signal action: {signal.action}")

    # Calculate quantity from target allocation and portfolio value
    # target_allocation is Percentage (0.0 to 1.0), portfolio_value is Decimal
    allocation_value = portfolio_value * signal.target_allocation.value

    # For now, use allocation_value as quantity (dollar amount)
    # In a real implementation, this might need current stock price to convert to shares
    quantity = allocation_value

    # Validate minimum quantity
    if quantity <= Decimal("0"):
        raise ValueError(f"Calculated quantity must be positive, got: {quantity}")

    # Validate limit price requirement
    if order_type == "limit" and limit_price is None:
        raise ValueError("Limit price required for limit orders")

    # Create ValidatedOrderDTO
    return ValidatedOrderDTO(
        symbol=signal.symbol.value,
        side=side,
        quantity=quantity,
        order_type=order_type,
        time_in_force=time_in_force,
        limit_price=limit_price,
        client_order_id=client_order_id,
        # Derived validation fields
        estimated_value=allocation_value,
        is_fractional=False,  # For now, assume whole dollar amounts
        normalized_quantity=quantity,
        risk_score=Decimal("1.0") - signal.confidence.value,  # Higher confidence = lower risk
        validation_timestamp=datetime.now(UTC),
    )
