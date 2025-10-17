"""Business Unit: shared | Status: current.

Tests for sonar_to_github_issues.py script.

Tests focus on security aspects of URL parsing and repository detection,
particularly around the vulnerability fixed in get_github_repo() function.
"""
from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

import pytest

# Import the functions we need to test
import sys
from pathlib import Path

# Add scripts directory to path so we can import the module
scripts_dir = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from sonar_to_github_issues import (
    _validate_and_return,
    get_github_repo,
)


class TestValidateAndReturn:
    """Test the _validate_and_return function for GitHub owner/repo validation."""

    def test_valid_owner_and_repo(self) -> None:
        """Test that valid owner and repo names are accepted."""
        result = _validate_and_return("owner", "repo")
        assert result == ("owner", "repo")

    def test_valid_owner_with_hyphens(self) -> None:
        """Test that owner names with hyphens are accepted."""
        result = _validate_and_return("my-org", "my-repo")
        assert result == ("my-org", "my-repo")

    def test_valid_repo_with_dots(self) -> None:
        """Test that repo names with dots are accepted."""
        result = _validate_and_return("owner", "repo.name")
        assert result == ("owner", "repo.name")

    def test_valid_repo_with_underscores(self) -> None:
        """Test that repo names with underscores are accepted."""
        result = _validate_and_return("owner", "repo_name")
        assert result == ("owner", "repo_name")

    def test_invalid_owner_path_traversal(self) -> None:
        """Test that path traversal in owner is rejected."""
        result = _validate_and_return("..", "repo")
        assert result is None

    def test_invalid_owner_multiple_dots(self) -> None:
        """Test that multiple dots in owner is rejected."""
        result = _validate_and_return("...", "repo")
        assert result is None

    def test_invalid_owner_path_with_slashes(self) -> None:
        """Test that owner with slashes is rejected."""
        result = _validate_and_return("../../etc/passwd", "repo")
        assert result is None

    def test_invalid_repo_path_traversal(self) -> None:
        """Test that path traversal in repo is rejected."""
        result = _validate_and_return("owner", "../admin")
        assert result is None

    def test_invalid_owner_with_slash(self) -> None:
        """Test that owner with slash is rejected."""
        result = _validate_and_return("owner/subpath", "repo")
        assert result is None

    def test_invalid_repo_with_slash(self) -> None:
        """Test that repo with slash is rejected."""
        result = _validate_and_return("owner", "repo/subpath")
        assert result is None

    def test_invalid_owner_starts_with_hyphen(self) -> None:
        """Test that owner starting with hyphen is rejected."""
        result = _validate_and_return("-owner", "repo")
        assert result is None

    def test_invalid_owner_too_long(self) -> None:
        """Test that owner longer than 39 characters is rejected."""
        long_owner = "a" * 40
        result = _validate_and_return(long_owner, "repo")
        assert result is None

    def test_invalid_repo_too_long(self) -> None:
        """Test that repo longer than 100 characters is rejected."""
        long_repo = "a" * 101
        result = _validate_and_return("owner", long_repo)
        assert result is None

    def test_invalid_owner_with_special_chars(self) -> None:
        """Test that owner with special characters is rejected."""
        result = _validate_and_return("owner@special", "repo")
        assert result is None

    def test_invalid_repo_with_special_chars(self) -> None:
        """Test that repo with query parameters is rejected."""
        result = _validate_and_return("owner", "repo?param=value")
        assert result is None

    def test_invalid_repo_with_fragment(self) -> None:
        """Test that repo with fragment is rejected."""
        result = _validate_and_return("owner", "repo#fragment")
        assert result is None

    def test_invalid_empty_owner(self) -> None:
        """Test that empty owner is rejected."""
        result = _validate_and_return("", "repo")
        assert result is None

    def test_invalid_empty_repo(self) -> None:
        """Test that empty repo is rejected."""
        result = _validate_and_return("owner", "")
        assert result is None


