#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Trade Ledger Factory for Trading System.

This module provides a factory to create the appropriate trade ledger implementation
based on trading mode (paper vs live) and configuration.
"""

from __future__ import annotations

import logging
import os

from ..protocols.trade_ledger import TradeLedger

logger = logging.getLogger(__name__)


def create_trade_ledger(
    *, paper_trading: bool = True, account_id: str | None = None
) -> TradeLedger:
    """Create appropriate trade ledger based on trading mode.

    Args:
        paper_trading: Whether this is for paper trading mode
        account_id: Account identifier for partitioning (used by S3 implementation)

    Returns:
        TradeLedger: S3TradeLedger for live trading, LocalTradeLedger for paper trading

    """
    if paper_trading:
        # Paper trading - use local file storage to avoid S3 dependency
        logger.info("Using local file trade ledger for paper trading mode")
        from ..persistence.local_trade_ledger import LocalTradeLedger

        return LocalTradeLedger()

    # Live trading - use S3 storage
    logger.info("Using S3 trade ledger for live trading mode")
    from ..persistence.s3_trade_ledger import S3TradeLedger

    bucket = os.getenv("S3_BUCKET_NAME")
    if not bucket:
        raise ValueError(
            "S3_BUCKET_NAME environment variable is required for live trading"
        )

    return S3TradeLedger(bucket=bucket, account_id=account_id)


def detect_paper_trading_from_environment() -> bool:
    """Detect if we're in paper trading mode based on environment.

    Returns:
        True if paper trading mode is detected, False otherwise

    """
    # Check for explicit paper trading environment variable
    if os.getenv("ALPACA_PAPER_TRADING", "").lower() in ("true", "1", "yes"):
        return True

    # Check Alpaca endpoint to determine trading mode (support both styles)
    endpoint = os.getenv("ALPACA_ENDPOINT", "") or os.getenv("ALPACA__ENDPOINT", "")
    if endpoint and "paper" in endpoint.lower():
        return True

    # Default to paper trading for safety if we can't determine mode
    if not endpoint:
        logger.warning("No ALPACA_ENDPOINT found, defaulting to paper trading mode")
        return True

    return False


def get_default_trade_ledger(account_id: str | None = None) -> TradeLedger:
    """Get trade ledger using environment-based detection.

    Args:
        account_id: Account identifier for partitioning

    Returns:
        TradeLedger: Appropriate implementation based on detected trading mode

    """
    paper_trading = detect_paper_trading_from_environment()
    return create_trade_ledger(paper_trading=paper_trading, account_id=account_id)
