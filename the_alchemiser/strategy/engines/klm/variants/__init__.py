"""Business Unit: strategy | Status: current

KLM Strategy Variants.

Collection of KLM strategy variants for ensemble evaluation.
"""

from __future__ import annotations

from .variant_520_22 import KLMVariant520_22
from .variant_530_18 import KLMVariant530_18
from .variant_410_38 import KlmVariant41038
from .variant_506_38 import KlmVariant50638
from .variant_830_21 import KlmVariant83021
from .variant_1200_28 import KlmVariant120028
from .variant_1280_26 import KlmVariant128026
from .variant_nova import KLMVariantNova

__all__ = [
    "KLMVariant520_22",
    "KLMVariant530_18", 
    "KlmVariant41038",
    "KlmVariant50638",
    "KlmVariant83021",
    "KlmVariant120028",
    "KlmVariant128026",
    "KLMVariantNova",
]
