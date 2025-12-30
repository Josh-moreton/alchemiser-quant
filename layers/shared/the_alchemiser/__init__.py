"""Business Unit: root | Status: current.

The Alchemiser Quantitative Trading System.

A multi-strategy quantitative trading system deployed as AWS Lambda microservices.
Integrates with Alpaca for trade execution and uses EventBridge for event routing.

Architecture:
    4 independent Lambda functions connected via EventBridge/SQS:
    - strategy_v2: Signal generation (scheduled trigger)
    - portfolio_v2: Rebalance planning (SignalGenerated → RebalancePlanned)
    - execution_v2: Trade execution (RebalancePlanned → TradeExecuted)
    - notifications_v2: Email notifications (TradeExecuted/WorkflowFailed → SNS)

Shared Module:
    shared: Cross-cutting concerns (config, schemas, adapters, logging, errors)

"""

from __future__ import annotations

__all__: list[str] = []
