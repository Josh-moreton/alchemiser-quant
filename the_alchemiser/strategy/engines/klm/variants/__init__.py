"""Business Unit: strategy | Status: current

KLM Strategy Variants.

Consolidated strategy variants for different market conditions.
"""

from __future__ import annotations

from ..base_variant import BaseKLMVariant
from .original import KlmVariant52022
from .scale_in import KlmVariant53018

# For backward compatibility, we need to import the other variants from the old location
# These will be gradually migrated or consolidated
from ...klm_workers.variant_410_38 import KlmVariant41038
from ...klm_workers.variant_506_38 import KlmVariant50638
from ...klm_workers.variant_830_21 import KlmVariant83021
from ...klm_workers.variant_1200_28 import KlmVariant120028
from ...klm_workers.variant_1280_26 import KlmVariant128026
from ...klm_workers.variant_nova import KLMVariantNova

__all__ = [
    "BaseKLMVariant",
    "KlmVariant41038",
    "KlmVariant50638", 
    "KlmVariant52022",
    "KlmVariant53018",
    "KlmVariant83021",
    "KlmVariant120028",
    "KlmVariant128026",
    "KLMVariantNova",
]