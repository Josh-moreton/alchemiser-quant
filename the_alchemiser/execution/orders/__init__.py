"""Business Unit: execution | Status: current

Order management and handling layer.

This module contains all order-related functionality including validation,
progressive orders, limit orders, and asset-specific order handling.

Consolidated from 15 files to 8 files for better maintainability:
- order_types.py (consolidated type definitions)
- schemas.py (consolidated DTOs and domain objects)
- consolidated_validation.py (consolidated validation logic)
- service.py (enhanced with lifecycle adapter)
- asset_order_handler.py, progressive_order_utils.py, request_builder.py (unchanged)
"""

from __future__ import annotations

# Import from consolidated modules
from .order_types import *
from .schemas import *
from .consolidated_validation import *
from .service import *

# Keep existing specialized modules
from .asset_order_handler import *
from .progressive_order_utils import *
from .request_builder import *
