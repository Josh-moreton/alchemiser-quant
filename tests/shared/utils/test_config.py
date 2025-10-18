"""Tests for shared.utils.config module.

This module tests the placeholder configuration utilities that will be
enhanced in Phase 2. Currently validates basic get/set functionality
and proper initialization.
"""

from __future__ import annotations

from the_alchemiser.shared.utils.config import (
    ModularConfig,
    get_global_config,
    load_module_config,
)


class TestModularConfig:
    """Test suite for ModularConfig placeholder class."""

    def test_initialization(self) -> None:
        """Test that ModularConfig initializes with empty config."""
        config = ModularConfig()
        assert config._config == {}

    def test_get_nonexistent_key_returns_none(self) -> None:
        """Test that get returns None for nonexistent keys."""
        config = ModularConfig()
        result = config.get("nonexistent")
        assert result is None

    def test_get_nonexistent_key_returns_default(self) -> None:
        """Test that get returns default value for nonexistent keys."""
        config = ModularConfig()
        result = config.get("nonexistent", "default_value")
        assert result == "default_value"

    def test_set_and_get_string_value(self) -> None:
        """Test setting and getting string configuration values."""
        config = ModularConfig()
        config.set("test_key", "test_value")
        assert config.get("test_key") == "test_value"

    def test_set_and_get_integer_value(self) -> None:
        """Test setting and getting integer configuration values."""
        config = ModularConfig()
        config.set("count", 42)
        assert config.get("count") == 42

    def test_set_and_get_dict_value(self) -> None:
        """Test setting and getting dict configuration values."""
        config = ModularConfig()
        test_dict = {"nested": "value", "count": 123}
        config.set("complex", test_dict)
        assert config.get("complex") == test_dict

    def test_set_and_get_list_value(self) -> None:
        """Test setting and getting list configuration values."""
        config = ModularConfig()
        test_list = ["item1", "item2", "item3"]
        config.set("items", test_list)
        assert config.get("items") == test_list

    def test_set_overwrites_existing_value(self) -> None:
        """Test that set overwrites existing configuration values."""
        config = ModularConfig()
        config.set("key", "original")
        config.set("key", "updated")
        assert config.get("key") == "updated"

    def test_multiple_keys_independent(self) -> None:
        """Test that multiple configuration keys are independent."""
        config = ModularConfig()
        config.set("key1", "value1")
        config.set("key2", "value2")
        assert config.get("key1") == "value1"
        assert config.get("key2") == "value2"

    def test_get_with_default_does_not_modify_config(self) -> None:
        """Test that getting with default doesn't modify internal state."""
        config = ModularConfig()
        config.get("nonexistent", "default")
        # Verify the key was not added to internal config
        assert "nonexistent" not in config._config

    def test_set_none_value(self) -> None:
        """Test that None can be explicitly set as a value."""
        config = ModularConfig()
        config.set("nullable", None)
        # Should return None because it's explicitly set, not because key is missing
        assert config.get("nullable") is None
        assert "nullable" in config._config

    def test_empty_string_key(self) -> None:
        """Test handling of empty string as key."""
        config = ModularConfig()
        config.set("", "empty_key_value")
        assert config.get("") == "empty_key_value"

    def test_boolean_values(self) -> None:
        """Test setting and getting boolean configuration values."""
        config = ModularConfig()
        config.set("enabled", True)
        config.set("disabled", False)
        assert config.get("enabled") is True
        assert config.get("disabled") is False


class TestLoadModuleConfig:
    """Test suite for load_module_config function."""

    def test_returns_modular_config_instance(self) -> None:
        """Test that load_module_config returns ModularConfig instance."""
        config = load_module_config()
        assert isinstance(config, ModularConfig)

    def test_returns_empty_config(self) -> None:
        """Test that load_module_config returns empty configuration."""
        config = load_module_config()
        assert config._config == {}

    def test_multiple_calls_return_independent_instances(self) -> None:
        """Test that multiple calls return independent instances."""
        config1 = load_module_config()
        config2 = load_module_config()

        # Modify one instance
        config1.set("test", "value")

        # Verify the other instance is unaffected
        assert config1.get("test") == "value"
        assert config2.get("test") is None


class TestGetGlobalConfig:
    """Test suite for get_global_config function."""

    def test_returns_modular_config_instance(self) -> None:
        """Test that get_global_config returns ModularConfig instance."""
        config = get_global_config()
        assert isinstance(config, ModularConfig)

    def test_returns_empty_config(self) -> None:
        """Test that get_global_config returns empty configuration."""
        config = get_global_config()
        assert config._config == {}

    def test_multiple_calls_return_independent_instances(self) -> None:
        """Test that multiple calls return independent instances."""
        config1 = get_global_config()
        config2 = get_global_config()

        # Modify one instance
        config1.set("global", "setting")

        # Verify the other instance is unaffected (no singleton behavior yet)
        assert config1.get("global") == "setting"
        assert config2.get("global") is None


class TestConfigTypeSafety:
    """Test suite for type safety of configuration values."""

    def test_accepts_any_type_for_value(self) -> None:
        """Test that config accepts values of any type."""
        config = ModularConfig()

        # Various types should all be accepted
        config.set("string", "text")
        config.set("int", 123)
        config.set("float", 3.14)
        config.set("bool", True)
        config.set("list", [1, 2, 3])
        config.set("dict", {"key": "value"})
        config.set("tuple", (1, 2))
        config.set("none", None)

        # All should be retrievable
        assert config.get("string") == "text"
        assert config.get("int") == 123
        assert config.get("float") == 3.14
        assert config.get("bool") is True
        assert config.get("list") == [1, 2, 3]
        assert config.get("dict") == {"key": "value"}
        assert config.get("tuple") == (1, 2)
        assert config.get("none") is None
