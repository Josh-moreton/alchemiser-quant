"""Business Unit: strategy | Status: current

KLM Strategy Variants.

Collection of KLM strategy variants for ensemble evaluation.
"""

from __future__ import annotations

from .original import KLMVariant520_22
from .scale_in import KLMVariant530_18

__all__ = ["KLMVariant520_22", "KLMVariant530_18"]
