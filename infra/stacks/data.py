"""Business Unit: infrastructure | Status: current.

Data stack: market data ingestion and storage.

Resources:
- DataFunction (Lambda)
- DataLayer (Lambda Layer, Makefile-built)
- MarketDataBucket (S3, RETAIN)
- MarketDataFetchRequestsTable (DynamoDB)
- BadDataMarkersTable (DynamoDB)
- DataRefreshSchedule (EventBridge Scheduler)
- EventBridge rule for MarketDataFetchRequested
"""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk import (
    CfnOutput,
    Duration,
    RemovalPolicy,
    aws_dynamodb as dynamodb,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_s3 as s3,
    aws_scheduler as scheduler,
    aws_ssm as ssm,
)
from constructs import Construct

from infra.config import StageConfig
from infra.constructs import (
    AlchemiserFunction,
    LocalShellBundling,
    alchemiser_table,
    lambda_execution_role,
    layer_from_ssm,
    scheduler_role,
)

_SSM_DATA_LAYER_SUFFIX = "data-deps-arn"


class DataStack(cdk.Stack):
    """Market data fetching, storage, and scheduling."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        config: StageConfig,
        event_bus: events.IEventBus,
        **kwargs: object,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ---- Shared layer (looked up from SSM to avoid cross-stack export lock) ----
        shared_code_layer = layer_from_ssm(
            self,
            "SharedCodeLayer",
            config=config,
            ssm_suffix="shared-code-arn",
        )

        # ---- Market Data S3 Bucket ----
        self.market_data_bucket = s3.Bucket(
            self,
            "MarketDataBucket",
            bucket_name=config.resource_name("market-data"),
            versioned=False,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="DeleteOldVersions",
                    noncurrent_version_expiration=Duration.days(30),
                    enabled=True,
                ),
            ],
        )
        cdk.Tags.of(self.market_data_bucket).add("Environment", config.stage)
        cdk.Tags.of(self.market_data_bucket).add("Service", "market-data")

        # ---- Fetch Requests Table ----
        self.fetch_requests_table = alchemiser_table(
            self,
            "MarketDataFetchRequestsTable",
            config=config,
            table_name_suffix="market-data-fetch-requests",
            partition_key=dynamodb.Attribute(name="PK", type=dynamodb.AttributeType.STRING),
            time_to_live_attribute="ttl",
            service_tag="market-data-fetch-requests",
        )

        # ---- Bad Data Markers Table ----
        self.bad_data_markers_table = alchemiser_table(
            self,
            "BadDataMarkersTable",
            config=config,
            table_name_suffix="bad-data-markers",
            partition_key=dynamodb.Attribute(name="PK", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="SK", type=dynamodb.AttributeType.STRING),
            time_to_live_attribute="TTL",
            service_tag="bad-data-markers",
        )

        # ---- Data Layer (Makefile-built: awswrangler + alpaca-py) ----
        # CDK BundlingOptions replicates the layers/data/Makefile logic.
        # LocalShellBundling runs locally first; Docker is only a fallback.
        _data_layer_cmd = (
            "curl -sL 'https://github.com/aws/aws-sdk-pandas/releases/download/3.10.0/awswrangler-layer-3.10.0-py3.12-arm64.zip' -o /tmp/awswrangler-layer.zip"
            " && unzip -q -o /tmp/awswrangler-layer.zip -d /asset-output"
            " && pip install -q alpaca-py==0.43.0 --no-deps -t /asset-output/python --upgrade"
            " && pip install -q msgpack sseclient-py websockets -t /asset-output/python --upgrade"
            " && pip install -q pydantic pydantic-settings -t /asset-output/python --upgrade --platform manylinux2014_aarch64 --only-binary=:all: --python-version 3.12 --implementation cp"
            " && pip install -q structlog -t /asset-output/python --upgrade"
            " && rm -f /tmp/awswrangler-layer.zip"
        )
        self.data_layer = _lambda.LayerVersion(
            self,
            "DataLayer",
            layer_version_name=config.resource_name("data-deps"),
            description="awswrangler 3.10.0 + alpaca-py (pandas, numpy, pyarrow included)",
            code=_lambda.Code.from_asset(
                "layers/data/",
                bundling=cdk.BundlingOptions(
                    image=_lambda.Runtime.PYTHON_3_12.bundling_image,
                    local=LocalShellBundling(_data_layer_cmd),
                    command=["bash", "-c", _data_layer_cmd],
                ),
            ),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_12],
            compatible_architectures=[_lambda.Architecture.ARM_64],
            removal_policy=RemovalPolicy.DESTROY,
        )

        # ---- Data Execution Role ----
        data_role = lambda_execution_role(
            self,
            "DataExecutionRole",
            config=config,
            policy_statements=[
                iam.PolicyStatement(
                    actions=["s3:GetObject", "s3:PutObject", "s3:ListBucket", "s3:DeleteObject"],
                    resources=[
                        self.market_data_bucket.bucket_arn,
                        f"{self.market_data_bucket.bucket_arn}/*",
                    ],
                ),
                iam.PolicyStatement(
                    actions=[
                        "dynamodb:PutItem",
                        "dynamodb:GetItem",
                        "dynamodb:DeleteItem",
                        "dynamodb:Query",
                    ],
                    resources=[self.fetch_requests_table.table_arn],
                ),
                iam.PolicyStatement(
                    actions=[
                        "dynamodb:PutItem",
                        "dynamodb:GetItem",
                        "dynamodb:DeleteItem",
                        "dynamodb:Query",
                        "dynamodb:Scan",
                    ],
                    resources=[self.bad_data_markers_table.table_arn],
                ),
                iam.PolicyStatement(
                    actions=["events:PutEvents"],
                    resources=[event_bus.event_bus_arn],
                ),
            ],
        )

        # ---- SSM: publish data layer ARN for cross-stack consumption ----
        ssm.StringParameter(
            self,
            "DataLayerArnParam",
            parameter_name=f"/{config.prefix}/layer/{_SSM_DATA_LAYER_SUFFIX}",
            string_value=self.data_layer.layer_version_arn,
            description="ARN of the DataLayer (awswrangler + numpy/pandas)",
        )

        # ---- Data Lambda Function ----
        data_fn = AlchemiserFunction(
            self,
            "DataFunction",
            config=config,
            function_name=config.resource_name("data"),
            code_uri="functions/data/",
            handler="lambda_handler.lambda_handler",
            layers=[shared_code_layer, self.data_layer],
            role=data_role,
            timeout_seconds=900,
            memory_size=1024,
            extra_env={
                "EVENT_BUS_NAME": event_bus.event_bus_name,
                "MARKET_DATA_BUCKET": self.market_data_bucket.bucket_name,
                "FETCH_REQUESTS_TABLE": self.fetch_requests_table.table_name,
                "BAD_DATA_MARKERS_TABLE": self.bad_data_markers_table.table_name,
                "FETCH_COOLDOWN_MINUTES": str(config.fetch_cooldown_minutes),
            },
        )
        self.data_function = data_fn.function

        # ---- EventBridge Rule: MarketDataFetchRequested -> DataFunction ----
        fetch_rule = events.Rule(
            self,
            "MarketDataFetchRequestedRule",
            event_bus=event_bus,
            event_pattern=events.EventPattern(
                source=["alchemiser.strategy"],
                detail_type=["MarketDataFetchRequested"],
            ),
        )
        fetch_rule.add_target(targets.LambdaFunction(self.data_function))

        # ---- EventBridge permission (explicit, matching SAM behavior) ----
        self.data_function.add_permission(
            "DataEventBridgePermission",
            principal=iam.ServicePrincipal("events.amazonaws.com"),
            source_arn=f"arn:aws:events:{self.region}:{self.account}:rule/{event_bus.event_bus_name}/*",
        )

        # ---- Data Refresh Schedule (EventBridge Scheduler) ----
        data_scheduler_role = scheduler_role(
            self, "DataSchedulerRole", target_function_arns=[self.data_function.function_arn]
        )

        scheduler.CfnSchedule(
            self,
            "DataRefreshSchedule",
            name=config.resource_name("data-refresh"),
            description=f"Daily market data refresh for {config.stage} (midnight & noon ET, Tue-Sat)",
            schedule_expression=config.data_refresh_schedule_expr,
            schedule_expression_timezone="America/New_York",
            flexible_time_window=scheduler.CfnSchedule.FlexibleTimeWindowProperty(mode="OFF"),
            target=scheduler.CfnSchedule.TargetProperty(
                arn=self.data_function.function_arn,
                role_arn=data_scheduler_role.role_arn,
                input='{"source": "schedule"}',
                retry_policy=scheduler.CfnSchedule.RetryPolicyProperty(
                    maximum_retry_attempts=2,
                ),
            ),
        )

        # ---- Outputs ----
        CfnOutput(
            self,
            "MarketDataBucketName",
            value=self.market_data_bucket.bucket_name,
            export_name=f"{config.prefix}-MarketDataBucket",
        )
        CfnOutput(
            self,
            "MarketDataFetchRequestsTableName",
            value=self.fetch_requests_table.table_name,
            export_name=f"{config.prefix}-MarketDataFetchRequestsTable",
        )
        CfnOutput(
            self,
            "BadDataMarkersTableName",
            value=self.bad_data_markers_table.table_name,
            export_name=f"{config.prefix}-BadDataMarkersTable",
        )
        CfnOutput(
            self,
            "DataFunctionArn",
            value=self.data_function.function_arn,
            export_name=f"{config.prefix}-DataFunction",
        )
