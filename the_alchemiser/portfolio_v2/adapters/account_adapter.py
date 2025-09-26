#!/usr/bin/env python3
"""Business Unit: portfolio | Status: current.

Account data adapter for portfolio_v2 module.

Provides DTO-based adapters for converting raw account data from brokers
into strongly-typed DTOs, eliminating raw dict usage in portfolio logic.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from the_alchemiser.shared.logging.logging_utils import get_logger

logger = get_logger(__name__)


class AccountInfoDTO(BaseModel):
    """DTO for account information from broker APIs."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    cash: Decimal = Field(..., ge=0, description="Available cash balance")
    buying_power: Decimal = Field(..., ge=0, description="Available buying power")
    portfolio_value: Decimal = Field(..., ge=0, description="Total portfolio value")
    equity: Decimal | None = Field(default=None, ge=0, description="Account equity")
    account_id: str | None = Field(default=None, description="Account identifier")

    @field_validator("cash", "buying_power", "portfolio_value", "equity", mode="before")
    @classmethod
    def convert_to_decimal(cls, v: Any) -> Decimal | None:
        """Convert numeric values to Decimal."""
        if v is None:
            return None
        if isinstance(v, Decimal):
            return v
        try:
            return Decimal(str(v))
        except (ValueError, TypeError):
            return Decimal("0")


class PositionDTO(BaseModel):
    """DTO for position data from broker APIs."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    symbol: str = Field(..., min_length=1, max_length=10, description="Trading symbol")
    quantity: Decimal = Field(..., description="Position quantity (shares)")
    market_value: Decimal = Field(..., description="Current market value")
    avg_entry_price: Decimal | None = Field(default=None, ge=0, description="Average entry price")
    unrealized_pl: Decimal | None = Field(default=None, description="Unrealized P&L")

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        """Normalize symbol to uppercase."""
        return v.strip().upper()

    @field_validator("quantity", "market_value", "avg_entry_price", "unrealized_pl", mode="before")
    @classmethod
    def convert_to_decimal(cls, v: Any) -> Decimal | None:
        """Convert numeric values to Decimal."""
        if v is None:
            return None
        if isinstance(v, Decimal):
            return v
        try:
            return Decimal(str(v))
        except (ValueError, TypeError):
            return Decimal("0")


def adapt_account_info(raw_account_data: dict[str, Any] | object) -> AccountInfoDTO:
    """Adapt raw account data to AccountInfoDTO.

    Args:
        raw_account_data: Raw account data from broker API (dict or object)

    Returns:
        AccountInfoDTO with normalized account information

    Raises:
        ValueError: If required fields are missing or invalid

    """
    try:
        if isinstance(raw_account_data, dict):
            return AccountInfoDTO(
                cash=raw_account_data.get("cash", 0),
                buying_power=raw_account_data.get("buying_power", 0),
                portfolio_value=raw_account_data.get("portfolio_value", 0),
                equity=raw_account_data.get("equity"),
                account_id=raw_account_data.get("account_id"),
            )
        # Handle object with attributes
        return AccountInfoDTO(
            cash=getattr(raw_account_data, "cash", 0),
            buying_power=getattr(raw_account_data, "buying_power", 0),
            portfolio_value=getattr(raw_account_data, "portfolio_value", 0),
            equity=getattr(raw_account_data, "equity", None),
            account_id=getattr(raw_account_data, "account_id", None),
        )
    except Exception as e:
        logger.error(f"Failed to adapt account info: {e}")
        # Return minimal valid DTO
        return AccountInfoDTO(
            cash=Decimal("0"),
            buying_power=Decimal("0"),
            portfolio_value=Decimal("0"),
        )


def adapt_positions(raw_positions: list[Any]) -> list[PositionDTO]:
    """Adapt raw position data to list of PositionDTOs.

    Args:
        raw_positions: Raw position data from broker API

    Returns:
        List of PositionDTO objects

    """
    positions = []

    for raw_position in raw_positions:
        try:
            if isinstance(raw_position, dict):
                position = PositionDTO(
                    symbol=raw_position.get("symbol", ""),
                    quantity=raw_position.get("qty", 0),
                    market_value=raw_position.get("market_value", 0),
                    avg_entry_price=raw_position.get("avg_entry_price"),
                    unrealized_pl=raw_position.get("unrealized_pl"),
                )
            else:
                # Handle object with attributes
                position = PositionDTO(
                    symbol=getattr(raw_position, "symbol", ""),
                    quantity=getattr(raw_position, "qty", 0),
                    market_value=getattr(raw_position, "market_value", 0),
                    avg_entry_price=getattr(raw_position, "avg_entry_price", None),
                    unrealized_pl=getattr(raw_position, "unrealized_pl", None),
                )
            positions.append(position)
        except Exception as e:
            logger.warning(f"Failed to adapt position {raw_position}: {e}")
            continue

    return positions


def generate_account_snapshot_id(account_info: AccountInfoDTO, positions: list[PositionDTO]) -> str:
    """Generate deterministic account snapshot ID.

    Args:
        account_info: Account information DTO
        positions: List of position DTOs

    Returns:
        Deterministic snapshot ID for correlation tracking

    """
    import hashlib

    try:
        # Create normalized snapshot data
        snapshot_data = {
            "account": {
                "cash": str(account_info.cash),
                "buying_power": str(account_info.buying_power),
                "portfolio_value": str(account_info.portfolio_value),
            },
            "positions": sorted(
                [
                    {
                        "symbol": pos.symbol,
                        "quantity": str(pos.quantity),
                        "market_value": str(pos.market_value),
                    }
                    for pos in positions
                ],
                key=lambda x: x["symbol"],
            ),
        }

        # Generate content hash only (no timestamp for deterministic behavior)
        import json

        content = json.dumps(snapshot_data, sort_keys=True, separators=(",", ":"))
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

        # Return deterministic snapshot ID based only on content
        return f"account_snapshot_{content_hash}"

    except Exception as e:
        logger.error(f"Failed to generate account snapshot ID: {e}")
        # Return content-based fallback hash
        fallback_data = f"{account_info.portfolio_value}_{len(positions)}"
        fallback_hash = hashlib.sha256(fallback_data.encode()).hexdigest()[:16]
        return f"account_fallback_{fallback_hash}"
