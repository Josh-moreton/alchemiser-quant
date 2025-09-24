#!/usr/bin/env python3
"""Business Unit: utilities; Status: current.

Base DTO primitives used across result-oriented response models.

Provides a single place for the ubiquitous success / error pattern to
eliminate duplication and ensure uniform semantics across facade methods.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class Result(BaseModel):
    """Common base for DTOs that expose success/error outcome fields."""

    model_config = ConfigDict(strict=True, frozen=True, validate_assignment=True)

    success: bool
    error: str | None = None

    @property
    def is_success(self) -> bool:  # Convenience mirror
        """Check if the result represents a successful operation."""
        return self.success



