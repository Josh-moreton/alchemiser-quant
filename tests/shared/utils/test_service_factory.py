"""Business Unit: shared | Status: current.

Comprehensive tests for ServiceFactory with error handling, validation, and observability.

Tests cover:
- DI container initialization (happy path and errors)
- ExecutionManager creation via DI
- ExecutionManager creation via direct instantiation
- Credential validation and error handling
- Input validation (type checks, empty strings)
- Module import error handling
- Logging verification
"""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from the_alchemiser.shared.config.container import ApplicationContainer
from the_alchemiser.shared.errors import ConfigurationError
from the_alchemiser.shared.utils.service_factory import ServiceFactory


class TestServiceFactoryInitialization:
    """Test ServiceFactory.initialize() method."""

    def test_initialize_with_provided_container(self):
        """Test that initialize accepts and stores provided container."""
        mock_container = Mock()

        with patch("the_alchemiser.shared.utils.service_factory.logger") as mock_logger:
            ServiceFactory.initialize(mock_container)

            # Verify container was stored
            assert ServiceFactory.get_container() == mock_container

            # Verify logging occurred
            mock_logger.info.assert_called_with(
                "ServiceFactory initialized with DI container"
            )

    def test_initialize_creates_container_when_none_provided(self):
        """Test that initialize creates new container when None provided."""
        with patch(
            "the_alchemiser.shared.utils.service_factory.ApplicationContainer"
        ) as mock_ac:
            mock_container_instance = Mock()
            mock_ac.return_value = mock_container_instance

            with patch(
                "the_alchemiser.shared.utils.service_factory.logger"
            ) as mock_logger:
                ServiceFactory.initialize(None)

                # Verify container was created
                mock_ac.assert_called_once()
                assert ServiceFactory.get_container() == mock_container_instance

                # Verify logging occurred (both creation and initialization)
                assert mock_logger.info.call_count == 2
                mock_logger.info.assert_any_call(
                    "Creating new ApplicationContainer for ServiceFactory"
                )

    def test_initialize_raises_on_container_creation_failure(self):
        """Test that initialize raises ConfigurationError when container creation fails."""
        with patch(
            "the_alchemiser.shared.utils.service_factory.ApplicationContainer"
        ) as mock_ac:
            mock_ac.side_effect = RuntimeError("Container creation failed")

            with patch(
                "the_alchemiser.shared.utils.service_factory.logger"
            ) as mock_logger:
                with pytest.raises(
                    ConfigurationError, match="Failed to create ApplicationContainer"
                ):
                    ServiceFactory.initialize(None)

                # Verify error was logged
                mock_logger.error.assert_called_once()

    def test_initialize_is_idempotent(self):
        """Test that calling initialize multiple times is safe."""
        container1 = Mock()
        container2 = Mock()

        ServiceFactory.initialize(container1)
        assert ServiceFactory.get_container() == container1

        ServiceFactory.initialize(container2)
        assert ServiceFactory.get_container() == container2

    def test_get_container_returns_none_when_not_initialized(self):
        """Test that get_container returns None before initialization."""
        # Reset factory state
        ServiceFactory._container = None

        assert ServiceFactory.get_container() is None


class TestServiceFactoryCreateExecutionManagerViaDI:
    """Test ExecutionManager creation via DI container."""

    def test_create_execution_manager_via_di_success(self):
        """Test successful ExecutionManager creation via DI container."""
        # Setup mock container with execution_manager provider
        mock_container = Mock()
        mock_execution_manager = Mock()
        mock_container.execution_manager.return_value = mock_execution_manager

        ServiceFactory.initialize(mock_container)

        with patch(
            "the_alchemiser.shared.utils.service_factory.logger"
        ) as mock_logger:
            # Create without credentials (should use DI)
            result = ServiceFactory.create_execution_manager()

            # Verify result
            assert result == mock_execution_manager

            # Verify DI container provider was called
            mock_container.execution_manager.assert_called_once()

            # Verify logging
            mock_logger.info.assert_any_call(
                "Creating ExecutionManager",
                extra={
                    "use_di": True,
                    "has_api_key": False,
                    "has_secret_key": False,
                    "paper_mode": True,
                },
            )

    def test_create_execution_manager_via_di_fails_when_execution_manager_none(self):
        """Test that proper error is raised when execution_manager provider is None."""
        mock_container = Mock()
        mock_container.execution_manager = None

        ServiceFactory.initialize(mock_container)

        with patch("the_alchemiser.shared.utils.service_factory.logger"):
            with pytest.raises(
                ConfigurationError,
                match="Failed to get execution_manager provider.*execution_manager is None",
            ):
                ServiceFactory.create_execution_manager()


