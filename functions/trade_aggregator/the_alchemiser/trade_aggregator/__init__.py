"""Business Unit: trade_aggregator | Status: current.

Trade Aggregator microservice for aggregating per-trade execution results.

Collects TradeExecuted events from parallel execution invocations and
emits a single AllTradesCompleted event when all trades in a run finish.
This eliminates race conditions in the notifications flow.

Architecture:
    - Trigger: EventBridge rule on TradeExecuted events
    - State: Reuses execution-runs DynamoDB table
    - Output: Single AllTradesCompleted event per run
    - Consumer: Notifications Lambda (one invocation per run)
"""

from the_alchemiser.trade_aggregator.lambda_handler import lambda_handler

__all__ = ["lambda_handler"]
