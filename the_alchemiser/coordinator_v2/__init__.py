"""Business Unit: coordinator_v2 | Status: current.

Strategy Coordinator Lambda module for multi-node signal aggregation.

This module orchestrates parallel execution of strategy files by:
1. Creating aggregation sessions in DynamoDB
2. Invoking Strategy Lambda once per DSL file (async)
3. Tracking session state for the Aggregator

The Coordinator enables horizontal scaling of strategy execution by
leveraging AWS Lambda's natural concurrency model.
"""

from __future__ import annotations

__all__: list[str] = []
