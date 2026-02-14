"""Business Unit: infrastructure | Status: current.

CDK application entry point.

Instantiates all stacks with cross-stack dependencies. Lambda layer ARNs
are shared via SSM Parameter Store (not CloudFormation Exports) to avoid
the "export in use" lock that blocks deployments when layer code changes.
Other resources (tables, queues, buckets) are still wired via Python
references since their physical IDs are stable.

Usage:
    cdk synth -c stage=dev
    cdk synth -c stage=prod
    cdk synth -c stage=ephemeral -c stack_name=alch-ephem-xyz
"""

from __future__ import annotations

import os

import aws_cdk as cdk

from infra.config import AlpacaConfig, StageConfig
from infra.stacks.dashboard import DashboardStack
from infra.stacks.data import DataStack
from infra.stacks.execution import ExecutionStack
from infra.stacks.foundation import FoundationStack
from infra.stacks.hedging import HedgingStack
from infra.stacks.notifications import NotificationsStack
from infra.stacks.strategy import StrategyStack

app = cdk.App()

# ---------- resolve stage from CDK context ----------
stage: str = app.node.try_get_context("stage") or os.environ.get("STAGE", "dev")
stack_name_override: str = app.node.try_get_context("stack_name") or os.environ.get("STACK_NAME", "")
notification_email: str = (
    app.node.try_get_context("notification_email")
    or os.environ.get("NOTIFICATION_EMAIL", "")
)

# ---------- Alpaca credentials from environment ----------
alpaca = AlpacaConfig(
    key=os.environ.get("ALPACA__KEY", ""),
    secret=os.environ.get("ALPACA__SECRET", ""),
    endpoint=os.environ.get("ALPACA__ENDPOINT", "https://paper-api.alpaca.markets/v2"),
    equity_deployment_pct=os.environ.get("ALPACA__EQUITY_DEPLOYMENT_PCT", "1.0"),
)

log_level: str = os.environ.get("ALCHEMISER_LOG_LEVEL", "INFO")

config = StageConfig(
    stage=stage,
    stack_name_override=stack_name_override,
    notification_email=notification_email,
    log_level=log_level,
    alpaca=alpaca,
)

# ---------- common stack kwargs ----------
env = cdk.Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
    region=os.environ.get("CDK_DEFAULT_REGION", "us-east-1"),
)

stack_prefix = config.prefix

# ===== Dependency graph (DAG) =====
#
#   Foundation
#   |  |  |  \__________
#   |  |  |             |
#   v  v  v             v
#  Data  Dashboard   Execution
#   |        |       /   |
#   |        |      /    |
#   v        v     v     v
#       Strategy     Hedging
#           |
#           v
#       Notifications
#
# Layers flow DOWN from Foundation (SharedCode, Notifications, Portfolio).
# Domain resources flow ACROSS via constructor params.

# ---------- 1. Foundation (shared layers + core tables) ----------
foundation = FoundationStack(
    app, f"{stack_prefix}-foundation",
    config=config,
    env=env,
)

# ---------- 2. Data ----------
data = DataStack(
    app, f"{stack_prefix}-data",
    config=config,
    event_bus=foundation.event_bus,
    env=env,
)
data.add_dependency(foundation)

# ---------- 3. Dashboard ----------
dashboard = DashboardStack(
    app, f"{stack_prefix}-dashboard",
    config=config,
    env=env,
)
dashboard.add_dependency(foundation)
dashboard.add_dependency(data)

# ---------- 4. Execution ----------
execution = ExecutionStack(
    app, f"{stack_prefix}-execution",
    config=config,
    event_bus=foundation.event_bus,
    trade_ledger_table=foundation.trade_ledger_table,
    account_data_table=dashboard.account_data_table,
    env=env,
)
execution.add_dependency(foundation)
execution.add_dependency(dashboard)

# ---------- 5. Strategy ----------
strategy = StrategyStack(
    app, f"{stack_prefix}-strategy",
    config=config,
    event_bus=foundation.event_bus,
    trade_ledger_table=foundation.trade_ledger_table,
    data_function=data.data_function,
    market_data_bucket=data.market_data_bucket,
    execution_fifo_queue=execution.execution_fifo_queue,
    execution_runs_table=execution.execution_runs_table,
    rebalance_plan_table=execution.rebalance_plan_table,
    env=env,
)
strategy.add_dependency(foundation)
strategy.add_dependency(data)
strategy.add_dependency(execution)

# ---------- 6. Hedging ----------
hedging = HedgingStack(
    app, f"{stack_prefix}-hedging",
    config=config,
    event_bus=foundation.event_bus,
    env=env,
)
hedging.add_dependency(foundation)
hedging.add_dependency(execution)

# ---------- 7. Notifications (last: depends on Execution + Strategy outputs) ----------
notifications = NotificationsStack(
    app, f"{stack_prefix}-notifications",
    config=config,
    event_bus=foundation.event_bus,
    trade_ledger_table=foundation.trade_ledger_table,
    execution_runs_table=execution.execution_runs_table,
    performance_reports_bucket=strategy.performance_reports_bucket,
    env=env,
)
notifications.add_dependency(foundation)
notifications.add_dependency(execution)
notifications.add_dependency(strategy)

app.synth()
