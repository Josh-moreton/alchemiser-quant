"""Business Unit: infrastructure | Status: current.

Hedging stack: options hedging evaluation, execution, and roll management.

Resources:
- HedgeEvaluatorFunction (Lambda)
- HedgeExecutorFunction (Lambda, SQS-triggered, reserved concurrency=3)
- HedgeRollManagerFunction (Lambda)
- HedgePositionsTable (DynamoDB, 1 GSI)
- HedgeHistoryTable (DynamoDB)
- HedgeKillSwitchTable (DynamoDB)
- IVHistoryTable (DynamoDB)
- HedgeExecutionQueue + DLQ (SQS Standard)
- AllTradesCompletedToHedge EventBridge Rule
"""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk import (
    Duration,
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
    lambda_execution_role,
    layer_from_ssm,
)


class HedgingStack(cdk.Stack):
    """Options hedging: evaluation, execution, and roll management."""

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

        # ---- Shared layers (looked up from SSM to avoid cross-stack export lock) ----
        shared_code_layer = layer_from_ssm(
            self,
            "SharedCodeLayer",
            config=config,
            ssm_suffix="shared-code-arn",
        )
        portfolio_layer = layer_from_ssm(
            self,
            "PortfolioLayer",
            config=config,
            ssm_suffix="portfolio-deps-arn",
        )
        execution_layer = layer_from_ssm(
            self,
            "ExecutionLayer",
            config=config,
            ssm_suffix="execution-deps-arn",
        )

        # ---- DynamoDB Tables ----
        self.hedge_positions_table = alchemiser_table(
            self,
            "HedgePositionsTable",
            config=config,
            table_name_suffix="hedge-positions",
            partition_key=dynamodb.Attribute(name="PK", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="SK", type=dynamodb.AttributeType.STRING),
            time_to_live_attribute="ttl",
            service_tag="hedge-positions",
            global_secondary_indexes=[
                {
                    "index_name": "GSI1-UnderlyingExpirationIndex",
                    "partition_key": dynamodb.Attribute(
                        name="GSI1PK", type=dynamodb.AttributeType.STRING
                    ),
                    "sort_key": dynamodb.Attribute(
                        name="GSI1SK", type=dynamodb.AttributeType.STRING
                    ),
                },
            ],
        )

        self.hedge_history_table = alchemiser_table(
            self,
            "HedgeHistoryTable",
            config=config,
            table_name_suffix="hedge-history",
            partition_key=dynamodb.Attribute(name="account_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(
                name="timestamp_action", type=dynamodb.AttributeType.STRING
            ),
            time_to_live_attribute="ttl",
            service_tag="hedge-history",
        )

        self.hedge_kill_switch_table = alchemiser_table(
            self,
            "HedgeKillSwitchTable",
            config=config,
            table_name_suffix="hedge-kill-switch",
            partition_key=dynamodb.Attribute(name="switch_id", type=dynamodb.AttributeType.STRING),
            service_tag="hedge-kill-switch",
        )

        self.iv_history_table = alchemiser_table(
            self,
            "IVHistoryTable",
            config=config,
            table_name_suffix="iv-history",
            partition_key=dynamodb.Attribute(
                name="underlying_symbol", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(name="record_date", type=dynamodb.AttributeType.STRING),
            time_to_live_attribute="ttl",
            service_tag="iv-history",
        )

        # ---- SQS Queues ----
        self.hedge_execution_dlq = sqs.Queue(
            self,
            "HedgeExecutionDLQ",
            queue_name=config.resource_name("hedge-execution-dlq"),
            retention_period=Duration.days(14),
        )
        self.hedge_execution_queue = sqs.Queue(
            self,
            "HedgeExecutionQueue",
            queue_name=config.resource_name("hedge-execution-queue"),
            visibility_timeout=Duration.seconds(900),
            retention_period=Duration.days(4),
            dead_letter_queue=sqs.DeadLetterQueue(
                max_receive_count=3, queue=self.hedge_execution_dlq
            ),
        )

        options_hedging_enabled = "true" if not config.is_production else "false"

        # ---- Hedge Evaluator Role ----
        evaluator_role = lambda_execution_role(
            self,
            "HedgeEvaluatorExecutionRole",
            config=config,
            policy_statements=[
                iam.PolicyStatement(
                    actions=["events:PutEvents"],
                    resources=[event_bus.event_bus_arn],
                ),
                iam.PolicyStatement(
                    actions=["sqs:SendMessage"],
                    resources=[self.hedge_execution_queue.queue_arn],
                ),
                iam.PolicyStatement(
                    actions=["dynamodb:GetItem", "dynamodb:Query"],
                    resources=[
                        self.hedge_positions_table.table_arn,
                        f"{self.hedge_positions_table.table_arn}/index/*",
                    ],
                ),
                iam.PolicyStatement(
                    actions=["dynamodb:PutItem"],
                    resources=[self.hedge_history_table.table_arn],
                ),
                iam.PolicyStatement(
                    actions=["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem"],
                    resources=[self.hedge_kill_switch_table.table_arn],
                ),
                iam.PolicyStatement(
                    actions=["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:Query"],
                    resources=[self.iv_history_table.table_arn],
                ),
            ],
        )

        # ---- Hedge Evaluator Lambda ----
        evaluator_fn = AlchemiserFunction(
            self,
            "HedgeEvaluatorFunction",
            config=config,
            function_name=config.resource_name("hedge-evaluator"),
            code_uri="functions/hedge_evaluator/",
            handler="lambda_handler.lambda_handler",
            layers=[shared_code_layer, portfolio_layer],
            role=evaluator_role,
            timeout_seconds=300,
            memory_size=512,
            extra_env={
                "OPTIONS_HEDGING_ENABLED": options_hedging_enabled,
                "EVENT_BUS_NAME": event_bus.event_bus_name,
                "HEDGE_EXECUTION_QUEUE_URL": self.hedge_execution_queue.queue_url,
                "HEDGE_POSITIONS_TABLE_NAME": self.hedge_positions_table.table_name,
                "HEDGE_HISTORY_TABLE_NAME": self.hedge_history_table.table_name,
                "HEDGE_KILL_SWITCH_TABLE": self.hedge_kill_switch_table.table_name,
                "IV_HISTORY_TABLE_NAME": self.iv_history_table.table_name,
            },
        )
        self.hedge_evaluator_function = evaluator_fn.function

        # ---- EventBridge Rule: AllTradesCompleted -> HedgeEvaluator ----
        all_trades_to_hedge_rule = events.Rule(
            self,
            "AllTradesCompletedToHedgeRule",
            rule_name=config.resource_name("trades-completed-to-hedge"),
            event_bus=event_bus,
            event_pattern=events.EventPattern(
                source=["alchemiser.trade_aggregator"],
                detail_type=["AllTradesCompleted"],
            ),
        )
        all_trades_to_hedge_rule.add_target(targets.LambdaFunction(self.hedge_evaluator_function))

        # ---- Hedge Executor Role ----
        executor_role = lambda_execution_role(
            self,
            "HedgeExecutorExecutionRole",
            config=config,
            policy_statements=[
                iam.PolicyStatement(
                    actions=["events:PutEvents"],
                    resources=[event_bus.event_bus_arn],
                ),
                iam.PolicyStatement(
                    actions=["sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes"],
                    resources=[self.hedge_execution_queue.queue_arn],
                ),
                iam.PolicyStatement(
                    actions=[
                        "dynamodb:PutItem",
                        "dynamodb:GetItem",
                        "dynamodb:UpdateItem",
                        "dynamodb:Query",
                    ],
                    resources=[
                        self.hedge_positions_table.table_arn,
                        f"{self.hedge_positions_table.table_arn}/index/*",
                    ],
                ),
                iam.PolicyStatement(
                    actions=["dynamodb:PutItem"],
                    resources=[self.hedge_history_table.table_arn],
                ),
                iam.PolicyStatement(
                    actions=["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem"],
                    resources=[self.hedge_kill_switch_table.table_arn],
                ),
            ],
        )

        # ---- Hedge Executor Lambda ----
        executor_fn = AlchemiserFunction(
            self,
            "HedgeExecutorFunction",
            config=config,
            function_name=config.resource_name("hedge-executor"),
            code_uri="functions/hedge_executor/",
            handler="lambda_handler.lambda_handler",
            layers=[shared_code_layer, execution_layer],
            role=executor_role,
            timeout_seconds=600,
            memory_size=1024,
            reserved_concurrent_executions=3,
            extra_env={
                "OPTIONS_HEDGING_ENABLED": options_hedging_enabled,
                "EVENT_BUS_NAME": event_bus.event_bus_name,
                "HEDGE_POSITIONS_TABLE_NAME": self.hedge_positions_table.table_name,
                "HEDGE_HISTORY_TABLE_NAME": self.hedge_history_table.table_name,
                "HEDGE_KILL_SWITCH_TABLE": self.hedge_kill_switch_table.table_name,
            },
        )
        self.hedge_executor_function = executor_fn.function

        # SQS event source
        self.hedge_executor_function.add_event_source(
            event_sources.SqsEventSource(
                self.hedge_execution_queue,
                batch_size=1,
                report_batch_item_failures=True,
            )
        )

        # ---- Hedge Roll Manager Role ----
        roll_mgr_role = lambda_execution_role(
            self,
            "HedgeRollManagerExecutionRole",
            config=config,
            policy_statements=[
                iam.PolicyStatement(
                    actions=["events:PutEvents"],
                    resources=[event_bus.event_bus_arn],
                ),
                iam.PolicyStatement(
                    actions=["sqs:SendMessage"],
                    resources=[self.hedge_execution_queue.queue_arn],
                ),
                iam.PolicyStatement(
                    actions=["dynamodb:GetItem", "dynamodb:Query", "dynamodb:Scan"],
                    resources=[
                        self.hedge_positions_table.table_arn,
                        f"{self.hedge_positions_table.table_arn}/index/*",
                    ],
                ),
                iam.PolicyStatement(
                    actions=["dynamodb:PutItem"],
                    resources=[self.hedge_history_table.table_arn],
                ),
            ],
        )

        # ---- Hedge Roll Manager Lambda ----
        roll_mgr_fn = AlchemiserFunction(
            self,
            "HedgeRollManagerFunction",
            config=config,
            function_name=config.resource_name("hedge-roll-manager"),
            code_uri="functions/hedge_roll_manager/",
            handler="lambda_handler.lambda_handler",
            layers=[shared_code_layer, portfolio_layer],
            role=roll_mgr_role,
            timeout_seconds=300,
            memory_size=512,
            extra_env={
                "OPTIONS_HEDGING_ENABLED": options_hedging_enabled,
                "EVENT_BUS_NAME": event_bus.event_bus_name,
                "HEDGE_EXECUTION_QUEUE_URL": self.hedge_execution_queue.queue_url,
                "HEDGE_POSITIONS_TABLE_NAME": self.hedge_positions_table.table_name,
                "HEDGE_HISTORY_TABLE_NAME": self.hedge_history_table.table_name,
            },
        )
        # HedgeRollManager uses SAM Schedule (not ScheduleV2), which maps to events.Rule
        events.Rule(
            self,
            "HedgeRollManagerDailyCheck",
            schedule=events.Schedule.cron(minute="45", hour="19", week_day="MON-FRI"),
            description="Daily hedge roll check (~3:45 PM ET, see comment for timezone note)",
            targets=[targets.LambdaFunction(roll_mgr_fn.function)],
        )
