"""Business Unit: scripts | Status: current.

S3 upload service for QuantStats reports.

Uploads HTML tearsheet reports to S3 and generates presigned URLs
for email distribution.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger(__name__)

# Presigned URL expiry (7 days in seconds)
PRESIGNED_URL_EXPIRY = 7 * 24 * 60 * 60


@dataclass
class UploadResult:
    """Result of S3 upload operation."""

    success: bool
    s3_key: str | None
    presigned_url: str | None
    error_message: str | None


@dataclass
class ManifestEntry:
    """Entry in the reports manifest."""

    s3_key: str
    presigned_url: str


@dataclass
class ReportsManifest:
    """Manifest of generated reports with URLs."""

    generated_at: str
    period_start: str | None
    period_end: str | None
    benchmark: str
    portfolio: ManifestEntry | None = None
    strategies: dict[str, ManifestEntry] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


class S3Uploader:
    """Uploads reports to S3 and generates presigned URLs.

    Handles HTML report uploads and manifest file creation
    for the QuantStats GitHub Action workflow.
    """

    def __init__(
        self,
        bucket_name: str,
        region: str = "us-east-1",
        url_expiry: int = PRESIGNED_URL_EXPIRY,
    ) -> None:
        """Initialize the S3 uploader.

        Args:
            bucket_name: S3 bucket name for reports
            region: AWS region
            url_expiry: Presigned URL expiry in seconds (default 7 days)

        """
        self._bucket = bucket_name
        self._region = region
        self._url_expiry = url_expiry

        # Configure S3 client with signature v4 for presigned URLs
        config = Config(signature_version="s3v4", region_name=region)
        self._s3 = boto3.client("s3", config=config)
        logger.info(f"S3Uploader initialized for bucket: {bucket_name}")

    def _get_date_prefix(self) -> str:
        """Get date-based prefix for S3 keys.

        Returns:
            Date string in YYYY-MM-DD format

        """
        return datetime.now(UTC).strftime("%Y-%m-%d")

    def upload_report(
        self,
        html_content: str,
        report_name: str,
        content_type: str = "text/html",
    ) -> UploadResult:
        """Upload an HTML report to S3.

        Args:
            html_content: HTML content to upload
            report_name: Name of the report (used in S3 key)
            content_type: MIME type for the content

        Returns:
            UploadResult with S3 key and presigned URL

        """
        date_prefix = self._get_date_prefix()
        s3_key = f"quantstats/{date_prefix}/{report_name}.html"

        logger.info(f"Uploading report to s3://{self._bucket}/{s3_key}")

        try:
            # Upload to S3
            self._s3.put_object(
                Bucket=self._bucket,
                Key=s3_key,
                Body=html_content.encode("utf-8"),
                ContentType=content_type,
            )

            # Generate presigned URL
            presigned_url = self._s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": self._bucket, "Key": s3_key},
                ExpiresIn=self._url_expiry,
            )

            logger.info(f"Successfully uploaded {report_name} to S3")
            return UploadResult(
                success=True,
                s3_key=s3_key,
                presigned_url=presigned_url,
                error_message=None,
            )

        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to upload {report_name}: {e}")
            return UploadResult(
                success=False,
                s3_key=None,
                presigned_url=None,
                error_message=str(e),
            )

    def upload_strategy_report(
        self,
        html_content: str,
        strategy_name: str,
    ) -> UploadResult:
        """Upload a strategy-specific tearsheet report.

        Args:
            html_content: HTML content to upload
            strategy_name: Name of the strategy

        Returns:
            UploadResult with S3 key and presigned URL

        """
        report_name = f"strategy_{strategy_name}"
        return self.upload_report(html_content, report_name)

    def upload_portfolio_report(
        self,
        html_content: str,
    ) -> UploadResult:
        """Upload the portfolio tearsheet report.

        Args:
            html_content: HTML content to upload

        Returns:
            UploadResult with S3 key and presigned URL

        """
        return self.upload_report(html_content, "portfolio_tearsheet")

    def upload_manifest(
        self,
        manifest: ReportsManifest,
    ) -> UploadResult:
        """Upload the reports manifest JSON.

        Args:
            manifest: ReportsManifest with all report URLs

        Returns:
            UploadResult for the manifest file

        """
        date_prefix = self._get_date_prefix()
        s3_key = f"quantstats/{date_prefix}/manifest.json"

        # Convert to JSON-serializable dict
        manifest_dict = {
            "generated_at": manifest.generated_at,
            "period_start": manifest.period_start,
            "period_end": manifest.period_end,
            "benchmark": manifest.benchmark,
            "reports": {
                "portfolio": None,
                "strategies": {},
            },
            "errors": manifest.errors,
        }

        if manifest.portfolio:
            manifest_dict["reports"]["portfolio"] = {
                "s3_key": manifest.portfolio.s3_key,
                "presigned_url": manifest.portfolio.presigned_url,
            }

        for strategy_name, entry in manifest.strategies.items():
            manifest_dict["reports"]["strategies"][strategy_name] = {
                "s3_key": entry.s3_key,
                "presigned_url": entry.presigned_url,
            }

        json_content = json.dumps(manifest_dict, indent=2)

        logger.info(f"Uploading manifest to s3://{self._bucket}/{s3_key}")

        try:
            self._s3.put_object(
                Bucket=self._bucket,
                Key=s3_key,
                Body=json_content.encode("utf-8"),
                ContentType="application/json",
            )

            presigned_url = self._s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": self._bucket, "Key": s3_key},
                ExpiresIn=self._url_expiry,
            )

            logger.info("Successfully uploaded manifest to S3")
            return UploadResult(
                success=True,
                s3_key=s3_key,
                presigned_url=presigned_url,
                error_message=None,
            )

        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to upload manifest: {e}")
            return UploadResult(
                success=False,
                s3_key=None,
                presigned_url=None,
                error_message=str(e),
            )

    def get_latest_manifest(self) -> ReportsManifest | None:
        """Retrieve the latest reports manifest from S3.

        Returns:
            ReportsManifest if found, None otherwise

        """
        date_prefix = self._get_date_prefix()
        s3_key = f"quantstats/{date_prefix}/manifest.json"

        try:
            response = self._s3.get_object(Bucket=self._bucket, Key=s3_key)
            content = response["Body"].read().decode("utf-8")
            data = json.loads(content)

            manifest = ReportsManifest(
                generated_at=data.get("generated_at", ""),
                period_start=data.get("period_start"),
                period_end=data.get("period_end"),
                benchmark=data.get("benchmark", "SPY"),
                errors=data.get("errors", []),
            )

            # Parse portfolio entry
            portfolio_data = data.get("reports", {}).get("portfolio")
            if portfolio_data:
                manifest.portfolio = ManifestEntry(
                    s3_key=portfolio_data["s3_key"],
                    presigned_url=portfolio_data["presigned_url"],
                )

            # Parse strategy entries
            strategies_data = data.get("reports", {}).get("strategies", {})
            for name, entry_data in strategies_data.items():
                manifest.strategies[name] = ManifestEntry(
                    s3_key=entry_data["s3_key"],
                    presigned_url=entry_data["presigned_url"],
                )

            return manifest

        except self._s3.exceptions.NoSuchKey:
            logger.info(f"No manifest found at {s3_key}")
            return None
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to get manifest: {e}")
            return None
