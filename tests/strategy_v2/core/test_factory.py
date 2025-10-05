"""Business Unit: strategy | Status: current

Test strategy orchestrator factory functions.

Validates factory functions for creating strategy orchestrators with proper
input validation, error handling, and security controls.
"""

from unittest.mock import Mock, patch

import pytest

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
    def test_create_orchestrator_with_valid_credentials(
        self, mock_adapter_class, mock_alpaca_class
    ):
        """Test creating orchestrator with valid API credentials."""
        # Arrange
        api_key = "test_api_key"
        secret_key = "test_secret_key"
        mock_alpaca_instance = Mock()
        mock_adapter_instance = Mock()
        mock_alpaca_class.return_value = mock_alpaca_instance
        mock_adapter_class.return_value = mock_adapter_instance

        # Act
        orchestrator = create_orchestrator(api_key, secret_key, paper=True)

        # Assert
        assert isinstance(orchestrator, SingleStrategyOrchestrator)
        mock_alpaca_class.assert_called_once_with(
            api_key=api_key, secret_key=secret_key, paper=True
        )
        mock_adapter_class.assert_called_once_with(mock_alpaca_instance)

    @patch("the_alchemiser.strategy_v2.core.factory.AlpacaManager")
    @patch("the_alchemiser.strategy_v2.core.factory.StrategyMarketDataAdapter")
    def test_create_orchestrator_defaults_to_paper_trading(
        self, mock_adapter_class, mock_alpaca_class
    ):
        """Test that orchestrator defaults to paper trading mode."""
        # Arrange
        api_key = "test_api_key"
        secret_key = "test_secret_key"

        # Act
        create_orchestrator(api_key, secret_key)

        # Assert - paper=True should be the default
        mock_alpaca_class.assert_called_once_with(
            api_key=api_key, secret_key=secret_key, paper=True
        )

    @patch("the_alchemiser.strategy_v2.core.factory.AlpacaManager")
    @patch("the_alchemiser.strategy_v2.core.factory.StrategyMarketDataAdapter")
    def test_create_orchestrator_with_live_trading(
        self, mock_adapter_class, mock_alpaca_class
    ):
        """Test creating orchestrator with live trading mode."""
        # Arrange
        api_key = "test_api_key"
        secret_key = "test_secret_key"

        # Act
        create_orchestrator(api_key, secret_key, paper=False)

        # Assert
        mock_alpaca_class.assert_called_once_with(
            api_key=api_key, secret_key=secret_key, paper=False
        )

    @patch("the_alchemiser.strategy_v2.core.factory.AlpacaManager")
    def test_create_orchestrator_with_empty_api_key(self, mock_alpaca_class):
        """Test that empty API key is rejected."""
        # Arrange
        api_key = ""
        secret_key = "test_secret_key"

        # Act & Assert - factory now validates before calling AlpacaManager
        with pytest.raises(ValueError, match="API key must be a non-empty string"):
            create_orchestrator(api_key, secret_key)

    @patch("the_alchemiser.strategy_v2.core.factory.AlpacaManager")
    def test_create_orchestrator_with_empty_secret_key(self, mock_alpaca_class):
        """Test that empty secret key is rejected."""
        # Arrange
        api_key = "test_api_key"
        secret_key = ""

        # Act & Assert - factory now validates before calling AlpacaManager
        with pytest.raises(ValueError, match="Secret key must be a non-empty string"):
            create_orchestrator(api_key, secret_key)

    @patch("the_alchemiser.strategy_v2.core.factory.AlpacaManager")
    def test_create_orchestrator_propagates_alpaca_errors(self, mock_alpaca_class):
        """Test that AlpacaManager initialization errors are propagated."""
        # Arrange
        api_key = "invalid_key"
        secret_key = "invalid_secret"
        mock_alpaca_class.side_effect = RuntimeError("Alpaca initialization failed")

        # Act & Assert
        with pytest.raises(RuntimeError, match="Alpaca initialization failed"):
            create_orchestrator(api_key, secret_key)

    @patch("the_alchemiser.strategy_v2.core.factory.AlpacaManager")
    @patch("the_alchemiser.strategy_v2.core.factory.StrategyMarketDataAdapter")
    def test_create_orchestrator_propagates_adapter_errors(
        self, mock_adapter_class, mock_alpaca_class
    ):
        """Test that adapter initialization errors are propagated."""
        # Arrange
        api_key = "test_api_key"
        secret_key = "test_secret_key"
        mock_adapter_class.side_effect = RuntimeError("Adapter initialization failed")

        # Act & Assert
        with pytest.raises(RuntimeError, match="Adapter initialization failed"):
            create_orchestrator(api_key, secret_key)

    @patch("the_alchemiser.strategy_v2.core.factory.AlpacaManager")
    def test_create_orchestrator_with_none_api_key(self, mock_alpaca_class):
        """Test that None API key is rejected."""
        # Act & Assert
        with pytest.raises(ValueError, match="API key must be a non-empty string"):
            create_orchestrator(None, "secret")  # type: ignore[arg-type]

    @patch("the_alchemiser.strategy_v2.core.factory.AlpacaManager")
    def test_create_orchestrator_with_none_secret_key(self, mock_alpaca_class):
        """Test that None secret key is rejected."""
        # Act & Assert
        with pytest.raises(ValueError, match="Secret key must be a non-empty string"):
            create_orchestrator("api_key", None)  # type: ignore[arg-type]

    @patch("the_alchemiser.strategy_v2.core.factory.AlpacaManager")
    def test_create_orchestrator_with_whitespace_only_api_key(self, mock_alpaca_class):
        """Test that whitespace-only API key is rejected."""
        # Act & Assert
        with pytest.raises(ValueError, match="API key must be a non-empty string"):
            create_orchestrator("   ", "secret")

    @patch("the_alchemiser.strategy_v2.core.factory.AlpacaManager")
    def test_create_orchestrator_with_whitespace_only_secret_key(self, mock_alpaca_class):
        """Test that whitespace-only secret key is rejected."""
        # Act & Assert
        with pytest.raises(ValueError, match="Secret key must be a non-empty string"):
            create_orchestrator("api_key", "   ")


