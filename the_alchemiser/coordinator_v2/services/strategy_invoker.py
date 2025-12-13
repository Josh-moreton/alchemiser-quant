"""Business Unit: coordinator_v2 | Status: current.

Service for invoking Strategy Lambda functions asynchronously.

Uses Lambda's async invocation (InvocationType='Event') to fan out
strategy execution across multiple concurrent Lambda invocations.
"""

from __future__ import annotations

import json
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
        session_id: str,
        correlation_id: str,
        dsl_file: str,
        allocation: float,
        strategy_number: int,
        total_strategies: int,
    ) -> str:
        """Invoke Strategy Lambda for a single strategy file.

        Args:
            session_id: Aggregation session ID.
            correlation_id: Workflow correlation ID.
            dsl_file: DSL strategy file name (e.g., '1-KMLM.clj').
            allocation: Weight allocation for this file (0-1).
            strategy_number: Order index (1-based).
            total_strategies: Total number of strategies in session.

        Returns:
            Lambda request ID for tracking.

        """
        payload = {
            "session_id": session_id,
            "correlation_id": correlation_id,
            "dsl_file": dsl_file,
            "allocation": allocation,
            "strategy_number": strategy_number,
            "total_strategies": total_strategies,
            "mode": "single_strategy",  # Signal single-file mode
        }

        logger.info(
            "Invoking Strategy Lambda for single file",
            extra={
                "function_name": self._function_name,
                "session_id": session_id,
                "dsl_file": dsl_file,
                "strategy_number": strategy_number,
                "total_strategies": total_strategies,
            },
        )

        response = self._client.invoke(
            FunctionName=self._function_name,
            InvocationType="Event",  # Async invocation
            Payload=json.dumps(payload),
        )

        # Response contains RequestId in headers for Event invocations
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
        session_id: str,
        correlation_id: str,
        strategy_configs: list[tuple[str, float]],
    ) -> list[str]:
        """Invoke Strategy Lambda for all strategy files in parallel.

        Args:
            session_id: Aggregation session ID.
            correlation_id: Workflow correlation ID.
            strategy_configs: List of (dsl_file, allocation) tuples.

        Returns:
            List of Lambda request IDs for all invocations.

        """
        request_ids = []
        total = len(strategy_configs)

        for idx, (dsl_file, allocation) in enumerate(strategy_configs, 1):
            request_id = self.invoke_for_strategy(
                session_id=session_id,
                correlation_id=correlation_id,
                dsl_file=dsl_file,
                allocation=allocation,
                strategy_number=idx,
                total_strategies=total,
            )
            request_ids.append(request_id)

        logger.info(
            "Invoked Strategy Lambda for all files",
            extra={
                "session_id": session_id,
                "correlation_id": correlation_id,
                "total_invocations": total,
                "strategy_files": [f for f, _ in strategy_configs],
            },
        )

        return request_ids
