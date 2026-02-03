#!/usr/bin/env python3
"""Business Unit: scripts | Status: current.

Dashboard settings module for centralized configuration.

Provides environment-aware table names and AWS region configuration
following the project's settings pattern (similar to CoordinatorSettings).
"""

from __future__ import annotations

import os
from typing import Any

from pydantic import BaseModel, Field


def _get_secret(key: str, default: str = "") -> str:
    """Get a value from Streamlit secrets or environment variables.
    
    Streamlit Cloud stores secrets in st.secrets, but boto3 doesn't read
    from there automatically. This helper checks both sources.
    """
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return os.environ.get(key, default)


class DashboardSettings(BaseModel):
    """Settings for dashboard data access.

    Loads configuration from Streamlit secrets or environment variables
    with smart defaults that derive table names from the STAGE variable.

    Streamlit Secrets (secrets.toml or Streamlit Cloud):
        AWS_ACCESS_KEY_ID: AWS access key for DynamoDB
        AWS_SECRET_ACCESS_KEY: AWS secret key for DynamoDB
        AWS_REGION: AWS region for DynamoDB, defaults to 'us-east-1'
        STAGE: Environment stage (dev/staging/prod), defaults to 'prod'

    Environment Variables (fallback):
        Same keys as above, checked if not in Streamlit secrets
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
    aws_access_key_id: str = Field(
        default="",
        description="AWS access key ID (from secrets or env)",
    )
    aws_secret_access_key: str = Field(
        default="",
        description="AWS secret access key (from secrets or env)",
    )

    @classmethod
    def from_environment(cls) -> DashboardSettings:
        """Load settings from Streamlit secrets or environment variables.

        Table names can be explicitly set via environment variables,
        or they will be derived from the stage using the pattern:
        alchemiser-{stage}-{resource-type}

        AWS credentials are read from Streamlit secrets first (for Streamlit Cloud),
        then fall back to environment variables (for local development).

        Returns:
            DashboardSettings instance with resolved configuration.

        """
        # Default to prod - Streamlit dashboard is production-focused
        stage = _get_secret("STAGE", _get_secret("APP__STAGE", "prod"))
        region = _get_secret("AWS_REGION", "us-east-1")
        
        # AWS credentials - check Streamlit secrets first, then env vars
        aws_access_key = _get_secret("AWS_ACCESS_KEY_ID", "")
        aws_secret_key = _get_secret("AWS_SECRET_ACCESS_KEY", "")

        # Use explicit table names if set, otherwise derive from stage
        return cls(
            aggregation_sessions_table=_get_secret(
                "AGGREGATION_TABLE_NAME",
                f"alchemiser-{stage}-aggregation-sessions",
            ),
            rebalance_plans_table=_get_secret(
                "REBALANCE_PLAN__TABLE_NAME",
                f"alchemiser-{stage}-rebalance-plans",
            ),
            trade_ledger_table=_get_secret(
                "TRADE_LEDGER__TABLE_NAME",
                f"alchemiser-{stage}-trade-ledger",
            ),
            aws_region=region,
            stage=stage,
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
        )
    
    def get_boto3_client_kwargs(self) -> dict[str, Any]:
        """Get kwargs for boto3.client() with credentials if available.
        
        Returns dict with region_name and credentials if configured.
        If no credentials are set, returns only region_name and boto3
        will use its default credential chain (env vars, AWS config, etc.).
        """
        kwargs: dict[str, Any] = {"region_name": self.aws_region}
        
        if self.aws_access_key_id and self.aws_secret_access_key:
            kwargs["aws_access_key_id"] = self.aws_access_key_id
            kwargs["aws_secret_access_key"] = self.aws_secret_access_key
        
        return kwargs
    
    def has_aws_credentials(self) -> bool:
        """Check if AWS credentials are configured."""
        return bool(self.aws_access_key_id and self.aws_secret_access_key)


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
