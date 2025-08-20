"""Shared numeric tolerances for tests.

Provides consistent tolerance values for floating-point comparisons across tests.
Use these instead of direct float equality checks to avoid precision issues.
"""

from decimal import Decimal

# Relative tolerance for float comparisons (1e-7 = 0.0000001)
DEFAULT_RTL = 1e-7

# Absolute tolerance for float comparisons (1e-12 = very small absolute difference)
DEFAULT_ATL = 1e-12

# Financial tolerance for Decimal comparisons (for money, percentages, allocations)
FINANCIAL_DECIMAL_TOLERANCE = Decimal("1e-8")

# Percentage tolerance for allocation comparisons (0.01% = 0.0001)
ALLOCATION_TOLERANCE = Decimal("0.0001")

# Confidence tolerance for ML/strategy confidence values (0.1% = 0.001)
CONFIDENCE_TOLERANCE = Decimal("0.001")
