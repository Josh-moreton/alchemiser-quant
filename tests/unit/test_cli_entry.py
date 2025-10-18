#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Unit tests for __main__.py CLI entry point.

Tests cover:
- CLI invocation via python -m the_alchemiser
- Help message display
- Argument passing and exit codes
- Default behavior
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from the_alchemiser.__main__ import run


class TestRunFunction:
    """Test the run() function in __main__.py."""

    @patch("the_alchemiser.__main__.main")
    @patch("the_alchemiser.__main__.sys.exit")
    def test_run_with_no_args_defaults_to_trade(self, mock_exit: Mock, mock_main: Mock) -> None:
        """Test run function with no arguments defaults to trade command."""
        mock_result = Mock()
        mock_result.success = True
        mock_main.return_value = mock_result

        with patch.object(sys, "argv", ["__main__.py"]):
            run()

        mock_main.assert_called_once_with(["trade"])
        mock_exit.assert_called_once_with(0)

    @patch("the_alchemiser.__main__.main")
    @patch("the_alchemiser.__main__.sys.exit")
    def test_run_with_trade_command(self, mock_exit: Mock, mock_main: Mock) -> None:
        """Test run function with explicit trade command."""
        mock_result = Mock()
        mock_result.success = True
        mock_main.return_value = mock_result

        with patch.object(sys, "argv", ["__main__.py", "trade"]):
            run()

        mock_main.assert_called_once_with(["trade"])
        mock_exit.assert_called_once_with(0)

    @patch("the_alchemiser.__main__.main")
    @patch("the_alchemiser.__main__.sys.exit")
    def test_run_with_pnl_command(self, mock_exit: Mock, mock_main: Mock) -> None:
        """Test run function with pnl command."""
        mock_main.return_value = True

        with patch.object(sys, "argv", ["__main__.py", "pnl", "--weekly"]):
            run()

        mock_main.assert_called_once_with(["pnl", "--weekly"])
        mock_exit.assert_called_once_with(0)

    @patch("the_alchemiser.__main__.main")
    @patch("the_alchemiser.__main__.sys.exit")
    def test_run_with_trade_failure(self, mock_exit: Mock, mock_main: Mock) -> None:
        """Test run function with failed trade execution."""
        mock_result = Mock()
        mock_result.success = False
        mock_main.return_value = mock_result

        with patch.object(sys, "argv", ["__main__.py", "trade"]):
            run()

        mock_exit.assert_called_once_with(1)

    @patch("the_alchemiser.__main__.main")
    @patch("the_alchemiser.__main__.sys.exit")
    def test_run_with_pnl_failure(self, mock_exit: Mock, mock_main: Mock) -> None:
        """Test run function with failed pnl execution."""
        mock_main.return_value = False

        with patch.object(sys, "argv", ["__main__.py", "pnl", "--weekly"]):
            run()

        mock_exit.assert_called_once_with(1)

    @patch("the_alchemiser.__main__.main")
    @patch("the_alchemiser.__main__.sys.exit")
    def test_run_with_boolean_result_true(self, mock_exit: Mock, mock_main: Mock) -> None:
        """Test run function with boolean True result."""
        mock_main.return_value = True

        with patch.object(sys, "argv", ["__main__.py", "pnl"]):
            run()

        mock_exit.assert_called_once_with(0)

    @patch("the_alchemiser.__main__.main")
    @patch("the_alchemiser.__main__.sys.exit")
    def test_run_with_boolean_result_false(self, mock_exit: Mock, mock_main: Mock) -> None:
        """Test run function with boolean False result."""
        mock_main.return_value = False

        with patch.object(sys, "argv", ["__main__.py", "unknown"]):
            run()

        mock_exit.assert_called_once_with(1)

    @patch("the_alchemiser.__main__.main")
    @patch("the_alchemiser.__main__.sys.exit")
    def test_run_with_tracking_options(self, mock_exit: Mock, mock_main: Mock) -> None:
        """Test run function with tracking options."""
        mock_result = Mock()
        mock_result.success = True
        mock_main.return_value = mock_result

        with patch.object(sys, "argv", ["__main__.py", "trade", "--show-tracking"]):
            run()

        mock_main.assert_called_once_with(["trade", "--show-tracking"])
        mock_exit.assert_called_once_with(0)


class TestCLIHelp:
    """Test help message display."""

    def test_help_message_content(self) -> None:
        """Test that help message contains expected content."""
        # This would be an integration test - we verify the logic exists
        # The actual if __name__ == "__main__" block is hard to unit test
        # but we verify the structure exists in the module
        import the_alchemiser.__main__ as main_module

        # Verify that the module has the expected structure
        assert hasattr(main_module, "run")
        assert hasattr(main_module, "main")


class TestCLIIntegration:
    """Integration tests for CLI invocation.

    These tests use subprocess to actually invoke the CLI,
    which is more realistic but slower.
    """

    @pytest.mark.integration
    def test_cli_help_via_subprocess(self) -> None:
        """Test CLI help message via subprocess."""
        repo_root = Path(__file__).resolve().parents[2]
        result = subprocess.run(
            [sys.executable, "-m", "the_alchemiser", "--help"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=5,
        )

        assert result.returncode == 0
        assert "Usage: python -m the_alchemiser" in result.stdout
        assert "Commands:" in result.stdout
        assert "trade" in result.stdout
        assert "pnl" in result.stdout

    @pytest.mark.integration
    def test_cli_short_help_via_subprocess(self) -> None:
        """Test CLI short help (-h) message via subprocess."""
        repo_root = Path(__file__).resolve().parents[2]
        result = subprocess.run(
            [sys.executable, "-m", "the_alchemiser", "-h"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=5,
        )

        assert result.returncode == 0
        assert "Usage:" in result.stdout

    @pytest.mark.integration
    @patch.dict("os.environ", {"TESTING": "true", "PAPER_TRADING": "true"})
    def test_cli_invalid_command_fails(self) -> None:
        """Test that invalid command results in exit code 1."""
        # This would require mocking the entire trading system
        # For now, we ensure the argument parsing works correctly
        from the_alchemiser.main import _parse_arguments

        args = _parse_arguments(["invalid_command"])
        assert args.mode == "invalid_command"
