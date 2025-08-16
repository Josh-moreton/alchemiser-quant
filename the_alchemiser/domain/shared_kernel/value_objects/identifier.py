from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Self, TypeVar
from uuid import UUID, uuid4

T_contra = TypeVar("T_contra", contravariant=True)


@dataclass(frozen=True)
class Identifier(Generic[T_contra]):
    """Base class for typed identifiers.

    Strongly-typed identifiers prevent accidental cross-entity ID usage.
    """

    value: UUID

    @classmethod
    def generate(cls) -> Self:
        return cls(value=uuid4())

    @classmethod
    def from_string(cls, value: str) -> Self:
        return cls(value=UUID(value))
