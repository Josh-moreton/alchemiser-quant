"""Business Unit: shared | Status: current.

Typed identifier base class for domain entities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID, uuid4


@dataclass(frozen=True)
class Identifier[T_contra]:
    """Base class for typed identifiers.

    Strongly-typed identifiers prevent accidental cross-entity ID usage.
    The type parameter T_contra is contravariant, allowing type-safe
    identifier usage across different entity types.

    Attributes:
        value: The UUID value of the identifier.

    Examples:
        >>> # Generate a new identifier
        >>> order_id = Identifier[Order].generate()
        >>> # Create from a string
        >>> user_id = Identifier[User].from_string("550e8400-e29b-41d4-a716-446655440000")
        >>> # Access the UUID value
        >>> str(order_id.value)
        '...'

    """

    value: UUID

    @classmethod
    def generate(cls) -> Self:
        """Generate a new unique identifier with a random UUID.

        Returns:
            A new Identifier instance with a random UUID4 value.

        Examples:
            >>> identifier = Identifier[MyEntity].generate()
            >>> isinstance(identifier.value, UUID)
            True

        """
        return cls(value=uuid4())

    @classmethod
    def from_string(cls, value: str) -> Self:
        """Create an identifier from a string UUID representation.

        Args:
            value: A string representation of a UUID. Accepts various formats:
                   - Standard: "550e8400-e29b-41d4-a716-446655440000"
                   - No hyphens: "550e8400e29b41d4a716446655440000"
                   - With braces: "{550e8400-e29b-41d4-a716-446655440000}"
                   - URN format: "urn:uuid:550e8400-e29b-41d4-a716-446655440000"

        Returns:
            A new Identifier instance with the parsed UUID value.

        Raises:
            ValueError: If the string is not a valid UUID format.

        Examples:
            >>> identifier = Identifier[MyEntity].from_string("550e8400-e29b-41d4-a716-446655440000")
            >>> str(identifier.value)
            '550e8400-e29b-41d4-a716-446655440000'

        """
        try:
            return cls(value=UUID(value))
        except (ValueError, AttributeError, TypeError) as e:
            raise ValueError(f"Invalid UUID string: {value!r}") from e
