#!/usr/bin/env python3
"""Test suite for shared.schemas.notifications module.

Tests EmailCredentials DTO for:
- Successful instantiation with valid data
- Field validation and constraints
- Frozen/immutability enforcement
- Sensitive data repr behavior
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from the_alchemiser.shared.schemas.notifications import EmailCredentials


class TestEmailCredentials:
    """Test EmailCredentials DTO."""

    def test_create_email_credentials_valid(self):
        """Test creating EmailCredentials with valid data."""
        creds = EmailCredentials(
            smtp_server="smtp.example.com",
            smtp_port=587,
            email_address="sender@example.com",
            email_password="secret123",
            recipient_email="recipient@example.com",
        )
        
        assert creds.smtp_server == "smtp.example.com"
        assert creds.smtp_port == 587
        assert creds.email_address == "sender@example.com"
        assert creds.email_password == "secret123"
        assert creds.recipient_email == "recipient@example.com"

    def test_email_credentials_password_repr_redacted(self):
        """Test that password is not shown in repr."""
        creds = EmailCredentials(
            smtp_server="smtp.example.com",
            smtp_port=587,
            email_address="sender@example.com",
            email_password="secret123",
            recipient_email="recipient@example.com",
        )
        
        repr_str = repr(creds)
        assert "secret123" not in repr_str
        assert "email_password" not in repr_str or "**" in repr_str

    def test_email_credentials_port_validation(self):
        """Test that smtp_port is validated."""
        # Port must be > 0
        with pytest.raises(ValidationError):
            EmailCredentials(
                smtp_server="smtp.example.com",
                smtp_port=0,
                email_address="sender@example.com",
                email_password="secret123",
                recipient_email="recipient@example.com",
            )
        
        # Port must be <= 65535
        with pytest.raises(ValidationError):
            EmailCredentials(
                smtp_server="smtp.example.com",
                smtp_port=65536,
                email_address="sender@example.com",
                email_password="secret123",
                recipient_email="recipient@example.com",
            )

    def test_email_credentials_password_min_length(self):
        """Test that password must have min_length=1."""
        with pytest.raises(ValidationError):
            EmailCredentials(
                smtp_server="smtp.example.com",
                smtp_port=587,
                email_address="sender@example.com",
                email_password="",  # Empty password should fail
                recipient_email="recipient@example.com",
            )

    def test_email_credentials_frozen(self):
        """Test that EmailCredentials is immutable."""
        creds = EmailCredentials(
            smtp_server="smtp.example.com",
            smtp_port=587,
            email_address="sender@example.com",
            email_password="secret123",
            recipient_email="recipient@example.com",
        )
        
        with pytest.raises(ValidationError):
            creds.smtp_port = 465

    def test_email_credentials_strict_validation(self):
        """Test that strict validation is enabled."""
        # String value for port should fail with strict=True
        with pytest.raises(ValidationError):
            EmailCredentials(
                smtp_server="smtp.example.com",
                smtp_port="587",  # type: ignore - intentionally wrong type
                email_address="sender@example.com",
                email_password="secret123",
                recipient_email="recipient@example.com",
            )
