from __future__ import annotations

"""Business Unit: shared | Status: current..
"""

#!/usr/bin/env python3
"""Business Unit: shared | Status: current..

    Returns None if data is None or invalid.
    """
    if data is None:
        return None

    try:
        return dict_to_portfolio_state_dto(data)
    except (KeyError, ValueError, TypeError):
        # Return minimal empty portfolio state for error cases
        return PortfolioStateDTO(
            total_portfolio_value=Decimal("0"),
            target_allocations={},
            current_allocations={},
            target_values={},
            current_values={},
            allocation_discrepancies={},
            largest_discrepancy=None,
            total_symbols=0,
            rebalance_needed=False,
        )
