#!/usr/bin/env python3
"""Business Unit: orchestration | Status: current.

Command-line argument parser for The Alchemiser Trading System.

Provides centralized argument parsing for the main application entry point.
"""

from __future__ import annotations

import argparse

from the_alchemiser.shared.constants import APPLICATION_NAME


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the command line argument parser.

    Returns:
        Configured ArgumentParser instance

    """
    parser = argparse.ArgumentParser(
        description=f"{APPLICATION_NAME} - Multi-Strategy Quantitative Trading System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  alchemiser trade                     # Execute trading (mode determined by stage)
        """,
    )

    parser.add_argument(
        "mode",
        choices=["trade"],
        help="Operation mode: trade (execute trading with integrated signal analysis)",
    )

    # Remove --live flag - trading mode now determined by deployment stage
    # parser.add_argument(
    #     "--live",
    #     action="store_true",
    #     help="Execute live trading (default: paper trading)",
    # )

    parser.add_argument(
        "--show-tracking",
        action="store_true",
        help="Display strategy performance tracking after trade execution",
    )

    parser.add_argument(
        "--export-tracking-json",
        type=str,
        help="Export tracking summary to JSON file after trade execution",
    )

    return parser
