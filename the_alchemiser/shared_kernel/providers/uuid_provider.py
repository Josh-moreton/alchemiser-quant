"""Business Unit: utilities; Status: current.

Deterministic UUID provider for smoke validation.

Provides predictable UUIDs to ensure deterministic behavior during
smoke validation and testing scenarios.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID, uuid4


class UUIDProviderPort(Protocol):
    """Protocol for UUID providers."""

    def generate(self) -> UUID:
        """Generate a new UUID."""
        ...


class DeterministicUUIDProvider(UUIDProviderPort):
    """UUID provider that returns predictable UUIDs.

    Useful for smoke validation where deterministic behavior is required.
    """

    def __init__(self, seed_base: str = "smoke-test") -> None:
        """Initialize with a seed base for predictable UUIDs.

        Args:
            seed_base: Base string for generating predictable UUIDs

        """
        self._seed_base = seed_base
        self._counter = 0

    def generate(self) -> UUID:
        """Generate a predictable UUID based on counter and seed."""
        self._counter += 1
        # Create a predictable UUID using a deterministic approach
        # We'll create UUIDs with a pattern that's recognizable but valid
        uuid_string = f"{self._seed_base}-{self._counter:04d}-4000-8000-000000000000"
        # Replace the seed base part with hex to make it a valid UUID
        hex_seed = self._seed_base.encode().hex()[:8]
        uuid_string = f"{hex_seed:0<8}-{self._counter:04d}-4000-8000-000000000000"
        return UUID(uuid_string)

    def reset(self) -> None:
        """Reset the counter for repeatable sequences."""
        self._counter = 0


class SystemUUIDProvider(UUIDProviderPort):
    """Real UUID provider for production use."""

    def generate(self) -> UUID:
        """Generate a random UUID."""
        return uuid4()
