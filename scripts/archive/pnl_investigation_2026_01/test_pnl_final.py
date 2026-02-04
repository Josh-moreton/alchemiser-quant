#!/usr/bin/env python3
"""Test the final P&L calculation with deposit subtraction."""

import sys
sys.path.insert(0, "layers/shared")

from datetime import datetime

# Load environment
from dotenv import load_dotenv
load_dotenv()

from the_alchemiser.shared.services.pnl_service import PnLService


def main() -> None:
    """Test P&L calculation."""
    print("Testing P&L calculation with deposit subtraction...")
    print("=" * 60)

    svc = PnLService()

    # Get current month P&L
    now = datetime.now()
    pnl = svc.get_calendar_month_pnl(now.year, now.month)

    print(f"\nPeriod: {pnl.period}")
    print(f"Date Range: {pnl.start_date} to {pnl.end_date}")

    if pnl.start_value:
        print(f"Start Value: ${pnl.start_value:,.2f}")
    else:
        print("Start Value: N/A")

    if pnl.end_value:
        print(f"End Value: ${pnl.end_value:,.2f}")
    else:
        print("End Value: N/A")

    if pnl.total_pnl:
        print(f"Total P&L: ${pnl.total_pnl:,.2f}")
    else:
        print("Total P&L: N/A")

    if pnl.total_pnl_pct:
        print(f"Total P&L %: {pnl.total_pnl_pct:.2f}%")
    else:
        print("Total P&L %: N/A")

    print("\n" + "=" * 60)
    print("Expected for December 2025:")
    print("  - Cumulative P&L (profit_loss[-1]): ~$2,974")
    print("  - Deposits: $1,313.09 + $1,500 + $200 = $3,013.09")
    print("  - TRUE P&L = $2,974 - $3,013 = ~-$39 (actual trading LOSS)")


if __name__ == "__main__":
    main()
