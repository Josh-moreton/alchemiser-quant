"""Business Unit: shared | Status: deprecated.

Time-in-force value object with validation.

.. deprecated:: 2.10.7
   TimeInForce is deprecated and will be removed in version 3.0.0.
   Use :class:`BrokerTimeInForce` from broker_enums.py instead, which provides
   superior functionality including from_string() and to_alpaca() conversion methods.

**DEPRECATION NOTICE:**
This module is DEPRECATED as of version 2.10.7 and will be removed in version 3.0.0.

**Reason for Deprecation:**
This module is currently UNUSED in production code. All production usage goes
through BrokerTimeInForce enum in broker_enums.py or Alpaca SDK directly.

**Issues Identified:**
1. DEAD CODE: No production code instantiates this class
2. VALIDATION REDUNDANCY: __post_init__ validation is unreachable due to Literal type
3. MISSING FEATURES: Lacks from_string() and to_alpaca() methods that BrokerTimeInForce has
4. ARCHITECTURAL DUPLICATION: BrokerTimeInForce provides superior functionality

**Migration Path:**
Use BrokerTimeInForce from broker_enums.py instead.
See FILE_REVIEW_time_in_force.md for full audit report.

**Usage (if not deprecated):**
    >>> from the_alchemiser.shared.types.time_in_force import TimeInForce
    >>> tif = TimeInForce(value="day")
    >>> tif.value
    'day'

**Valid Values:**
- "day": Day order (expires at market close)
- "gtc": Good-til-canceled (persists across sessions)
- "ioc": Immediate-or-cancel (fill immediately or cancel)
- "fok": Fill-or-kill (complete fill immediately or cancel)
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class TimeInForce:
    """Time-in-force specification with validation.
    
    .. deprecated:: 2.10.7
       TimeInForce is deprecated. Use BrokerTimeInForce from broker_enums.py instead.
       This class will be removed in version 3.0.0.
    
    **DEPRECATED**: This class is deprecated as of version 2.10.7 and will be removed
    in version 3.0.0. Use BrokerTimeInForce from broker_enums.py instead, which provides
    from_string() and to_alpaca() conversion methods.
    
    **WARNING**: This class has validation redundancy. The Literal type constraint
    at the type-checking level makes the __post_init__ runtime validation unreachable
    in normal use.
    
    Attributes:
        value: One of "day", "gtc", "ioc", or "fok"
    
    Raises:
        ValueError: If value is not one of the valid options (unreachable in practice
                    due to Literal type constraint)
        DeprecationWarning: On instantiation (always)
    
    Example:
        >>> # DEPRECATED: Use BrokerTimeInForce instead
        >>> tif = TimeInForce(value="gtc")  # Raises DeprecationWarning
        >>> tif.value
        'gtc'
    """

    value: Literal["day", "gtc", "ioc", "fok"]
    """Time-in-force value. Type checker enforces valid values."""

    def __post_init__(self) -> None:
        """Validate the time-in-force value after initialization.
        
        NOTE: This validation is technically unreachable in normal use because
        the Literal type constraint prevents invalid values at type-check time.
        This method exists only for runtime safety in case the type system is
        bypassed (e.g., via type: ignore or dynamic construction).
        
        Raises:
            ValueError: If value is not in the valid set
            DeprecationWarning: Always raised to warn about deprecation
        """
        # Emit deprecation warning
        warnings.warn(
            "TimeInForce is deprecated as of version 2.10.7 and will be removed in "
            "version 3.0.0. Use BrokerTimeInForce from broker_enums.py instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        
        # Validate (unreachable in normal use due to Literal constraint)
        valid_values = {"day", "gtc", "ioc", "fok"}
        if self.value not in valid_values:
            raise ValueError(f"TimeInForce must be one of {valid_values}")
