#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Notification schema DTOs for The Alchemiser Trading System.

This module contains Pydantic models for email notifications and SMTP configuration.
Extracted from reporting.py to provide a focused schema for notification infrastructure.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class EmailCredentials(BaseModel):
    """Email service credentials.

    Contains SMTP configuration for sending emails. Sensitive data should
    be redacted from logs. Password field has repr=False to prevent logging.

    Examples:
        >>> creds = EmailCredentials(
        ...     smtp_server="smtp.gmail.com",
        ...     smtp_port=587,
        ...     email_address="sender@example.com",
        ...     email_password="secret_password",
        ...     recipient_email="recipient@example.com"
        ... )

    """

    model_config = ConfigDict(strict=True, frozen=True, validate_assignment=True)

    smtp_server: str = Field(description="SMTP server hostname")
    smtp_port: int = Field(description="SMTP server port", gt=0, le=65535)
    email_address: str = Field(description="Sender email address")
    email_password: str = Field(description="Email password (sensitive)", repr=False, min_length=1)
    recipient_email: str = Field(description="Default recipient email address")


# Public API
__all__ = [
    "EmailCredentials",
]
