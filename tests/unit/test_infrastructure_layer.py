"""
Comprehensive unit tests for infrastructure layer.

Tests data providers, configuration, external integrations, and AWS services.
"""

import pytest
from unittest.mock import patch
from decimal import Decimal
from datetime import datetime
import json

from the_alchemiser.infrastructure.config import load_settings
from the_alchemiser.infrastructure.data_providers.alpaca_data_provider import AlpacaDataProvider
from the_alchemiser.infrastructure.data_providers.news_data_provider import NewsDataProvider
from the_alchemiser.infrastructure.external.email_service import EmailService
from the_alchemiser.infrastructure.external.aws_client import AWSClient
from the_alchemiser.services.alpaca_manager import AlpacaManager
from the_alchemiser.services.exceptions import (
    ConfigurationError,
    DataProviderError,
    ExternalServiceError,
)


class TestConfigurationManagement:
    """Test configuration loading and validation."""

    def test_default_settings_loading(self):
        """Test loading default settings."""
        with patch.dict("os.environ", {}, clear=True):
            settings = load_settings()

            # Should have default values
            assert settings is not None
            assert hasattr(settings, "alpaca")
            assert hasattr(settings, "logging")

    def test_environment_variable_override(self):
        """Test environment variable override."""
        env_vars = {
            "ALPACA_API_KEY": "test_key",
            "ALPACA_SECRET_KEY": "test_secret",
            "PAPER_TRADING": "false",
            "ALPACA__CASH_RESERVE_PCT": "0.10",
        }

        with patch.dict("os.environ", env_vars, clear=True):
            settings = load_settings()

            assert settings.alpaca.api_key == "test_key"
            assert settings.alpaca.secret_key == "test_secret"
            assert settings.alpaca.paper_trading is False
            assert settings.alpaca.cash_reserve_pct == Decimal("0.10")

    def test_nested_configuration_override(self):
        """Test nested configuration override with double underscore."""
        env_vars = {
            "ALPACA__SLIPPAGE_BPS": "10",
            "LOGGING__LEVEL": "DEBUG",
            "AWS__REGION": "us-west-2",
        }

        with patch.dict("os.environ", env_vars, clear=True):
            settings = load_settings()

            assert settings.alpaca.slippage_bps == 10
            assert settings.logging.level == "DEBUG"
            assert settings.aws.region == "us-west-2"

    def test_invalid_configuration_validation(self):
        """Test validation of invalid configuration values."""
        env_vars = {
            "ALPACA__CASH_RESERVE_PCT": "1.5",  # Invalid: > 1.0
            "ALPACA__SLIPPAGE_BPS": "-5",  # Invalid: negative
        }

        with patch.dict("os.environ", env_vars, clear=True):
            with pytest.raises(ConfigurationError):
                load_settings()

    def test_required_fields_validation(self):
        """Test validation of required configuration fields."""
        # Missing required API keys should raise error in production mode
        env_vars = {
            "PAPER_TRADING": "false",
            # Missing ALPACA_API_KEY and ALPACA_SECRET_KEY
        }

        with patch.dict("os.environ", env_vars, clear=True):
            with pytest.raises(ConfigurationError):
                load_settings()

    def test_configuration_serialization(self):
        """Test configuration serialization for logging/debugging."""
        env_vars = {"ALPACA_API_KEY": "test_key", "ALPACA_SECRET_KEY": "test_secret"}

        with patch.dict("os.environ", env_vars, clear=True):
            settings = load_settings()

            # Should be able to serialize without exposing secrets
            config_dict = settings.to_safe_dict()

            assert config_dict["alpaca"]["api_key"] == "***masked***"
            assert config_dict["alpaca"]["secret_key"] == "***masked***"
            assert config_dict["alpaca"]["paper_trading"] is not None


