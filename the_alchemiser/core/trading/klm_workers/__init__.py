"""
KLM Strategy Workers Package

This package contains all individual strategy variants for the KLM ensemble system.
Each variant is implemented as a separate module for better maintainability.
"""

from .base_klm_variant import BaseKLMVariant
from .variant_410_38 import KLMVariant410_38
from .variant_506_38 import KLMVariant506_38
from .variant_520_22 import KLMVariant520_22
from .variant_530_18 import KLMVariant530_18
from .variant_830_21 import KLMVariant830_21
from .variant_1200_28 import KLMVariant1200_28
from .variant_1280_26 import KLMVariant1280_26
from .variant_nova import KLMVariantNova

__all__ = [
    "BaseKLMVariant",
    "KLMVariant506_38",
    "KLMVariant1280_26",
    "KLMVariant1200_28",
    "KLMVariant520_22",
    "KLMVariant530_18",
    "KLMVariant410_38",
    "KLMVariantNova",
    "KLMVariant830_21",
]
