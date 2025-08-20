"""Tests for S3 logging production hygiene guards."""

import logging
import os
from unittest.mock import patch

import pytest

from the_alchemiser.infrastructure.logging.logging_utils import (
    configure_production_logging,
    setup_logging,
)


class TestS3LoggingProductionHygiene:
    """Test that S3 logging is properly guarded in Lambda environments."""

    def setup_method(self):
        """Reset logging state before each test."""
        root_logger = logging.getLogger()
        root_logger.handlers.clear()

    def test_setup_logging_blocks_s3_in_lambda_without_explicit_enable(self, caplog):
        """Test that setup_logging blocks S3 logging in Lambda unless explicitly enabled."""
        with patch.dict(
            os.environ,
            {
                "AWS_LAMBDA_FUNCTION_NAME": "test-lambda",
                "ENABLE_S3_LOGGING": "",  # Not enabled
            },
        ):
            caplog.clear()

            # Try to setup S3 logging in Lambda without explicit enable
            setup_logging(
                log_level=logging.INFO,
                log_file="s3://test-bucket/logs/test.log",
                structured_format=True,
            )

            # Should have warned about blocking S3 logging
            warning_logs = [record for record in caplog.records if record.levelno == logging.WARNING]
            assert len(warning_logs) >= 1
            
            found_s3_warning = False
            for log in warning_logs:
                if "S3 logging requested in Lambda environment" in log.message:
                    found_s3_warning = True
                    break
            
            assert found_s3_warning, "Expected warning about S3 logging being blocked"

    def test_configure_production_logging_blocks_s3_in_lambda_by_default(self, caplog):
        """Test that production logging blocks S3 in Lambda by default."""
        with patch.dict(
            os.environ,
            {
                "AWS_LAMBDA_FUNCTION_NAME": "test-lambda",
                "ENABLE_S3_LOGGING": "",  # Not enabled
            },
        ):
            caplog.clear()

            configure_production_logging(
                log_level=logging.INFO,
                log_file="s3://test-bucket/logs/production.log"
            )

            # Should have logged info about defaulting to CloudWatch
            info_logs = [record for record in caplog.records if record.levelno == logging.INFO]
            cloudwatch_log_found = any(
                "CloudWatch-only logging" in log.message for log in info_logs
            )
            assert cloudwatch_log_found, "Should log about defaulting to CloudWatch-only logging"

    @pytest.mark.parametrize("enable_value", ["0", "false", "no", "off", "", "invalid"])
    def test_enable_s3_logging_env_var_falsy_values(self, enable_value, caplog):
        """Test that various falsy values for ENABLE_S3_LOGGING block S3 logging."""
        with patch.dict(
            os.environ,
            {
                "AWS_LAMBDA_FUNCTION_NAME": "test-lambda",
                "ENABLE_S3_LOGGING": enable_value,
            },
        ):
            caplog.clear()

            setup_logging(
                log_level=logging.INFO,
                log_file="s3://test-bucket/logs/test.log",
                structured_format=True,
            )

            # Should have warned about S3 logging being blocked
            warning_logs = [record for record in caplog.records if record.levelno == logging.WARNING]
            found_s3_warning = any(
                "S3 logging requested in Lambda environment" in log.message 
                for log in warning_logs
            )
            assert found_s3_warning, f"Should block S3 logging with ENABLE_S3_LOGGING={enable_value}"

    def test_s3_logging_allowed_outside_lambda(self):
        """Test that S3 logging is allowed outside Lambda environments."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove AWS_LAMBDA_FUNCTION_NAME if it exists
            os.environ.pop("AWS_LAMBDA_FUNCTION_NAME", None)

            # This should not raise an exception about S3 logging being blocked
            # (it will fail on AWS credentials, but that's expected and not our concern)
            try:
                setup_logging(
                    log_level=logging.INFO,
                    log_file="s3://test-bucket/logs/test.log",
                    structured_format=True,
                )
            except Exception as e:
                # Only credentials errors are expected outside Lambda
                if "Unable to locate credentials" not in str(e) and "NoCredentialsError" not in str(e):
                    pytest.fail(f"Unexpected error outside Lambda: {e}")

    def test_cloudwatch_only_logging_works_in_lambda(self):
        """Test that CloudWatch-only logging works correctly in Lambda."""
        with patch.dict(
            os.environ,
            {
                "AWS_LAMBDA_FUNCTION_NAME": "test-lambda",
            },
        ):
            # Configure without any S3 logging
            configure_production_logging(log_level=logging.INFO, log_file=None)

            # Should have console handlers for CloudWatch
            root_logger = logging.getLogger()
            console_handlers = [h for h in root_logger.handlers if isinstance(h, logging.StreamHandler)]
            assert len(console_handlers) >= 1, "Should have console handler for CloudWatch"

            # Should not have any S3 handlers
            from the_alchemiser.infrastructure.s3.s3_utils import S3FileHandler
            s3_handlers = [h for h in root_logger.handlers if isinstance(h, S3FileHandler)]
            assert len(s3_handlers) == 0, "Should not have S3FileHandler"