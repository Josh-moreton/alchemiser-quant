#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Base DTO primitives used across result-oriented response models.

Provides a single place for the ubiquitous success / error pattern to
eliminate duplication and ensure uniform semantics across facade methods.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class Result(BaseModel):
    """Common base for DTOs that expose success/error outcome fields.

    This class provides a standardized pattern for returning operation results
    across the trading system. All service methods that can succeed or fail
    should return a subclass of Result to maintain consistent error handling.

    Attributes:
        success: True if the operation succeeded, False otherwise.
        error: Error message when success=False. Should be None when success=True,
               though this is not enforced to allow flexibility in edge cases.

    Example:
        >>> # Success case
        >>> result = Result(success=True)
        >>> assert result.is_success
        >>> assert result.error is None

        >>> # Error case
        >>> result = Result(success=False, error="Operation failed")
        >>> assert not result.is_success
        >>> assert result.error == "Operation failed"

    Note:
        - Immutable (frozen=True) - cannot be modified after creation
        - Strict validation (strict=True) - type coercion disabled
        - Widely subclassed (23+ subclasses across the system)
    """

    model_config = ConfigDict(strict=True, frozen=True, validate_assignment=True)

    success: bool
    error: str | None = None

    @property
    def is_success(self) -> bool:
        """Check if the result represents a successful operation.

        Convenience property that mirrors the success field for readability.

        Returns:
            bool: True if operation succeeded, False otherwise.
        """
        return self.success


# Backward compatibility alias - to be removed in v3.0.0
ResultDTO = Result
