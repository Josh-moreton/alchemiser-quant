"""Business Unit: shared | Status: current.

Tests for the_alchemiser.shared.config.__init__ module.

This module tests the config facade module's public API, ensuring that
all exports work correctly and the facade pattern is properly implemented.
"""

import pytest


@pytest.mark.unit
class TestConfigModuleInterface:
    """Test suite for config module public API."""

    def test_all_exports_are_defined(self) -> None:
        """Test that __all__ list matches expected exports."""
        from the_alchemiser.shared import config

        # Check __all__ exists
        assert hasattr(config, "__all__"), "Module must define __all__"

        expected_exports = {
            "Config",
            "Settings",
            "classify_symbol",
            "get_etf_symbols",
            "is_etf",
            "load_settings",
        }
        actual_exports = set(config.__all__)

        assert (
            actual_exports == expected_exports
        ), f"__all__ mismatch. Expected: {expected_exports}, Got: {actual_exports}"

    def test_all_exports_are_importable(self) -> None:
        """Test that all items in __all__ can be imported."""
        from the_alchemiser.shared import config

        for export_name in config.__all__:
            assert hasattr(
                config, export_name
            ), f"Export '{export_name}' in __all__ but not found in module"

    def test_settings_export(self) -> None:
        """Test Settings class is correctly exported."""
        from the_alchemiser.shared.config import Settings

        assert Settings is not None
        # Settings is a Pydantic BaseSettings class
        assert hasattr(Settings, "model_config") or hasattr(
            Settings, "__init__"
        ), "Settings should be a Pydantic model"

    def test_config_alias(self) -> None:
        """Test Config is an alias for Settings (backward compatibility)."""
        from the_alchemiser.shared.config import Config, Settings

        assert Config is Settings, "Config should be an alias for Settings"

    def test_load_settings_export(self) -> None:
        """Test load_settings function is correctly exported."""
        from the_alchemiser.shared.config import load_settings

        assert load_settings is not None
        assert callable(load_settings), "load_settings should be callable"

        # Test that it returns a Settings instance
        settings = load_settings()
        from the_alchemiser.shared.config import Settings

        assert isinstance(
            settings, Settings
        ), "load_settings should return Settings instance"

    def test_classify_symbol_export(self) -> None:
        """Test classify_symbol function is correctly exported."""
        from the_alchemiser.shared.config import classify_symbol

        assert classify_symbol is not None
        assert callable(classify_symbol), "classify_symbol should be callable"

        # Test basic functionality
        result = classify_symbol("AAPL")
        assert result in [
            "STOCK",
            "ETF",
            "CRYPTO",
            "OPTION",
            "FUTURE",
        ], "classify_symbol should return a valid asset type"

    def test_is_etf_export(self) -> None:
        """Test is_etf function is correctly exported."""
        from the_alchemiser.shared.config import is_etf

        assert is_etf is not None
        assert callable(is_etf), "is_etf should be callable"

        # Test basic functionality
        assert isinstance(is_etf("SPY"), bool), "is_etf should return bool"

    def test_get_etf_symbols_export(self) -> None:
        """Test get_etf_symbols function is correctly exported."""
        from the_alchemiser.shared.config import get_etf_symbols

        assert get_etf_symbols is not None
        assert callable(get_etf_symbols), "get_etf_symbols should be callable"

        # Test basic functionality
        symbols = get_etf_symbols()
        assert isinstance(symbols, set), "get_etf_symbols should return a set"
        assert len(symbols) > 0, "get_etf_symbols should return non-empty set"

    def test_no_unintended_exports(self) -> None:
        """Test that only intended items are exported (no leaks)."""
        from the_alchemiser.shared import config

        # Get all public symbols (excluding dunder)
        public_symbols = [name for name in dir(config) if not name.startswith("_")]

        # Get __all__
        declared_exports = set(config.__all__)

        # Public symbols should only include __all__ items (and no extras)
        extra_exports = set(public_symbols) - declared_exports

        # Allow module-level metadata, stdlib imports, and submodules
        # Note: Python imports make submodules visible even if not in __all__
        # This is expected behavior for facade modules
        allowed_extras = {
            "annotations",  # from __future__ import annotations (if present)
            # Submodules (imported by this module)
            "config",  # .config submodule
            "symbols_config",  # .symbols_config submodule
            "strategy_profiles",  # transitive import from .config
        }

        unexpected_exports = extra_exports - allowed_extras

        assert not unexpected_exports, (
            f"Unexpected public exports found (not in __all__): {unexpected_exports}. "
            f"Either add to __all__ or prefix with underscore."
        )

    def test_star_import_behavior(self) -> None:
        """Test that 'from config import *' only imports __all__ items."""
        # Create a clean namespace
        namespace: dict[str, object] = {}
        exec("from the_alchemiser.shared.config import *", namespace)

        # Remove builtins
        imported_names = {
            name for name in namespace.keys() if not name.startswith("__")
        }

        expected_names = {
            "Config",
            "Settings",
            "classify_symbol",
            "get_etf_symbols",
            "is_etf",
            "load_settings",
        }

        assert (
            imported_names == expected_names
        ), f"Star import should only import __all__ items. Got: {imported_names}, Expected: {expected_names}"

    def test_module_has_docstring(self) -> None:
        """Test module has proper docstring with business unit marker."""
        from the_alchemiser.shared import config

        assert config.__doc__ is not None, "Module must have docstring"
        assert (
            "Business Unit: shared" in config.__doc__
        ), "Docstring must contain business unit marker"
        assert (
            "Status: current" in config.__doc__
        ), "Docstring must contain status marker"

    def test_backward_compatibility_config_alias(self) -> None:
        """Test that Config alias works in practice for backward compatibility."""
        from the_alchemiser.shared.config import Config

        # Should be able to instantiate using Config
        config_instance = Config()

        # Should have same attributes as Settings
        assert hasattr(config_instance, "alpaca"), "Config should have alpaca settings"
        assert hasattr(
            config_instance, "strategy"
        ), "Config should have strategy settings"
        assert hasattr(config_instance, "aws"), "Config should have aws settings"

    def test_settings_structure(self) -> None:
        """Test Settings has expected nested configuration structure."""
        from the_alchemiser.shared.config import Settings

        settings = Settings()

        # Verify nested settings exist
        assert hasattr(settings, "logging"), "Settings should have logging config"
        assert hasattr(settings, "alpaca"), "Settings should have alpaca config"
        assert hasattr(settings, "aws"), "Settings should have aws config"
        assert hasattr(settings, "alerts"), "Settings should have alerts config"
        assert hasattr(settings, "strategy"), "Settings should have strategy config"
        assert hasattr(settings, "email"), "Settings should have email config"
        assert hasattr(settings, "data"), "Settings should have data config"
        assert hasattr(settings, "tracking"), "Settings should have tracking config"
        assert hasattr(
            settings, "trade_ledger"
        ), "Settings should have trade_ledger config"
        assert hasattr(
            settings, "execution"
        ), "Settings should have execution config"

    def test_symbol_classification_integration(self) -> None:
        """Test symbol classification functions work correctly."""
        from the_alchemiser.shared.config import (
            classify_symbol,
            get_etf_symbols,
            is_etf,
        )

        # Test classify_symbol
        assert classify_symbol("SPY") == "ETF"
        assert classify_symbol("AAPL") == "STOCK"
        assert classify_symbol("BTCUSD") == "CRYPTO"

        # Test is_etf
        assert is_etf("SPY") is True
        assert is_etf("QQQ") is True
        assert is_etf("AAPL") is False

        # Test get_etf_symbols
        etf_symbols = get_etf_symbols()
        assert "SPY" in etf_symbols
        assert "QQQ" in etf_symbols
        assert isinstance(etf_symbols, set)

    def test_module_structure(self) -> None:
        """Test module is a package with expected structure."""
        from the_alchemiser.shared import config

        # Should be a package (has __path__ or __file__ points to __init__.py)
        assert hasattr(config, "__file__"), "Module should have __file__ attribute"
        assert config.__file__.endswith(
            "__init__.py"
        ), "Module __file__ should point to __init__.py"

    def test_repeated_import_returns_same_object(self) -> None:
        """Test that repeated imports return the same objects (singleton behavior)."""
        from the_alchemiser.shared.config import Settings as Settings1
        from the_alchemiser.shared.config import Settings as Settings2

        assert Settings1 is Settings2, "Repeated imports should return same class"

        from the_alchemiser.shared.config import load_settings as load_settings1
        from the_alchemiser.shared.config import load_settings as load_settings2

        assert (
            load_settings1 is load_settings2
        ), "Repeated imports should return same function"

    def test_invalid_attribute_access_raises_error(self) -> None:
        """Test that accessing non-existent attributes raises AttributeError."""
        from the_alchemiser.shared import config

        with pytest.raises(AttributeError):
            _ = config.NonExistentAttribute  # type: ignore[attr-defined]

    def test_all_exports_are_accessible(self) -> None:
        """Test all exports can be accessed via dot notation."""
        from the_alchemiser.shared import config

        for export_name in config.__all__:
            attr = getattr(config, export_name)
            assert attr is not None, f"Export {export_name} should not be None"