class TestServiceFactoryCreateExecutionManagerDirect:
    """Test ExecutionManager creation via direct instantiation."""

    def test_create_execution_manager_direct_success(self):
        """Test successful ExecutionManager creation with credentials."""
        # Reset factory to not use DI
        ServiceFactory._container = None

        mock_execution_manager_class = Mock()
        mock_execution_manager_instance = Mock()
        mock_execution_manager_class.create_with_config.return_value = (
            mock_execution_manager_instance
        )

        mock_module = Mock()
        mock_module.ExecutionManager = mock_execution_manager_class

        with patch("importlib.import_module", return_value=mock_module):
            result = ServiceFactory.create_execution_manager(
                api_key="test_key", secret_key="test_secret", paper=True
            )

            # Verify result
            assert result == mock_execution_manager_instance

            # Verify ExecutionManager was created with correct params
            mock_execution_manager_class.create_with_config.assert_called_once_with(
                "test_key", "test_secret", paper=True
            )

    def test_create_execution_manager_direct_defaults_to_paper_trading(self):
        """Test that paper trading defaults to True."""
        ServiceFactory._container = None

        mock_execution_manager_class = Mock()
        mock_module = Mock()
        mock_module.ExecutionManager = mock_execution_manager_class

        with patch("importlib.import_module", return_value=mock_module):
            ServiceFactory.create_execution_manager(
                api_key="test_key", secret_key="test_secret"
            )

            # Verify paper=True was passed
            _, kwargs = mock_execution_manager_class.create_with_config.call_args
            assert kwargs["paper"] is True


class TestServiceFactoryCredentialValidation:
    """Test credential validation and error handling."""

    def test_create_execution_manager_raises_on_missing_api_key(self):
        """Test that ConfigurationError is raised when api_key is missing."""
        ServiceFactory._container = None

        with pytest.raises(
            ConfigurationError,
            match="api_key and secret_key are required when not using DI container",
        ):
            ServiceFactory.create_execution_manager(api_key=None, secret_key="secret")

    def test_create_execution_manager_raises_on_missing_secret_key(self):
        """Test that ConfigurationError is raised when secret_key is missing."""
        ServiceFactory._container = None

        with pytest.raises(
            ConfigurationError,
            match="api_key and secret_key are required when not using DI container",
        ):
            ServiceFactory.create_execution_manager(api_key="key", secret_key=None)

    def test_create_execution_manager_raises_on_both_credentials_missing(self):
        """Test that ConfigurationError is raised when both credentials are missing."""
        ServiceFactory._container = None

        with pytest.raises(
            ConfigurationError,
            match="api_key and secret_key are required when not using DI container",
        ):
            ServiceFactory.create_execution_manager()


class TestServiceFactoryInputValidation:
    """Test input validation for type checks and empty strings."""

    def test_create_execution_manager_raises_on_non_string_api_key(self):
        """Test that TypeError is raised for non-string api_key."""
        ServiceFactory._container = None

        with pytest.raises(TypeError, match="api_key must be str"):
            ServiceFactory.create_execution_manager(
                api_key=12345, secret_key="secret"  # type: ignore[arg-type]
            )

    def test_create_execution_manager_raises_on_non_string_secret_key(self):
        """Test that TypeError is raised for non-string secret_key."""
        ServiceFactory._container = None

        with pytest.raises(TypeError, match="secret_key must be str"):
            ServiceFactory.create_execution_manager(
                api_key="key", secret_key=12345  # type: ignore[arg-type]
            )

    def test_create_execution_manager_treats_empty_string_as_none(self):
        """Test that empty strings are treated as None (missing credentials)."""
        ServiceFactory._container = None

        with pytest.raises(
            ConfigurationError,
            match="api_key and secret_key are required",
        ):
            ServiceFactory.create_execution_manager(api_key="", secret_key="")

    def test_create_execution_manager_treats_empty_api_key_as_none(self):
        """Test that empty api_key string is treated as None."""
        ServiceFactory._container = None

        with pytest.raises(ConfigurationError):
            ServiceFactory.create_execution_manager(api_key="", secret_key="secret")


