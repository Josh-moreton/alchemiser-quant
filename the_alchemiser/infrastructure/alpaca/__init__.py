"""Business Unit: utilities; Status: current.

Alpaca infrastructure adapters package.

This package contains all Alpaca-specific infrastructure implementations,
properly separated from application and domain layers.
"""

from __future__ import annotations

__all__ = [
    "AlpacaAssetMetadataProvider",
    "AlpacaGateway",
]

# Defer imports to avoid circular dependencies
def __getattr__(name: str) -> object:
    if name == "AlpacaGateway":
        from .alpaca_gateway import AlpacaGateway
        return AlpacaGateway
    if name == "AlpacaAssetMetadataProvider":
        from .asset_metadata_adapter import AlpacaAssetMetadataProvider
        return AlpacaAssetMetadataProvider
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")