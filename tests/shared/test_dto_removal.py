"""Test to verify that the deprecated dto module has been removed."""

import importlib
import pytest


def test_dto_module_import_raises_error():
    """Test that importing the_alchemiser.shared.dto raises ImportError.
    
    This test ensures that the deprecated DTO shim has been fully removed
    and no longer provides backward compatibility.
    """
    with pytest.raises(ModuleNotFoundError, match="No module named 'the_alchemiser.shared.dto'"):
        importlib.import_module("the_alchemiser.shared.dto")


def test_dto_submodule_imports_raise_error():
    """Test that importing from the_alchemiser.shared.dto submodules raises ImportError."""
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("the_alchemiser.shared.dto.strategy_allocation_dto")
    
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("the_alchemiser.shared.dto.trade_ledger_dto")