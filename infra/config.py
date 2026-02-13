"""Business Unit: infrastructure | Status: current.

Stage-aware configuration for all CDK stacks.

Replaces the nested !If conditionals from template.yaml with native Python
conditionals. Every stack receives a StageConfig instance to resolve
environment-specific values (Alpaca credentials, resource naming, etc.).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class AlpacaConfig:
    """Alpaca API credentials per stage."""

    key: str
    secret: str
    endpoint: str
    equity_deployment_pct: str = "1.0"


@dataclass(frozen=True)
class StageConfig:
    """Centralised stage configuration - replaces all !If conditionals."""

    stage: str
    stack_name_override: str = ""
    notification_email: str = ""
    data_refresh_schedule_expr: str = "cron(0 0,12 ? * TUE-SAT *)"
    fetch_cooldown_minutes: int = 15

    # Per-environment Alpaca configs (populated by app.py from env vars / secrets)
    alpaca: AlpacaConfig = field(
        default_factory=lambda: AlpacaConfig(key="", secret="", endpoint="https://paper-api.alpaca.markets/v2"),
    )

    # ---------- derived helpers ----------

    @property
    def is_production(self) -> bool:
        return self.stage == "prod"

    @property
    def is_staging(self) -> bool:
        return self.stage == "staging"

    @property
    def is_ephemeral(self) -> bool:
        return self.stage == "ephemeral"

    @property
    def use_stack_name(self) -> bool:
        return self.is_ephemeral or bool(self.stack_name_override)

    @property
    def prefix(self) -> str:
        """Resource naming prefix: 'alchemiser-<stage>' or custom stack name."""
        if self.use_stack_name and self.stack_name_override:
            return self.stack_name_override
        return f"alchemiser-{self.stage}"

    @property
    def app_stage_value(self) -> str:
        """Value for APP__STAGE env var (prod stays prod, staging stays staging, rest -> dev)."""
        if self.is_production:
            return "prod"
        if self.is_staging:
            return "staging"
        return "dev"

    @property
    def resolved_notification_email(self) -> str:
        return self.notification_email or "notifications@rwxt.org"

    @property
    def title_case(self) -> str:
        mapping = {"dev": "Dev", "staging": "Staging", "prod": "Production", "ephemeral": "Ephemeral"}
        return mapping.get(self.stage, self.stage.capitalize())

    def resource_name(self, suffix: str) -> str:
        """Generate a physical resource name: '<prefix>-<suffix>'."""
        return f"{self.prefix}-{suffix}"

    @property
    def global_env_vars(self) -> dict[str, str]:
        """Environment variables applied to every Lambda (replaces SAM Globals)."""
        return {
            "APP__STAGE": self.app_stage_value,
            "ALPACA__KEY": self.alpaca.key,
            "ALPACA__SECRET": self.alpaca.secret,
            "ALPACA__ENDPOINT": self.alpaca.endpoint,
            "ALPACA__EQUITY_DEPLOYMENT_PCT": self.alpaca.equity_deployment_pct,
        }
