"""Business Unit: strategy_reports | Status: current.

Lambda handler for Strategy Reports microservice.

Reads daily returns Parquet files written by the Strategy Analytics
Lambda and generates quantstats HTML tearsheet reports per strategy.
Reports are written to S3 under the ``strategy-reports/`` prefix.

Triggered daily by EventBridge schedule, running after the analytics
Lambda has completed.
"""

from __future__ import annotations

import io
import json
import os
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import boto3
import pandas as pd
import quantstats as qs

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


def _read_daily_returns(
    s3_client: S3Client,
    bucket: str,
    strategy_name: str,
) -> pd.Series | None:
    """Read daily returns Parquet for a strategy and return as a pd.Series."""
    key = f"{S3_ANALYTICS_PREFIX}/{strategy_name}/daily_returns.parquet"
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        buf = io.BytesIO(response["Body"].read())
        df = pd.read_parquet(buf)

        if df.empty or "pnl" not in df.columns or "date" not in df.columns:
            return None

        df["date"] = pd.to_datetime(df["date"], utc=True)
        df = df.set_index("date").sort_index()

        series: pd.Series = df["pnl"]
        return series

    except s3_client.exceptions.NoSuchKey:
        logger.warning("No daily returns found", extra={"strategy": strategy_name})
        return None
    except Exception:
        logger.exception("Failed to read daily returns", extra={"strategy": strategy_name})
        return None


def _generate_tearsheet_html(
    returns: pd.Series,
    strategy_name: str,
) -> str | None:
    """Generate a quantstats HTML tearsheet string from daily P&L series.

    quantstats expects a returns series (percentage or dollar). We pass
    dollar P&L as-is -- the tearsheet will show absolute metrics.
    """
    if returns is None or len(returns) < 5:
        logger.info(
            "Insufficient data for tearsheet",
            extra={"strategy": strategy_name, "points": len(returns) if returns is not None else 0},
        )
        return None

    try:
        html = qs.reports.html(
            returns,
            title=strategy_name,
            output=None,  # Return HTML string instead of writing file
            download_filename=None,
        )
        return str(html)
    except Exception:
        logger.exception(
            "quantstats tearsheet generation failed",
            extra={"strategy": strategy_name},
        )
        return None


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


def _process_strategy_report(
    s3_client: S3Client,
    bucket_name: str,
    strategy_name: str,
) -> bool:
    """Generate and write a tearsheet report for a single strategy.

    Args:
        s3_client: Boto3 S3 client.
        bucket_name: S3 bucket for output.
        strategy_name: Name of the strategy.

    Returns:
        True if a report was generated, False otherwise.

    """
    returns = _read_daily_returns(s3_client, bucket_name, strategy_name)
    if returns is None:
        return False

    html = _generate_tearsheet_html(returns, strategy_name)
    if html is None:
        return False

    report_key = f"{S3_REPORTS_PREFIX}/{strategy_name}/tearsheet.html"
    s3_client.put_object(
        Bucket=bucket_name,
        Key=report_key,
        Body=html.encode("utf-8"),
        ContentType="text/html",
    )

    logger.info(
        "Tearsheet written",
        extra={"strategy": strategy_name, "key": report_key},
    )
    return True


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
    """Generate quantstats HTML tearsheet reports for each strategy.

    Reads the analytics manifest, fetches each strategy's daily returns
    Parquet from S3, generates a quantstats tearsheet, and writes the
    HTML report back to S3.

    Args:
        event: Lambda event (EventBridge schedule or direct invoke).
        context: Lambda context.

    Returns:
        Response with report generation count.

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
        return {"statusCode": 200, "body": {"reports_generated": 0}}

    reports_generated = 0

    for strategy_name in strategy_names:
        try:
            if _process_strategy_report(s3_client, bucket_name, strategy_name):
                reports_generated += 1
        except Exception:
            logger.exception(
                "Failed to generate report",
                extra={"strategy": strategy_name},
            )

    _write_reports_manifest(
        s3_client, bucket_name, run_id, run_timestamp, stage,
        reports_generated, strategy_names,
    )

    logger.info(
        "Strategy reports run complete",
        extra={"run_id": run_id, "reports": reports_generated},
    )

    return {
        "statusCode": 200,
        "body": {
            "run_id": run_id,
            "reports_generated": reports_generated,
        },
    }