class TestGetGithubRepo:
    """Test the get_github_repo function for secure URL parsing."""

    def test_valid_https_url(self) -> None:
        """Test parsing a valid HTTPS GitHub URL."""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "https://github.com/owner/repo.git"
        mock_proc.stderr = ""

        with patch("subprocess.run", return_value=mock_proc), \
             patch("shutil.which", side_effect=lambda x: "/usr/bin/git" if x == "git" else None):
            result = get_github_repo()
            assert result == ("owner", "repo")

    def test_valid_https_url_without_git_extension(self) -> None:
        """Test parsing a valid HTTPS GitHub URL without .git extension."""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "https://github.com/owner/repo"
        mock_proc.stderr = ""

        with patch("subprocess.run", return_value=mock_proc), \
             patch("shutil.which", side_effect=lambda x: "/usr/bin/git" if x == "git" else None):
            result = get_github_repo()
            assert result == ("owner", "repo")

    def test_valid_ssh_url(self) -> None:
        """Test parsing a valid SSH GitHub URL."""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "git@github.com:owner/repo.git"
        mock_proc.stderr = ""

        with patch("subprocess.run", return_value=mock_proc), \
             patch("shutil.which", side_effect=lambda x: "/usr/bin/git" if x == "git" else None):
            result = get_github_repo()
            assert result == ("owner", "repo")

    def test_valid_ssh_url_without_git_extension(self) -> None:
        """Test parsing a valid SSH GitHub URL without .git extension."""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "git@github.com:owner/repo"
        mock_proc.stderr = ""

        with patch("subprocess.run", return_value=mock_proc), \
             patch("shutil.which", side_effect=lambda x: "/usr/bin/git" if x == "git" else None):
            result = get_github_repo()
            assert result == ("owner", "repo")

    def test_https_url_with_query_parameters(self) -> None:
        """Test that query parameters are stripped from HTTPS URLs."""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "https://github.com/owner/repo?malicious=param"
        mock_proc.stderr = ""

        with patch("subprocess.run", return_value=mock_proc), \
             patch("shutil.which", side_effect=lambda x: "/usr/bin/git" if x == "git" else None):
            result = get_github_repo()
            # Query parameters should be stripped, leaving valid owner/repo
            assert result == ("owner", "repo")

    def test_https_url_with_fragment(self) -> None:
        """Test that fragments are stripped from HTTPS URLs."""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "https://github.com/owner/repo#fragment"
        mock_proc.stderr = ""

        with patch("subprocess.run", return_value=mock_proc), \
             patch("shutil.which", side_effect=lambda x: "/usr/bin/git" if x == "git" else None):
            result = get_github_repo()
            # Fragment should be stripped, leaving valid owner/repo
            assert result == ("owner", "repo")

    def test_path_traversal_attack_https(self) -> None:
        """Test that path traversal in HTTPS URL is rejected."""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "https://github.com/../../../etc/passwd"
        mock_proc.stderr = ""

        with patch("subprocess.run", return_value=mock_proc), \
             patch("shutil.which", side_effect=lambda x: "/usr/bin/git" if x == "git" else None):
            result = get_github_repo()
            assert result is None

    def test_wrong_domain_in_https_url(self) -> None:
        """Test that non-GitHub domain is rejected."""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "https://evil.com/github.com/fake/repo"
        mock_proc.stderr = ""

        with patch("subprocess.run", return_value=mock_proc), \
             patch("shutil.which", side_effect=lambda x: "/usr/bin/git" if x == "git" else None):
            result = get_github_repo()
            assert result is None

    def test_multiple_github_com_in_url(self) -> None:
        """Test that URL with multiple github.com is handled correctly."""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = (
            "https://evil.com/github.com/fake/repo?redirect=https://github.com/real/repo"
        )
        mock_proc.stderr = ""

        with patch("subprocess.run", return_value=mock_proc), \
             patch("shutil.which", side_effect=lambda x: "/usr/bin/git" if x == "git" else None):
            result = get_github_repo()
            # Should reject because domain is evil.com, not github.com
            assert result is None

    def test_url_encoded_slash(self) -> None:
        """Test that URL-encoded slashes are not parsed."""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "https://github.com/owner%2frepo"
        mock_proc.stderr = ""

        with patch("subprocess.run", return_value=mock_proc), \
             patch("shutil.which", side_effect=lambda x: "/usr/bin/git" if x == "git" else None):
            result = get_github_repo()
            # URL-encoded slash should result in invalid owner/repo
            assert result is None

    def test_null_byte_injection(self) -> None:
        """Test that null byte injection is rejected."""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "https://github.com/owner/repo\x00null"
        mock_proc.stderr = ""

        with patch("subprocess.run", return_value=mock_proc), \
             patch("shutil.which", side_effect=lambda x: "/usr/bin/git" if x == "git" else None):
            result = get_github_repo()
            # Null byte should be rejected by validation
            assert result is None

    def test_ssh_url_with_subdirectory_path(self) -> None:
        """Test that SSH URL with extra path segments is rejected."""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "git@github.com:owner/repo/subdir.git"
        mock_proc.stderr = ""

        with patch("subprocess.run", return_value=mock_proc), \
             patch("shutil.which", side_effect=lambda x: "/usr/bin/git" if x == "git" else None):
            result = get_github_repo()
            # Should reject because regex expects only owner/repo
            assert result is None

    def test_https_url_with_extra_path_segments(self) -> None:
        """Test that HTTPS URL with extra path segments uses first two segments."""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "https://github.com/owner/repo/extra/path.git"
        mock_proc.stderr = ""

        with patch("subprocess.run", return_value=mock_proc), \
             patch("shutil.which", side_effect=lambda x: "/usr/bin/git" if x == "git" else None):
            result = get_github_repo()
            # Should extract first two segments
            assert result == ("owner", "repo")

    def test_owner_repo_env_valid(self) -> None:
        """Test parsing from GITHUB_REPOSITORY environment variable format."""
        result = get_github_repo("owner/repo")
        assert result == ("owner", "repo")

    def test_owner_repo_env_invalid_format(self) -> None:
        """Test that invalid format in env is rejected."""
        with patch("shutil.which", return_value=None):
            result = get_github_repo("invalid-format-no-slash")
            assert result is None

    def test_owner_repo_env_path_traversal(self) -> None:
        """Test that path traversal in env format is rejected."""
        result = get_github_repo("../../../etc/passwd")
        assert result is None

    def test_git_command_not_available(self) -> None:
        """Test handling when git command is not available."""
        with patch("shutil.which", return_value=None):
            result = get_github_repo()
            assert result is None

    def test_git_command_returns_error(self) -> None:
        """Test handling when git command returns error."""
        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_proc.stdout = ""
        mock_proc.stderr = "fatal: not a git repository"

        with patch("subprocess.run", return_value=mock_proc), \
             patch("shutil.which", side_effect=lambda x: "/usr/bin/git" if x == "git" else None):
            result = get_github_repo()
            assert result is None

    def test_git_command_returns_empty_output(self) -> None:
        """Test handling when git command returns empty output."""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = ""
        mock_proc.stderr = ""

        with patch("subprocess.run", return_value=mock_proc), \
             patch("shutil.which", side_effect=lambda x: "/usr/bin/git" if x == "git" else None):
            result = get_github_repo()
            assert result is None