class TestCreateOrchestratorWithAdapter:
    """Test create_orchestrator_with_adapter factory function."""

    def test_create_orchestrator_with_valid_adapter(self):
        """Test creating orchestrator with pre-configured adapter."""
        # Arrange
        mock_adapter = Mock(spec=StrategyMarketDataAdapter)

        # Act
        orchestrator = create_orchestrator_with_adapter(mock_adapter)

        # Assert
        assert isinstance(orchestrator, SingleStrategyOrchestrator)
        # Verify the adapter was passed to the orchestrator
        assert orchestrator._market_data == mock_adapter

    def test_create_orchestrator_with_none_adapter(self):
        """Test that None adapter is rejected."""
        # Act & Assert - factory now validates inputs
        with pytest.raises(TypeError, match="market_data_adapter cannot be None"):
            create_orchestrator_with_adapter(None)  # type: ignore[arg-type]

    def test_create_orchestrator_with_invalid_adapter_type(self):
        """Test that invalid adapter type is rejected."""
        # Arrange
        invalid_adapter = "not_an_adapter"

        # Act & Assert - factory now validates inputs
        with pytest.raises(TypeError, match="must be StrategyMarketDataAdapter"):
            create_orchestrator_with_adapter(invalid_adapter)  # type: ignore[arg-type]


class TestFactoryIntegration:
    """Integration tests for factory functions."""

    def test_both_factories_produce_same_type(self):
        """Test that both factory functions produce the same orchestrator type."""
        # Arrange
        mock_adapter = Mock(spec=StrategyMarketDataAdapter)

        # Act
        with patch("the_alchemiser.strategy_v2.core.factory.AlpacaManager"):
            with patch(
                "the_alchemiser.strategy_v2.core.factory.StrategyMarketDataAdapter"
            ) as mock_adapter_class:
                mock_adapter_class.return_value = mock_adapter
                orchestrator1 = create_orchestrator("key", "secret")

        orchestrator2 = create_orchestrator_with_adapter(mock_adapter)

        # Assert - both should be the same type
        assert type(orchestrator1) == type(orchestrator2)
        assert isinstance(orchestrator1, SingleStrategyOrchestrator)
        assert isinstance(orchestrator2, SingleStrategyOrchestrator)
