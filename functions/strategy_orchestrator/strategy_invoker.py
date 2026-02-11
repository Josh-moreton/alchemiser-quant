"""Business Unit: coordinator | Status: current.

Service for invoking Strategy Lambda functions asynchronously.

Uses Lambda's async invocation (InvocationType='Event') to fan out
strategy execution across multiple concurrent Lambda invocations.

Each strategy worker independently evaluates DSL, calculates rebalance,
and enqueues trades -- no aggregation step required.
"""

from __future__ import annotations

import json
from decimal import Decimal
from typing import TYPE_CHECKING

import boto3

from the_alchemiser.shared.logging import get_logger

if TYPE_CHECKING:
    from mypy_boto3_lambda import LambdaClient

logger = get_logger(__name__)


class StrategyInvoker:
    """Invokes Strategy Lambda functions asynchronously.

    Uses Lambda's Event invocation type for fire-and-forget execution.
    Each strategy file runs in its own Lambda invocation concurrently.
    """

    def __init__(
        self,
        function_name: str,
        region: str | None = None,
    ) -> None:
        """Initialize the strategy invoker.

        Args:
            function_name: Strategy Lambda function name or ARN.
            region: AWS region (defaults to AWS_REGION env var).

        """
        self._function_name = function_name
        self._region = region
        self._client: LambdaClient = boto3.client("lambda", region_name=region)
        logger.debug(
            "StrategyInvoker initialized",
            extra={"function_name": function_name},
        )

    def invoke_for_strategy(
        self,
        correlation_id: str,
        dsl_file: str,
        allocation: Decimal,
    ) -> str:
        """Invoke Strategy Lambda for a single strategy file.

        Args:
            correlation_id: Workflow correlation ID.
            dsl_file: DSL strategy file name (e.g., '1-KMLM.clj').
            allocation: Weight allocation for this file (0-1) as Decimal.

        Returns:
            Lambda request ID for tracking.

        """
        payload = {
            "correlation_id": correlation_id,
            "dsl_file": dsl_file,
            "allocation": float(allocation),
        }

        logger.info(
            "Invoking Strategy Lambda",
            extra={
                "function_name": self._function_name,
                "correlation_id": correlation_id,
                "dsl_file": dsl_file,
                "allocation": str(allocation),
            },
        )

        response = self._client.invoke(
            FunctionName=self._function_name,
            InvocationType="Event",  # Async invocation
            Payload=json.dumps(payload),
        )

        request_id = response.get("ResponseMetadata", {}).get("RequestId", "unknown")

        logger.debug(
            "Strategy Lambda invoked",
            extra={
                "dsl_file": dsl_file,
                "request_id": request_id,
                "status_code": response.get("StatusCode"),
            },
        )

        return request_id

    def invoke_all_strategies(
        self,
        correlation_id: str,
        strategy_configs: list[tuple[str, Decimal]],
    ) -> list[str]:
        """Invoke Strategy Lambda for all strategy files in parallel.

        Args:
            correlation_id: Workflow correlation ID.
            strategy_configs: List of (dsl_file, allocation) tuples.

        Returns:
            List of Lambda request IDs for all invocations.

        """
        request_ids = []

        for dsl_file, allocation in strategy_configs:
            request_id = self.invoke_for_strategy(
                correlation_id=correlation_id,
                dsl_file=dsl_file,
                allocation=allocation,
            )
            request_ids.append(request_id)

        logger.info(
            "Invoked Strategy Lambda for all files",
            extra={
                "correlation_id": correlation_id,
                "total_invocations": len(strategy_configs),
                "strategy_files": [f for f, _ in strategy_configs],
            },
        )

        return request_ids
