"""Business Unit: infrastructure | Status: current.

Strategy stack: orchestration, workers, analytics, and reports.

Resources:
- StrategyOrchestratorFunction (Lambda)
- StrategyFunction / StrategyWorker (Lambda)
- ScheduleManagerFunction (Lambda)
- StrategyAnalyticsFunction (Lambda)
- StrategyReportsFunction (Lambda)
- StrategyLayer (Lambda Layer, Makefile-built: awswrangler + alpaca-py)
- NotificationsLayer (ref, used by Orchestrator + ScheduleManager)
- GroupHistoricalSelectionsTable (DynamoDB)
- PerformanceReportsBucket (S3)
- Schedules: ScheduleManager morning, Analytics daily, Reports daily
- Alarms: orchestrator errors, strategy worker errors
- StrategyFunctionEventInvokeConfig (async failure destination)
"""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk import (
    CfnOutput,
    Duration,
    RemovalPolicy,
    aws_cloudwatch as cloudwatch,
    aws_dynamodb as dynamodb,
    aws_events as events,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_s3 as s3,
    aws_scheduler as scheduler,
    aws_sqs as sqs,
)
from constructs import Construct

from infra.config import StageConfig
from infra.constructs import (
    AlchemiserFunction,
    alchemiser_table,
    lambda_execution_role,
    scheduler_role,
)


