"""Business Unit: strategy | Status: current

Test factory functions for strategy orchestrator creation.

Tests input validation, error handling, logging, and proper object creation
for the factory functions in strategy_v2.core.factory.
"""

from unittest.mock import Mock, patch

import pytest

from the_alchemiser.shared.errors.exceptions import ConfigurationError
from the_alchemiser.strategy_v2.adapters.market_data_adapter import (
    StrategyMarketDataAdapter,
)
from the_alchemiser.strategy_v2.core.factory import (
    create_orchestrator,
    create_orchestrator_with_adapter,
)
from the_alchemiser.strategy_v2.core.orchestrator import SingleStrategyOrchestrator


class TestCreateOrchestrator:
    """Test create_orchestrator factory function."""

    @patch("the_alchemiser.strategy_v2.core.factory.AlpacaManager")
    @patch("the_alchemiser.strategy_v2.core.factory.StrategyMarketDataAdapter")
    def test_create_orchestrator_success_paper_mode(self, mock_adapter_class, mock_alpaca_class):
        """Test successful orchestrator creation in paper mode."""
        api_key = "test_api_key_123"
        secret_key = "test_secret_key_456"

        # Mock the dependencies
        mock_alpaca_instance = Mock()
        mock_alpaca_class.return_value = mock_alpaca_instance
        mock_adapter_instance = Mock()
        mock_adapter_class.return_value = mock_adapter_instance

        # Create orchestrator
        result = create_orchestrator(api_key, secret_key, paper=True)

        # Verify AlpacaManager was created with correct args
        mock_alpaca_class.assert_called_once_with(
            api_key=api_key, secret_key=secret_key, paper=True
        )

        # Verify adapter was created with AlpacaManager
        mock_adapter_class.assert_called_once_with(mock_alpaca_instance)

        # Verify result is an orchestrator
        assert isinstance(result, SingleStrategyOrchestrator)

    @patch("the_alchemiser.strategy_v2.core.factory.AlpacaManager")
    @patch("the_alchemiser.strategy_v2.core.factory.StrategyMarketDataAdapter")
    def test_create_orchestrator_success_live_mode(self, mock_adapter_class, mock_alpaca_class):
        """Test successful orchestrator creation in live mode."""
        api_key = "test_api_key_123"
        secret_key = "test_secret_key_456"

        # Mock the dependencies
        mock_alpaca_instance = Mock()
        mock_alpaca_class.return_value = mock_alpaca_instance
        mock_adapter_instance = Mock()
        mock_adapter_class.return_value = mock_adapter_instance

        # Create orchestrator
        result = create_orchestrator(api_key, secret_key, paper=False)

        # Verify AlpacaManager was created with paper=False
        mock_alpaca_class.assert_called_once_with(
            api_key=api_key, secret_key=secret_key, paper=False
        )

        # Verify result is an orchestrator
        assert isinstance(result, SingleStrategyOrchestrator)

    def test_create_orchestrator_empty_api_key(self):
        """Test that empty API key raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            create_orchestrator("", "secret_key", paper=True)

        assert "API key must be a non-empty string" in str(exc_info.value)
        assert exc_info.value.config_key == "api_key"

    def test_create_orchestrator_none_api_key(self):
        """Test that None API key raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            create_orchestrator(None, "secret_key", paper=True)  # type: ignore

        assert "API key must be a non-empty string" in str(exc_info.value)

    def test_create_orchestrator_invalid_api_key_type(self):
        """Test that non-string API key raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            create_orchestrator(123, "secret_key", paper=True)  # type: ignore

        assert "API key must be a non-empty string" in str(exc_info.value)

    def test_create_orchestrator_empty_secret_key(self):
        """Test that empty secret key raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            create_orchestrator("api_key", "", paper=True)

        assert "Secret key must be a non-empty string" in str(exc_info.value)
        assert exc_info.value.config_key == "secret_key"

    def test_create_orchestrator_none_secret_key(self):
        """Test that None secret key raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            create_orchestrator("api_key", None, paper=True)  # type: ignore

        assert "Secret key must be a non-empty string" in str(exc_info.value)

    def test_create_orchestrator_invalid_secret_key_type(self):
        """Test that non-string secret key raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            create_orchestrator("api_key", 456, paper=True)  # type: ignore

        assert "Secret key must be a non-empty string" in str(exc_info.value)

    @patch("the_alchemiser.strategy_v2.core.factory.AlpacaManager")
    def test_create_orchestrator_propagates_alpaca_error(self, mock_alpaca_class):
        """Test that AlpacaManager errors are propagated."""
        mock_alpaca_class.side_effect = ValueError("Invalid Alpaca credentials")

        with pytest.raises(ValueError, match="Invalid Alpaca credentials"):
            create_orchestrator("api_key", "secret_key", paper=True)

    @patch("the_alchemiser.strategy_v2.core.factory.AlpacaManager")
    @patch("the_alchemiser.strategy_v2.core.factory.StrategyMarketDataAdapter")
    def test_create_orchestrator_propagates_adapter_error(
        self, mock_adapter_class, mock_alpaca_class
    ):
        """Test that StrategyMarketDataAdapter errors are propagated."""
        mock_alpaca_class.return_value = Mock()
        mock_adapter_class.side_effect = RuntimeError("Adapter initialization failed")

        with pytest.raises(RuntimeError, match="Adapter initialization failed"):
            create_orchestrator("api_key", "secret_key", paper=True)

    @patch("the_alchemiser.strategy_v2.core.factory.logger")
    @patch("the_alchemiser.strategy_v2.core.factory.AlpacaManager")
    @patch("the_alchemiser.strategy_v2.core.factory.StrategyMarketDataAdapter")
    def test_create_orchestrator_logs_creation(
        self, mock_adapter_class, mock_alpaca_class, mock_logger
    ):
        """Test that orchestrator creation is logged."""
        mock_alpaca_class.return_value = Mock()
        mock_adapter_class.return_value = Mock()

        create_orchestrator("api_key", "secret_key", paper=True)

        # Verify info logs were called
        assert mock_logger.info.call_count >= 2
        # First call should be about creation
        first_call_msg = mock_logger.info.call_args_list[0][0][0]
        assert "Creating strategy orchestrator" in first_call_msg


