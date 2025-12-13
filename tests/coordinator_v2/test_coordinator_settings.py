"""Business Unit: coordinator_v2 | Status: current.

Unit tests for CoordinatorSettings configuration.
"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from the_alchemiser.coordinator_v2.config.coordinator_settings import (
    CoordinatorSettings,
)


class TestCoordinatorSettings:
    """Tests for CoordinatorSettings configuration class."""

    def test_default_values(self) -> None:
        """Test that default values are set correctly."""
        settings = CoordinatorSettings()

        # Defaults from implementation
        assert settings.aggregation_table_name == ""
        assert settings.strategy_lambda_function_name == ""
        assert settings.aggregation_timeout_seconds == 600
        assert settings.enable_multi_node is False

    def test_custom_values(self) -> None:
        """Test settings with custom values."""
        settings = CoordinatorSettings(
            aggregation_table_name="custom-table",
            strategy_lambda_function_name="CustomLambda",
            aggregation_timeout_seconds=300,
            enable_multi_node=True,
        )

        assert settings.aggregation_table_name == "custom-table"
        assert settings.strategy_lambda_function_name == "CustomLambda"
        assert settings.aggregation_timeout_seconds == 300
        assert settings.enable_multi_node is True

    def test_from_environment(self) -> None:
        """Test loading settings from environment variables."""
        env_vars = {
            "AGGREGATION_TABLE_NAME": "env-table",
            "STRATEGY_FUNCTION_NAME": "EnvStrategyLambda",
            "AGGREGATION_TIMEOUT_SECONDS": "120",
            "ENABLE_MULTI_NODE_STRATEGY": "true",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            settings = CoordinatorSettings.from_environment()

            assert settings.aggregation_table_name == "env-table"
            assert settings.strategy_lambda_function_name == "EnvStrategyLambda"
            assert settings.aggregation_timeout_seconds == 120
            assert settings.enable_multi_node is True

    def test_from_environment_with_defaults(self) -> None:
        """Test that defaults are used when env vars are not set."""
        env_vars_to_clear = [
            "AGGREGATION_TABLE_NAME",
            "STRATEGY_FUNCTION_NAME",
            "AGGREGATION_TIMEOUT_SECONDS",
            "ENABLE_MULTI_NODE_STRATEGY",
        ]

        clean_env = {k: v for k, v in os.environ.items() if k not in env_vars_to_clear}

        with patch.dict(os.environ, clean_env, clear=True):
            settings = CoordinatorSettings.from_environment()

            assert settings.aggregation_table_name == ""
            assert settings.strategy_lambda_function_name == ""
            assert settings.aggregation_timeout_seconds == 600
            assert settings.enable_multi_node is False

    def test_enable_multi_node_false_by_default(self) -> None:
        """Test that multi-node mode is disabled by default."""
        env_vars: dict[str, str] = {}
        with patch.dict(os.environ, env_vars, clear=True):
            settings = CoordinatorSettings.from_environment()
            assert settings.enable_multi_node is False

    def test_enable_multi_node_case_insensitive(self) -> None:
        """Test that ENABLE_MULTI_NODE_STRATEGY is case-insensitive."""
        for true_value in ["true", "True", "TRUE"]:
            env_vars = {"ENABLE_MULTI_NODE_STRATEGY": true_value}
            with patch.dict(os.environ, env_vars, clear=True):
                settings = CoordinatorSettings.from_environment()
                assert settings.enable_multi_node is True

        for false_value in ["false", "False", "FALSE", "no", "0", ""]:
            env_vars = {"ENABLE_MULTI_NODE_STRATEGY": false_value}
            with patch.dict(os.environ, env_vars, clear=True):
                settings = CoordinatorSettings.from_environment()
                assert settings.enable_multi_node is False