class StrategyStack(cdk.Stack):
    """Strategy orchestration, worker execution, analytics and reports."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        config: StageConfig,
        event_bus: events.IEventBus,
        shared_code_layer: _lambda.ILayerVersion,
        trade_ledger_table: dynamodb.ITable,
        data_function: _lambda.IFunction,
        market_data_bucket: s3.IBucket,
        execution_fifo_queue: sqs.IQueue,
        execution_runs_table: dynamodb.ITable,
        rebalance_plan_table: dynamodb.ITable,
        notifications_layer: _lambda.ILayerVersion,
        **kwargs: object,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ---- Strategy Layer (Makefile-built: awswrangler + alpaca-py) ----
        self.strategy_layer = _lambda.LayerVersion(
            self,
            "StrategyLayer",
            layer_version_name=config.resource_name("strategy-deps"),
            description="awswrangler 3.10.0 + alpaca-py (pandas, numpy, pyarrow included)",
            code=_lambda.Code.from_asset(
                "layers/strategy/",
                bundling=cdk.BundlingOptions(
                    image=_lambda.Runtime.PYTHON_3_12.bundling_image,
                    command=[
                        "bash",
                        "-c",
                        (
                            "curl -sL 'https://aws-data-wrangler-public-artifacts.s3.amazonaws.com/releases/3.10.0/awswrangler-layer-3.10.0-py3.12.zip' -o /tmp/awswrangler-layer.zip"
                            " && unzip -q -o /tmp/awswrangler-layer.zip -d /asset-output"
                            " && pip install -q alpaca-py==0.43.0 --no-deps -t /asset-output/python --upgrade"
                            " && pip install -q msgpack sseclient-py websockets -t /asset-output/python --upgrade"
                            " && pip install -q pydantic pydantic-settings structlog dependency-injector cachetools -t /asset-output/python --upgrade"
                            " && rm -f /tmp/awswrangler-layer.zip"
                        ),
                    ],
                ),
            ),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_12],
            compatible_architectures=[_lambda.Architecture.X86_64],
            removal_policy=RemovalPolicy.RETAIN,
        )

        # ---- Group Historical Selections Table ----
        self.group_history_table = alchemiser_table(
            self, "GroupHistoricalSelectionsTable",
            config=config,
            table_name_suffix="group-history",
            partition_key=dynamodb.Attribute(name="group_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="record_date", type=dynamodb.AttributeType.STRING),
            time_to_live_attribute="ttl",
            service_tag="group-history",
        )

        # ---- Performance Reports Bucket ----
        self.performance_reports_bucket = s3.Bucket(
            self, "PerformanceReportsBucket",
            bucket_name=(
                f"{config.stack_name_override}-performance-reports"
                if config.stack_name_override
                else f"alchemiser-{config.stage}-reports"
            ),
            lifecycle_rules=[
                s3.LifecycleRule(id="DeleteOldReports", expiration=Duration.days(30), enabled=True),
            ],
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
        )
        cdk.Tags.of(self.performance_reports_bucket).add("Environment", config.stage)
        cdk.Tags.of(self.performance_reports_bucket).add("Service", "performance-reports")

        # ---- Strategy Worker Role ----
        strategy_role = lambda_execution_role(
            self, "StrategyExecutionRole", config=config,
            policy_statements=[
                iam.PolicyStatement(
                    actions=["events:PutEvents"],
                    resources=[event_bus.event_bus_arn],
                ),
                iam.PolicyStatement(
                    actions=["dynamodb:PutItem", "dynamodb:GetItem", "dynamodb:Query"],
                    resources=[trade_ledger_table.table_arn, f"{trade_ledger_table.table_arn}/index/*"],
                ),
                iam.PolicyStatement(
                    actions=["s3:GetObject", "s3:ListBucket"],
                    resources=[market_data_bucket.bucket_arn, f"{market_data_bucket.bucket_arn}/*"],
                ),
                iam.PolicyStatement(
                    actions=["lambda:InvokeFunction"],
                    resources=[data_function.function_arn],
                ),
                iam.PolicyStatement(
                    actions=["dynamodb:GetItem", "dynamodb:Query", "dynamodb:PutItem"],
                    resources=[self.group_history_table.table_arn],
                ),
                iam.PolicyStatement(
                    actions=["sqs:SendMessage", "sqs:GetQueueAttributes"],
                    resources=[execution_fifo_queue.queue_arn],
                ),
                iam.PolicyStatement(
                    actions=["dynamodb:PutItem", "dynamodb:GetItem", "dynamodb:UpdateItem", "dynamodb:Query"],
                    resources=[execution_runs_table.table_arn],
                ),
                iam.PolicyStatement(
                    actions=["dynamodb:PutItem", "dynamodb:GetItem", "dynamodb:Query"],
                    resources=[rebalance_plan_table.table_arn, f"{rebalance_plan_table.table_arn}/index/*"],
                ),
            ],
        )

        # ---- Strategy Worker Lambda ----
        strategy_fn = AlchemiserFunction(
            self, "StrategyFunction",
            config=config,
            function_name=config.resource_name("strategy-worker"),
            code_uri="functions/strategy_worker/",
            handler="lambda_handler.lambda_handler",
            layers=[shared_code_layer, self.strategy_layer],
            role=strategy_role,
            timeout_seconds=900,
            memory_size=1024,
            extra_env={
                "EVENT_BUS_NAME": event_bus.event_bus_name,
                "MARKET_DATA_BUCKET": market_data_bucket.bucket_name,
                "TRADE_LEDGER__TABLE_NAME": trade_ledger_table.table_name,
                "DATA_FUNCTION_NAME": data_function.function_name,
                "STAGE": config.stage,
                "SYNC_REFRESH_TIMEOUT_SECONDS": "300",
                "GROUP_HISTORY_TABLE": self.group_history_table.table_name,
                "EXECUTION_FIFO_QUEUE_URL": execution_fifo_queue.queue_url,
                "EXECUTION_RUNS_TABLE_NAME": execution_runs_table.table_name,
                "REBALANCE_PLAN__TABLE_NAME": rebalance_plan_table.table_name,
            },
        )
        self.strategy_function = strategy_fn.function

        # Async failure destination -> EventBridge
        _lambda.CfnEventInvokeConfig(
            self, "StrategyFunctionEventInvokeConfig",
            function_name=self.strategy_function.function_name,
            qualifier="$LATEST",
            maximum_retry_attempts=2,
            destination_config=_lambda.CfnEventInvokeConfig.DestinationConfigProperty(
                on_failure=_lambda.CfnEventInvokeConfig.OnFailureProperty(
                    destination=event_bus.event_bus_arn,
                ),
            ),
        )

        # ---- Strategy Orchestrator Role ----
        orchestrator_role = lambda_execution_role(
            self, "StrategyOrchestratorExecutionRole", config=config,
            policy_statements=[
                iam.PolicyStatement(
                    actions=["events:PutEvents"],
                    resources=[event_bus.event_bus_arn],
                ),
                iam.PolicyStatement(
                    actions=["lambda:InvokeFunction", "lambda:InvokeAsync"],
                    resources=[self.strategy_function.function_arn],
                ),
                iam.PolicyStatement(
                    actions=["dynamodb:PutItem"],
                    resources=[execution_runs_table.table_arn],
                ),
            ],
        )

        # ---- Strategy Orchestrator Lambda ----
        orchestrator_fn = AlchemiserFunction(
            self, "StrategyOrchestratorFunction",
            config=config,
            function_name=config.resource_name("strategy-orchestrator"),
            code_uri="functions/strategy_orchestrator/",
            handler="lambda_handler.lambda_handler",
            layers=[shared_code_layer, notifications_layer],
            role=orchestrator_role,
            timeout_seconds=60,
            memory_size=512,
            extra_env={
                "EVENT_BUS_NAME": event_bus.event_bus_name,
                "STRATEGY_FUNCTION_NAME": self.strategy_function.function_name,
                "EXECUTION_RUNS_TABLE_NAME": execution_runs_table.table_name,
            },
        )
        self.orchestrator_function = orchestrator_fn.function

        # ---- Scheduler Role (shared for Schedule Manager -> Orchestrator invocation) ----
        strategy_scheduler_role = scheduler_role(
            self, "StrategySchedulerRole",
            target_function_arns=[
                self.strategy_function.function_arn,
                self.orchestrator_function.function_arn,
            ],
        )

        # ---- Schedule Manager Role ----
        schedule_mgr_role = lambda_execution_role(
            self, "ScheduleManagerExecutionRole", config=config,
            policy_statements=[
                iam.PolicyStatement(
                    actions=["scheduler:CreateSchedule", "scheduler:DeleteSchedule", "scheduler:GetSchedule"],
                    resources=[
                        f"arn:aws:scheduler:{cdk.Aws.REGION}:{cdk.Aws.ACCOUNT_ID}:schedule/default/*-trading-execution-*",
                    ],
                ),
                iam.PolicyStatement(
                    actions=["iam:PassRole"],
                    resources=[strategy_scheduler_role.role_arn],
                    conditions={"StringEquals": {"iam:PassedToService": "scheduler.amazonaws.com"}},
                ),
                iam.PolicyStatement(
                    actions=["events:PutEvents"],
                    resources=[event_bus.event_bus_arn],
                ),
            ],
        )

        # ---- Schedule Manager Lambda ----
        schedule_mgr_fn = AlchemiserFunction(
            self, "ScheduleManagerFunction",
            config=config,
            function_name=config.resource_name("schedule-manager"),
            code_uri="functions/schedule_manager/",
            handler="lambda_handler.lambda_handler",
            layers=[shared_code_layer, notifications_layer],
            role=schedule_mgr_role,
            timeout_seconds=60,
            memory_size=256,
            extra_env={
                "ORCHESTRATOR_FUNCTION_ARN": self.orchestrator_function.function_arn,
                "SCHEDULER_ROLE_ARN": strategy_scheduler_role.role_arn,
                "SCHEDULE_GROUP_NAME": "default",
                "MINUTES_BEFORE_CLOSE": "15",
                "EVENT_BUS_NAME": event_bus.event_bus_name,
            },
        )
        self.schedule_manager_function = schedule_mgr_fn.function

        # Schedule Manager morning schedule
        schedule_mgr_scheduler_role = scheduler_role(
            self, "ScheduleManagerSchedulerRole",
            target_function_arns=[self.schedule_manager_function.function_arn],
        )
        scheduler.CfnSchedule(
            self, "ScheduleManagerSchedule",
            name=config.resource_name("schedule-manager"),
            description="Run Schedule Manager at 9:00 AM ET to set up today's trading schedule",
            schedule_expression="cron(0 9 ? * MON-FRI *)",
            schedule_expression_timezone="America/New_York",
            flexible_time_window=scheduler.CfnSchedule.FlexibleTimeWindowProperty(mode="OFF"),
            target=scheduler.CfnSchedule.TargetProperty(
                arn=self.schedule_manager_function.function_arn,
                role_arn=schedule_mgr_scheduler_role.role_arn,
                input='{"source": "morning_schedule"}',
                retry_policy=scheduler.CfnSchedule.RetryPolicyProperty(maximum_retry_attempts=2),
            ),
        )

        # ---- Strategy Analytics ----
        analytics_role = lambda_execution_role(
            self, "StrategyAnalyticsExecutionRole", config=config,
            policy_statements=[
                iam.PolicyStatement(
                    actions=["dynamodb:Query", "dynamodb:GetItem", "dynamodb:Scan"],
                    resources=[trade_ledger_table.table_arn, f"{trade_ledger_table.table_arn}/index/*"],
                ),
                iam.PolicyStatement(
                    actions=["s3:PutObject"],
                    resources=[f"{self.performance_reports_bucket.bucket_arn}/strategy-analytics/*"],
                ),
            ],
        )
        analytics_fn = AlchemiserFunction(
            self, "StrategyAnalyticsFunction",
            config=config,
            function_name=f"alchemiser-{config.stage}-strategy-analytics",
            code_uri="functions/strategy_analytics/",
            handler="lambda_handler.lambda_handler",
            layers=[shared_code_layer, self.strategy_layer],
            role=analytics_role,
            timeout_seconds=120,
            memory_size=1024,
            extra_env={
                "TRADE_LEDGER__TABLE_NAME": trade_ledger_table.table_name,
                "PERFORMANCE_REPORTS_BUCKET": self.performance_reports_bucket.bucket_name,
                "STAGE": config.stage,
            },
        )
        # ScheduleV2: daily at 9 PM ET
        scheduler.CfnSchedule(
            self, "StrategyAnalyticsSchedule",
            name=f"alchemiser-{config.stage}-strategy-analytics",
            schedule_expression="cron(0 21 ? * MON-FRI *)",
            schedule_expression_timezone="America/New_York",
            description="Run strategy analytics daily at 9 PM ET (after market close)",
            flexible_time_window=scheduler.CfnSchedule.FlexibleTimeWindowProperty(mode="OFF"),
            target=scheduler.CfnSchedule.TargetProperty(
                arn=analytics_fn.function.function_arn,
                role_arn=scheduler_role(
                    self, "StrategyAnalyticsSchedulerRole",
                    target_function_arns=[analytics_fn.function.function_arn],
                ).role_arn,
            ),
        )

        # ---- Strategy Reports ----
        reports_role = lambda_execution_role(
            self, "StrategyReportsExecutionRole", config=config,
            policy_statements=[
                iam.PolicyStatement(
                    actions=["s3:GetObject"],
                    resources=[f"{self.performance_reports_bucket.bucket_arn}/strategy-analytics/*"],
                ),
                iam.PolicyStatement(
                    actions=["s3:PutObject"],
                    resources=[f"{self.performance_reports_bucket.bucket_arn}/strategy-reports/*"],
                ),
            ],
        )
        reports_fn = AlchemiserFunction(
            self, "StrategyReportsFunction",
            config=config,
            function_name=f"alchemiser-{config.stage}-strategy-reports",
            code_uri="functions/strategy_reports/",
            handler="lambda_handler.lambda_handler",
            layers=[shared_code_layer, self.strategy_layer],
            role=reports_role,
            timeout_seconds=300,
            memory_size=2048,
            extra_env={
                "PERFORMANCE_REPORTS_BUCKET": self.performance_reports_bucket.bucket_name,
                "STAGE": config.stage,
            },
        )
        # ScheduleV2: daily at 9:15 PM ET
        scheduler.CfnSchedule(
            self, "StrategyReportsSchedule",
            name=f"alchemiser-{config.stage}-strategy-reports",
            schedule_expression="cron(15 21 ? * MON-FRI *)",
            schedule_expression_timezone="America/New_York",
            description="Run strategy reports daily at 9:15 PM ET (after analytics Lambda)",
            flexible_time_window=scheduler.CfnSchedule.FlexibleTimeWindowProperty(mode="OFF"),
            target=scheduler.CfnSchedule.TargetProperty(
                arn=reports_fn.function.function_arn,
                role_arn=scheduler_role(
                    self, "StrategyReportsSchedulerRole",
                    target_function_arns=[reports_fn.function.function_arn],
                ).role_arn,
            ),
        )

        # ---- CloudWatch Alarms ----
        cloudwatch.Alarm(
            self, "StrategyOrchestratorErrorsAlarm",
            alarm_name=config.resource_name("orchestrator-errors"),
            alarm_description="Alert when Strategy Orchestrator Lambda has errors (timeouts, crashes)",
            metric=self.orchestrator_function.metric_errors(
                period=Duration.seconds(60), statistic="Sum",
            ),
            threshold=1,
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
        )

        cloudwatch.Alarm(
            self, "StrategyWorkerErrorsAlarm",
            alarm_name=config.resource_name("strategy-worker-errors"),
            alarm_description="Alert when Strategy Worker Lambda has errors (timeouts, crashes)",
            metric=self.strategy_function.metric_errors(
                period=Duration.seconds(60), statistic="Sum",
            ),
            threshold=1,
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
        )

        # ---- Outputs ----
        CfnOutput(self, "PerformanceReportsBucketName",
                  value=self.performance_reports_bucket.bucket_name,
                  export_name=f"{config.prefix}-PerformanceReportsBucket")
        CfnOutput(self, "GroupHistoricalSelectionsTableName",
                  value=self.group_history_table.table_name,
                  export_name=f"{config.prefix}-GroupHistoricalSelectionsTable")
