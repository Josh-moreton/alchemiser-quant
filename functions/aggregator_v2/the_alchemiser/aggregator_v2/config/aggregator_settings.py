"""Business Unit: aggregator_v2 | Status: current.

Configuration settings for the Signal Aggregator Lambda.
"""

from __future__ import annotations

import os

from pydantic import BaseModel, Field


class AggregatorSettings(BaseModel):
    """Settings for the Signal Aggregator Lambda."""

    # DynamoDB table for aggregation state (shared with Coordinator)
    aggregation_table_name: str = Field(
        default="",
        description="DynamoDB table name for aggregation session state",
    )

    # Allocation tolerance for validation (default 1%)
    allocation_tolerance: float = Field(
        default=0.01,
        description="Tolerance for total allocation validation (0.01 = 1%)",
    )

    @classmethod
    def from_environment(cls) -> AggregatorSettings:
        """Create settings from environment variables.

        Environment variables:
            AGGREGATION_TABLE_NAME: DynamoDB table for session state
            ALLOCATION_TOLERANCE: Tolerance for allocation validation

        Returns:
            AggregatorSettings with values from environment.

        """
        return cls(
            aggregation_table_name=os.environ.get("AGGREGATION_TABLE_NAME", ""),
            allocation_tolerance=float(os.environ.get("ALLOCATION_TOLERANCE", "0.01")),
        )
