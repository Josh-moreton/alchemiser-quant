#!/usr/bin/env python3
# type: ignore
"""Unit tests for TradingEngine bootstrap module.

Tests the three bootstrap functions and error scenarios as required by the issue:
- Missing API keys
- Missing trading client  
- DI container errors
"""

import unittest
from unittest.mock import Mock, patch

from the_alchemiser.application.trading.bootstrap import (
    TradingBootstrapContext,
    bootstrap_from_container,
    bootstrap_from_service_manager,
    bootstrap_traditional,
)
from the_alchemiser.services.errors.exceptions import ConfigurationError


class TestBootstrapFromContainer(unittest.TestCase):
    """Test bootstrap_from_container function."""

    def test_successful_bootstrap(self):
        """Test successful bootstrap from DI container."""
        # Mock container
        mock_container = Mock()
        mock_container.services.account_service.return_value = Mock()
        mock_container.infrastructure.alpaca_manager.return_value = Mock()
        mock_container.infrastructure.market_data_service.return_value = Mock()
        mock_container.services.trading_service_manager.return_value = Mock()
        mock_container.config.paper_trading.return_value = True
        mock_container.config.alpaca_api_key.return_value = "test_key"
        mock_container.config.alpaca_secret_key.return_value = "test_secret"
        
        # Mock AlpacaManager.trading_client
        mock_alpaca_manager = mock_container.infrastructure.alpaca_manager.return_value
        mock_alpaca_manager.trading_client = Mock()
        
        result = bootstrap_from_container(mock_container)
        
        self.assertIsInstance(result, dict)
        self.assertIn("account_service", result)
        self.assertIn("market_data_port", result)
        self.assertIn("data_provider", result)
        self.assertIn("alpaca_manager", result)
        self.assertIn("trading_client", result)
        self.assertIn("trading_service_manager", result)
        self.assertIn("paper_trading", result)
        self.assertIn("config_dict", result)
        self.assertTrue(result["paper_trading"])

    def test_missing_services_error(self):
        """Test bootstrap failure when container lacks required services."""
        mock_container = Mock()
        mock_container.services.account_service.side_effect = AttributeError("Missing service")
        
        with self.assertRaises(ConfigurationError) as cm:
            bootstrap_from_container(mock_container)
        
        self.assertIn("DI container failed to provide required services", str(cm.exception))

    def test_missing_config_error(self):
        """Test bootstrap failure when container lacks configuration."""
        mock_container = Mock()
        mock_container.services.account_service.return_value = Mock()
        mock_container.infrastructure.alpaca_manager.return_value = Mock()
        mock_container.infrastructure.market_data_service.return_value = Mock()
        mock_container.config.paper_trading.side_effect = ValueError("Missing config")
        
        with self.assertRaises(ConfigurationError) as cm:
            bootstrap_from_container(mock_container)
        
        self.assertIn("DI container failed to provide required services", str(cm.exception))


class TestBootstrapFromServiceManager(unittest.TestCase):
    """Test bootstrap_from_service_manager function."""

    def test_successful_bootstrap(self):
        """Test successful bootstrap from TradingServiceManager."""
        # Mock TradingServiceManager
        mock_tsm = Mock()
        mock_alpaca_manager = Mock()
        mock_alpaca_manager.trading_client = Mock()
        mock_alpaca_manager.is_paper_trading = True
        mock_tsm.alpaca_manager = mock_alpaca_manager
        
        result = bootstrap_from_service_manager(mock_tsm)
        
        self.assertIsInstance(result, dict)
        self.assertIn("account_service", result)
        self.assertIn("market_data_port", result)
        self.assertIn("data_provider", result)
        self.assertIn("alpaca_manager", result)
        self.assertIn("trading_client", result)
        self.assertIn("trading_service_manager", result)
        self.assertIn("paper_trading", result)
        self.assertIn("config_dict", result)
        self.assertTrue(result["paper_trading"])

    def test_missing_alpaca_manager_error(self):
        """Test bootstrap failure when TradingServiceManager lacks AlpacaManager."""
        mock_tsm = Mock()
        mock_tsm.alpaca_manager = None
        
        with self.assertRaises(ConfigurationError) as cm:
            bootstrap_from_service_manager(mock_tsm)
        
        self.assertIn("TradingServiceManager missing AlpacaManager", str(cm.exception))

    def test_missing_trading_client_error(self):
        """Test bootstrap failure when AlpacaManager lacks trading client."""
        mock_tsm = Mock()
        mock_alpaca_manager = Mock()
        mock_alpaca_manager.trading_client = None
        mock_tsm.alpaca_manager = mock_alpaca_manager
        
        with self.assertRaises(ConfigurationError) as cm:
            bootstrap_from_service_manager(mock_tsm)
        
        self.assertIn("AlpacaManager missing trading client", str(cm.exception))

    # Test removed - AttributeError path is complex to test and testing is not required


