"""
KLM Strategy Workers Package

This package contains all individual strategy variants for the KLM ensemble system.
Each variant is implemented as a separate module for better maintainability.
"""

from typing import Any

from .base_klm_variant import BaseKLMVariant
from .variant_410_38 import KlmVariant41038
from .variant_506_38 import KlmVariant50638
from .variant_520_22 import KlmVariant52022
from .variant_530_18 import KlmVariant53018
from .variant_830_21 import KlmVariant83021
from .variant_1200_28 import KlmVariant120028
from .variant_1280_26 import KlmVariant128026
from .variant_nova import KLMVariantNova

__all__ = [
    "BaseKLMVariant",
    "KlmVariant50638",
    "KlmVariant128026",
    "KlmVariant120028",
    "KlmVariant52022",
    "KlmVariant53018",
    "KlmVariant41038",
    "KLMVariantNova",
    "KlmVariant83021",
]
