"""Business Unit: root | Status: current.

The Alchemiser Quantitative Trading System.

A multi-strategy quantitative trading system deployed as AWS Lambda microservices.
Integrates with Alpaca for trade execution and uses EventBridge for event routing.

Architecture:
    Per-strategy books -- each strategy worker independently rebalances and enqueues trades:
    - strategy_v2: Signal generation + per-strategy rebalance (scheduled trigger)
    - execution_v2: Trade execution (SQS → TradeExecuted)
    - notifications_v2: Email notifications (TradeExecuted/WorkflowFailed → SNS)

Shared Module:
    shared: Cross-cutting concerns (config, schemas, adapters, logging, errors)

"""

from __future__ import annotations

__all__: list[str] = []
