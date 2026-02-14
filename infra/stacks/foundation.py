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
    aws_ssm as ssm,
)
from constructs import Construct

from infra.config import StageConfig
from infra.constructs import LocalShellBundling, alchemiser_table


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
            removal_policy=RemovalPolicy.DESTROY,
        )

        # ---- Notifications Layer (shared: used by Orchestrator, ScheduleManager, TradeAggregator) ----
        _notifications_layer_cmd = (
            "pip install -q alpaca-py==0.43.0 --no-deps -t /asset-output/python --upgrade"
            " && pip install -q msgpack sseclient-py websockets -t /asset-output/python --upgrade"
            " && pip install -q pydantic pydantic-settings -t /asset-output/python --upgrade"
            " --platform manylinux2014_x86_64 --only-binary=:all: --python-version 3.12 --implementation cp"
            " && pip install -q dependency-injector -t /asset-output/python --upgrade"
            " --platform manylinux2014_x86_64 --only-binary=:all: --python-version 3.12 --implementation cp"
            " && pip install -q structlog 'cachetools>=6,<7' pyyaml -t /asset-output/python --upgrade"
            " && pip install -q httpx httpcore anyio h11 requests certifi charset-normalizer"
            " idna urllib3 python-dateutil pytz tzdata -t /asset-output/python --upgrade"
        )
        self.notifications_layer = _lambda.LayerVersion(
            self,
            "NotificationsLayer",
            layer_version_name=config.resource_name("notifications-deps"),
            description="Notifications Lambda dependencies (pydantic, structlog, alpaca-py)",
            code=_lambda.Code.from_asset(
                "layers/notifications/",
                bundling=cdk.BundlingOptions(
                    image=_lambda.Runtime.PYTHON_3_12.bundling_image,
                    local=LocalShellBundling(_notifications_layer_cmd),
                    command=["bash", "-c", _notifications_layer_cmd],
                ),
            ),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_12],
            compatible_architectures=[_lambda.Architecture.X86_64],
            removal_policy=RemovalPolicy.DESTROY,
        )

        # ---- Portfolio Layer (shared: used by Hedging, Dashboard, AccountData) ----
        _portfolio_layer_cmd = (
            "pip install -q alpaca-py==0.43.0 --no-deps -t /asset-output/python --upgrade"
            " && pip install -q msgpack sseclient-py websockets -t /asset-output/python --upgrade"
            " && pip install -q pydantic pydantic-settings -t /asset-output/python --upgrade"
            " --platform manylinux2014_x86_64 --only-binary=:all: --python-version 3.12 --implementation cp"
            " && pip install -q dependency-injector -t /asset-output/python --upgrade"
            " --platform manylinux2014_x86_64 --only-binary=:all: --python-version 3.12 --implementation cp"
            " && pip install -q structlog 'cachetools>=6,<7' pyyaml -t /asset-output/python --upgrade"
            " && pip install -q httpx httpcore anyio h11 requests certifi charset-normalizer"
            " idna urllib3 python-dateutil pytz tzdata -t /asset-output/python --upgrade"
        )
        self.portfolio_layer = _lambda.LayerVersion(
            self,
            "PortfolioLayer",
            layer_version_name=config.resource_name("portfolio-deps"),
            description="Portfolio Lambda dependencies (alpaca-py, pydantic)",
            code=_lambda.Code.from_asset(
                "layers/portfolio/",
                bundling=cdk.BundlingOptions(
                    image=_lambda.Runtime.PYTHON_3_12.bundling_image,
                    local=LocalShellBundling(_portfolio_layer_cmd),
                    command=["bash", "-c", _portfolio_layer_cmd],
                ),
            ),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_12],
            compatible_architectures=[_lambda.Architecture.X86_64],
            removal_policy=RemovalPolicy.DESTROY,
        )

        # ---- SSM Parameters for cross-stack layer references ----
        # Lambda layers create a NEW physical resource (ARN) on every code
        # change. CDK auto-generates CloudFormation Exports when a construct
        # is referenced from another stack, and CloudFormation refuses to
        # update an export that is still imported elsewhere. This blocks
        # every deploy where shared layer code changes.
        #
        # By publishing layer ARNs to SSM and having consuming stacks read
        # them via dynamic references, we break the CloudFormation export
        # dependency. add_dependency ordering ensures this stack deploys
        # first, so the SSM parameter is always up-to-date.
        ssm.StringParameter(
            self,
            "SharedCodeLayerArnParam",
            parameter_name=f"/{config.prefix}/layer/shared-code-arn",
            string_value=self.shared_code_layer.layer_version_arn,
            description="ARN of the SharedCodeLayer (latest version)",
        )
        ssm.StringParameter(
            self,
            "NotificationsLayerArnParam",
            parameter_name=f"/{config.prefix}/layer/notifications-deps-arn",
            string_value=self.notifications_layer.layer_version_arn,
            description="ARN of the NotificationsLayer (latest version)",
        )
        ssm.StringParameter(
            self,
            "PortfolioLayerArnParam",
            parameter_name=f"/{config.prefix}/layer/portfolio-deps-arn",
            string_value=self.portfolio_layer.layer_version_arn,
            description="ARN of the PortfolioLayer (latest version)",
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