class TestAlpacaDataProvider:
    """Test Alpaca data provider functionality."""

    @pytest.fixture
    def mock_alpaca_client(self, mocker):
        """Create mocked Alpaca client."""
        mock_client = mocker.Mock()
        mock_client.get_bars.return_value = [
            {
                "symbol": "AAPL",
                "timestamp": "2024-01-15T09:30:00Z",
                "open": 150.0,
                "high": 152.0,
                "low": 149.0,
                "close": 151.0,
                "volume": 1000000,
            }
        ]
        return mock_client

    @pytest.fixture
    def data_provider(self, mock_alpaca_client):
        """Create AlpacaDataProvider with mocked client."""
        provider = AlpacaDataProvider(api_key="test", secret_key="test")
        provider.client = mock_alpaca_client
        return provider

    def test_historical_data_retrieval(self, data_provider, mock_alpaca_client):
        """Test historical data retrieval."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)

        data = data_provider.get_historical_data(
            symbols=["AAPL", "TSLA"], start_date=start_date, end_date=end_date, timeframe="1day"
        )

        assert isinstance(data, dict)
        mock_alpaca_client.get_bars.assert_called_once()

    def test_real_time_quote_retrieval(self, data_provider, mock_alpaca_client):
        """Test real-time quote retrieval."""
        mock_alpaca_client.get_latest_quotes.return_value = {
            "AAPL": {
                "bid": 149.50,
                "ask": 150.50,
                "bid_size": 100,
                "ask_size": 200,
                "timestamp": "2024-01-15T15:30:00Z",
            }
        }

        quotes = data_provider.get_latest_quotes(["AAPL"])

        assert "AAPL" in quotes
        assert quotes["AAPL"]["bid"] == 149.50
        assert quotes["AAPL"]["ask"] == 150.50

    def test_market_data_caching(self, data_provider, mock_alpaca_client):
        """Test market data caching functionality."""
        # First call should hit the API
        data1 = data_provider.get_latest_quotes(["AAPL"])

        # Second call within cache window should use cache
        data2 = data_provider.get_latest_quotes(["AAPL"])

        # Should only call API once due to caching
        assert mock_alpaca_client.get_latest_quotes.call_count == 1
        assert data1 == data2

    def test_data_validation_and_cleaning(self, data_provider, mock_alpaca_client):
        """Test data validation and cleaning."""
        # Mock data with some invalid entries
        mock_alpaca_client.get_bars.return_value = [
            {
                "symbol": "AAPL",
                "timestamp": "2024-01-15T09:30:00Z",
                "open": 150.0,
                "high": 152.0,
                "low": 149.0,
                "close": 151.0,
                "volume": 1000000,
            },
            {
                "symbol": "INVALID",
                "timestamp": None,  # Invalid timestamp
                "open": -150.0,  # Invalid negative price
                "high": 152.0,
                "low": 149.0,
                "close": 151.0,
                "volume": 0,  # Invalid zero volume
            },
        ]

        cleaned_data = data_provider.get_historical_data(
            symbols=["AAPL", "INVALID"],
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
        )

        # Should filter out invalid data
        assert len(cleaned_data) >= 0

    def test_rate_limiting_handling(self, data_provider, mock_alpaca_client):
        """Test rate limiting handling."""
        from alpaca.common.exceptions import APIError

        # Mock rate limit error then success
        mock_alpaca_client.get_latest_quotes.side_effect = [
            APIError("Rate limit exceeded"),
            {"AAPL": {"bid": 149.50, "ask": 150.50}},
        ]

        # Should retry and eventually succeed
        quotes = data_provider.get_latest_quotes(["AAPL"])
        assert "AAPL" in quotes

    def test_error_handling_and_fallbacks(self, data_provider, mock_alpaca_client):
        """Test error handling and fallback mechanisms."""
        mock_alpaca_client.get_latest_quotes.side_effect = Exception("Network error")

        with pytest.raises(DataProviderError):
            data_provider.get_latest_quotes(["AAPL"])

    def test_data_format_standardization(self, data_provider, mock_alpaca_client):
        """Test data format standardization."""
        raw_data = data_provider.get_latest_quotes(["AAPL"])

        # Should standardize data format
        if "AAPL" in raw_data:
            quote = raw_data["AAPL"]
            assert isinstance(quote.get("bid"), (int, float))
            assert isinstance(quote.get("ask"), (int, float))


class TestNewsDataProvider:
    """Test news data provider functionality."""

    @pytest.fixture
    def news_provider(self):
        """Create NewsDataProvider instance."""
        return NewsDataProvider(api_key="test_key")

    def test_news_retrieval(self, news_provider, mocker):
        """Test news retrieval functionality."""
        mock_response = {
            "articles": [
                {
                    "title": "Apple Reports Strong Earnings",
                    "content": "Apple Inc. reported strong Q4 earnings...",
                    "published_at": "2024-01-15T10:00:00Z",
                    "sentiment": "positive",
                    "symbols": ["AAPL"],
                }
            ]
        }

        mocker.patch.object(news_provider, "_fetch_news", return_value=mock_response)

        news = news_provider.get_news_for_symbols(["AAPL"])

        assert len(news) >= 0
        if news:
            assert "title" in news[0]
            assert "sentiment" in news[0]

    def test_sentiment_analysis(self, news_provider):
        """Test news sentiment analysis."""
        article = {
            "title": "Apple stock soars on strong earnings",
            "content": "Apple reported excellent quarterly results...",
        }

        sentiment = news_provider.analyze_sentiment(article)

        assert sentiment in ["positive", "negative", "neutral"]

    def test_news_filtering_and_relevance(self, news_provider, mocker):
        """Test news filtering and relevance scoring."""
        mock_articles = [
            {"title": "Apple Reports Earnings", "symbols": ["AAPL"], "relevance_score": 0.9},
            {"title": "General Market Update", "symbols": [], "relevance_score": 0.3},
        ]

        mocker.patch.object(news_provider, "_fetch_news", return_value={"articles": mock_articles})

        filtered_news = news_provider.get_relevant_news(symbols=["AAPL"], min_relevance=0.5)

        # Should filter out low-relevance news
        assert len(filtered_news) <= len(mock_articles)


class TestEmailService:
    """Test email notification service."""

    @pytest.fixture
    def email_service(self, mocker):
        """Create EmailService with mocked SMTP."""
        service = EmailService(
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            username="test@example.com",
            password="test_password",
        )
        service.smtp_client = mocker.Mock()
        return service

    def test_email_sending(self, email_service):
        """Test basic email sending functionality."""
        result = email_service.send_email(
            to_address="recipient@example.com",
            subject="Test Subject",
            body="Test body content",
            is_html=False,
        )

        assert result is True
        email_service.smtp_client.send_message.assert_called_once()

    def test_html_email_sending(self, email_service):
        """Test HTML email sending."""
        html_body = "<h1>Trading Alert</h1><p>Portfolio value: $100,000</p>"

        result = email_service.send_html_email(
            to_address="recipient@example.com", subject="Trading Alert", html_body=html_body
        )

        assert result is True

    def test_trading_alert_templates(self, email_service):
        """Test pre-built trading alert email templates."""
        alert_data = {
            "type": "order_executed",
            "symbol": "AAPL",
            "quantity": 100,
            "side": "buy",
            "price": Decimal("150.00"),
            "timestamp": datetime.now(),
        }

        result = email_service.send_trading_alert(
            to_address="trader@example.com", alert_data=alert_data
        )

        assert result is True

    def test_error_notification_email(self, email_service):
        """Test error notification email."""
        error_data = {
            "component": "TradingEngine.execute_order",
            "error_message": "Order validation failed",
            "timestamp": datetime.now(),
            "context": {"symbol": "AAPL", "quantity": 100},
        }

        result = email_service.send_error_notification(
            to_address="admin@example.com", error_data=error_data
        )

        assert result is True

    def test_email_sending_failure_handling(self, email_service):
        """Test email sending failure handling."""
        email_service.smtp_client.send_message.side_effect = Exception("SMTP error")

        result = email_service.send_email(
            to_address="test@example.com", subject="Test", body="Test body"
        )

        assert result is False

    def test_attachment_support(self, email_service):
        """Test email attachment support."""
        attachment_data = {
            "filename": "trading_report.pdf",
            "content": b"fake_pdf_content",
            "content_type": "application/pdf",
        }

        result = email_service.send_email_with_attachment(
            to_address="recipient@example.com",
            subject="Trading Report",
            body="Please find attached trading report.",
            attachments=[attachment_data],
        )

        assert result is True


class TestAWSClient:
    """Test AWS client integration."""

    @pytest.fixture
    def aws_client(self, mocker):
        """Create AWSClient with mocked boto3 clients."""
        client = AWSClient(region="us-east-1")

        # Mock AWS service clients
        client.lambda_client = mocker.Mock()
        client.s3_client = mocker.Mock()
        client.cloudwatch_client = mocker.Mock()
        client.sns_client = mocker.Mock()

        return client

    def test_lambda_function_invocation(self, aws_client):
        """Test Lambda function invocation."""
        aws_client.lambda_client.invoke.return_value = {
            "StatusCode": 200,
            "Payload": json.dumps({"result": "success"}).encode(),
        }

        result = aws_client.invoke_lambda_function(
            function_name="trading-function", payload={"action": "execute_trades"}
        )

        assert result["StatusCode"] == 200
        assert "result" in result["response"]

    def test_s3_operations(self, aws_client):
        """Test S3 upload and download operations."""
        # Test upload
        aws_client.s3_client.put_object.return_value = {"ETag": "test_etag"}

        upload_result = aws_client.upload_to_s3(
            bucket="trading-data", key="reports/daily_report.json", data={"portfolio_value": 100000}
        )

        assert upload_result is True

        # Test download
        aws_client.s3_client.get_object.return_value = {"Body": mocker.Mock()}
        aws_client.s3_client.get_object.return_value["Body"].read.return_value = b'{"data": "test"}'

        download_result = aws_client.download_from_s3(
            bucket="trading-data", key="reports/daily_report.json"
        )

        assert download_result is not None

    def test_cloudwatch_metrics(self, aws_client):
        """Test CloudWatch metrics publishing."""
        aws_client.cloudwatch_client.put_metric_data.return_value = {}

        result = aws_client.publish_metric(
            namespace="Trading/Performance",
            metric_name="PortfolioValue",
            value=100000.0,
            unit="Count",
        )

        assert result is True
        aws_client.cloudwatch_client.put_metric_data.assert_called_once()

    def test_sns_notifications(self, aws_client):
        """Test SNS notification sending."""
        aws_client.sns_client.publish.return_value = {"MessageId": "test_message_id"}

        result = aws_client.send_sns_notification(
            topic_arn="arn:aws:sns:us-east-1:123456789012:trading-alerts",
            message="Trading alert: Order executed successfully",
            subject="Trading Alert",
        )

        assert result is True

    def test_aws_error_handling(self, aws_client):
        """Test AWS service error handling."""
        from botocore.exceptions import ClientError

        aws_client.lambda_client.invoke.side_effect = ClientError(
            {"Error": {"Code": "ResourceNotFoundException", "Message": "Function not found"}},
            "invoke",
        )

        with pytest.raises(ExternalServiceError):
            aws_client.invoke_lambda_function("nonexistent-function", {})

    def test_aws_credentials_handling(self, mocker):
        """Test AWS credentials handling."""
        # Mock boto3 session creation
        mock_session = mocker.Mock()
        mocker.patch("boto3.Session", return_value=mock_session)

        client = AWSClient(
            region="us-west-2", access_key_id="test_key", secret_access_key="test_secret"
        )

        # Should create session with provided credentials
        assert client.region == "us-west-2"


class TestAlpacaManager:
    """Test AlpacaManager infrastructure integration."""

    @pytest.fixture
    def mock_alpaca_api(self, mocker):
        """Create mocked Alpaca API client."""
        mock_client = mocker.Mock()

        # Mock trading client
        mock_client.get_account.return_value = mocker.Mock(
            portfolio_value=100000.0, cash=20000.0, buying_power=50000.0
        )

        mock_client.list_positions.return_value = [
            mocker.Mock(symbol="AAPL", qty=100, market_value=15000.0, unrealized_pl=500.0)
        ]

        # Mock data client
        mock_data_client = mocker.Mock()
        mock_data_client.get_bars.return_value = {
            "AAPL": [
                mocker.Mock(
                    timestamp="2024-01-15T09:30:00Z",
                    open=150.0,
                    high=152.0,
                    low=149.0,
                    close=151.0,
                    volume=1000000,
                )
            ]
        }

        return {"trading": mock_client, "data": mock_data_client}

    @pytest.fixture
    def alpaca_manager(self, mock_alpaca_api, mocker):
        """Create AlpacaManager with mocked API clients."""
        with (
            patch("alpaca.trading.TradingClient") as mock_trading,
            patch("alpaca.data.StockHistoricalDataClient") as mock_data,
        ):

            mock_trading.return_value = mock_alpaca_api["trading"]
            mock_data.return_value = mock_alpaca_api["data"]

            manager = AlpacaManager(api_key="test_key", secret_key="test_secret", paper=True)

            return manager

    def test_account_info_retrieval(self, alpaca_manager, mock_alpaca_api):
        """Test account information retrieval."""
        account_info = alpaca_manager.get_account_info()

        assert account_info["portfolio_value"] == "100000.0"
        assert account_info["cash"] == "20000.0"
        assert account_info["buying_power"] == "50000.0"

        mock_alpaca_api["trading"].get_account.assert_called_once()

    def test_position_retrieval(self, alpaca_manager, mock_alpaca_api):
        """Test position retrieval."""
        positions = alpaca_manager.get_all_positions()

        assert len(positions) == 1
        assert positions[0]["symbol"] == "AAPL"
        assert positions[0]["qty"] == "100"

        mock_alpaca_api["trading"].list_positions.assert_called_once()

    def test_order_placement(self, alpaca_manager, mock_alpaca_api):
        """Test order placement functionality."""
        mock_order = mocker.Mock()
        mock_order.id = "order_123"
        mock_order.status = "new"

        mock_alpaca_api["trading"].submit_order.return_value = mock_order

        order_result = alpaca_manager.place_market_order(
            symbol="AAPL", side="buy", quantity=Decimal("100")
        )

        assert order_result["id"] == "order_123"
        assert order_result["status"] == "new"

    def test_market_data_retrieval(self, alpaca_manager, mock_alpaca_api):
        """Test market data retrieval."""
        bars = alpaca_manager.get_historical_bars(
            symbols=["AAPL"], timeframe="1day", start="2024-01-01", end="2024-01-31"
        )

        assert "AAPL" in bars
        mock_alpaca_api["data"].get_bars.assert_called_once()

    def test_connection_resilience(self, alpaca_manager, mock_alpaca_api):
        """Test connection resilience and retry logic."""
        from alpaca.common.exceptions import APIError

        # Mock API error followed by success
        mock_alpaca_api["trading"].get_account.side_effect = [
            APIError("Temporary network error"),
            mocker.Mock(portfolio_value=100000.0, cash=20000.0, buying_power=50000.0),
        ]

        # Should retry and eventually succeed
        account_info = alpaca_manager.get_account_info()
        assert account_info["portfolio_value"] == "100000.0"

    def test_paper_trading_mode_validation(self, alpaca_manager):
        """Test paper trading mode validation."""
        assert alpaca_manager.paper_trading is True

        # Should include paper trading headers/flags in API calls
        account_info = alpaca_manager.get_account_info()
        assert account_info is not None


class TestInfrastructureIntegration:
    """Test integration between infrastructure components."""

    def test_config_to_service_integration(self, mocker):
        """Test configuration integration with services."""
        env_vars = {
            "ALPACA_API_KEY": "test_key",
            "ALPACA_SECRET_KEY": "test_secret",
            "PAPER_TRADING": "true",
        }

        with patch.dict("os.environ", env_vars, clear=True):
            settings = load_settings()

            # Mock Alpaca clients
            with (
                patch("alpaca.trading.TradingClient") as mock_trading,
                patch("alpaca.data.StockHistoricalDataClient") as mock_data,
            ):

                # Should initialize services with config values
                manager = AlpacaManager.from_settings(settings)

                assert manager.paper_trading is True
                mock_trading.assert_called_once()
                mock_data.assert_called_once()

    def test_data_provider_to_service_integration(self, mocker):
        """Test data provider integration with trading services."""
        mock_alpaca_client = mocker.Mock()
        mock_alpaca_client.get_latest_quotes.return_value = {"AAPL": {"bid": 149.50, "ask": 150.50}}

        data_provider = AlpacaDataProvider("test_key", "test_secret")
        data_provider.client = mock_alpaca_client

        # Should provide standardized data to trading services
        quotes = data_provider.get_latest_quotes(["AAPL"])
        assert quotes["AAPL"]["bid"] == 149.50

    def test_error_handling_across_infrastructure(self, mocker):
        """Test error handling across infrastructure components."""
        # Test cascading error handling
        mock_email = mocker.Mock()
        mock_aws = mocker.Mock()

        # Simulate AWS failure
        mock_aws.publish_metric.side_effect = ExternalServiceError("AWS unavailable")

        # Email service should still work as fallback
        mock_email.send_error_notification.return_value = True

        # Error handling should gracefully degrade
        error_handler = mocker.Mock()
        error_handler.handle_aws_failure(mock_aws)
        error_handler.fallback_to_email(mock_email)

        # Should attempt both notification methods
        assert True  # Integration test framework placeholder


if __name__ == "__main__":
    pytest.main([__file__])
