"""Business Unit: infrastructure | Status: current.

Dashboard stack: account data Lambda and schedule for Streamlit dashboard.

Resources:
- AccountDataFunction (Lambda)
- AccountDataTable (DynamoDB, PK+SK, TTL, PITR)
- AccountDataSchedule (EventBridge Scheduler, every 6 hours)
"""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk import (
    CfnOutput,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_scheduler as scheduler,
)
from constructs import Construct

from infra.config import StageConfig
from infra.constructs import (
    AlchemiserFunction,
    alchemiser_table,
    lambda_execution_role,
    layer_from_ssm,
    scheduler_role,
)


class DashboardStack(cdk.Stack):
    """Account data ingestion for the Streamlit dashboard."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        config: StageConfig,
        **kwargs: object,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ---- Shared layers (looked up from SSM to avoid cross-stack export lock) ----
        shared_code_layer = layer_from_ssm(
            self, "SharedCodeLayer", config=config, ssm_suffix="shared-code-arn",
        )
        portfolio_layer = layer_from_ssm(
            self, "PortfolioLayer", config=config, ssm_suffix="portfolio-deps-arn",
        )

        # ---- DynamoDB Table ----
        self.account_data_table = alchemiser_table(
            self,
            "AccountDataTable",
            config=config,
            table_name_suffix="account-data",
            partition_key=dynamodb.Attribute(name="PK", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="SK", type=dynamodb.AttributeType.STRING),
            time_to_live_attribute="ExpiresAt",
            point_in_time_recovery=True,
            service_tag="account-data",
        )

        # ---- IAM Role ----
        account_data_role = lambda_execution_role(
            self,
            "AccountDataExecutionRole",
            config=config,
            policy_statements=[
                iam.PolicyStatement(
                    actions=["dynamodb:PutItem", "dynamodb:GetItem", "dynamodb:Query", "dynamodb:BatchWriteItem"],
                    resources=[self.account_data_table.table_arn],
                ),
            ],
        )

        # ---- Lambda Function ----
        account_data_fn = AlchemiserFunction(
            self,
            "AccountDataFunction",
            config=config,
            function_name=config.resource_name("account-data"),
            code_uri="functions/account_data/",
            handler="lambda_handler.handler",
            layers=[shared_code_layer, portfolio_layer],
            role=account_data_role,
            timeout_seconds=300,
            memory_size=256,
            extra_env={
                "ACCOUNT_DATA_TABLE": self.account_data_table.table_name,
            },
        )
        self.account_data_function = account_data_fn.function

        # ---- EventBridge Scheduler: every 6 hours ----
        sched_role = scheduler_role(
            self,
            "AccountDataSchedulerRole",
            target_function_arns=[self.account_data_function.function_arn],
        )

        scheduler.CfnSchedule(
            self,
            "AccountDataSchedule",
            name=config.resource_name("account-data"),
            description="Fetch account data from Alpaca every 6 hours (4 AM, 10 AM, 4 PM, 10 PM ET)",
            schedule_expression="cron(0 4,10,16,22 * * ? *)",
            schedule_expression_timezone="America/New_York",
            flexible_time_window=scheduler.CfnSchedule.FlexibleTimeWindowProperty(mode="OFF"),
            target=scheduler.CfnSchedule.TargetProperty(
                arn=self.account_data_function.function_arn,
                role_arn=sched_role.role_arn,
                input='{"source": "scheduled"}',
                retry_policy=scheduler.CfnSchedule.RetryPolicyProperty(maximum_retry_attempts=2),
            ),
        )

        # ---- Outputs ----
        CfnOutput(
            self,
            "AccountDataTableName",
            value=self.account_data_table.table_name,
            export_name=f"{config.prefix}-AccountDataTable",
            description="DynamoDB table for account data snapshots (dashboard data source)",
        )