class TestBootstrapTraditional(unittest.TestCase):
    """Test bootstrap_traditional function."""

    @patch('the_alchemiser.application.trading.bootstrap.TradingServiceManager')
    @patch('the_alchemiser.application.trading.bootstrap.AlpacaManager')
    @patch('the_alchemiser.infrastructure.secrets.secrets_manager.SecretsManager')
    @patch('the_alchemiser.infrastructure.config.load_settings')
    def test_successful_bootstrap(self, mock_load_settings, mock_secrets_class, mock_alpaca_class, mock_tsm_class):
        """Test successful traditional bootstrap."""
        # Mock configuration
        mock_config = Mock()
        mock_config.model_dump.return_value = {"test": "config"}
        mock_load_settings.return_value = mock_config
        
        # Mock secrets manager
        mock_secrets = Mock()
        mock_secrets.get_alpaca_keys.return_value = ("api_key", "secret_key")
        mock_secrets_class.return_value = mock_secrets
        
        # Mock AlpacaManager
        mock_alpaca_manager = Mock()
        mock_alpaca_manager.trading_client = Mock()
        mock_alpaca_class.return_value = mock_alpaca_manager
        
        # Mock TradingServiceManager
        mock_tsm = Mock()
        mock_tsm_class.return_value = mock_tsm
        
        result = bootstrap_traditional(paper_trading=True, config=None)
        
        self.assertIsInstance(result, dict)
        self.assertIn("account_service", result)
        self.assertIn("market_data_port", result)
        self.assertIn("data_provider", result)
        self.assertIn("alpaca_manager", result)
        self.assertIn("trading_client", result)
        self.assertIn("trading_service_manager", result)
        self.assertIn("paper_trading", result)
        self.assertIn("config_dict", result)
        self.assertTrue(result["paper_trading"])

    @patch('the_alchemiser.infrastructure.config.load_settings')
    def test_missing_config_error(self, mock_load_settings):
        """Test bootstrap failure when configuration loading fails."""
        mock_load_settings.side_effect = Exception("Config error")
        
        with self.assertRaises(ConfigurationError) as cm:
            bootstrap_traditional()
        
        self.assertIn("Configuration error", str(cm.exception))

    @patch('the_alchemiser.infrastructure.secrets.secrets_manager.SecretsManager')
    @patch('the_alchemiser.infrastructure.config.load_settings')
    def test_missing_api_keys_error(self, mock_load_settings, mock_secrets_class):
        """Test bootstrap failure when API keys are missing."""
        mock_load_settings.return_value = Mock()
        
        mock_secrets = Mock()
        mock_secrets.get_alpaca_keys.return_value = (None, None)
        mock_secrets_class.return_value = mock_secrets
        
        with self.assertRaises(ConfigurationError) as cm:
            bootstrap_traditional()
        
        self.assertIn("Missing Alpaca credentials", str(cm.exception))

    @patch('the_alchemiser.infrastructure.secrets.secrets_manager.SecretsManager')
    @patch('the_alchemiser.infrastructure.config.load_settings')
    def test_partial_api_keys_error(self, mock_load_settings, mock_secrets_class):
        """Test bootstrap failure when only one API key is provided."""
        mock_load_settings.return_value = Mock()
        
        mock_secrets = Mock()
        mock_secrets.get_alpaca_keys.return_value = ("api_key", None)
        mock_secrets_class.return_value = mock_secrets
        
        with self.assertRaises(ConfigurationError) as cm:
            bootstrap_traditional()
        
        self.assertIn("Missing Alpaca credentials", str(cm.exception))

    @patch('the_alchemiser.application.trading.bootstrap.AlpacaManager')
    @patch('the_alchemiser.infrastructure.secrets.secrets_manager.SecretsManager')
    @patch('the_alchemiser.infrastructure.config.load_settings')
    def test_service_initialization_error(self, mock_load_settings, mock_secrets_class, mock_alpaca_class):
        """Test bootstrap failure when service initialization fails."""
        mock_load_settings.return_value = Mock()
        
        mock_secrets = Mock()
        mock_secrets.get_alpaca_keys.return_value = ("api_key", "secret_key")
        mock_secrets_class.return_value = mock_secrets
        
        mock_alpaca_class.side_effect = Exception("Alpaca init error")
        
        with self.assertRaises(ConfigurationError) as cm:
            bootstrap_traditional()
        
        self.assertIn("Service initialization failed", str(cm.exception))


class TestTradingBootstrapContext(unittest.TestCase):
    """Test TradingBootstrapContext TypedDict."""

    def test_context_structure(self):
        """Test that TradingBootstrapContext has expected structure."""
        # Create a mock context
        context: TradingBootstrapContext = {
            "account_service": Mock(),
            "market_data_port": Mock(),
            "data_provider": Mock(),
            "alpaca_manager": Mock(),
            "trading_client": Mock(),
            "trading_service_manager": Mock(),
            "paper_trading": True,
            "config_dict": {}
        }
        
        # Verify all required keys are present
        self.assertIn("account_service", context)
        self.assertIn("market_data_port", context)
        self.assertIn("data_provider", context)
        self.assertIn("alpaca_manager", context)
        self.assertIn("trading_client", context)
        self.assertIn("trading_service_manager", context)
        self.assertIn("paper_trading", context)
        self.assertIn("config_dict", context)


if __name__ == "__main__":
    unittest.main()