"""
Example test demonstrating pytest-mock usage.

This test shows how to use pytest-mock fixtures in The Alchemiser testing framework.
"""

from decimal import Decimal

import pytest


class TestPytestMockIntegration:
    """Test pytest-mock integration and fixtures."""

    def test_alpaca_client_mock(self, mock_alpaca_client):
        """Test that the Alpaca client mock works correctly."""
        # Test that the mock is properly configured
        assert mock_alpaca_client is not None

        # Test order submission
        order = mock_alpaca_client.submit_order()
        assert order.id == "test_order_123"
        assert order.status == "ACCEPTED"

        # Test account retrieval
        account = mock_alpaca_client.get_account()
        assert account.buying_power == Decimal("50000.00")
        assert account.portfolio_value == Decimal("100000.00")

        # Test positions
        positions = mock_alpaca_client.get_positions()
        assert positions == []

    def test_aws_clients_mock(self, mock_aws_clients):
        """Test that AWS client mocks work correctly."""
        # Test S3 operations
        s3_client = mock_aws_clients["s3"]
        put_response = s3_client.put_object()
        assert put_response["ETag"] == "test_etag"

        get_response = s3_client.get_object()
        assert get_response["ContentLength"] == 1024

        # Test Secrets Manager
        secrets_client = mock_aws_clients["secretsmanager"]
        secret = secrets_client.get_secret_value()
        assert "api_key" in secret["SecretString"]

        # Test CloudWatch
        cloudwatch_client = mock_aws_clients["cloudwatch"]
        response = cloudwatch_client.put_metric_data()
        assert response == {}

    def test_environment_variables_mock(self, mock_environment_variables):
        """Test that environment variables are properly mocked."""
        import os

        assert os.environ.get("AWS_REGION") == "us-east-1"
        assert os.environ.get("ALPACA_API_KEY") == "test_key"
        assert os.environ.get("S3_BUCKET") == "test-alchemiser-bucket"

    def test_manual_mocking_with_mocker(self, mocker):
        """Test manual mocking using the mocker fixture."""
        # Create a simple mock function
        mock_api_function = mocker.Mock()
        mock_api_function.return_value = {"status": "success"}

        # Use the mock
        result = mock_api_function("test_param")

        # Verify the mock was called correctly
        assert result["status"] == "success"
        mock_api_function.assert_called_once_with("test_param")

        # Test patching a module function
        mock_patch = mocker.patch("os.path.exists")
        mock_patch.return_value = True

        import os.path

        assert os.path.exists("/fake/path") is True
        mock_patch.assert_called_once_with("/fake/path")

    def test_mock_return_values(self, mocker):
        """Test setting custom return values with pytest-mock."""
        # Create a mock with specific return values
        mock_api_call = mocker.Mock()
        mock_api_call.return_value = {"status": "success", "data": [1, 2, 3]}

        # Use the mock
        result = mock_api_call()
        assert result["status"] == "success"
        assert result["data"] == [1, 2, 3]

        # Test side effects
        mock_api_call.side_effect = [{"attempt": 1}, {"attempt": 2}, {"attempt": 3}]

        assert mock_api_call()["attempt"] == 1
        assert mock_api_call()["attempt"] == 2
        assert mock_api_call()["attempt"] == 3

    def test_mock_exceptions(self, mocker):
        """Test mocking exceptions with pytest-mock."""
        mock_failing_function = mocker.Mock()
        mock_failing_function.side_effect = ConnectionError("Network timeout")

        with pytest.raises(ConnectionError, match="Network timeout"):
            mock_failing_function()

    def test_patch_multiple_targets(self, mocker):
        """Test patching multiple targets simultaneously."""
        # Patch multiple functions at once
        mock_exists = mocker.Mock(return_value=True)
        mock_isfile = mocker.Mock(return_value=True)
        mock_getsize = mocker.Mock(return_value=1024)

        mocker.patch("os.path.exists", mock_exists)
        mocker.patch("os.path.isfile", mock_isfile)
        mocker.patch("os.path.getsize", mock_getsize)

        import os.path

        assert os.path.exists("/fake/path") is True
        assert os.path.isfile("/fake/file") is True
        assert os.path.getsize("/fake/file") == 1024

        # Verify all patches were called
        mock_exists.assert_called_once()
        mock_isfile.assert_called_once()
        mock_getsize.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
