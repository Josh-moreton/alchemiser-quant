#!/usr/bin/env python3
"""Business Unit: utilities; Status: current.

Order listing DTOs for The Alchemiser Trading System.

This module contains DTOs for order listing operations, including
open orders retrieval and order history.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from the_alchemiser.shared.schemas.base import Result


class EnrichedOrderView(BaseModel):
    """DTO for enriched order data with domain mapping."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    raw: dict[str, Any]
    domain: dict[str, Any]  # Domain order object serialized
    summary: dict[str, Any]  # Order summary


class OpenOrdersView(Result):
    """DTO for open orders list response."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    orders: list[EnrichedOrderView]
    symbol_filter: str | None = None


class EnrichedPositionView(BaseModel):
    """DTO for enriched position data with domain mapping."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    raw: dict[str, Any]
    summary: dict[str, Any]  # Position summary


class EnrichedPositionsView(Result):
    """DTO for enriched positions list response."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    positions: list[EnrichedPositionView]


# Backward compatibility aliases - will be removed in future version
EnrichedOrderDTO = EnrichedOrderView
OpenOrdersDTO = OpenOrdersView
EnrichedPositionDTO = EnrichedPositionView
EnrichedPositionsDTO = EnrichedPositionsView
