#!/usr/bin/env python3
"""Business Unit: scripts | Status: current.

Dashboard settings module for centralized configuration.

Provides environment-aware table names and AWS region configuration
following the project's settings pattern (similar to CoordinatorSettings).
"""

from __future__ import annotations

import os

from pydantic import BaseModel, Field


class DashboardSettings(BaseModel):
    """Settings for dashboard data access.

    Loads configuration from environment variables with smart defaults
    that derive table names from the STAGE environment variable.

    Environment Variables:
        STAGE or APP__STAGE: Environment stage (dev/staging/prod), defaults to 'dev'
        AWS_REGION: AWS region for DynamoDB, defaults to 'us-east-1'
        AGGREGATION_TABLE_NAME: Override for aggregation sessions table
        REBALANCE_PLAN__TABLE_NAME: Override for rebalance plans table
        TRADE_LEDGER__TABLE_NAME: Override for trade ledger table
    """

    aggregation_sessions_table: str = Field(
        default="",
        description="DynamoDB table name for aggregation sessions",
    )
    rebalance_plans_table: str = Field(
        default="",
        description="DynamoDB table name for rebalance plans",
    )
    trade_ledger_table: str = Field(
        default="",
        description="DynamoDB table name for trade ledger",
    )
    aws_region: str = Field(
        default="us-east-1",
        description="AWS region for DynamoDB access",
    )
    stage: str = Field(
        default="dev",
        description="Environment stage (dev/staging/prod)",
    )

    @classmethod
    def from_environment(cls) -> DashboardSettings:
        """Load settings from environment variables.

        Table names can be explicitly set via environment variables,
        or they will be derived from the stage using the pattern:
        alchemiser-{stage}-{resource-type}

        Returns:
            DashboardSettings instance with resolved configuration.

        """
        stage = os.environ.get("STAGE", os.environ.get("APP__STAGE", "dev"))
        region = os.environ.get("AWS_REGION", "us-east-1")

        # Use explicit table names if set, otherwise derive from stage
        return cls(
            aggregation_sessions_table=os.environ.get(
                "AGGREGATION_TABLE_NAME",
                f"alchemiser-{stage}-aggregation-sessions",
            ),
            rebalance_plans_table=os.environ.get(
                "REBALANCE_PLAN__TABLE_NAME",
                f"alchemiser-{stage}-rebalance-plans",
            ),
            trade_ledger_table=os.environ.get(
                "TRADE_LEDGER__TABLE_NAME",
                f"alchemiser-{stage}-trade-ledger",
            ),
            aws_region=region,
            stage=stage,
        )


# Singleton instance loaded once per process
_settings: DashboardSettings | None = None


def get_dashboard_settings() -> DashboardSettings:
    """Get dashboard settings (singleton).

    Returns the same DashboardSettings instance on repeated calls
    to avoid reloading environment variables unnecessarily.

    Returns:
        DashboardSettings instance with current configuration.

    """
    global _settings
    if _settings is None:
        _settings = DashboardSettings.from_environment()
    return _settings
