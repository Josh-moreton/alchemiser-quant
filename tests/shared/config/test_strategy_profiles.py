"""Tests for the_alchemiser.shared.config.strategy_profiles module.

This module tests the strategy profile constants that serve as fallback
configuration when JSON config files fail to load.
"""

from decimal import Decimal

import pytest


@pytest.mark.unit
def test_strategy_profiles_module_imports():
    """Verify strategy_profiles module can be imported and has required attributes."""
    from the_alchemiser.shared.config import strategy_profiles

    # Verify module has business unit header
    assert hasattr(strategy_profiles, "__doc__")
    assert strategy_profiles.__doc__ is not None
    assert "Business Unit:" in strategy_profiles.__doc__
    assert "utilities" in strategy_profiles.__doc__
    assert "Status: current" in strategy_profiles.__doc__


@pytest.mark.unit
def test_strategy_name_constants_are_defined():
    """Verify all active strategy name constants are defined with correct types."""
    from the_alchemiser.shared.config.strategy_profiles import (
        STRATEGY_BITCOIN,
        STRATEGY_GRAIL,
        STRATEGY_KMLM,
        STRATEGY_QUANTUM,
        STRATEGY_SEMICONDUCTORS,
    )

    # All should be strings
    assert isinstance(STRATEGY_GRAIL, str)
    assert isinstance(STRATEGY_KMLM, str)
    assert isinstance(STRATEGY_SEMICONDUCTORS, str)
    assert isinstance(STRATEGY_BITCOIN, str)
    assert isinstance(STRATEGY_QUANTUM, str)

    # All should end with .clj (Clojure DSL files)
    assert STRATEGY_GRAIL.endswith(".clj")
    assert STRATEGY_KMLM.endswith(".clj")
    assert STRATEGY_SEMICONDUCTORS.endswith(".clj")
    assert STRATEGY_BITCOIN.endswith(".clj")
    assert STRATEGY_QUANTUM.endswith(".clj")

    # Should have nested directory structure (foundation/ or tactical/)
    assert STRATEGY_GRAIL.startswith("foundation/")
    assert STRATEGY_KMLM.startswith("foundation/")
    assert STRATEGY_SEMICONDUCTORS.startswith("foundation/")
    assert STRATEGY_BITCOIN.startswith("tactical/")
    assert STRATEGY_QUANTUM.startswith("tactical/")


@pytest.mark.unit
def test_dev_dsl_files_list():
    """Verify DEV_DSL_FILES list is properly structured."""
    from the_alchemiser.shared.config.strategy_profiles import DEV_DSL_FILES

    # Should be a list
    assert isinstance(DEV_DSL_FILES, list)

    # Should contain all 5 dev strategies
    assert len(DEV_DSL_FILES) == 5

    # All items should be strings
    assert all(isinstance(item, str) for item in DEV_DSL_FILES)

    # All items should end with .clj
    assert all(item.endswith(".clj") for item in DEV_DSL_FILES)

    # Should contain expected strategies (order preserved)
    assert "foundation/grail.clj" in DEV_DSL_FILES
    assert "foundation/kmlm.clj" in DEV_DSL_FILES
    assert "foundation/semiconductors.clj" in DEV_DSL_FILES
    assert "tactical/bitcoin.clj" in DEV_DSL_FILES
    assert "tactical/quantum.clj" in DEV_DSL_FILES

    # No duplicates
    assert len(DEV_DSL_FILES) == len(set(DEV_DSL_FILES))


@pytest.mark.unit
def test_dev_dsl_allocations_dict():
    """Verify DEV_DSL_ALLOCATIONS dict is properly structured."""
    from the_alchemiser.shared.config.strategy_profiles import (
        DEV_DSL_ALLOCATIONS,
        DEV_DSL_FILES,
    )

    # Should be a dict
    assert isinstance(DEV_DSL_ALLOCATIONS, dict)

    # Should have 5 entries (one per dev strategy)
    assert len(DEV_DSL_ALLOCATIONS) == 5

    # All keys should be strings (strategy filenames)
    assert all(isinstance(k, str) for k in DEV_DSL_ALLOCATIONS.keys())

    # All values should be floats
    assert all(isinstance(v, float) for v in DEV_DSL_ALLOCATIONS.values())

    # All values should be in valid range [0, 1]
    assert all(0.0 <= v <= 1.0 for v in DEV_DSL_ALLOCATIONS.values())

    # All keys should match entries in DEV_DSL_FILES
    assert set(DEV_DSL_ALLOCATIONS.keys()) == set(DEV_DSL_FILES)


