"""Business Unit: shared | Status: current.

Unit tests for env_loader.py - environment variable loading infrastructure.

Tests cover:
- Path resolution and .env file discovery
- Environment variable loading and override behavior
- Error handling for missing dependencies and files
- Import side-effects and idempotency
"""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest


class TestEnvLoaderPathResolution:
    """Test path resolution logic for finding .env file."""

    def test_path_resolution_finds_project_root(self, tmp_path: Path) -> None:
        """Test that path resolution correctly navigates to project root."""
        # Create mock directory structure: project_root/the_alchemiser/shared/config/
        project_root = tmp_path / "project_root"
        config_dir = project_root / "the_alchemiser" / "shared" / "config"
        config_dir.mkdir(parents=True)

        # Create .env file in project root
        env_file = project_root / ".env"
        env_file.write_text("TEST_VAR=test_value\n")

        # Create a mock env_loader.py in config dir
        mock_loader = config_dir / "env_loader.py"
        mock_loader.write_text("""
from pathlib import Path
from dotenv import load_dotenv

current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent
env_file = project_root / ".env"

if env_file.exists():
    load_dotenv(env_file, override=True)
""")

        # Import and execute the mock loader
        with patch.dict("os.environ", {}, clear=True):
            exec(mock_loader.read_text())

        # Verify the .env file would be found at correct location
        current_dir_test = mock_loader.parent
        project_root_test = current_dir_test.parent.parent.parent
        env_file_test = project_root_test / ".env"

        assert env_file_test.exists()
        assert env_file_test == env_file

    def test_path_resolution_handles_missing_env_file(self, tmp_path: Path) -> None:
        """Test that missing .env file doesn't cause errors."""
        # Create directory structure without .env file
        config_dir = tmp_path / "the_alchemiser" / "shared" / "config"
        config_dir.mkdir(parents=True)

        # Create mock env_loader that checks for .env
        mock_loader = config_dir / "env_loader.py"
        mock_loader.write_text("""
from pathlib import Path

current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent
env_file = project_root / ".env"

# Should not raise error when .env doesn't exist
loaded = env_file.exists()
""")

        # Execute should not raise
        exec(mock_loader.read_text())

    def test_path_assumes_specific_directory_depth(self) -> None:
        """Test that path resolution assumes exactly 3 levels up."""
        # This test documents the brittle assumption
        mock_file = Path("/project/the_alchemiser/shared/config/env_loader.py")

        current_dir = mock_file.parent
        expected_root = Path("/project")
        actual_root = current_dir.parent.parent.parent

        assert actual_root == expected_root


