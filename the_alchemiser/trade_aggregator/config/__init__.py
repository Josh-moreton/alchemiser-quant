"""Business Unit: trade_aggregator | Status: current.

Aggregator settings loaded from environment variables.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class TradeAggregatorSettings:
    """Configuration for Trade Aggregator service.

    Attributes:
        execution_runs_table_name: DynamoDB table for execution run state.

    """

    execution_runs_table_name: str

    @classmethod
    def from_environment(cls) -> TradeAggregatorSettings:
        """Load settings from environment variables.

        Returns:
            TradeAggregatorSettings with values from environment.

        Raises:
            ValueError: If required environment variables are missing.

        """
        table_name = os.environ.get("EXECUTION_RUNS_TABLE_NAME", "")
        if not table_name:
            raise ValueError("EXECUTION_RUNS_TABLE_NAME environment variable is required")

        return cls(execution_runs_table_name=table_name)