@pytest.mark.unit
def test_dev_allocations_sum_to_one():
    """Verify DEV_DSL_ALLOCATIONS weights sum to 1.0 (within tolerance)."""
    from the_alchemiser.shared.config.strategy_profiles import DEV_DSL_ALLOCATIONS

    # Sum all allocation weights
    total = sum(DEV_DSL_ALLOCATIONS.values())

    # Should sum to approximately 1.0 (100%)
    # Using tight tolerance since these are hand-coded constants
    assert 0.999 <= total <= 1.001, f"Dev allocations sum to {total}, expected ~1.0"

    # Also verify with Decimal for precision
    decimal_total = sum(Decimal(str(v)) for v in DEV_DSL_ALLOCATIONS.values())
    assert Decimal("0.999") <= decimal_total <= Decimal("1.001")


@pytest.mark.unit
def test_dev_allocations_individual_values():
    """Verify DEV_DSL_ALLOCATIONS has expected allocation values."""
    from the_alchemiser.shared.config.strategy_profiles import (
        DEV_DSL_ALLOCATIONS,
        STRATEGY_BITCOIN,
        STRATEGY_GRAIL,
        STRATEGY_KMLM,
        STRATEGY_QUANTUM,
        STRATEGY_SEMICONDUCTORS,
    )

    # Verify each strategy has expected allocation (equal weight in dev)
    assert DEV_DSL_ALLOCATIONS[STRATEGY_GRAIL] == 0.2  # 20%
    assert DEV_DSL_ALLOCATIONS[STRATEGY_KMLM] == 0.2  # 20%
    assert DEV_DSL_ALLOCATIONS[STRATEGY_SEMICONDUCTORS] == 0.2  # 20%
    assert DEV_DSL_ALLOCATIONS[STRATEGY_BITCOIN] == 0.2  # 20%
    assert DEV_DSL_ALLOCATIONS[STRATEGY_QUANTUM] == 0.2  # 20%


@pytest.mark.unit
def test_prod_dsl_files_list():
    """Verify PROD_DSL_FILES list is properly structured."""
    from the_alchemiser.shared.config.strategy_profiles import (
        DEV_DSL_FILES,
        PROD_DSL_FILES,
    )

    # Should be a list
    assert isinstance(PROD_DSL_FILES, list)

    # Should contain 3 prod strategies (subset of dev)
    assert len(PROD_DSL_FILES) == 3

    # All items should be strings
    assert all(isinstance(item, str) for item in PROD_DSL_FILES)

    # All items should end with .clj
    assert all(item.endswith(".clj") for item in PROD_DSL_FILES)

    # Should contain expected strategies
    assert "foundation/kmlm.clj" in PROD_DSL_FILES
    assert "foundation/semiconductors.clj" in PROD_DSL_FILES
    assert "tactical/bitcoin.clj" in PROD_DSL_FILES

    # No duplicates
    assert len(PROD_DSL_FILES) == len(set(PROD_DSL_FILES))

    # All prod strategies should be in dev strategies (prod is subset)
    assert set(PROD_DSL_FILES).issubset(set(DEV_DSL_FILES))


