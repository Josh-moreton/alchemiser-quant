"""Business Unit: coordinator | Status: current.

Configuration settings for the Strategy Coordinator Lambda.
"""

from __future__ import annotations

import os

from pydantic import BaseModel, Field


class CoordinatorSettings(BaseModel):
    """Settings for the Strategy Coordinator Lambda.

    Configures the Strategy Lambda function name for per-strategy invocation.
    """

    # Strategy Lambda function name (ARN or name)
    strategy_lambda_function_name: str = Field(
        default="",
        description="Name or ARN of the Strategy Lambda to invoke",
    )

    @classmethod
    def from_environment(cls) -> CoordinatorSettings:
        """Create settings from environment variables.

        Environment variables:
            STRATEGY_FUNCTION_NAME: Strategy Lambda function name/ARN

        Returns:
            CoordinatorSettings with values from environment.

        """
        return cls(
            strategy_lambda_function_name=os.environ.get("STRATEGY_FUNCTION_NAME", ""),
        )
