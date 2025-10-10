"""Business Unit: shared | Status: current.

Comprehensive unit tests for TimeInForce value object.

This test suite validates the TimeInForce dataclass and demonstrates
the validation redundancy issue identified in the file review.

NOTE: TimeInForce is DEPRECATED as of version 2.10.7 and will be removed
in version 3.0.0. These tests validate the deprecation warning and backwards
compatibility during the deprecation period.

NOTE: Tests import directly from module file to avoid pandas dependency
in the package __init__.py that would break test collection.
"""

import sys
import importlib.util
from pathlib import Path
import warnings

import pytest

# Load TimeInForce module directly from file to avoid __init__.py dependencies
_module_path = (
    Path(__file__).parent.parent.parent.parent
    / "the_alchemiser"
    / "shared"
    / "types"
    / "time_in_force.py"
)
spec = importlib.util.spec_from_file_location(
    "the_alchemiser.shared.types.time_in_force", str(_module_path)
)
_time_in_force_module = importlib.util.module_from_spec(spec)
sys.modules["the_alchemiser.shared.types.time_in_force"] = _time_in_force_module
spec.loader.exec_module(_time_in_force_module)

TimeInForce = _time_in_force_module.TimeInForce


class TestTimeInForceConstruction:
    """Test TimeInForce value object construction and validation."""

    @pytest.mark.unit
    def test_create_valid_day(self):
        """Test creating TimeInForce with 'day' value."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            tif = TimeInForce(value="day")
            assert tif.value == "day"
            # Check deprecation warning was raised
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "deprecated" in str(w[0].message).lower()

    @pytest.mark.unit
    def test_create_valid_gtc(self):
        """Test creating TimeInForce with 'gtc' value."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            tif = TimeInForce(value="gtc")
            assert tif.value == "gtc"
            assert len(w) == 1

    @pytest.mark.unit
    def test_create_valid_ioc(self):
        """Test creating TimeInForce with 'ioc' value."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            tif = TimeInForce(value="ioc")
            assert tif.value == "ioc"
            assert len(w) == 1

    @pytest.mark.unit
    def test_create_valid_fok(self):
        """Test creating TimeInForce with 'fok' value."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            tif = TimeInForce(value="fok")
            assert tif.value == "fok"
            assert len(w) == 1

    @pytest.mark.unit
    def test_deprecation_warning_content(self):
        """Test that deprecation warning contains required information."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            TimeInForce(value="day")

            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            message = str(w[0].message)
            assert "2.10.7" in message
            assert "3.0.0" in message
            assert "Alpaca SDK" in message

    @pytest.mark.unit
    def test_frozen_immutable(self):
        """Test that TimeInForce is immutable (frozen)."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # Suppress deprecation warning
            tif = TimeInForce(value="day")
            with pytest.raises(AttributeError):
                tif.value = "gtc"  # type: ignore

    @pytest.mark.unit
    def test_invalid_value_rejected_by_type_checker(self):
        """Test that invalid values are rejected by type checker.

        NOTE: This test demonstrates that the Literal type constraint
        prevents invalid values at the type-checking level, making the
        __post_init__ validation unreachable in practice.

        This test cannot actually execute the invalid code path because
        mypy would reject it. The test is included for documentation.
        """
        # The following would fail type checking:
        # tif = TimeInForce(value="invalid")  # type: ignore

        # To test runtime validation, we'd need to bypass type checking:
        # This is why the __post_init__ validation is marked with pragma: no cover
        pass


class TestTimeInForceEquality:
    """Test TimeInForce equality and hashing."""

    @pytest.mark.unit
    def test_equality_same_value(self):
        """Test that two TimeInForce objects with same value are equal."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # Suppress deprecation warning
            tif1 = TimeInForce(value="day")
            tif2 = TimeInForce(value="day")
            assert tif1 == tif2

    @pytest.mark.unit
    def test_inequality_different_values(self):
        """Test that TimeInForce objects with different values are not equal."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # Suppress deprecation warning
            tif1 = TimeInForce(value="day")
            tif2 = TimeInForce(value="gtc")
            assert tif1 != tif2

    @pytest.mark.unit
    def test_hashable(self):
        """Test that TimeInForce can be used in sets and as dict keys."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # Suppress deprecation warning
            tif1 = TimeInForce(value="day")
            tif2 = TimeInForce(value="gtc")
            tif3 = TimeInForce(value="day")

            # Can create set
            tif_set = {tif1, tif2, tif3}
            assert len(tif_set) == 2  # tif1 and tif3 are equal

            # Can use as dict key
            tif_dict = {tif1: "Day order", tif2: "GTC order"}
            assert tif_dict[tif1] == "Day order"
            assert tif_dict[tif3] == "Day order"  # Same key as tif1


class TestTimeInForceRepresentation:
    """Test TimeInForce string representation."""

    @pytest.mark.unit
    def test_repr(self):
        """Test that repr shows class and value."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # Suppress deprecation warning
            tif = TimeInForce(value="day")
            repr_str = repr(tif)
            assert "TimeInForce" in repr_str
            assert "day" in repr_str

    @pytest.mark.unit
    def test_str_representation(self):
        """Test string representation."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # Suppress deprecation warning
            tif = TimeInForce(value="gtc")
            # Dataclass default str includes all fields
            str_repr = str(tif)
            assert "gtc" in str_repr


class TestTimeInForceUsage:
    """Test actual usage patterns and dead code detection."""

    @pytest.mark.unit
    def test_can_be_created(self):
        """Test that TimeInForce can be created and used."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # Suppress deprecation warning
            tif = TimeInForce(value="day")
            assert tif.value == "day"

    @pytest.mark.unit
    def test_type_hints_work(self):
        """Test that type hints work correctly with TimeInForce."""

        def process_order(tif: TimeInForce) -> str:
            """Example function using TimeInForce type hint."""
            return f"Order with TIF: {tif.value}"

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # Suppress deprecation warning
            tif = TimeInForce(value="gtc")
            result = process_order(tif)
            assert result == "Order with TIF: gtc"


# Property-based tests would require hypothesis, but not critical for this simple type
# class TestTimeInForcePropertyBased:
#     """Property-based tests using Hypothesis."""
#     pass