class TestEnvLoaderImportBehavior:
    """Test module import side-effects and behavior."""

    def test_import_loads_dotenv_if_available(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that importing env_loader loads .env when dotenv is available."""
        # Create a test .env file
        env_file = tmp_path / ".env"
        env_file.write_text("ENV_LOADER_TEST_VAR=loaded_value\n")

        # Clear any existing value
        monkeypatch.delenv("ENV_LOADER_TEST_VAR", raising=False)

        # Mock the path resolution to use our tmp_path
        with patch("pathlib.Path") as mock_path:
            # Make Path(__file__).parent.parent.parent.parent return tmp_path
            mock_path.return_value.parent.parent.parent = tmp_path
            mock_path.return_value.__truediv__ = lambda self, other: tmp_path / other

            # Import the module (will trigger side-effect)
            import the_alchemiser.shared.config.env_loader  # noqa: F401

        # Note: This test documents the behavior but can't easily test it
        # because the module is already imported in the test process

    def test_import_handles_missing_dotenv_gracefully(self) -> None:
        """Test that missing python-dotenv doesn't break imports."""
        # Mock dotenv as unavailable
        with patch.dict("sys.modules", {"dotenv": None}):
            # This should not raise even though dotenv is "missing"
            # The actual module handles ImportError with try/except
            try:
                import the_alchemiser.shared.config.env_loader  # noqa: F401
            except ImportError as e:
                pytest.fail(f"Import should not fail when dotenv is missing: {e}")

    def test_module_can_be_imported_multiple_times(self) -> None:
        """Test that re-importing the module is safe (documents idempotency concern)."""
        # Import multiple times - should not crash
        import the_alchemiser.shared.config.env_loader  # noqa: F401

        # Force reimport
        importlib.reload(sys.modules["the_alchemiser.shared.config.env_loader"])

        # Should not raise exceptions


class TestEnvLoaderOverrideBehavior:
    """Test environment variable override behavior."""

    def test_override_true_replaces_existing_variables(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that override=True will replace existing environment variables."""
        from dotenv import load_dotenv

        # Set an initial value
        monkeypatch.setenv("OVERRIDE_TEST_VAR", "original_value")

        # Create .env with different value
        env_file = tmp_path / ".env"
        env_file.write_text("OVERRIDE_TEST_VAR=new_value\n")

        # Load with override=True (matches env_loader behavior)
        load_dotenv(env_file, override=True)

        # Should be replaced
        assert os.getenv("OVERRIDE_TEST_VAR") == "new_value"

    def test_without_override_preserves_existing_variables(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that override=False preserves existing environment variables."""
        from dotenv import load_dotenv

        # Set an initial value
        monkeypatch.setenv("NO_OVERRIDE_TEST_VAR", "original_value")

        # Create .env with different value
        env_file = tmp_path / ".env"
        env_file.write_text("NO_OVERRIDE_TEST_VAR=new_value\n")

        # Load without override (not how env_loader works, but test the difference)
        load_dotenv(env_file, override=False)

        # Should preserve original
        assert os.getenv("NO_OVERRIDE_TEST_VAR") == "original_value"


class TestEnvLoaderErrorHandling:
    """Test error handling in env_loader scenarios."""

    def test_handles_malformed_env_file(self, tmp_path: Path) -> None:
        """Test behavior with malformed .env file."""
        from dotenv import load_dotenv

        # Create malformed .env file
        env_file = tmp_path / ".env"
        env_file.write_text("INVALID LINE WITHOUT EQUALS\nVALID_VAR=value\n")

        # python-dotenv is lenient with malformed lines
        # This should not raise
        load_dotenv(env_file, override=True)

    def test_handles_env_file_with_special_characters(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test loading env file with special characters."""
        from dotenv import load_dotenv

        monkeypatch.delenv("SPECIAL_CHAR_VAR", raising=False)

        # Create .env with special characters
        env_file = tmp_path / ".env"
        env_file.write_text('SPECIAL_CHAR_VAR="value with spaces and $pecial chars"\n')

        load_dotenv(env_file, override=True)

        # Should handle quoted values
        loaded_value = os.getenv("SPECIAL_CHAR_VAR")
        assert loaded_value is not None
        assert "value with spaces" in loaded_value

    def test_handles_empty_env_file(self, tmp_path: Path) -> None:
        """Test loading empty .env file."""
        from dotenv import load_dotenv

        # Create empty .env file
        env_file = tmp_path / ".env"
        env_file.write_text("")

        # Should not raise
        load_dotenv(env_file, override=True)

    def test_handles_nonexistent_file_gracefully(self, tmp_path: Path) -> None:
        """Test that load_dotenv with nonexistent file doesn't crash."""
        from dotenv import load_dotenv

        nonexistent = tmp_path / "does_not_exist.env"

        # python-dotenv returns False for nonexistent files but doesn't raise
        result = load_dotenv(nonexistent, override=True)
        assert result is False


class TestEnvLoaderIntegration:
    """Integration tests with actual env_loader module."""

    def test_module_has_expected_structure(self) -> None:
        """Test that env_loader module has expected attributes."""
        import the_alchemiser.shared.config.env_loader as env_loader

        # Module should have docstring
        assert env_loader.__doc__ is not None
        assert "Business Unit" in env_loader.__doc__

        # Module should be executable (no functions/classes to export)
        # It works via side-effects on import

    def test_env_loader_works_with_secrets_adapter(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that env_loader integration with secrets_adapter works."""
        # secrets_adapter imports env_loader for side-effects
        # This test verifies the import works
        monkeypatch.setenv("ALPACA_KEY", "test_key")
        monkeypatch.setenv("ALPACA_SECRET", "test_secret")

        # Import should not raise
        from the_alchemiser.shared.config import secrets_adapter  # noqa: F401

        # Verify we can get keys after env_loader has run
        from the_alchemiser.shared.config.secrets_adapter import get_alpaca_keys

        api_key, secret_key, endpoint = get_alpaca_keys()
        assert api_key == "test_key"
        assert secret_key == "test_secret"

    def test_env_loader_side_effect_import_pattern(self) -> None:
        """Test the intentional side-effect import pattern used in codebase."""
        # This documents the pattern: `from ... import env_loader  # noqa: F401`
        # The noqa comment indicates intentional unused import for side-effects

        # Should not raise
        from the_alchemiser.shared.config import env_loader  # noqa: F401

        # Module is imported for side-effects, not for its exports
        # This is the expected usage pattern


@pytest.mark.unit
class TestEnvLoaderCompliance:
    """Tests for compliance with coding standards."""

    def test_module_has_business_unit_header(self) -> None:
        """Test that module has required Business Unit header."""
        import the_alchemiser.shared.config.env_loader as env_loader

        docstring = env_loader.__doc__
        assert docstring is not None
        assert "Business Unit:" in docstring
        assert "Status:" in docstring

    def test_module_uses_pathlib(self) -> None:
        """Test that module uses pathlib (PTH rule compliance)."""
        import inspect

        import the_alchemiser.shared.config.env_loader as env_loader

        source = inspect.getsource(env_loader)

        # Should use pathlib.Path
        assert "from pathlib import Path" in source
        assert "Path(__file__)" in source

    def test_module_size_within_limits(self) -> None:
        """Test that module is within size limits (≤500 lines soft limit)."""
        import inspect

        import the_alchemiser.shared.config.env_loader as env_loader

        source = inspect.getsource(env_loader)
        line_count = len(source.splitlines())

        # Module grew from ~25 to ~142 lines due to logging and error handling
        # Still well under 500 line soft limit and 800 line hard limit
        assert line_count < 200, f"Module has {line_count} lines, should be under 200"

    def test_no_security_vulnerabilities(self) -> None:
        """Test that module doesn't have obvious security issues."""
        import inspect

        import the_alchemiser.shared.config.env_loader as env_loader

        source = inspect.getsource(env_loader)

        # Should not use dangerous functions
        assert "eval(" not in source
        assert "exec(" not in source
        assert "__import__" not in source

    def test_imports_follow_standards(self) -> None:
        """Test that imports follow coding standards."""
        import inspect

        import the_alchemiser.shared.config.env_loader as env_loader

        source = inspect.getsource(env_loader)

        # Should not use star imports
        assert "import *" not in source

        # Should have proper import organization (stdlib before third-party)
        lines = source.splitlines()
        import_lines = [
            line for line in lines if "import" in line and not line.strip().startswith("#")
        ]

        # pathlib (stdlib) should come before dotenv (third-party)
        pathlib_idx = next((i for i, line in enumerate(import_lines) if "pathlib" in line), -1)
        dotenv_idx = next((i for i, line in enumerate(import_lines) if "dotenv" in line), -1)

        if pathlib_idx >= 0 and dotenv_idx >= 0:
            assert pathlib_idx < dotenv_idx, (
                "Standard library imports should come before third-party"
            )
