"""Business Unit: infrastructure | Status: current.

Execution stack: trade execution and aggregation.

Resources:
- ExecutionFunction (Lambda, SQS-triggered, reserved concurrency=10)
- TradeAggregatorFunction (Lambda, EventBridge-triggered)
- ExecutionQueue + DLQ (SQS Standard)
- ExecutionFifoQueue + DLQ (SQS FIFO)
- ExecutionRunsTable (DynamoDB)
- RebalancePlanTable (DynamoDB, 1 GSI, PITR)
- CloudWatch Alarms: DLQ, FIFO DLQ, stuck runs
"""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk import (
    CfnOutput,
    Duration,
    aws_cloudwatch as cloudwatch,
    aws_dynamodb as dynamodb,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_lambda_event_sources as event_sources,
    aws_sqs as sqs,
)
from constructs import Construct

from infra.config import StageConfig
from infra.constructs import (
    AlchemiserFunction,
    alchemiser_table,
    bundled_layer_code,
    lambda_execution_role,
    layer_from_ssm,
)


class ExecutionStack(cdk.Stack):
    """Trade execution microservices and queues."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        config: StageConfig,
        event_bus: events.IEventBus,
        trade_ledger_table: dynamodb.ITable,
        account_data_table: dynamodb.ITable,
        **kwargs: object,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ---- Shared layers (looked up from SSM to avoid cross-stack export lock) ----
        shared_code_layer = layer_from_ssm(
            self,
            "SharedCodeLayer",
            config=config,
            ssm_suffix="shared-code-arn",
        )
        notifications_layer = layer_from_ssm(
            self,
            "NotificationsLayer",
            config=config,
            ssm_suffix="notifications-deps-arn",
        )

        # ---- Execution Layer ----
        _execution_layer_cmd = (
            "pip install -q alpaca-py==0.43.0 --no-deps -t /asset-output/python --upgrade"
            " && pip install -q msgpack websockets -t /asset-output/python --upgrade --platform manylinux2014_aarch64 --only-binary=:all: --python-version 3.12 --implementation cp"
            " && pip install -q 'pydantic>=2.0.0' -t /asset-output/python --upgrade --platform manylinux2014_aarch64 --only-binary=:all: --python-version 3.12 --implementation cp"
            " && pip install -q dependency-injector -t /asset-output/python --upgrade --platform manylinux2014_aarch64 --only-binary=:all: --python-version 3.12 --implementation cp"
            " && pip install -q charset-normalizer pyyaml -t /asset-output/python --upgrade --platform manylinux2014_aarch64 --only-binary=:all: --python-version 3.12 --implementation cp"
            " && pip install -q pydantic-settings python-dotenv sseclient-py structlog 'cachetools>=6,<7' -t /asset-output/python --upgrade --no-deps"
            " && pip install -q httpx httpcore anyio h11 requests certifi"
            " idna urllib3 python-dateutil pytz tzdata -t /asset-output/python --upgrade --no-deps"
        )
        self.execution_layer = _lambda.LayerVersion(
            self,
            "ExecutionLayer",
            layer_version_name=config.resource_name("execution-deps"),
            description="Execution Lambda dependencies (alpaca-py, pydantic)",
            code=bundled_layer_code(_execution_layer_cmd),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_12],
            compatible_architectures=[_lambda.Architecture.ARM_64],
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )

        # Publish execution layer ARN to SSM so hedging stack can look it up
        # without a CloudFormation cross-stack export.
        from aws_cdk import aws_ssm as ssm

        ssm.StringParameter(
            self,
            "ExecutionLayerArnParam",
            parameter_name=f"/{config.prefix}/layer/execution-deps-arn",
            string_value=self.execution_layer.layer_version_arn,
            description="ARN of the ExecutionLayer (latest version)",
        )

        # ---- SQS Queues ----
        self.execution_dlq = sqs.Queue(
            self,
            "ExecutionDLQ",
            queue_name=config.resource_name("execution-dlq"),
            retention_period=Duration.days(14),
        )
        self.execution_queue = sqs.Queue(
            self,
            "ExecutionQueue",
            queue_name=config.resource_name("execution-queue"),
            visibility_timeout=Duration.seconds(900),
            retention_period=Duration.days(4),
            dead_letter_queue=sqs.DeadLetterQueue(max_receive_count=3, queue=self.execution_dlq),
        )

        self.execution_fifo_dlq = sqs.Queue(
            self,
            "ExecutionFifoDLQ",
            queue_name=config.resource_name("execution-dlq.fifo"),
            fifo=True,
            retention_period=Duration.days(14),
        )
        self.execution_fifo_queue = sqs.Queue(
            self,
            "ExecutionFifoQueue",
            queue_name=config.resource_name("execution.fifo"),
            fifo=True,
            content_based_deduplication=False,
            deduplication_scope=sqs.DeduplicationScope.MESSAGE_GROUP,
            fifo_throughput_limit=sqs.FifoThroughputLimit.PER_MESSAGE_GROUP_ID,
            visibility_timeout=Duration.seconds(900),
            retention_period=Duration.days(4),
            dead_letter_queue=sqs.DeadLetterQueue(
                max_receive_count=3, queue=self.execution_fifo_dlq
            ),
        )

        # ---- DynamoDB Tables ----
        self.execution_runs_table = alchemiser_table(
            self,
            "ExecutionRunsTable",
            config=config,
            table_name_suffix="execution-runs",
            partition_key=dynamodb.Attribute(name="PK", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="SK", type=dynamodb.AttributeType.STRING),
            time_to_live_attribute="TTL",
            service_tag="execution-runs",
        )

        self.rebalance_plan_table = alchemiser_table(
            self,
            "RebalancePlanTable",
            config=config,
            table_name_suffix="rebalance-plans",
            partition_key=dynamodb.Attribute(name="PK", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="SK", type=dynamodb.AttributeType.STRING),
            time_to_live_attribute="ttl",
            point_in_time_recovery=True,
            service_tag="rebalance-plans",
            global_secondary_indexes=[
                {
                    "index_name": "GSI1-CorrelationIndex",
                    "partition_key": dynamodb.Attribute(
                        name="GSI1PK", type=dynamodb.AttributeType.STRING
                    ),
                    "sort_key": dynamodb.Attribute(
                        name="GSI1SK", type=dynamodb.AttributeType.STRING
                    ),
                },
            ],
        )

        # ---- Execution Role ----
        execution_role = lambda_execution_role(
            self,
            "ExecutionExecutionRole",
            config=config,
            policy_statements=[
                iam.PolicyStatement(
                    actions=["events:PutEvents"],
                    resources=[event_bus.event_bus_arn],
                ),
                iam.PolicyStatement(
                    actions=[
                        "sqs:ReceiveMessage",
                        "sqs:DeleteMessage",
                        "sqs:GetQueueAttributes",
                        "sqs:SendMessage",
                    ],
                    resources=[self.execution_queue.queue_arn, self.execution_fifo_queue.queue_arn],
                ),
                iam.PolicyStatement(
                    actions=[
                        "dynamodb:PutItem",
                        "dynamodb:GetItem",
                        "dynamodb:Query",
                        "dynamodb:BatchWriteItem",
                        "dynamodb:UpdateItem",
                    ],
                    resources=[
                        trade_ledger_table.table_arn,
                        f"{trade_ledger_table.table_arn}/index/*",
                    ],
                ),
                iam.PolicyStatement(
                    actions=[
                        "dynamodb:PutItem",
                        "dynamodb:GetItem",
                        "dynamodb:UpdateItem",
                        "dynamodb:Query",
                    ],
                    resources=[self.execution_runs_table.table_arn],
                ),
            ],
        )

        # ---- Execution Lambda ----
        exec_fn = AlchemiserFunction(
            self,
            "ExecutionFunction",
            config=config,
            function_name=config.resource_name("execution"),
            code_uri="functions/execution/",
            handler="lambda_handler.lambda_handler",
            layers=[shared_code_layer, self.execution_layer],
            role=execution_role,
            timeout_seconds=600,
            memory_size=1024,
            reserved_concurrent_executions=10,
            extra_env={
                "EVENT_BUS_NAME": event_bus.event_bus_name,
                "TRADE_LEDGER__TABLE_NAME": trade_ledger_table.table_name,
                "EXECUTION_RUNS_TABLE_NAME": self.execution_runs_table.table_name,
                "EXECUTION_FIFO_QUEUE_URL": self.execution_fifo_queue.queue_url,
            },
        )
        self.execution_function = exec_fn.function

        # SQS event sources
        self.execution_function.add_event_source(
            event_sources.SqsEventSource(
                self.execution_queue,
                batch_size=1,
                report_batch_item_failures=True,
            )
        )
        self.execution_function.add_event_source(
            event_sources.SqsEventSource(
                self.execution_fifo_queue,
                batch_size=1,
                report_batch_item_failures=True,
            )
        )

        # ---- Trade Aggregator Role ----
        aggregator_role = lambda_execution_role(
            self,
            "TradeAggregatorExecutionRole",
            config=config,
            policy_statements=[
                iam.PolicyStatement(
                    actions=["events:PutEvents"],
                    resources=[event_bus.event_bus_arn],
                ),
                iam.PolicyStatement(
                    actions=[
                        "dynamodb:GetItem",
                        "dynamodb:PutItem",
                        "dynamodb:UpdateItem",
                        "dynamodb:Query",
                    ],
                    resources=[self.execution_runs_table.table_arn],
                ),
                iam.PolicyStatement(
                    actions=["dynamodb:GetItem", "dynamodb:Query"],
                    resources=[account_data_table.table_arn],
                ),
            ],
        )

        # ---- Trade Aggregator Lambda ----
        aggregator_fn = AlchemiserFunction(
            self,
            "TradeAggregatorFunction",
            config=config,
            function_name=config.resource_name("trade-aggregator"),
            code_uri="functions/trade_aggregator/",
            handler="lambda_handler.lambda_handler",
            layers=[shared_code_layer, notifications_layer],
            role=aggregator_role,
            timeout_seconds=60,
            memory_size=512,
            extra_env={
                "EVENT_BUS_NAME": event_bus.event_bus_name,
                "EXECUTION_RUNS_TABLE_NAME": self.execution_runs_table.table_name,
                "ENVIRONMENT": config.stage,
                "ACCOUNT_DATA_TABLE": account_data_table.table_name,
            },
        )
        self.trade_aggregator_function = aggregator_fn.function

        # EventBridge rule: TradeExecuted -> TradeAggregator
        trade_executed_rule = events.Rule(
            self,
            "TradeExecutedRule",
            event_bus=event_bus,
            event_pattern=events.EventPattern(
                source=["alchemiser.execution"],
                detail_type=["TradeExecuted"],
            ),
        )
        trade_executed_rule.add_target(targets.LambdaFunction(self.trade_aggregator_function))

        # Explicit EventBridge permission
        self.trade_aggregator_function.add_permission(
            "TradeAggregatorEventBridgePermission",
            principal=iam.ServicePrincipal("events.amazonaws.com"),
            source_arn=f"arn:aws:events:{self.region}:{self.account}:rule/{event_bus.event_bus_name}/*",
        )

        # ---- CloudWatch Alarms ----
        cloudwatch.Alarm(
            self,
            "DLQMessageAlarm",
            alarm_name=config.resource_name("dlq-messages"),
            alarm_description="Alert when messages land in the execution DLQ after 3 failed attempts",
            metric=self.execution_dlq.metric_approximate_number_of_messages_visible(
                period=Duration.seconds(60),
                statistic="Sum",
            ),
            threshold=1,
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
        )

        cloudwatch.Alarm(
            self,
            "FifoDLQMessageAlarm",
            alarm_name=config.resource_name("parallel-dlq-messages"),
            alarm_description="Alert when per-trade execution messages hit parallel DLQ after 3 retries",
            metric=self.execution_fifo_dlq.metric_approximate_number_of_messages_visible(
                period=Duration.seconds(60),
                statistic="Sum",
            ),
            threshold=1,
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
        )

        cloudwatch.Alarm(
            self,
            "StuckRunsAlarm",
            alarm_name=config.resource_name("stuck-execution-runs"),
            alarm_description="Alert when execution runs are stuck in RUNNING state for >30 minutes",
            metric=cloudwatch.Metric(
                namespace="Alchemiser/Execution",
                metric_name="StuckRuns",
                statistic="Maximum",
                period=Duration.seconds(300),
                dimensions_map={"TableName": self.execution_runs_table.table_name},
            ),
            threshold=1,
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
        )

        # ---- Outputs ----
        CfnOutput(
            self,
            "ExecutionRunsTableName",
            value=self.execution_runs_table.table_name,
            export_name=f"{config.prefix}-ExecutionRunsTable",
        )
        CfnOutput(
            self,
            "RebalancePlanTableName",
            value=self.rebalance_plan_table.table_name,
            export_name=f"{config.prefix}-RebalancePlanTable",
        )
        CfnOutput(
            self,
            "ExecutionFifoQueueUrl",
            value=self.execution_fifo_queue.queue_url,
            export_name=f"{config.prefix}-ExecutionFifoQueue",
        )
