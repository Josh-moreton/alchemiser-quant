"""Test config module for complexity reduction validation."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from the_alchemiser.shared.config.config import StrategySettings

if TYPE_CHECKING:
    pass


class TestStrategySettingsComplexityRefactor:
    """Test refactored StrategySettings methods."""

    def test_get_stage_profile_prod(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test _get_stage_profile returns production profile."""
        monkeypatch.setenv("APP__STAGE", "prod")
        files, allocations = StrategySettings._get_stage_profile()
        assert isinstance(files, list)
        assert isinstance(allocations, dict)
        assert len(files) > 0
        assert len(allocations) > 0
        # Verify it's production profile by checking for prod-specific strategies
        assert "foundation/kmlm.clj" in files

    def test_get_stage_profile_dev(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test _get_stage_profile returns dev profile."""
        monkeypatch.setenv("APP__STAGE", "dev")
        files, allocations = StrategySettings._get_stage_profile()
        assert isinstance(files, list)
        assert isinstance(allocations, dict)
        assert len(files) > 0
        assert len(allocations) > 0
        # Dev has more strategies than prod
        assert "foundation/kmlm.clj" in files

    def test_get_stage_profile_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test _get_stage_profile defaults to dev when no stage set."""
        monkeypatch.delenv("APP__STAGE", raising=False)
        monkeypatch.delenv("STAGE", raising=False)
        files, allocations = StrategySettings._get_stage_profile()
        assert isinstance(files, list)
        assert isinstance(allocations, dict)
        # Should default to dev profile
        assert len(files) > 0

    def test_derive_files_from_allocations(self) -> None:
        """Test _derive_files_from_allocations method."""
        settings = StrategySettings(
            dsl_files=[],
            dsl_allocations={"file1.clj": 0.5, "file2.clj": 0.5},
        )
        settings._derive_files_from_allocations()
        assert settings.dsl_files == ["file1.clj", "file2.clj"]

    def test_derive_allocations_from_files(self) -> None:
        """Test _derive_allocations_from_files creates equal weights."""
        settings = StrategySettings(
            dsl_files=["file1.clj", "file2.clj", "file3.clj"],
            dsl_allocations={},
        )
        settings._derive_allocations_from_files()
        expected_weight = 1.0 / 3
        assert len(settings.dsl_allocations) == 3
        for file in settings.dsl_files:
            assert settings.dsl_allocations[file] == pytest.approx(expected_weight)

    def test_apply_env_profile_both_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test _apply_env_profile loads from stage when both fields empty."""
        monkeypatch.setenv("APP__STAGE", "prod")
        settings = StrategySettings()
        assert len(settings.dsl_files) > 0
        assert len(settings.dsl_allocations) > 0

    def test_apply_env_profile_explicit_values(self) -> None:
        """Test _apply_env_profile preserves explicit values."""
        explicit_files = ["custom.clj"]
        explicit_allocations = {"custom.clj": 1.0}
        settings = StrategySettings(dsl_files=explicit_files, dsl_allocations=explicit_allocations)
        # Values should be preserved
        assert settings.dsl_files == explicit_files
        assert settings.dsl_allocations == explicit_allocations

    def test_apply_env_profile_files_only(self) -> None:
        """Test _apply_env_profile derives allocations when only files provided."""
        files = ["file1.clj", "file2.clj"]
        settings = StrategySettings(dsl_files=files, dsl_allocations={})
        assert len(settings.dsl_allocations) == 2
        assert all(v == 0.5 for v in settings.dsl_allocations.values())

    def test_apply_env_profile_allocations_only(self) -> None:
        """Test _apply_env_profile derives files when only allocations provided."""
        allocations = {"file1.clj": 0.6, "file2.clj": 0.4}
        settings = StrategySettings(dsl_files=[], dsl_allocations=allocations)
        assert set(settings.dsl_files) == set(allocations.keys())
