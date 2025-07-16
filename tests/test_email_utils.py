"""Tests for email utilities module."""

import pytest
from unittest.mock import patch, MagicMock
from src.core.email_utils import send_email


class TestEmailUtils:
    """Test email utilities functionality."""

    @patch('src.core.email_utils.smtplib.SMTP')
    def test_send_email_success(self, mock_smtp):
        """Test successful email sending."""
        # Mock the SMTP server
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        # Test parameters
        subject = "Test Subject"
        body = "Test email body"
        smtp_server = "smtp.test.com"
        smtp_port = 587
        smtp_user = "test@test.com"
        smtp_password = "password"
        to_email = "recipient@test.com"
        
        # Call the function
        result = send_email(subject, body, smtp_server, smtp_port, smtp_user, smtp_password, to_email)
        
        # Verify success
        assert result is True
        
        # Verify SMTP calls
        mock_smtp.assert_called_once_with(smtp_server, smtp_port)
        mock_server.ehlo.assert_called()
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with(smtp_user, smtp_password)
        mock_server.sendmail.assert_called_once()

    @patch('src.core.email_utils.smtplib.SMTP')
    def test_send_email_failure(self, mock_smtp):
        """Test email sending failure."""
        # Mock SMTP to raise an exception
        mock_smtp.side_effect = Exception("SMTP connection failed")
        
        # Test parameters
        subject = "Test Subject"
        body = "Test email body"
        smtp_server = "smtp.test.com"
        smtp_port = 587
        smtp_user = "test@test.com"
        smtp_password = "password"
        to_email = "recipient@test.com"
        
        # Call the function
        result = send_email(subject, body, smtp_server, smtp_port, smtp_user, smtp_password, to_email)
        
        # Verify failure
        assert result is False

    @patch('src.core.email_utils.smtplib.SMTP')
    def test_send_email_login_failure(self, mock_smtp):
        """Test email sending with login failure."""
        # Mock the SMTP server with login failure
        mock_server = MagicMock()
        mock_server.login.side_effect = Exception("Authentication failed")
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        # Test parameters
        subject = "Test Subject"
        body = "Test email body"
        smtp_server = "smtp.test.com"
        smtp_port = 587
        smtp_user = "test@test.com"
        smtp_password = "wrong_password"
        to_email = "recipient@test.com"
        
        # Call the function
        result = send_email(subject, body, smtp_server, smtp_port, smtp_user, smtp_password, to_email)
        
        # Verify failure
        assert result is False

    @patch('src.core.email_utils.smtplib.SMTP')
    def test_send_email_message_format(self, mock_smtp):
        """Test that email message is properly formatted."""
        # Mock the SMTP server
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        # Test parameters
        subject = "Nuclear Trading Alert"
        body = "Portfolio rebalanced successfully!"
        smtp_server = "smtp.test.com"
        smtp_port = 587
        smtp_user = "trader@test.com"
        smtp_password = "password"
        to_email = "recipient@test.com"
        
        # Call the function
        result = send_email(subject, body, smtp_server, smtp_port, smtp_user, smtp_password, to_email)
        
        # Verify success
        assert result is True
        
        # Verify sendmail was called with proper message structure
        mock_server.sendmail.assert_called_once()
        call_args = mock_server.sendmail.call_args
        assert call_args[0][0] == smtp_user  # From
        assert call_args[0][1] == to_email   # To
        
        # The message should contain the subject and body
        message = call_args[0][2]
        assert "Nuclear Trading Alert" in message
        assert "Portfolio rebalanced successfully!" in message
