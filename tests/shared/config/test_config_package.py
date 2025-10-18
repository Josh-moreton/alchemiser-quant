"""Tests for the_alchemiser.config package.

This module tests the config resource package that bundles JSON configuration files.
The package uses importlib.resources to access bundled configuration files in Lambda deployments.
"""

from importlib import resources as importlib_resources

import pytest


@pytest.mark.unit
def test_config_package_is_importable():
    """Verify the_alchemiser.config package can be imported.

    This test documents that the config package exists as a resource package
    for bundled JSON configuration files.
    """
    from the_alchemiser import config

    # Verify package has an __init__.py
    assert hasattr(config, "__file__")
    assert config.__file__.endswith("__init__.py")

    # Verify package has the expected docstring
    assert config.__doc__ is not None
    assert "Business Unit: shared" in config.__doc__
    assert "Status: current" in config.__doc__


@pytest.mark.unit
def test_config_package_contains_bundled_json_files():
    """Verify JSON configuration files are bundled with the config package.

    These files are used by StrategySettings._get_stage_profile() to load
    environment-specific strategy configurations.
    """
    # Verify files can be located using importlib.resources
    pkg_files = importlib_resources.files("the_alchemiser.config")

    # Verify dev config exists
    dev_config = pkg_files.joinpath("strategy.dev.json")
    assert dev_config.exists(), "strategy.dev.json should be bundled in the package"

    # Verify prod config exists
    prod_config = pkg_files.joinpath("strategy.prod.json")
    assert prod_config.exists(), "strategy.prod.json should be bundled in the package"


@pytest.mark.unit
def test_bundled_json_files_are_valid():
    """Verify bundled JSON files have valid structure.

    Both dev and prod configs should contain 'files' and 'allocations' keys
    that are validated by StrategySettings.
    """
    import json

    pkg_files = importlib_resources.files("the_alchemiser.config")

    # Test dev config structure
    with pkg_files.joinpath("strategy.dev.json").open("r", encoding="utf-8") as f:
        dev_data = json.load(f)
    assert "files" in dev_data, "Dev config must have 'files' key"
    assert "allocations" in dev_data, "Dev config must have 'allocations' key"
    assert isinstance(dev_data["files"], list), "files must be a list"
    assert isinstance(dev_data["allocations"], dict), "allocations must be a dict"

    # Test prod config structure
    with pkg_files.joinpath("strategy.prod.json").open("r", encoding="utf-8") as f:
        prod_data = json.load(f)
    assert "files" in prod_data, "Prod config must have 'files' key"
    assert "allocations" in prod_data, "Prod config must have 'allocations' key"
    assert isinstance(prod_data["files"], list), "files must be a list"
    assert isinstance(prod_data["allocations"], dict), "allocations must be a dict"

    # Verify allocations sum to approximately 1.0
    dev_total = sum(dev_data["allocations"].values())
    assert 0.99 <= dev_total <= 1.01, f"Dev allocations should sum to ~1.0, got {dev_total}"

    prod_total = sum(prod_data["allocations"].values())
    assert 0.99 <= prod_total <= 1.01, f"Prod allocations should sum to ~1.0, got {prod_total}"

    # Verify files and allocations keys match
    assert set(dev_data["files"]) == set(dev_data["allocations"].keys()), (
        "Dev config: files list must match allocation keys"
    )
    assert set(prod_data["files"]) == set(prod_data["allocations"].keys()), (
        "Prod config: files list must match allocation keys"
    )