@pytest.mark.unit
def test_prod_dsl_allocations_dict():
    """Verify PROD_DSL_ALLOCATIONS dict is properly structured."""
    from the_alchemiser.shared.config.strategy_profiles import (
        PROD_DSL_ALLOCATIONS,
        PROD_DSL_FILES,
    )

    # Should be a dict
    assert isinstance(PROD_DSL_ALLOCATIONS, dict)

    # Should have 3 entries (one per prod strategy)
    assert len(PROD_DSL_ALLOCATIONS) == 3

    # All keys should be strings (strategy filenames)
    assert all(isinstance(k, str) for k in PROD_DSL_ALLOCATIONS.keys())

    # All values should be floats
    assert all(isinstance(v, float) for v in PROD_DSL_ALLOCATIONS.values())

    # All values should be in valid range [0, 1]
    assert all(0.0 <= v <= 1.0 for v in PROD_DSL_ALLOCATIONS.values())

    # All keys should match entries in PROD_DSL_FILES
    assert set(PROD_DSL_ALLOCATIONS.keys()) == set(PROD_DSL_FILES)


@pytest.mark.unit
def test_prod_allocations_sum_to_one():
    """Verify PROD_DSL_ALLOCATIONS weights sum to 1.0 (within tolerance)."""
    from the_alchemiser.shared.config.strategy_profiles import PROD_DSL_ALLOCATIONS

    # Sum all allocation weights
    total = sum(PROD_DSL_ALLOCATIONS.values())

    # Should sum to approximately 1.0 (100%)
    # Using tight tolerance since these are hand-coded constants
    assert 0.999 <= total <= 1.001, f"Prod allocations sum to {total}, expected ~1.0"

    # Also verify with Decimal for precision
    decimal_total = sum(Decimal(str(v)) for v in PROD_DSL_ALLOCATIONS.values())
    assert Decimal("0.999") <= decimal_total <= Decimal("1.001")


@pytest.mark.unit
def test_prod_allocations_individual_values():
    """Verify PROD_DSL_ALLOCATIONS has expected allocation values."""
    from the_alchemiser.shared.config.strategy_profiles import (
        PROD_DSL_ALLOCATIONS,
        STRATEGY_BITCOIN,
        STRATEGY_KMLM,
        STRATEGY_SEMICONDUCTORS,
    )

    # Verify each strategy has expected allocation
    assert PROD_DSL_ALLOCATIONS[STRATEGY_KMLM] == 0.4  # 40%
    assert PROD_DSL_ALLOCATIONS[STRATEGY_SEMICONDUCTORS] == 0.4  # 40%
    assert PROD_DSL_ALLOCATIONS[STRATEGY_BITCOIN] == 0.2  # 20%


@pytest.mark.unit
def test_prod_allocations_differ_from_dev():
    """Verify PROD allocations are intentionally different from DEV for shared strategies."""
    from the_alchemiser.shared.config.strategy_profiles import (
        DEV_DSL_ALLOCATIONS,
        PROD_DSL_ALLOCATIONS,
        STRATEGY_BITCOIN,
        STRATEGY_KMLM,
        STRATEGY_SEMICONDUCTORS,
    )

    # KMLM has higher allocation in prod (40% vs 20%)
    assert PROD_DSL_ALLOCATIONS[STRATEGY_KMLM] > DEV_DSL_ALLOCATIONS[STRATEGY_KMLM]
    assert PROD_DSL_ALLOCATIONS[STRATEGY_KMLM] == 0.4
    assert DEV_DSL_ALLOCATIONS[STRATEGY_KMLM] == 0.2

    # Semiconductors has higher allocation in prod (40% vs 20%)
    assert PROD_DSL_ALLOCATIONS[STRATEGY_SEMICONDUCTORS] > DEV_DSL_ALLOCATIONS[STRATEGY_SEMICONDUCTORS]
    assert PROD_DSL_ALLOCATIONS[STRATEGY_SEMICONDUCTORS] == 0.4
    assert DEV_DSL_ALLOCATIONS[STRATEGY_SEMICONDUCTORS] == 0.2

    # Bitcoin has same allocation (20% in both)
    assert PROD_DSL_ALLOCATIONS[STRATEGY_BITCOIN] == DEV_DSL_ALLOCATIONS[STRATEGY_BITCOIN]
    assert PROD_DSL_ALLOCATIONS[STRATEGY_BITCOIN] == 0.2


