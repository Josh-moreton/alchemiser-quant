"""Business Unit: reporting | Status: current.

Report generator service for creating and storing PDF reports.

Orchestrates the report generation workflow:
1. Load snapshot from DynamoDB
2. Render PDF
3. Upload to S3
4. Emit ReportReady event
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime

from the_alchemiser.shared.events import EventBus, ReportReady
from the_alchemiser.shared.logging import generate_request_id, get_logger
from the_alchemiser.shared.repositories.account_snapshot_repository import (
    AccountSnapshotRepository,
)
from the_alchemiser.shared.schemas.account_snapshot import AccountSnapshot

from .renderer import ReportRenderer

logger = get_logger(__name__)

__all__ = ["ReportGeneratorService"]


class ReportGeneratorService:
    """Service for generating and storing PDF account reports."""

    def __init__(
        self,
        snapshot_repository: AccountSnapshotRepository,
        event_bus: EventBus,
        s3_bucket: str,
    ) -> None:
        """Initialize report generator service.

        Args:
            snapshot_repository: Repository for loading snapshots
            event_bus: Event bus for publishing ReportReady events
            s3_bucket: S3 bucket name for storing reports

        """
        self.snapshot_repository = snapshot_repository
        self.event_bus = event_bus
        self.s3_bucket = s3_bucket
        self.renderer = ReportRenderer()
        self._aws_account_id: str | None = None
        logger.debug("Report generator service initialized", s3_bucket=s3_bucket)

    def generate_report_from_snapshot(
        self,
        snapshot: AccountSnapshot,
        report_type: str = "account_summary",
        correlation_id: str | None = None,
    ) -> ReportReady:
        """Generate PDF report from snapshot and upload to S3.

        Args:
            snapshot: Account snapshot to generate report from
            report_type: Type of report to generate
            correlation_id: Optional correlation ID for tracing

        Returns:
            ReportReady event with report metadata

        """
        if correlation_id is None:
            correlation_id = generate_request_id()

        logger.info(
            "Generating report from snapshot",
            snapshot_id=snapshot.snapshot_id,
            report_type=report_type,
            correlation_id=correlation_id,
        )

        # Generate unique report ID
        report_id = f"report-{uuid.uuid4().hex[:12]}"

        # Render PDF
        report_metadata = {
            "report_version": "1.0",
            "report_type": report_type,
        }

        pdf_bytes, generation_metadata = self.renderer.render_pdf(
            snapshot=snapshot,
            report_metadata=report_metadata,
        )

        # Construct S3 key
        # Format: reports/{account_id}/{YYYY}/{MM}/{report_type}_{snapshot_id}_{report_id}.pdf
        period_end = snapshot.period_end
        s3_key = (
            f"reports/{snapshot.account_id}/{period_end.year:04d}/"
            f"{period_end.month:02d}/{report_type}_{snapshot.snapshot_id}_{report_id}.pdf"
        )

        # Upload to S3
        self._upload_to_s3(pdf_bytes, s3_key)

        # Build S3 URI
        s3_uri = f"s3://{self.s3_bucket}/{s3_key}"

        # Create ReportReady event
        report_ready_event = ReportReady(
            event_id=generate_request_id(),
            correlation_id=correlation_id,
            causation_id=correlation_id,
            timestamp=datetime.now(UTC),
            source_module="reporting",
            source_component="ReportGeneratorService",
            report_id=report_id,
            account_id=snapshot.account_id,
            report_type=report_type,
            period_start=snapshot.period_start.isoformat(),
            period_end=snapshot.period_end.isoformat(),
            s3_bucket=self.s3_bucket,
            s3_key=s3_key,
            s3_uri=s3_uri,
            file_size_bytes=generation_metadata["file_size_bytes"],
            generation_time_ms=generation_metadata["generation_time_ms"],
            snapshot_id=snapshot.snapshot_id,
            metadata={
                "report_version": report_metadata["report_version"],
                "snapshot_version": snapshot.snapshot_version,
            },
        )

        # Publish event
        self.event_bus.publish(report_ready_event)

        logger.info(
            "Report generated and uploaded",
            report_id=report_id,
            s3_uri=s3_uri,
            file_size_bytes=generation_metadata["file_size_bytes"],
            generation_time_ms=generation_metadata["generation_time_ms"],
        )

        return report_ready_event

    def generate_report_from_snapshot_id(
        self,
        account_id: str,
        snapshot_id: str,
        report_type: str = "account_summary",
        correlation_id: str | None = None,
    ) -> ReportReady:
        """Generate report by loading snapshot from repository.

        Args:
            account_id: Account identifier
            snapshot_id: Snapshot identifier (ISO timestamp)
            report_type: Type of report to generate
            correlation_id: Optional correlation ID for tracing

        Returns:
            ReportReady event with report metadata

        Raises:
            ValueError: If snapshot not found

        """
        logger.info(
            "Loading snapshot for report generation",
            account_id=account_id,
            snapshot_id=snapshot_id,
        )

        # Parse snapshot_id as ISO timestamp
        period_end = datetime.fromisoformat(snapshot_id)

        # Load snapshot
        snapshot = self.snapshot_repository.get_snapshot(account_id, period_end)

        if snapshot is None:
            error_msg = f"Snapshot not found: {account_id} at {snapshot_id}"
            logger.error("Snapshot not found", account_id=account_id, snapshot_id=snapshot_id)
            raise ValueError(error_msg)

        # Generate report
        return self.generate_report_from_snapshot(snapshot, report_type, correlation_id)

    def generate_report_from_latest_snapshot(
        self,
        account_id: str,
        report_type: str = "account_summary",
        correlation_id: str | None = None,
    ) -> ReportReady:
        """Generate report from the latest snapshot for an account.

        Args:
            account_id: Account identifier
            report_type: Type of report to generate
            correlation_id: Optional correlation ID for tracing

        Returns:
            ReportReady event with report metadata

        Raises:
            ValueError: If no snapshots found for account

        """
        logger.info("Loading latest snapshot for report generation", account_id=account_id)

        # Load latest snapshot
        snapshot = self.snapshot_repository.get_latest_snapshot(account_id)

        if snapshot is None:
            error_msg = f"No snapshots found for account: {account_id}"
            logger.error("No snapshots found", account_id=account_id)
            raise ValueError(error_msg)

        # Generate report
        return self.generate_report_from_snapshot(snapshot, report_type, correlation_id)

    def _get_aws_account_id(self) -> str:
        """Get AWS account ID from STS (cached).

        Returns:
            AWS account ID

        Raises:
            Exception: If unable to retrieve account ID

        """
        if self._aws_account_id is not None:
            return self._aws_account_id

        import boto3
        from botocore.exceptions import BotoCoreError, ClientError

        try:
            sts_client = boto3.client("sts")
            identity = sts_client.get_caller_identity()
            self._aws_account_id = str(identity["Account"])
            return self._aws_account_id
        except (ClientError, BotoCoreError, KeyError) as e:
            logger.error("Failed to retrieve AWS account ID", error=str(e))
            raise

    def _upload_to_s3(self, pdf_bytes: bytes, s3_key: str) -> None:
        """Upload PDF to S3 bucket.

        Args:
            pdf_bytes: PDF content as bytes
            s3_key: S3 key (path) for the object

        """
        import boto3
        from botocore.exceptions import BotoCoreError, ClientError

        logger.debug("Uploading PDF to S3", s3_key=s3_key, size_bytes=len(pdf_bytes))

        try:
            s3_client = boto3.client("s3")

            # Get AWS account ID for bucket ownership verification
            account_id = self._get_aws_account_id()

            # Calculate checksum for data integrity
            checksum = hashlib.sha256(pdf_bytes).hexdigest()

            # Upload with metadata and bucket ownership verification
            s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=s3_key,
                Body=pdf_bytes,
                ContentType="application/pdf",
                ExpectedBucketOwner=account_id,
                Metadata={
                    "sha256": checksum,
                    "generated_at": datetime.now(UTC).isoformat(),
                },
            )

            logger.info("PDF uploaded to S3", s3_key=s3_key, checksum=checksum)

        except (ClientError, BotoCoreError) as e:
            logger.error("Failed to upload PDF to S3", s3_key=s3_key, error=str(e))
            raise