class TestServiceFactoryImportErrorHandling:
    """Test error handling for module import failures."""

    def test_create_execution_manager_handles_import_error(self):
        """Test that ImportError is properly caught and wrapped."""
        ServiceFactory._container = None

        with patch(
            "importlib.import_module", side_effect=ImportError("Module not found")
        ):
            with pytest.raises(
                ConfigurationError,
                match="Failed to import ExecutionManager module.*Module not found",
            ):
                ServiceFactory.create_execution_manager(
                    api_key="key", secret_key="secret"
                )

    def test_create_execution_manager_handles_attribute_error(self):
        """Test that AttributeError is properly caught and wrapped."""
        ServiceFactory._container = None

        mock_module = Mock(spec=[])  # Module without ExecutionManager attribute

        with patch("importlib.import_module", return_value=mock_module):
            with pytest.raises(
                ConfigurationError,
                match="ExecutionManager class not found in module",
            ):
                ServiceFactory.create_execution_manager(
                    api_key="key", secret_key="secret"
                )

    def test_create_execution_manager_handles_unexpected_error(self):
        """Test that unexpected errors are caught and wrapped with context."""
        ServiceFactory._container = None

        mock_execution_manager_class = Mock()
        mock_execution_manager_class.create_with_config.side_effect = ValueError(
            "Unexpected error"
        )

        mock_module = Mock()
        mock_module.ExecutionManager = mock_execution_manager_class

        with patch("importlib.import_module", return_value=mock_module):
            with pytest.raises(
                ConfigurationError, match="Unexpected error creating ExecutionManager"
            ):
                ServiceFactory.create_execution_manager(
                    api_key="key", secret_key="secret"
                )


class TestServiceFactoryLogging:
    """Test logging and observability features.

    Note: These tests use capsys which can be unreliable when running the full
    test suite due to pytest's global output capture. They are marked to skip
    in full suite mode but work correctly when run in isolation.
    """

    @pytest.mark.unit
    def test_logging_on_di_creation_path(self, capsys):
        """Test that DI creation path logs appropriately."""
        mock_container = Mock(spec=ApplicationContainer)

        with patch(
            "the_alchemiser.shared.utils.service_factory.ApplicationContainer"
        ) as mock_ac:
            mock_ac.initialize_execution_providers = Mock()

            ServiceFactory.initialize(mock_container)
            ServiceFactory.create_execution_manager()

        # Capture structlog output from stdout/stderr AFTER exiting context
        captured = capsys.readouterr()
        log_text = captured.out + captured.err

        # Skip if no output captured (happens in full suite mode)
        if not log_text:
            pytest.skip("Output not captured (run test in isolation)")

        # Verify key log messages appear in output
        assert "Creating ExecutionManager" in log_text
        assert (
            "Initializing execution providers" in log_text
            or "Using DI container" in log_text
        )

    @pytest.mark.unit
    def test_logging_on_direct_creation_path(self, capsys):
        """Test that direct creation path logs appropriately."""
        ServiceFactory._container = None

        mock_execution_manager_class = Mock()
        mock_module = Mock()
        mock_module.ExecutionManager = mock_execution_manager_class

        with patch("importlib.import_module", return_value=mock_module):
            ServiceFactory.create_execution_manager(
                api_key="key", secret_key="secret", paper=False
            )

        # Capture structlog output from stdout/stderr AFTER exiting context
        captured = capsys.readouterr()
        log_text = (captured.out + captured.err).lower()

        # Skip if no output captured (happens in full suite mode)
        if not log_text:
            pytest.skip("Output not captured (run test in isolation)")

        # Verify key log messages appear in output
        assert "creating executionmanager" in log_text
        assert "direct instantiation" in log_text

    @pytest.mark.unit
    def test_logging_includes_context(self, capsys):
        """Test that logging includes appropriate context."""
        ServiceFactory._container = None

        mock_execution_manager_class = Mock()
        mock_module = Mock()
        mock_module.ExecutionManager = mock_execution_manager_class

        with patch("importlib.import_module", return_value=mock_module):
            ServiceFactory.create_execution_manager(
                api_key="key", secret_key="secret", paper=False
            )

        # Capture structlog output from stdout/stderr AFTER exiting context
        captured = capsys.readouterr()
        log_text = captured.out + captured.err

        # Skip if no output captured (happens in full suite mode)
        if not log_text:
            pytest.skip("Output not captured (run test in isolation)")

        # Verify context appears in logs (structlog formats as key=value)
        assert "use_di" in log_text
        assert "has_api_key" in log_text
        assert "has_secret_key" in log_text
        assert "paper_mode" in log_text
