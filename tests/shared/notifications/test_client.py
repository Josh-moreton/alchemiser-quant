#!/usr/bin/env python3
"""Test suite for shared/notifications/client.py.

Tests EmailClient for:
- Cognitive complexity reduction in send_notification
- ExpectedBucketOwner parameter for S3 security
- Helper method functionality
- S3 URI parsing
- Error handling
"""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from the_alchemiser.shared.notifications.client import EmailClient
from the_alchemiser.shared.schemas.notifications import EmailCredentials


class TestEmailClientHelpers:
    """Test suite for EmailClient helper methods."""

    @pytest.fixture
    def email_client(self):
        """Create EmailClient instance for testing."""
        return EmailClient()

    def test_parse_s3_uri_valid(self, email_client):
        """Test parsing valid S3 URI."""
        result = email_client._parse_s3_uri("s3://my-bucket/path/to/file.pdf")
        assert result is not None
        assert result == ("my-bucket", "path/to/file.pdf")

    def test_parse_s3_uri_invalid_scheme(self, email_client):
        """Test parsing S3 URI with invalid scheme."""
        result = email_client._parse_s3_uri("http://my-bucket/path/to/file.pdf")
        assert result is None

    def test_parse_s3_uri_missing_key(self, email_client):
        """Test parsing S3 URI with missing key."""
        result = email_client._parse_s3_uri("s3://my-bucket")
        assert result is None

    def test_parse_s3_uri_empty(self, email_client):
        """Test parsing empty S3 URI."""
        result = email_client._parse_s3_uri("")
        assert result is None


class TestEmailClientS3Security:
    """Test suite for S3 security improvements."""

    @pytest.fixture
    def email_client(self):
        """Create EmailClient instance for testing."""
        return EmailClient()

    @pytest.fixture
    def mock_s3_client(self):
        """Create mock S3 client."""
        mock_client = Mock()
        mock_response = {"Body": Mock()}
        mock_response["Body"].read.return_value = b"test content"
        mock_client.get_object.return_value = mock_response
        return mock_client

    def test_download_s3_file_with_expected_bucket_owner(self, email_client, mock_s3_client):
        """Test S3 download with ExpectedBucketOwner parameter."""
        result = email_client._download_s3_file(
            s3_client=mock_s3_client,
            bucket="test-bucket",
            key="test-key",
            s3_uri="s3://test-bucket/test-key",
            expected_bucket_owner="123456789012",
        )

        assert result == b"test content"
        mock_s3_client.get_object.assert_called_once_with(
            Bucket="test-bucket", Key="test-key", ExpectedBucketOwner="123456789012"
        )

    def test_download_s3_file_without_expected_bucket_owner(self, email_client, mock_s3_client):
        """Test S3 download without ExpectedBucketOwner parameter."""
        result = email_client._download_s3_file(
            s3_client=mock_s3_client,
            bucket="test-bucket",
            key="test-key",
            s3_uri="s3://test-bucket/test-key",
            expected_bucket_owner=None,
        )

        assert result == b"test content"
        mock_s3_client.get_object.assert_called_once_with(Bucket="test-bucket", Key="test-key")

    def test_download_s3_file_client_error(self, email_client):
        """Test S3 download with ClientError."""
        from botocore.exceptions import ClientError

        mock_client = Mock()
        mock_client.get_object.side_effect = ClientError(
            error_response={"Error": {"Code": "NoSuchKey", "Message": "Key not found"}},
            operation_name="GetObject",
        )

        result = email_client._download_s3_file(
            s3_client=mock_client,
            bucket="test-bucket",
            key="test-key",
            s3_uri="s3://test-bucket/test-key",
            expected_bucket_owner=None,
        )

        assert result is None


class TestEmailClientSendNotification:
    """Test suite for send_notification method."""

    @pytest.fixture
    def email_client(self):
        """Create EmailClient instance for testing."""
        return EmailClient()

    @pytest.fixture
    def mock_email_config(self):
        """Create mock email configuration."""
        return EmailCredentials(
            smtp_server="smtp.example.com",
            smtp_port=587,
            email_address="sender@example.com",
            email_password="password",
            recipient_email="recipient@example.com",
        )

    @patch("the_alchemiser.shared.notifications.client.smtplib.SMTP")
    def test_send_notification_without_attachments(
        self, mock_smtp, email_client, mock_email_config
    ):
        """Test sending notification without attachments."""
        email_client._config = mock_email_config

        result = email_client.send_notification(
            subject="Test Subject", html_content="<html>Test Content</html>"
        )

        assert result is True
        mock_smtp.assert_called_once()

    @patch("the_alchemiser.shared.notifications.client.boto3.client")
    @patch("the_alchemiser.shared.notifications.client.smtplib.SMTP")
    def test_send_notification_with_s3_attachments_and_owner(
        self, mock_smtp, mock_boto_client, email_client, mock_email_config
    ):
        """Test sending notification with S3 attachments and expected bucket owner."""
        email_client._config = mock_email_config

        # Mock S3 client
        mock_s3_client = Mock()
        mock_response = {"Body": Mock()}
        mock_response["Body"].read.return_value = b"test pdf content"
        mock_s3_client.get_object.return_value = mock_response
        mock_boto_client.return_value = mock_s3_client

        result = email_client.send_notification(
            subject="Test Subject",
            html_content="<html>Test Content</html>",
            s3_attachments=[("report.pdf", "s3://test-bucket/report.pdf", "application/pdf")],
            expected_bucket_owner="123456789012",
        )

        assert result is True
        mock_s3_client.get_object.assert_called_once_with(
            Bucket="test-bucket", Key="report.pdf", ExpectedBucketOwner="123456789012"
        )

    def test_send_notification_no_config(self, email_client):
        """Test sending notification when config is not available."""
        email_client._config = None
        with patch.object(email_client._email_config, "get_config", return_value=None):
            result = email_client.send_notification(
                subject="Test Subject", html_content="<html>Test Content</html>"
            )

        assert result is False

    def test_send_notification_no_recipient(self, email_client):
        """Test sending notification when no recipient is configured."""
        mock_config = EmailCredentials(
            smtp_server="smtp.example.com",
            smtp_port=587,
            email_address="sender@example.com",
            email_password="password",
            recipient_email="",
        )
        email_client._config = mock_config

        result = email_client.send_notification(
            subject="Test Subject", html_content="<html>Test Content</html>"
        )

        assert result is False
