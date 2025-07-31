"""
KLM Strategy Variant 410/38 - "MonkeyBusiness Simons variant"

This variant is IDENTICAL to 506/38 except:
- L/S Rotator uses FTLS/KMLM/SSO/UUP (includes SSO)
- Everything else is exactly the same: FNGU switcher, UUP/FTLS/KMLM rotator

Since 506/38 was just corrected to use FNGU, 410/38 only differs in the SSO addition.
"""

from typing import Dict, Tuple, Union, Optional
import pandas as pd
from .variant_506_38 import KLMVariant506_38
from the_alchemiser.core.utils.common import ActionType


class KLMVariant410_38(KLMVariant506_38):
    """
    Variant 410/38 - MonkeyBusiness Simons variant
    
    Identical to 506/38 except L/S Rotator includes SSO in the candidate list.
    """
    
    def __init__(self):
        super().__init__()
        self.name = "410/38"
        self.description = "MonkeyBusiness Simons variant - Same as 506/38 + SSO in rotator"
    
    def _evaluate_long_short_rotator(self, indicators: Dict) -> Tuple[str, str, str]:
        """
        410/38 L/S Rotator - SAME as 506/38 but includes SSO
        
        CLJ: "Long/Short Rotator with FTLS KMLM SSO UUP"
        Adds SSO to the UUP/FTLS/KMLM candidates from 506/38
        """
        
        # 410/38 includes SSO in addition to the base set
        rotator_symbols = ['UUP', 'FTLS', 'KMLM', 'SSO']
        
        # Apply volatility filter (stdev-return window 6)
        volatility_candidates = []
        for symbol in rotator_symbols:
            if symbol in indicators and 'stdev_return_6' in indicators[symbol]:
                stdev = indicators[symbol]['stdev_return_6']
                volatility_candidates.append((symbol, stdev))
        
        if volatility_candidates:
            # Select bottom 1 by volatility (lowest standard deviation)
            bottom_1 = self.apply_select_bottom_filter(volatility_candidates, 1)
            selected_symbol = bottom_1[0][0]
            selected_stdev = bottom_1[0][1]
            
            result = (selected_symbol, ActionType.BUY.value, 
                     f"410/38 L/S Rotator: {selected_symbol} (lowest volatility: {selected_stdev:.3f})")
            
        else:
            # Fallback to KMLM since it's defensive
            result = ('KMLM', ActionType.BUY.value, "410/38 L/S Rotator: KMLM fallback")
        
        self.log_decision(result[0], result[1], result[2])
        return result
    
    def get_required_symbols(self) -> list:
        """
        410/38 Required symbols - same as 506/38 plus SSO
        """
        
        # Get base symbols from 506/38
        base_symbols = super().get_required_symbols()
        
        # Add SSO for the enhanced L/S Rotator
        additional_symbols = ['SSO']
        
        return list(set(base_symbols + additional_symbols))
