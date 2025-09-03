#!/usr/bin/env python3
"""Business Unit: execution | Status: current.."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    symbol: str = Field(description="Trading symbol (normalized to uppercase)")
    action: TradingAction = Field(description="Trading action (BUY or SELL)")
    quantity: Decimal = Field(description="Quantity to trade (must be positive)")
    estimated_price: Decimal = Field(description="Estimated execution price (must be positive)")
    reasoning: str = Field(description="Reasoning behind the trading decision")

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        if not v or not v.strip():  # pragma: no cover - defensive
            raise ValueError("Symbol cannot be empty")
        symbol = v.strip().upper()
        if not symbol.isalnum():
            raise ValueError("Symbol must be alphanumeric")
        return symbol

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Quantity must be greater than 0")
        return v

    @field_validator("estimated_price")
    @classmethod
    def validate_estimated_price(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Estimated price must be greater than 0")
        return v

    # NOTE: LimitOrderResultDTO moved to interfaces/schemas/orders.py to avoid duplicate
    # definitions and provide richer success/failure semantics. This placeholder comment
    # preserves historical context for the refactor.


class WebSocketResult(BaseModel):
    """Outcome of WebSocket operations (status, message, completed orders)."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    status: WebSocketStatus = Field(description="WebSocket operation status")
    message: str = Field(description="Status or error message")
    orders_completed: list[str] = Field(
        default_factory=list, description="List of completed order IDs"
    )


class Quote(BaseModel):
    """Real-time quote data with positive bid/ask prices and sizes."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    bid_price: Decimal = Field(description="Bid price (must be > 0)")
    ask_price: Decimal = Field(description="Ask price (must be > 0)")
    bid_size: Decimal = Field(description="Bid size (must be > 0)")
    ask_size: Decimal = Field(description="Ask size (must be > 0)")
    timestamp: str = Field(description="Quote timestamp in ISO format")

    @field_validator("bid_price", "ask_price")
    @classmethod
    def validate_prices(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Price must be greater than 0")
        return v

    @field_validator("bid_size", "ask_size")
    @classmethod
    def validate_sizes(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Size must be greater than 0")
        return v


class LambdaEvent(BaseModel):
    """AWS Lambda event configuration parameters."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    mode: str | None = Field(default=None, description="Execution mode")
    trading_mode: str | None = Field(default=None, description="Trading mode (paper/live)")
    ignore_market_hours: bool | None = Field(
        default=None, description="Whether to ignore market hours"
    )
    arguments: list[str] | None = Field(
        default=None, description="Additional command line arguments"
    )


class OrderHistory(BaseModel):
    """Historical order data with metadata for analysis/reporting."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    orders: list[OrderDetails] = Field(description="List of historical orders")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata about the order history"
    )


__all__ = [
    # Primary DTO exports (new naming policy)
    "ExecutionResult",
    "LambdaEvent",
    "OrderHistory",
    "Quote",
    "TradingPlan",
    "WebSocketResult",
    # Backward compatibility aliases
    "ExecutionResultDTO",
    "LambdaEventDTO",
    "OrderHistoryDTO",
    "QuoteDTO",
    "TradingPlanDTO",
    "WebSocketResultDTO",
]


# Backward compatibility aliases - will be removed in future version
ExecutionResultDTO = ExecutionResult
LambdaEventDTO = LambdaEvent
OrderHistoryDTO = OrderHistory
QuoteDTO = Quote
TradingPlanDTO = TradingPlan
WebSocketResultDTO = WebSocketResult
