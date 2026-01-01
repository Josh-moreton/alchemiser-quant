"""Business Unit: shared; Status: current.

Protocol definitions for dependency inversion.

This package contains protocol (interface) definitions that allow domain logic
to remain independent of infrastructure implementations. Protocols use structural
subtyping (PEP 544) to define contracts without requiring explicit inheritance.
"""

from the_alchemiser.shared.protocols.asset_metadata import (
    AssetClass,
    AssetMetadataProvider,
)

__all__ = [
    "AssetClass",
    "AssetMetadataProvider",
]
