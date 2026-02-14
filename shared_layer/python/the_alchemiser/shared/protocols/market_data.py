"""Business Unit: shared | Status: current.

Market data Protocols for SDK interoperability.

Defines lightweight Protocols to interact with broker SDK "bar" models
without importing SDK types directly. This keeps business logic typed and
independent from vendor-specific classes.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ModelDumpable(Protocol):
    """Protocol for SDK/Pydantic models that support `model_dump()` serialization."""

    def model_dump(self) -> dict[str, Any]:
        """Return a dict representation of the model."""
        ...


@runtime_checkable
class BarsIterable(Protocol, Iterable[ModelDumpable]):
    """Protocol representing an iterable collection of bar-like models."""

    # Iterable contract inherited; no additional members required
    ...
