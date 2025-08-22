#!/usr/bin/env python3
"""
Order listing DTOs for The Alchemiser Trading System.

This module contains DTOs for order listing operations, including
open orders retrieval and order history.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from the_alchemiser.interfaces.schemas.orders import OrderExecutionResultDTO


class EnrichedOrderDTO(BaseModel):
    """
    DTO for enriched order data with domain mapping.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    raw: dict[str, Any]
    domain: dict[str, Any]  # Domain order object serialized
    summary: dict[str, Any]  # Order summary


class OpenOrdersDTO(BaseModel):
    """
    DTO for open orders list response.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    success: bool
    orders: list[EnrichedOrderDTO]
    symbol_filter: str | None = None
    error: str | None = None


class EnrichedPositionDTO(BaseModel):
    """
    DTO for enriched position data with domain mapping.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    raw: dict[str, Any]
    summary: dict[str, Any]  # Position summary


class EnrichedPositionsDTO(BaseModel):
    """
    DTO for enriched positions list response.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    success: bool
    positions: list[EnrichedPositionDTO]
    error: str | None = None