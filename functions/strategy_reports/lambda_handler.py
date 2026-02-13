"""Business Unit: strategy_reports | Status: current.

Lambda handler for Strategy Reports microservice.

Placeholder for future tearsheet generation. quantstats is too large
for the Lambda layer (>250 MB unzipped), so tearsheet generation is
performed locally via dashboard scripts instead.

Currently this Lambda reads the analytics manifest and writes a
reports manifest echoing the available strategies so the dashboard
can discover them.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import boto3

from the_alchemiser.shared.logging import configure_application_logging, get_logger

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client

configure_application_logging()
logger = get_logger(__name__)

S3_ANALYTICS_PREFIX = "strategy-analytics"
S3_REPORTS_PREFIX = "strategy-reports"


def _read_manifest(s3_client: S3Client, bucket: str) -> dict[str, Any]:
    """Read the analytics manifest to discover available strategies."""
    try:
        response = s3_client.get_object(
            Bucket=bucket,
            Key=f"{S3_ANALYTICS_PREFIX}/_manifest.json",
        )
        return json.loads(response["Body"].read().decode("utf-8"))  # type: ignore[no-any-return]
    except s3_client.exceptions.NoSuchKey:
        logger.warning("No analytics manifest found -- has analytics Lambda run?")
        return {}
    except Exception:
        logger.exception("Failed to read analytics manifest")
        return {}


def _validate_reports_config() -> tuple[str, str]:
    """Validate and return reports configuration from environment.

    Returns:
        Tuple of (bucket_name, stage).

    Raises:
        ValueError: If required environment variables are missing.

    """
    bucket_name = os.environ.get("PERFORMANCE_REPORTS_BUCKET", "")
    stage = os.environ.get("STAGE", "dev")

    if not bucket_name:
        raise ValueError("Missing PERFORMANCE_REPORTS_BUCKET")
    return bucket_name, stage


def _write_reports_manifest(
    s3_client: S3Client,
    bucket_name: str,
    run_id: str,
    run_timestamp: str,
    stage: str,
    reports_generated: int,
    strategy_names: list[str],
) -> None:
    """Write the reports manifest to S3."""
    reports_manifest = {
        "run_id": run_id,
        "run_timestamp": run_timestamp,
        "stage": stage,
        "reports_generated": reports_generated,
        "strategy_names": strategy_names,
    }
    s3_client.put_object(
        Bucket=bucket_name,
        Key=f"{S3_REPORTS_PREFIX}/_manifest.json",
        Body=json.dumps(reports_manifest, default=str).encode("utf-8"),
        ContentType="application/json",
    )


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Write a reports manifest echoing available strategies.

    Tearsheet generation via quantstats is handled locally (the
    library exceeds Lambda layer size limits). This handler reads
    the analytics manifest and writes a reports manifest so the
    dashboard can discover which strategies have data.

    Args:
        event: Lambda event (EventBridge schedule or direct invoke).
        context: Lambda context.

    Returns:
        Response with strategy count.

    """
    run_id = str(uuid.uuid4())[:8]
    run_timestamp = datetime.now(UTC).isoformat()

    try:
        bucket_name, stage = _validate_reports_config()
    except ValueError:
        logger.error("Missing PERFORMANCE_REPORTS_BUCKET environment variable")
        return {"statusCode": 500, "body": {"error": "Missing configuration"}}

    logger.info(
        "Strategy reports run starting",
        extra={"run_id": run_id, "stage": stage},
    )

    s3_client = boto3.client("s3")

    manifest = _read_manifest(s3_client, bucket_name)
    strategy_names: list[str] = manifest.get("strategy_names", [])

    if not strategy_names:
        logger.warning("No strategies in manifest -- nothing to report")
        return {"statusCode": 200, "body": {"strategies": 0}}

    _write_reports_manifest(
        s3_client,
        bucket_name,
        run_id,
        run_timestamp,
        stage,
        len(strategy_names),
        strategy_names,
    )

    logger.info(
        "Strategy reports manifest written",
        extra={"run_id": run_id, "strategies": len(strategy_names)},
    )

    return {
        "statusCode": 200,
        "body": {
            "run_id": run_id,
            "strategies": len(strategy_names),
        },
    }