@pytest.mark.unit
def test_strategy_constants_match_files():
    """Verify active strategy constants match what's in the FILES lists."""
    from the_alchemiser.shared.config.strategy_profiles import (
        DEV_DSL_FILES,
        STRATEGY_BITCOIN,
        STRATEGY_GRAIL,
        STRATEGY_KMLM,
        STRATEGY_QUANTUM,
        STRATEGY_SEMICONDUCTORS,
    )

    # All active strategy constants should be in dev files
    assert STRATEGY_GRAIL in DEV_DSL_FILES
    assert STRATEGY_KMLM in DEV_DSL_FILES
    assert STRATEGY_SEMICONDUCTORS in DEV_DSL_FILES
    assert STRATEGY_BITCOIN in DEV_DSL_FILES
    assert STRATEGY_QUANTUM in DEV_DSL_FILES


@pytest.mark.unit
def test_no_negative_allocations():
    """Verify no allocations are negative."""
    from the_alchemiser.shared.config.strategy_profiles import (
        DEV_DSL_ALLOCATIONS,
        PROD_DSL_ALLOCATIONS,
    )

    # All dev allocations should be non-negative
    assert all(v >= 0.0 for v in DEV_DSL_ALLOCATIONS.values())

    # All prod allocations should be non-negative
    assert all(v >= 0.0 for v in PROD_DSL_ALLOCATIONS.values())


@pytest.mark.unit
def test_no_allocations_exceed_one():
    """Verify no single allocation exceeds 100%."""
    from the_alchemiser.shared.config.strategy_profiles import (
        DEV_DSL_ALLOCATIONS,
        PROD_DSL_ALLOCATIONS,
    )

    # No dev allocation should exceed 1.0 (100%)
    assert all(v <= 1.0 for v in DEV_DSL_ALLOCATIONS.values())

    # No prod allocation should exceed 1.0 (100%)
    assert all(v <= 1.0 for v in PROD_DSL_ALLOCATIONS.values())


@pytest.mark.unit
def test_constants_are_immutable():
    """Verify constants can't be accidentally reassigned (not enforced but documented)."""
    from the_alchemiser.shared.config import strategy_profiles

    # Constants should be module-level attributes
    assert hasattr(strategy_profiles, "STRATEGY_KMLM")
    assert hasattr(strategy_profiles, "DEV_DSL_FILES")
    assert hasattr(strategy_profiles, "DEV_DSL_ALLOCATIONS")
    assert hasattr(strategy_profiles, "PROD_DSL_FILES")
    assert hasattr(strategy_profiles, "PROD_DSL_ALLOCATIONS")

    # Note: Python doesn't enforce constant immutability at module level
    # This test just verifies they exist and are accessible


@pytest.mark.unit
def test_consistency_with_json_config_dev():
    """Verify Python constants are consistent with dev JSON config."""
    import json
    from importlib import resources as importlib_resources

    from the_alchemiser.shared.config.strategy_profiles import (
        DEV_DSL_ALLOCATIONS,
        DEV_DSL_FILES,
    )

    # Load dev JSON config
    pkg_files = importlib_resources.files("the_alchemiser.config")
    with pkg_files.joinpath("strategy.dev.json").open("r", encoding="utf-8") as f:
        json_config = json.load(f)

    # Files should match
    assert set(DEV_DSL_FILES) == set(json_config["files"])

    # Allocations should match
    assert json_config["allocations"] == DEV_DSL_ALLOCATIONS


@pytest.mark.unit
def test_consistency_with_json_config_prod():
    """Verify Python constants are consistent with prod JSON config."""
    import json
    from importlib import resources as importlib_resources

    from the_alchemiser.shared.config.strategy_profiles import (
        PROD_DSL_ALLOCATIONS,
        PROD_DSL_FILES,
    )

    # Load prod JSON config
    pkg_files = importlib_resources.files("the_alchemiser.config")
    with pkg_files.joinpath("strategy.prod.json").open("r", encoding="utf-8") as f:
        json_config = json.load(f)

    # Files should match
    assert set(PROD_DSL_FILES) == set(json_config["files"])

    # Allocations should match
    assert json_config["allocations"] == PROD_DSL_ALLOCATIONS
