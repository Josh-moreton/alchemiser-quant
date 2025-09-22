"""Business Unit: strategy | Status: current.

KLM Strategy Variants.

Single variant implementation focused on the original CLJ specification.
"""

from __future__ import annotations

from .variant_original import KlmVariantOriginal

__all__ = [
    "KlmVariantOriginal",
]
