"""Business Unit: shared | Status: current.

Typed identifier base class for domain entities.

This module provides a generic base class for creating strongly-typed identifiers
that prevent accidental cross-entity ID usage at compile time.

Usage:
    Create a typed identifier for your entity:

    >>> class OrderIdentifier(Identifier[None]):
    ...     '''Strongly-typed identifier for Order entities.'''
    ...     pass

    Generate new identifier:
    >>> order_id = OrderIdentifier.generate()
    >>> str(order_id.value)  # '550e8400-e29b-41d4-a716-446655440000'

    Parse from string:
    >>> order_id = OrderIdentifier.from_string("550e8400-e29b-41d4-a716-446655440000")
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID, uuid4


@dataclass(frozen=True)
class Identifier[T_contra]:
    """Base class for typed identifiers.

    Strongly-typed identifiers prevent accidental cross-entity ID usage.
    """

    value: UUID

    def __str__(self) -> str:
        """Return string representation of the identifier for logging.

        Returns:
            String representation of the UUID value.

        """
        return str(self.value)

    @classmethod
    def generate(cls) -> Self:
        """Generate a new unique identifier with a random UUID.

        Uses UUID v4 (cryptographically strong random) for identifier generation.
        Note: This method is non-deterministic by design.

        Returns:
            New identifier instance with unique UUID value.

        Example:
            >>> order_id = OrderIdentifier.generate()
            >>> isinstance(order_id.value, UUID)
            True

        """
        return cls(value=uuid4())

    @classmethod
    def from_string(cls, value: str) -> Self:
        """Create an identifier from a string UUID representation.

        Args:
            value: UUID string in standard format (with or without hyphens,
                  case-insensitive). Example: '550e8400-e29b-41d4-a716-446655440000'

        Returns:
            Identifier instance with parsed UUID value.

        Raises:
            ValueError: If the string is not a valid UUID format.

        Example:
            >>> order_id = OrderIdentifier.from_string(
            ...     "550e8400-e29b-41d4-a716-446655440000"
            ... )
            >>> str(order_id.value)
            '550e8400-e29b-41d4-a716-446655440000'

        """
        return cls(value=UUID(value))
