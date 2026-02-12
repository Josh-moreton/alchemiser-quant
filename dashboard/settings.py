#!/usr/bin/env python3
"""Business Unit: dashboard | Status: current.

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

        if hasattr(st, "secrets"):
            # Debug: show available secret keys (not values!)
            if key in st.secrets:
                value = str(st.secrets[key])
                # Return masked value for debugging
                return value
            # Key not found in secrets
    except Exception as e:
        # Log exception for debugging
        import streamlit as st

        st.warning(f"Exception reading secret '{key}': {type(e).__name__}: {e}")

    # Fallback to environment variable
    return os.environ.get(key, default)


def debug_secrets_info() -> dict[str, str]:
    """Return debug info about secrets configuration (no sensitive values)."""
    info = {}
    try:
        import streamlit as st

        if hasattr(st, "secrets"):
            info["secrets_available"] = "Yes"
            info["secrets_keys"] = ", ".join(st.secrets.keys()) if st.secrets else "None"
            info["AWS_ACCESS_KEY_ID_present"] = "Yes" if "AWS_ACCESS_KEY_ID" in st.secrets else "No"
            info["AWS_SECRET_ACCESS_KEY_present"] = (
                "Yes" if "AWS_SECRET_ACCESS_KEY" in st.secrets else "No"
            )

            # Check if keys might be nested under a section
            for section_key in st.secrets.keys():
                try:
                    section = st.secrets[section_key]
                    if hasattr(section, "keys"):
                        nested_keys = list(section.keys())
                        if nested_keys:
                            info[f"section_{section_key}_keys"] = ", ".join(nested_keys)
                except Exception:
                    pass
        else:
            info["secrets_available"] = "No (st.secrets not present)"
    except Exception as e:
        info["secrets_error"] = f"{type(e).__name__}: {e}"

    # Check environment variables
    info["env_AWS_ACCESS_KEY_ID"] = "Set" if os.environ.get("AWS_ACCESS_KEY_ID") else "Not set"
    info["env_AWS_SECRET_ACCESS_KEY"] = (
        "Set" if os.environ.get("AWS_SECRET_ACCESS_KEY") else "Not set"
    )

    return info


class DashboardSettings(BaseModel):
    """Settings for dashboard data access.

    Loads configuration from Streamlit secrets or environment variables
    with smart defaults that derive table names from the STAGE variable.

    Stage is controlled dynamically via the dashboard sidebar selector
    (not from environment variables or secrets).  Default: ``dev``.

    Streamlit Secrets (secrets.toml or Streamlit Cloud):
        AWS_ACCESS_KEY_ID: AWS access key for DynamoDB
        AWS_SECRET_ACCESS_KEY: AWS secret key for DynamoDB
        AWS_REGION: AWS region for DynamoDB, defaults to 'us-east-1'
        ALPACA_KEY: Alpaca API key (for account ID auto-discovery)
        ALPACA_SECRET: Alpaca API secret (for account ID auto-discovery)

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
    hedge_positions_table: str = Field(
        default="",
        description="DynamoDB table name for hedge positions",
    )
    hedge_history_table: str = Field(
        default="",
        description="DynamoDB table name for hedge history audit trail",
    )
    account_data_table: str = Field(
        default="",
        description="DynamoDB table name for account data snapshots",
    )
    strategy_performance_table: str = Field(
        default="",
        description="DynamoDB table name for strategy performance snapshots",
    )
    account_id: str = Field(
        default="",
        description="Alpaca account ID for DynamoDB lookups",
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
    def from_environment(
        cls,
        stage_override: str | None = None,
    ) -> DashboardSettings:
        """Load settings from Streamlit secrets or environment variables.

        Table names can be explicitly set via environment variables,
        or they will be derived from the stage using the pattern:
        alchemiser-{stage}-{resource-type}

        AWS credentials are read from Streamlit secrets first (for Streamlit Cloud),
        then fall back to environment variables (for local development).

        Args:
            stage_override: If provided, use this stage instead of reading
                from secrets/env.  Used by the dashboard sidebar switcher.

        Returns:
            DashboardSettings instance with resolved configuration.

        """
        # Stage is purely UI-driven; default to dev
        stage = stage_override or "dev"
        region = _get_secret("AWS_REGION", "us-east-1")

        # AWS credentials - check Streamlit secrets first, then env vars
        aws_access_key = _get_secret("AWS_ACCESS_KEY_ID", "")
        aws_secret_key = _get_secret("AWS_SECRET_ACCESS_KEY", "")

        # Resolve account ID: try stage-specific key first, then generic fallback.
        # Streamlit Cloud doesn't support per-environment secrets natively, so
        # we use a naming convention: ACCOUNT_ID_DEV, _STAGING, _PROD.
        account_id = _get_secret(
            f"ACCOUNT_ID_{stage.upper()}",
            _get_secret("ACCOUNT_ID", ""),
        )

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
            hedge_positions_table=_get_secret(
                "HEDGE_POSITIONS_TABLE_NAME",
                f"alchemiser-{stage}-hedge-positions",
            ),
            hedge_history_table=_get_secret(
                "HEDGE_HISTORY_TABLE_NAME",
                f"alchemiser-{stage}-hedge-history",
            ),
            account_data_table=_get_secret(
                "ACCOUNT_DATA_TABLE",
                f"alchemiser-{stage}-account-data",
            ),
            strategy_performance_table=_get_secret(
                "STRATEGY_PERFORMANCE_TABLE",
                f"alchemiser-{stage}-strategy-performance",
            ),
            account_id=account_id,
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
_stage_override: str = "dev"


def set_stage(stage: str) -> None:
    """Override the active stage and clear cached settings.

    Call this when the user changes the environment selector in the
    dashboard sidebar.  Clears the singleton so the next call to
    ``get_dashboard_settings`` rebuilds with the new stage.

    Also clears all ``st.cache_data`` caches so pages re-fetch from
    the correct DynamoDB tables.

    Args:
        stage: Environment name (dev / staging / prod).

    """
    global _settings, _stage_override
    _stage_override = stage
    _settings = None

    # Clear the auto-discovered account ID so it re-discovers from the new table
    from data.account import reset_account_cache

    reset_account_cache()

    # Flush every page-level cache so data is re-read from the new tables
    import streamlit as st

    st.cache_data.clear()


def get_active_stage() -> str:
    """Return the currently active stage (UI-driven, default ``dev``)."""
    return _stage_override


def get_dashboard_settings() -> DashboardSettings:
    """Get dashboard settings (singleton).

    Returns the same DashboardSettings instance on repeated calls
    to avoid reloading environment variables unnecessarily.

    If ``set_stage`` was called, the singleton is rebuilt with the
    overridden stage.

    Returns:
        DashboardSettings instance with current configuration.

    """
    global _settings
    if _settings is None:
        _settings = DashboardSettings.from_environment(stage_override=_stage_override)
    return _settings
