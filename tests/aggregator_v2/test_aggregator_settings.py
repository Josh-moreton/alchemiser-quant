"""Business Unit: aggregator_v2 | Status: current.

Unit tests for AggregatorSettings configuration.
"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from the_alchemiser.aggregator_v2.config.aggregator_settings import (
    AggregatorSettings,
)


class TestAggregatorSettings:
    """Tests for AggregatorSettings configuration class."""

    def test_default_values(self) -> None:
        """Test that default values are set correctly."""
        settings = AggregatorSettings()

        assert settings.aggregation_table_name == ""
        assert settings.allocation_tolerance == 0.01

    def test_custom_values(self) -> None:
        """Test settings with custom values."""
        settings = AggregatorSettings(
            aggregation_table_name="custom-table",
            allocation_tolerance=0.05,
        )

        assert settings.aggregation_table_name == "custom-table"
        assert settings.allocation_tolerance == 0.05

    def test_from_environment(self) -> None:
        """Test loading settings from environment variables."""
        env_vars = {
            "AGGREGATION_TABLE_NAME": "env-table",
            "ALLOCATION_TOLERANCE": "0.02",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            settings = AggregatorSettings.from_environment()

            assert settings.aggregation_table_name == "env-table"
            assert settings.allocation_tolerance == 0.02

    def test_from_environment_with_defaults(self) -> None:
        """Test that defaults are used when env vars are not set."""
        env_vars_to_clear = [
            "AGGREGATION_TABLE_NAME",
            "ALLOCATION_TOLERANCE",
        ]

        clean_env = {k: v for k, v in os.environ.items() if k not in env_vars_to_clear}

        with patch.dict(os.environ, clean_env, clear=True):
            settings = AggregatorSettings.from_environment()

            assert settings.aggregation_table_name == ""
            assert settings.allocation_tolerance == 0.01
