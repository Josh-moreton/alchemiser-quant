"""Business Unit: coordinator_v2 | Status: current.

Configuration settings for the Strategy Coordinator Lambda.
"""

from __future__ import annotations

import os

from pydantic import BaseModel, Field


class CoordinatorSettings(BaseModel):
    """Settings for the Strategy Coordinator Lambda.

    Configures aggregation timeouts, Lambda function names, and DynamoDB table.
    """

    # Aggregation timeout in seconds (10 minutes default)
    aggregation_timeout_seconds: int = Field(
        default=600,
        description="Maximum time to wait for all strategies to complete",
    )

    # Strategy Lambda function name (ARN or name)
    strategy_lambda_function_name: str = Field(
        default="",
        description="Name or ARN of the Strategy Lambda to invoke",
    )

    # DynamoDB table for aggregation state
    aggregation_table_name: str = Field(
        default="",
        description="DynamoDB table name for aggregation session state",
    )

    @classmethod
    def from_environment(cls) -> CoordinatorSettings:
        """Create settings from environment variables.

        Environment variables:
            AGGREGATION_TIMEOUT_SECONDS: Max wait time for aggregation
            STRATEGY_FUNCTION_NAME: Strategy Lambda function name/ARN
            AGGREGATION_TABLE_NAME: DynamoDB table for session state

        Returns:
            CoordinatorSettings with values from environment.

        """
        return cls(
            aggregation_timeout_seconds=int(os.environ.get("AGGREGATION_TIMEOUT_SECONDS", "600")),
            strategy_lambda_function_name=os.environ.get("STRATEGY_FUNCTION_NAME", ""),
            aggregation_table_name=os.environ.get("AGGREGATION_TABLE_NAME", ""),
        )
