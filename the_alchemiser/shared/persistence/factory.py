#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Persistence Handler Factory for Trading System.

This module provides a factory to create the appropriate persistence handler
based on trading mode (paper vs live) and configuration.
"""

from __future__ import annotations

import logging
import os

from the_alchemiser.shared.persistence.local_handler import LocalFileHandler
from the_alchemiser.shared.protocols.persistence import PersistenceHandler


def create_persistence_handler(*, paper_trading: bool = True) -> PersistenceHandler:
    """Create appropriate persistence handler based on trading mode.

    Args:
        paper_trading: Whether this is for paper trading mode

    Returns:
        PersistenceHandler: S3Handler for live trading, LocalFileHandler for paper trading

    """
    if paper_trading:
        # Paper trading - use local file storage to avoid S3 dependency
        logging.info("Using local file storage for paper trading mode")
        return LocalFileHandler()
    # Live trading - use S3 storage
    logging.info("Using S3 storage for live trading mode")
    from the_alchemiser.shared.persistence.s3_handler import S3Handler

    return S3Handler()


def detect_paper_trading_from_environment() -> bool:
    """Detect if we're in paper trading mode based on environment.

    Returns:
        True if paper trading mode is detected, False otherwise

    """
    # Check for explicit paper trading environment variable
    if os.getenv("ALPACA_PAPER_TRADING", "").lower() in ("true", "1", "yes"):
        return True

    # Check Alpaca endpoint to determine trading mode
    endpoint = os.getenv("ALPACA_ENDPOINT", "")
    if endpoint and "paper" in endpoint.lower():
        return True

    # Default to paper trading for safety if we can't determine mode
    if not endpoint:
        logging.warning("No ALPACA_ENDPOINT found, defaulting to paper trading mode")
        return True

    return False


def get_default_persistence_handler() -> PersistenceHandler:
    """Get persistence handler using environment-based detection.

    Returns:
        PersistenceHandler: Appropriate handler based on detected trading mode

    """
    paper_trading = detect_paper_trading_from_environment()
    return create_persistence_handler(paper_trading=paper_trading)