class TestCreateOrchestratorWithAdapter:
    """Test create_orchestrator_with_adapter factory function."""

    def test_create_orchestrator_with_adapter_success(self):
        """Test successful orchestrator creation with adapter."""
        mock_adapter = Mock(spec=StrategyMarketDataAdapter)

        result = create_orchestrator_with_adapter(mock_adapter)

        assert isinstance(result, SingleStrategyOrchestrator)
        assert result._market_data == mock_adapter

    def test_create_orchestrator_with_adapter_none(self):
        """Test that None adapter raises ValueError."""
        with pytest.raises(ValueError, match="market_data_adapter must not be None"):
            create_orchestrator_with_adapter(None)  # type: ignore

    def test_create_orchestrator_with_adapter_invalid_type(self):
        """Test that invalid adapter type raises ValueError."""
        invalid_adapter = Mock()  # Not a StrategyMarketDataAdapter

        with pytest.raises(ValueError) as exc_info:
            create_orchestrator_with_adapter(invalid_adapter)

        assert "market_data_adapter must be StrategyMarketDataAdapter" in str(exc_info.value)

    def test_create_orchestrator_with_adapter_wrong_class(self):
        """Test that wrong class type raises ValueError."""
        # Use a plain string instead of adapter
        with pytest.raises(ValueError) as exc_info:
            create_orchestrator_with_adapter("not an adapter")  # type: ignore

        assert "must be StrategyMarketDataAdapter" in str(exc_info.value)
        assert "str" in str(exc_info.value)

    @patch("the_alchemiser.strategy_v2.core.factory.logger")
    def test_create_orchestrator_with_adapter_logs_creation(self, mock_logger):
        """Test that orchestrator creation with adapter is logged."""
        mock_adapter = Mock(spec=StrategyMarketDataAdapter)

        create_orchestrator_with_adapter(mock_adapter)

        # Verify info logs were called
        assert mock_logger.info.call_count >= 2
        # Should log about creating with adapter
        log_messages = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any("with provided adapter" in msg for msg in log_messages)
        assert any("created successfully" in msg for msg in log_messages)

    @patch("the_alchemiser.strategy_v2.core.factory.logger")
    def test_create_orchestrator_with_adapter_logs_none_error(self, mock_logger):
        """Test that None adapter error is logged."""
        with pytest.raises(ValueError):
            create_orchestrator_with_adapter(None)  # type: ignore

        # Verify error was logged
        mock_logger.error.assert_called_once()
        error_msg = mock_logger.error.call_args[0][0]
        assert "None market_data_adapter" in error_msg


class TestFactoryIdempotency:
    """Test that factory functions can be called multiple times safely."""

    @patch("the_alchemiser.strategy_v2.core.factory.AlpacaManager")
    @patch("the_alchemiser.strategy_v2.core.factory.StrategyMarketDataAdapter")
    def test_create_orchestrator_multiple_calls(self, mock_adapter_class, mock_alpaca_class):
        """Test that multiple calls create independent orchestrators."""
        mock_alpaca_class.return_value = Mock()
        mock_adapter_class.return_value = Mock()

        orchestrator1 = create_orchestrator("key1", "secret1", paper=True)
        orchestrator2 = create_orchestrator("key2", "secret2", paper=False)

        # Should create separate instances
        assert orchestrator1 is not orchestrator2
        # Should have called AlpacaManager twice
        assert mock_alpaca_class.call_count == 2

    def test_create_orchestrator_with_adapter_multiple_calls(self):
        """Test that multiple calls with adapters work correctly."""
        adapter1 = Mock(spec=StrategyMarketDataAdapter)
        adapter2 = Mock(spec=StrategyMarketDataAdapter)

        orchestrator1 = create_orchestrator_with_adapter(adapter1)
        orchestrator2 = create_orchestrator_with_adapter(adapter2)

        # Should create separate instances
        assert orchestrator1 is not orchestrator2
        # Each should have its own adapter
        assert orchestrator1._market_data == adapter1
        assert orchestrator2._market_data == adapter2
