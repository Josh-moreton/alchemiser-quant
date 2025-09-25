"""Business Unit: portfolio | Status: current.

Portfolio state management and rebalancing logic.

Provides DTO-based adapters for converting raw broker data into strongly-typed
objects, eliminating raw dict usage in portfolio analysis logic.
"""

from .account_adapter import (
    AccountInfoDTO,
    PositionDTO,
    adapt_account_info,
    adapt_positions,
    generate_account_snapshot_id,
)

__all__ = [
    "AccountInfoDTO",
    "PositionDTO", 
    "adapt_account_info",
    "adapt_positions",
    "generate_account_snapshot_id",
]
