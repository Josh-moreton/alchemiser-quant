#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Main entry point for The Alchemiser Trading System.

This module is now a minimal stub. All trading execution happens via Lambda functions:
- Strategy Lambda: Signal generation (triggered by EventBridge Schedule)
- Portfolio Lambda: Rebalance planning (triggered by SignalGenerated events)
- Execution Lambda: Trade execution (triggered by RebalancePlanned events)
- Notifications Lambda: Email notifications (triggered by TradeExecuted/WorkflowFailed events)

For local development, deploy to dev environment and test there.
"""

from __future__ import annotations

__all__ = ["main"]

import sys

from the_alchemiser.shared.logging import (
    configure_application_logging,
    generate_request_id,
    get_logger,
    set_request_id,
)


def main(argv: list[str] | None = None) -> bool:
    """Serve as main entry point for The Alchemiser Trading System.

    NOTE: This is now a stub. Trading is executed via Lambda functions.
    Deploy to dev environment and test there.

    Args:
        argv: Command line arguments (unused)

    Returns:
        False - local execution is no longer supported

    """
    # Setup logging and request tracking
    configure_application_logging()
    request_id = generate_request_id()
    set_request_id(request_id)

    logger = get_logger(__name__)
    logger.info(
        "Local execution is no longer supported",
        request_id=request_id,
    )

    print(
        "\n"
        "╔════════════════════════════════════════════════════════════════════╗\n"
        "║  Local execution is no longer supported.                           ║\n"
        "║                                                                    ║\n"
        "║  The Alchemiser now runs as AWS Lambda functions:                  ║\n"
        "║    - Strategy Lambda: Generates trading signals                    ║\n"
        "║    - Portfolio Lambda: Creates rebalance plans                     ║\n"
        "║    - Execution Lambda: Executes trades via Alpaca                  ║\n"
        "║    - Notifications Lambda: Sends email notifications               ║\n"
        "║                                                                    ║\n"
        "║  To test, deploy to dev environment:                               ║\n"
        "║    make deploy                                                     ║\n"
        "║                                                                    ║\n"
        "║  Then trigger manually via AWS Console or CLI:                     ║\n"
        "║    aws lambda invoke --function-name the-alchemiser-strategy-dev   ║\n"
        "║                                                                    ║\n"
        "╚════════════════════════════════════════════════════════════════════╝\n"
    )

    return False


if __name__ == "__main__":
    result = main()
    sys.exit(0 if result else 1)
