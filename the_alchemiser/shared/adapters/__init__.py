#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Shared adapter implementations for cross-module asset metadata and broker operations.

Provides protocol-based adapters that bridge domain protocols with external broker APIs,
enabling dependency inversion and testability across modules.

Public API:
    AlpacaAssetMetadataAdapter: Alpaca-backed asset metadata provider implementation

Module boundaries:
    - Leaf module: No dependencies on strategy/portfolio/execution modules
    - Imports from shared only (protocols, brokers, value_objects)
    - Re-exports adapter implementations for consumption by business modules
    - Enforces dependency inversion via Protocol pattern
"""

from __future__ import annotations

from . import alpaca_asset_metadata_adapter
from .alpaca_asset_metadata_adapter import AlpacaAssetMetadataAdapter

__all__ = [
    "AlpacaAssetMetadataAdapter",
]

# Version for compatibility tracking
__version__ = "1.0.0"

# Clean up namespace to prevent module leakage
del alpaca_asset_metadata_adapter
