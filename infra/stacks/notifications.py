"""Business Unit: infrastructure | Status: current.

Notifications stack: email notifications via SES, triggered by EventBridge rules.

Resources:
- NotificationsFunction (Lambda)
- 8 EventBridge Rules routing domain events to NotificationsFunction
- NotificationsErrorsAlarm (CloudWatch)
"""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk import (
    aws_cloudwatch as cloudwatch,
    aws_dynamodb as dynamodb,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_s3 as s3,
)
from constructs import Construct

from infra.config import StageConfig
from infra.constructs import AlchemiserFunction, lambda_execution_role, layer_from_ssm


class NotificationsStack(cdk.Stack):
    """Notifications: SES email delivery triggered by EventBridge domain events."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        config: StageConfig,
        event_bus: events.IEventBus,
        trade_ledger_table: dynamodb.ITable,
        execution_runs_table: dynamodb.ITable,
        performance_reports_bucket: s3.IBucket,
        **kwargs: object,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ---- Shared layers (looked up from SSM to avoid cross-stack export lock) ----
        shared_code_layer = layer_from_ssm(
            self, "SharedCodeLayer", config=config, ssm_suffix="shared-code-arn",
        )
        notifications_layer = layer_from_ssm(
            self, "NotificationsLayer", config=config, ssm_suffix="notifications-deps-arn",
        )

        # ---- IAM Role ----
        notifications_role = lambda_execution_role(
            self,
            "NotificationsExecutionRole",
            config=config,
            policy_statements=[
                iam.PolicyStatement(
                    actions=["events:PutEvents"],
                    resources=[event_bus.event_bus_arn],
                ),
                iam.PolicyStatement(
                    actions=["dynamodb:Query", "dynamodb:GetItem", "dynamodb:Scan"],
                    resources=[
                        trade_ledger_table.table_arn,
                        f"{trade_ledger_table.table_arn}/index/*",
                    ],
                ),
                iam.PolicyStatement(
                    actions=["s3:PutObject", "s3:GetObject"],
                    resources=[f"{performance_reports_bucket.bucket_arn}/*"],
                ),
                # SES permissions for email sending
                iam.PolicyStatement(
                    actions=["ses:SendEmail", "ses:SendRawEmail"],
                    resources=["*"],
                ),
                # Notification session: read strategy results, claim lock, mark sent
                iam.PolicyStatement(
                    actions=["dynamodb:GetItem", "dynamodb:UpdateItem", "dynamodb:Query"],
                    resources=[execution_runs_table.table_arn],
                ),
            ],
        )

        allow_real_emails = "true" if config.is_production else "false"

        # ---- Notifications Lambda ----
        notifications_fn = AlchemiserFunction(
            self,
            "NotificationsFunction",
            config=config,
            function_name=config.resource_name("notifications"),
            code_uri="functions/notifications/",
            handler="lambda_handler.lambda_handler",
            layers=[shared_code_layer, notifications_layer],
            role=notifications_role,
            timeout_seconds=60,
            memory_size=512,
            extra_env={
                "EVENT_BUS_NAME": event_bus.event_bus_name,
                "PERFORMANCE_REPORTS_BUCKET": performance_reports_bucket.bucket_name,
                "TRADE_LEDGER__TABLE_NAME": trade_ledger_table.table_name,
                "STACK_NAME": config.prefix,
                "SES_FROM_ADDRESS": "noreply@mail.octarine.capital",
                "SES_FROM_NAME": "Octarine Capital",
                "SES_REPLY_TO_ADDRESS": "noreply@mail.octarine.capital",
                "SES_REGION": cdk.Aws.REGION,
                "NOTIFICATION_EMAIL": config.resolved_notification_email,
                "ALLOW_REAL_EMAILS": allow_real_emails,
                "EXECUTION_RUNS_TABLE_NAME": execution_runs_table.table_name,
            },
        )
        self.notifications_function = notifications_fn.function

        # ---- EventBridge Rules ----
        # 1. AllStrategiesCompleted
        _domain_rule(
            self, "AllStrategiesCompletedRule",
            config=config,
            event_bus=event_bus,
            target=self.notifications_function,
            source=["alchemiser.coordinator"],
            detail_type=["AllStrategiesCompleted"],
        )

        # 2. AllTradesCompleted
        _domain_rule(
            self, "AllTradesCompletedRule",
            config=config,
            event_bus=event_bus,
            target=self.notifications_function,
            source=["alchemiser.trade_aggregator"],
            detail_type=["AllTradesCompleted"],
        )

        # 3. WorkflowFailed (prefix match - any alchemiser.* source)
        workflow_failed_rule = events.Rule(
            self,
            "WorkflowFailedRule",
            rule_name=config.resource_name("workflow-failed-to-notifications"),
            event_bus=event_bus,
            event_pattern=events.EventPattern(
                source=events.Match.prefix("alchemiser."),
                detail_type=["WorkflowFailed"],
            ),
        )
        workflow_failed_rule.add_target(targets.LambdaFunction(self.notifications_function))

        # 4. HedgeEvaluationCompleted
        _domain_rule(
            self, "HedgeEvaluationCompletedRule",
            config=config,
            event_bus=event_bus,
            target=self.notifications_function,
            source=["alchemiser.hedge"],
            detail_type=["HedgeEvaluationCompleted"],
        )

        # 5. DataLakeUpdateCompleted
        _domain_rule(
            self, "DataLakeUpdateCompletedRule",
            config=config,
            event_bus=event_bus,
            target=self.notifications_function,
            source=["alchemiser.data"],
            detail_type=["DataLakeUpdateCompleted"],
        )

        # 6. ScheduleCreated
        _domain_rule(
            self, "ScheduleCreatedRule",
            config=config,
            event_bus=event_bus,
            target=self.notifications_function,
            source=["alchemiser.coordinator"],
            detail_type=["ScheduleCreated"],
        )

        # 7. Lambda async invocation failures (Lambda Destinations)
        _domain_rule(
            self, "LambdaAsyncFailureRule",
            config=config,
            event_bus=event_bus,
            target=self.notifications_function,
            source=["lambda"],
            detail_type=["Lambda Function Invocation Result - Failure"],
        )

        # 8. CloudWatch Alarm State Changes (default bus, not custom event bus)
        alarm_rule = events.Rule(
            self,
            "CloudWatchAlarmRule",
            rule_name=config.resource_name("cw-alarm-to-notifications"),
            # CloudWatch alarms publish to the DEFAULT EventBridge bus
            event_pattern=events.EventPattern(
                source=["aws.cloudwatch"],
                detail_type=["CloudWatch Alarm State Change"],
                detail={
                    "alarmName": [{"prefix": "alch-"}],
                    "state": {"value": ["ALARM"]},
                },
            ),
        )
        alarm_rule.add_target(targets.LambdaFunction(self.notifications_function))

        # ---- CloudWatch Alarm ----
        cloudwatch.Alarm(
            self,
            "NotificationsErrorsAlarm",
            alarm_name=config.resource_name("notifications-errors"),
            alarm_description="CRITICAL: Alert when Notifications Lambda fails (notifications won't be sent)",
            metric=self.notifications_function.metric_errors(period=cdk.Duration.minutes(5)),
            evaluation_periods=1,
            threshold=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
        )


def _domain_rule(
    scope: Construct,
    construct_id: str,
    *,
    config: StageConfig,
    event_bus: events.IEventBus,
    target: _lambda.IFunction,
    source: list[str],
    detail_type: list[str],
) -> events.Rule:
    """Helper to create a simple EventBridge rule on the custom event bus."""
    rule = events.Rule(
        scope,
        construct_id,
        event_bus=event_bus,
        event_pattern=events.EventPattern(
            source=source,
            detail_type=detail_type,
        ),
    )
    rule.add_target(targets.LambdaFunction(target))
    return rule
