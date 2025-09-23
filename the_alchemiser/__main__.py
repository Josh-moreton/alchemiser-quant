#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Minimal module entry point for The Alchemiser Trading System.

Provides convenience access via `python -m the_alchemiser` for local runs.
Only supports the basic trade functionality with minimal configuration.
"""

from __future__ import annotations

import sys

from the_alchemiser.main import main


def run(config_path: str | None = None) -> None:
    """Run The Alchemiser Trading System programmatically.

    Args:
        config_path: Optional path to configuration file (not currently used)

    """
    # For the module entry point, we always run in trade mode
    # This is the simplest interface for local development/testing
    result = main(["trade"])

    # Handle both TradeRunResultDTO and boolean return types
    success = getattr(result, "success", False) if hasattr(result, "success") else bool(result)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    # Simple argument parsing - only support optional --config flag
    config_path = None
    if len(sys.argv) > 1:
        if sys.argv[1] == "--config" and len(sys.argv) > 2:
            config_path = sys.argv[2]
        elif sys.argv[1] in ["--help", "-h"]:
            print("Usage: python -m the_alchemiser [--config CONFIG_PATH]")
            print("       python -m the_alchemiser --help")
            print()
            print("Runs The Alchemiser Trading System in trade mode.")
            print("For more advanced usage, use the programmatic API or Lambda handler.")
            sys.exit(0)
        else:
            print(f"Unknown argument: {sys.argv[1]}")
            print("Use --help for usage information.")
            sys.exit(1)

    run(config_path)
