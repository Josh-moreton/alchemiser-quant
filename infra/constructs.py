"""Business Unit: infrastructure | Status: current.

Reusable CDK constructs shared across all Alchemiser stacks.

Provides:
- AlchemiserFunction: Lambda function with default settings
- alchemiser_table: DynamoDB table factory with standard settings
- LocalShellBundling: Docker-free local bundling for Lambda layers
- standard_tags: Tag helper matching current naming conventions
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import aws_cdk as cdk
import jsii
from aws_cdk import (
    Duration,
    RemovalPolicy,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    aws_lambda as _lambda,
)
from constructs import Construct

from infra.config import StageConfig

# Resolve pip from the running interpreter's venv so local bundling
# works even when 'pip' is not on the system PATH.
_VENV_PIP = str(Path(sys.executable).parent / "pip")


@jsii.implements(cdk.ILocalBundling)
class LocalShellBundling:
    """Run layer build commands locally, avoiding Docker dependency.

    The shell command should use '/asset-output' as the output directory
    placeholder -- it will be replaced with the actual CDK output path at
    bundle time.  Bare 'pip' references are automatically rewritten to the
    venv-resolved pip so builds succeed without Docker.
    """

    def __init__(self, command: str) -> None:
        self._command = command

    def try_bundle(self, output_dir: str, options: Any = None) -> bool:
        """Execute the build command locally, return True on success."""
        cmd = self._command.replace("/asset-output", output_dir)
        # Replace bare 'pip install' with venv pip so it works without
        # pip on the system PATH.
        if shutil.which("pip") is None:
            cmd = cmd.replace("pip install", f"{_VENV_PIP} install")
        result = subprocess.run(  # noqa: S603
            ["bash", "-c", cmd],
            check=False,
        )
        return result.returncode == 0

PYTHON_RUNTIME = _lambda.Runtime.PYTHON_3_12
X86_64 = _lambda.Architecture.X86_64


class AlchemiserFunction(Construct):
    """Lambda function with Alchemiser defaults.

    Applies:
    - python3.12, x86_64
    - 900s timeout / 512 MB (overridable)
    - global env vars from StageConfig
    - standard tags
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        config: StageConfig,
        function_name: str,
        code_uri: str,
        handler: str,
        layers: list[_lambda.ILayerVersion],
        role: iam.IRole,
        timeout_seconds: int = 900,
        memory_size: int = 512,
        reserved_concurrent_executions: int | None = None,
        extra_env: dict[str, str] | None = None,
    ) -> None:
        super().__init__(scope, construct_id)

        env_vars = {**config.global_env_vars}
        if extra_env:
            env_vars.update(extra_env)

        self.function = _lambda.Function(
            self,
            "Fn",
            function_name=function_name,
            runtime=PYTHON_RUNTIME,
            architecture=X86_64,
            code=_lambda.Code.from_asset(
                code_uri,
                exclude=[
                    ".mypy_cache",
                    "__pycache__",
                    "*.pyc",
                    ".pytest_cache",
                    "*.egg-info",
                ],
            ),
            handler=handler,
            role=role,
            layers=layers,
            timeout=Duration.seconds(timeout_seconds),
            memory_size=memory_size,
            reserved_concurrent_executions=reserved_concurrent_executions,
            environment=env_vars,
        )

        cdk.Tags.of(self.function).add("Environment", config.stage)

    @property
    def function_arn(self) -> str:
        return self.function.function_arn

    @property
    def function_name_attr(self) -> str:
        return self.function.function_name


def alchemiser_table(
    scope: Construct,
    construct_id: str,
    *,
    config: StageConfig,
    table_name_suffix: str,
    partition_key: dynamodb.Attribute,
    sort_key: dynamodb.Attribute | None = None,
    time_to_live_attribute: str | None = None,
    point_in_time_recovery: bool = False,
    removal_policy: RemovalPolicy = RemovalPolicy.RETAIN,
    service_tag: str = "",
    global_secondary_indexes: list[dict[str, Any]] | None = None,
) -> dynamodb.Table:
    """Create a standard Alchemiser DynamoDB table.

    Matches the current template.yaml conventions:
    - PAY_PER_REQUEST billing
    - SSE enabled (AWS-managed)
    - Environment + Service tags
    """
    table = dynamodb.Table(
        scope,
        construct_id,
        table_name=config.resource_name(table_name_suffix),
        billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
        partition_key=partition_key,
        sort_key=sort_key,
        time_to_live_attribute=time_to_live_attribute,
        point_in_time_recovery=point_in_time_recovery,
        encryption=dynamodb.TableEncryption.AWS_MANAGED,
        removal_policy=removal_policy,
    )

    cdk.Tags.of(table).add("Environment", config.stage)
    if service_tag:
        cdk.Tags.of(table).add("Service", service_tag)

    if global_secondary_indexes:
        for gsi in global_secondary_indexes:
            table.add_global_secondary_index(
                index_name=gsi["index_name"],
                partition_key=gsi["partition_key"],
                sort_key=gsi.get("sort_key"),
                projection_type=gsi.get("projection_type", dynamodb.ProjectionType.ALL),
            )

    return table


def lambda_execution_role(
    scope: Construct,
    construct_id: str,
    *,
    config: StageConfig,
    policy_statements: list[iam.PolicyStatement],
    role_name: str | None = None,
) -> iam.Role:
    """Create an IAM execution role for a Lambda function.

    Includes AWSLambdaBasicExecutionRole managed policy and custom inline policy.
    """
    role = iam.Role(
        scope,
        construct_id,
        assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
        managed_policies=[
            iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
        ],
        role_name=role_name,
    )

    if policy_statements:
        role.attach_inline_policy(
            iam.Policy(
                scope,
                f"{construct_id}Policy",
                statements=policy_statements,
            )
        )

    cdk.Tags.of(role).add("Environment", config.stage)
    return role


def scheduler_role(
    scope: Construct,
    construct_id: str,
    *,
    target_function_arns: list[str],
) -> iam.Role:
    """Create an IAM role for EventBridge Scheduler to invoke Lambda functions."""
    role = iam.Role(
        scope,
        construct_id,
        assumed_by=iam.ServicePrincipal("scheduler.amazonaws.com"),
    )
    role.add_to_policy(
        iam.PolicyStatement(
            actions=["lambda:InvokeFunction"],
            resources=target_function_arns,
        )
    )
    return role
