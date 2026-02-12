"""Business Unit: coordinator_v2 | Status: current.

Configuration settings for the Schedule Manager Lambda.
"""

from __future__ import annotations

import os

from pydantic import BaseModel, Field


class ScheduleManagerSettings(BaseModel):
    """Settings for the Schedule Manager Lambda from environment variables."""

    orchestrator_function_arn: str = Field(
        default="",
        description="ARN of the Strategy Orchestrator Lambda to trigger",
    )
    scheduler_role_arn: str = Field(
        default="",
        description="IAM role ARN for EventBridge Scheduler",
    )
    schedule_group_name: str = Field(
        default="default",
        description="EventBridge Scheduler group name",
    )
    minutes_before_close: int = Field(
        default=15,
        description="Minutes before market close to trigger execution",
    )
    app_stage: str = Field(
        default="dev",
        description="Application deployment stage (dev/prod)",
    )

    @classmethod
    def from_environment(cls) -> ScheduleManagerSettings:
        """Create settings from environment variables.

        Returns:
            ScheduleManagerSettings with values from environment.

        """
        return cls(
            orchestrator_function_arn=os.environ.get("ORCHESTRATOR_FUNCTION_ARN", ""),
            scheduler_role_arn=os.environ.get("SCHEDULER_ROLE_ARN", ""),
            schedule_group_name=os.environ.get("SCHEDULE_GROUP_NAME", "default"),
            minutes_before_close=int(os.environ.get("MINUTES_BEFORE_CLOSE", "15")),
            app_stage=os.environ.get("APP__STAGE", "dev"),
        )
