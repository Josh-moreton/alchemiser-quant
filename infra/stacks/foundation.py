"""Business Unit: infrastructure | Status: current.

Foundation stack: shared resources consumed by all other stacks.

Resources:
- AlchemiserEventBus (EventBridge)
- SharedCodeLayer (Lambda Layer)
- NotificationsLayer (Lambda Layer)
- PortfolioLayer (Lambda Layer)
- TradeLedgerTable (DynamoDB, 5 GSIs)
- DLQAlertTopic + email subscription (SNS)
"""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk import (
    CfnOutput,
    RemovalPolicy,
    aws_dynamodb as dynamodb,
    aws_events as events,
    aws_lambda as _lambda,
    aws_sns as sns,
    aws_sns_subscriptions as sns_subs,
)
from constructs import Construct

from infra.config import StageConfig
from infra.constructs import alchemiser_table


class FoundationStack(cdk.Stack):
    """Shared resources referenced by all domain stacks."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        config: StageConfig,
        **kwargs: object,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.config = config

        # ---- EventBridge Bus ----
        self.event_bus = events.EventBus(
            self,
            "AlchemiserEventBus",
            event_bus_name=config.resource_name("events"),
        )

        # ---- Shared Code Layer ----
        # Directory must contain python/the_alchemiser/ so Lambda finds
        # the module at /opt/python/the_alchemiser/ at runtime.
        self.shared_code_layer = _lambda.LayerVersion(
            self,
            "SharedCodeLayer",
            layer_version_name=config.resource_name("shared-code"),
            description="Shared business logic (the_alchemiser.shared module)",
            code=_lambda.Code.from_asset("shared_layer/"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_12],
            compatible_architectures=[_lambda.Architecture.X86_64],
            removal_policy=RemovalPolicy.RETAIN,
        )

        # ---- Notifications Layer (shared: used by Orchestrator, ScheduleManager, TradeAggregator) ----
        # NOTE: This layer currently only contains requirements.txt, NOT installed
        # packages. Adding bundling (pip install) would change the physical
        # resource, which CloudFormation blocks when the layer's ARN is exported
        # to other stacks. Lambdas that need pydantic/structlog should use their
        # own domain-specific layer (e.g., strategy_layer, execution_layer).
        self.notifications_layer = _lambda.LayerVersion(
            self,
            "NotificationsLayer",
            layer_version_name=config.resource_name("notifications-deps"),
            description="Notifications Lambda dependencies (pydantic, structlog, alpaca-py)",
            code=_lambda.Code.from_asset("layers/notifications/"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_12],
            removal_policy=RemovalPolicy.RETAIN,
        )

        # ---- Portfolio Layer (shared: used by Hedging, Dashboard, AccountData) ----
        # NOTE: This layer is missing bundling (no pip install), so it only
        # contains requirements.txt. Adding bundling requires first removing
        # cross-stack export references from dashboard/hedging stacks to avoid
        # CloudFormation "export in use" errors.
        self.portfolio_layer = _lambda.LayerVersion(
            self,
            "PortfolioLayer",
            layer_version_name=config.resource_name("portfolio-deps"),
            description="Portfolio Lambda dependencies (alpaca-py, pydantic)",
            code=_lambda.Code.from_asset("layers/portfolio/"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_12],
            removal_policy=RemovalPolicy.RETAIN,
        )

        # ---- Trade Ledger Table (5 GSIs) ----
        gsi_attrs = []
        for i in range(1, 6):
            gsi_attrs.extend([
                {"name": f"GSI{i}PK", "type": dynamodb.AttributeType.STRING},
                {"name": f"GSI{i}SK", "type": dynamodb.AttributeType.STRING},
            ])

        self.trade_ledger_table = alchemiser_table(
            self,
            "TradeLedgerTable",
            config=config,
            table_name_suffix="trade-ledger",
            partition_key=dynamodb.Attribute(name="PK", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="SK", type=dynamodb.AttributeType.STRING),
            point_in_time_recovery=True,
            service_tag="trade-ledger",
            global_secondary_indexes=[
                {
                    "index_name": "GSI1-CorrelationIndex",
                    "partition_key": dynamodb.Attribute(name="GSI1PK", type=dynamodb.AttributeType.STRING),
                    "sort_key": dynamodb.Attribute(name="GSI1SK", type=dynamodb.AttributeType.STRING),
                },
                {
                    "index_name": "GSI2-SymbolIndex",
                    "partition_key": dynamodb.Attribute(name="GSI2PK", type=dynamodb.AttributeType.STRING),
                    "sort_key": dynamodb.Attribute(name="GSI2SK", type=dynamodb.AttributeType.STRING),
                },
                {
                    "index_name": "GSI3-StrategyIndex",
                    "partition_key": dynamodb.Attribute(name="GSI3PK", type=dynamodb.AttributeType.STRING),
                    "sort_key": dynamodb.Attribute(name="GSI3SK", type=dynamodb.AttributeType.STRING),
                },
                {
                    "index_name": "GSI4-CorrelationSnapshotIndex",
                    "partition_key": dynamodb.Attribute(name="GSI4PK", type=dynamodb.AttributeType.STRING),
                    "sort_key": dynamodb.Attribute(name="GSI4SK", type=dynamodb.AttributeType.STRING),
                },
                {
                    "index_name": "GSI5-StrategyLotsIndex",
                    "partition_key": dynamodb.Attribute(name="GSI5PK", type=dynamodb.AttributeType.STRING),
                    "sort_key": dynamodb.Attribute(name="GSI5SK", type=dynamodb.AttributeType.STRING),
                },
            ],
        )

        # ---- DLQ Alert SNS Topic ----
        self.dlq_alert_topic = sns.Topic(
            self,
            "DLQAlertTopic",
            topic_name=config.resource_name("dlq-alerts"),
            display_name="Alchemiser DLQ Alert",
        )
        self.dlq_alert_topic.add_subscription(
            sns_subs.EmailSubscription(config.resolved_notification_email)
        )

        # ---- Outputs ----
        CfnOutput(
            self,
            "TradeLedgerTableName",
            value=self.trade_ledger_table.table_name,
            export_name=f"{config.prefix}-TradeLedgerTable",
            description="DynamoDB table for trade ledger persistence",
        )
