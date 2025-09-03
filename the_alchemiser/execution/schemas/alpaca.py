#!/usr/bin/env python3
"""Business Unit: execution | Status: current..)")
    order_type: str = Field(description="Order type (market, limit, etc.)")
    type: str = Field(description="Alias for order_type")
    side: Literal["buy", "sell"] = Field(description="Order side")
    time_in_force: str = Field(description="Time in force (day, gtc, etc.)")

    # Order status and timing
    status: str = Field(description="Order status")
    created_at: datetime = Field(description="Order creation timestamp")
    updated_at: datetime = Field(description="Order last update timestamp")
    submitted_at: datetime | None = Field(default=None, description="Order submission timestamp")
    filled_at: datetime | None = Field(default=None, description="Order fill timestamp")
    expired_at: datetime | None = Field(default=None, description="Order expiration timestamp")
    canceled_at: datetime | None = Field(default=None, description="Order cancellation timestamp")

    @field_validator("qty", "filled_qty", "notional", "filled_avg_price")
    @classmethod
    def validate_financial_values(cls, v: Decimal | None) -> Decimal | None:
        """Validate financial values are non-negative when provided."""
        if v is not None and v < 0:
            raise ValueError("Financial values cannot be negative")
        return v

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """Validate and normalize symbol."""
        if not v or not v.strip():
            raise ValueError("Symbol cannot be empty")
        return v.strip().upper()


class AlpacaErrorDTO(BaseModel):
    """DTO for Alpaca API error responses.

    Provides structured error information with consistent format
    for error handling and debugging.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    code: int = Field(description="HTTP error code")
    message: str = Field(description="Error message")
    details: dict[str, Any] | None = Field(default=None, description="Additional error details")
    request_id: str | None = Field(default=None, description="Request ID for tracking")

    @field_validator("code")
    @classmethod
    def validate_error_code(cls, v: int) -> int:
        """Validate error code is a valid HTTP status code."""
        if not (100 <= v <= 599):
            raise ValueError("Error code must be a valid HTTP status code")
        return v

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        """Validate error message is not empty."""
        if not v or not v.strip():
            raise ValueError("Error message cannot be empty")
        return v.strip()
