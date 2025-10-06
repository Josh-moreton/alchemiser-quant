#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Module entry point for The Alchemiser Trading System.

Provides convenience access via `python -m the_alchemiser` for local runs.
Supports trade functionality and P&L analysis with minimal configuration.
"""

from __future__ import annotations

import sys

from the_alchemiser.main import main


def run() -> None:
    """Run The Alchemiser Trading System programmatically."""
    # Parse command line arguments
    result = main(sys.argv[1:]) if len(sys.argv) > 1 else main(["trade"])

    # Handle both TradeRunResult and boolean return types
    success = getattr(result, "success", False) if hasattr(result, "success") else bool(result)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    # Enhanced argument parsing with help
    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h"]:
        print("Usage: python -m the_alchemiser [COMMAND] [OPTIONS]")
        print()
        print("Commands:")
        print("  trade                Run trading system (default)")
        print("  pnl --weekly        Show weekly P&L report")
        print("  pnl --monthly       Show monthly P&L report")
        print("  pnl --period 1M     Show P&L for specific period (1W, 1M, 3M, 1A)")
        print()
        print("P&L Options:")
        print("  --periods N         Number of periods back to analyze (default: 1)")
        print("  --detailed          Show detailed daily breakdown")
        print()
        print("General Options:")
        print("  --config PATH       Use specific config file")
        print("  --help, -h          Show this help message")
        print()
        print("Examples:")
        print("  python -m the_alchemiser                    # Run trading")
        print("  python -m the_alchemiser pnl --weekly      # Weekly P&L report")
        print("  python -m the_alchemiser pnl --monthly --detailed  # Detailed monthly P&L")
        print("  python -m the_alchemiser pnl --period 3M   # 3-month P&L")
        sys.stdout.flush()  # Ensure help text is displayed even if output is buffered
        sys.exit(0)

    run()
